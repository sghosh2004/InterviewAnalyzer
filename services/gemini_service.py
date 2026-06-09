import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

try:
    from google import genai
except Exception:  # pragma: no cover
    genai = None

try:
    import google.generativeai as legacy_genai
except Exception:  # pragma: no cover
    legacy_genai = None


def _load_env_file(env_path: Optional[str] = None) -> None:
    path = Path(env_path or ".env")
    if not path.exists():
        return

    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, raw_value = line.split("=", 1)
        key = key.strip()
        value = raw_value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_env_file()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
DEFAULT_GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
DEFAULT_MAX_OUTPUT_TOKENS = int(os.environ.get("GEMINI_MAX_OUTPUT_TOKENS", "800"))
DEFAULT_MAX_ATTEMPTS = int(os.environ.get("GEMINI_MAX_ATTEMPTS", "4"))
DEFAULT_API_TIMEOUT = int(os.environ.get("GEMINI_API_TIMEOUT", "60"))


def _configure_gemini_client() -> Any:
    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured. Please set GEMINI_API_KEY in your .env file."
        )

    # Prefer new google-genai if available
    if genai is not None:
        # The new SDK exposes a simple configuration; create a client-like wrapper
        try:
            return genai.Client(api_key=GEMINI_API_KEY)
        except Exception:
            # Some versions of genai expose top-level helpers instead of Client
            return genai

    if legacy_genai is not None:
        legacy_genai.configure(api_key=GEMINI_API_KEY)
        logger.warning(
            "Using deprecated google.generativeai package. Consider upgrading to google-genai."
        )
        return legacy_genai

    raise ImportError(
        "No Gemini client is installed. Install `google-genai` or `google-generative-ai`."
    )


def _build_resume_prompt(resume_text: str) -> str:
    return (
        "You are an HR analytics assistant. Analyze the resume text and return ONLY a valid JSON object. "
        "NO markdown, explanations, or extra text.\n\n"
        "Return exactly this schema:\n"
        "{\n"
        "  \"candidate_name\": \"\",\n"
        "  \"ats_score\": 0,\n"
        "  \"skills\": [],\n"
        "  \"experience\": \"\",\n"
        "  \"education\": [],\n"
        "  \"recommendations\": []\n"
        "}\n\n"
        "For recommendations: provide 3-4 specific improvements (not 5). Keep each under 120 chars.\n"
        "If missing: return empty string or list.\n\n"
        "Resume:\n"
        + resume_text.strip()[:3000]  # Limit input to first 3000 chars to save tokens
    )


def _build_response_schema() -> Dict[str, Any]:
    return {
        "type": "OBJECT",
        "properties": {
            "candidate_name": {"type": "STRING"},
            "ats_score": {"type": "NUMBER"},
            "skills": {"type": "ARRAY", "items": {"type": "STRING"}},
            "experience": {"type": "STRING"},
            "education": {"type": "ARRAY", "items": {"type": "STRING"}},
            "recommendations": {"type": "ARRAY", "items": {"type": "STRING"}},
        },
        "required": [
            "candidate_name",
            "ats_score",
            "skills",
            "experience",
            "education",
            "recommendations",
        ],
    }


def _clean_json_text(raw_text: str) -> str:
    cleaned = raw_text.strip()
    cleaned = re.sub(r"```(?:json)?", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\r\n", "\n", cleaned)
    cleaned = re.sub(r"\n```", "", cleaned)

    # Locate outer-most JSON object by braces
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1:
        # If no braces found, try to find a JSON-like substring using regex
        m = re.search(r"(\{[\s\S]*\})", cleaned)
        if m:
            json_text = m.group(1)
        else:
            logger.error("Response text that failed to parse: %s", raw_text[:2000])
            raise ValueError(
                f"Unable to locate a JSON object in Gemini response. "
                f"Response was: {raw_text[:500]!r}"
            )
    else:
        json_text = cleaned[start : end + 1]

    # Remove common markdown/formatting artifacts and trailing commas
    json_text = re.sub(r",(\s*[}\]])", r"\1", json_text)

    # Repair common issues: unbalanced quotes or brackets and unterminated strings
    def _repair_text(s: str) -> str:
        # Remove control characters that may break JSON
        s = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", s)

        # Count double quotes; if odd, try appending a closing quote before final brace
        if s.count('"') % 2 == 1:
            # insert a closing quote before the last closing brace if plausible
            last_brace = s.rfind('}')
            if last_brace != -1:
                s = s[:last_brace] + '"' + s[last_brace:]
            else:
                s = s + '"'

        # Ensure brackets are balanced: attempt to close any unbalanced arrays/objects
        opens = s.count('{') - s.count('}')
        if opens > 0:
            s = s + ("}" * opens)
        opens_arr = s.count('[') - s.count(']')
        if opens_arr > 0:
            s = s + ("]" * opens_arr)

        return s

    repaired = _repair_text(json_text)

    return repaired


def _extract_response_text(response: Any) -> str:
    if response is None:
        logger.error("Response is None")
        return ""

    logger.info("Response type: %s", type(response).__name__)
    
    if isinstance(response, str):
        logger.info("Response is string")
        return response.strip()

    # Check for response schema output (new SDK)
    if hasattr(response, "parsed") and response.parsed is not None:
        logger.info("Found parsed attribute")
        parsed = response.parsed
        if isinstance(parsed, dict):
            logger.info("Parsed is dict: %s", list(parsed.keys()))
            return json.dumps(parsed)
        elif isinstance(parsed, str):
            return parsed.strip()

    if hasattr(response, "text") and isinstance(response.text, str):
        logger.info("Found text attribute: %s chars", len(response.text))
        return response.text.strip()

    # Try common response attributes
    for attr in ("content", "result", "output"):
        value = getattr(response, attr, None)
        if isinstance(value, str) and value.strip():
            logger.info("Found %s attribute: %s chars", attr, len(value))
            return value.strip()

    # Handle outputs array (legacy SDK)
    if hasattr(response, "outputs"):
        outputs = getattr(response, "outputs")
        logger.info("Found outputs array with %s items", len(outputs) if outputs else 0)
        if outputs:
            first_output = outputs[0]
            if isinstance(first_output, dict):
                content = first_output.get("content")
            else:
                content = getattr(first_output, "content", None)
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict):
                        text = item.get("text")
                    else:
                        text = getattr(item, "text", None)
                    if isinstance(text, str) and text.strip():
                        logger.info("Found text in outputs: %s chars", len(text))
                        return text.strip()
            elif isinstance(content, str) and content.strip():
                logger.info("Found content string: %s chars", len(content))
                return content.strip()

    if hasattr(response, "output"):
        output = getattr(response, "output")
        if isinstance(output, str) and output.strip():
            logger.info("Found output attribute: %s chars", len(output))
            return output.strip()

    # Log all attributes for debugging
    logger.warning("Could not extract text. Response attributes: %s", dir(response))
    return ""


def _parse_json_response(raw_text: str) -> Dict[str, Any]:
    if not raw_text or not raw_text.strip():
        raise ValueError("Gemini returned an empty response.")

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        # Try to clean and repair the text before a second parse attempt
        cleaned = _clean_json_text(raw_text)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            # As a last resort, try truncating after the last closing brace and parse again
            last_end = cleaned.rfind('}')
            if last_end != -1:
                truncated = cleaned[: last_end + 1]
                try:
                    return json.loads(truncated)
                except json.JSONDecodeError:
                    pass

            logger.error("Failed to parse Gemini JSON. Raw snippet: %s", raw_text[:1000])
            raise ValueError(
                "Gemini response could not be parsed as valid JSON. "
                f"Raw response snippet: {raw_text[:400]!r}"
            ) from exc


def _normalize_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        items = re.split(r"[\n,]+", value)
        return [item.strip() for item in items if item.strip()]
    return []


def _normalize_score(value: Any) -> int:
    if isinstance(value, (int, float)):
        return max(0, min(100, int(value)))
    if isinstance(value, str):
        digits = re.findall(r"\d+", value)
        if digits:
            return max(0, min(100, int(digits[0])))
    return 0


def _normalize_profile(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "candidate_name": str(profile.get("candidate_name", "")).strip(),
        "ats_score": _normalize_score(profile.get("ats_score", 0)),
        "skills": _normalize_list(profile.get("skills", [])),
        "experience": str(profile.get("experience", "")).strip(),
        "education": _normalize_list(profile.get("education", [])),
        "recommendations": _normalize_list(profile.get("recommendations", [])),
    }


def _call_gemini_api_with_timeout(client: Any, model_name: str, prompt: str) -> Any:
    """Call Gemini API with a timeout to prevent hanging."""
    def _api_call():
        # Preferred path: new google-genai SDK
        if genai is not None:
            logger.info("Attempting genai client generation methods")
            # Try models.generate_content (most reliable with schema)
            if hasattr(client, "models") and hasattr(client.models, "generate_content"):
                logger.info("Using models.generate_content with response schema")
                try:
                    return client.models.generate_content(
                        model=model_name,
                        contents=[prompt],
                        config={
                            "temperature": 0.0,
                            "maxOutputTokens": DEFAULT_MAX_OUTPUT_TOKENS,
                            "responseMimeType": "application/json",
                            "responseSchema": _build_response_schema(),
                        },
                    )
                except Exception as e:
                    logger.warning("Schema-based call failed, retrying without schema: %s", e)
                    return client.models.generate_content(
                        model=model_name,
                        contents=[prompt],
                        config={
                            "temperature": 0.0,
                            "maxOutputTokens": DEFAULT_MAX_OUTPUT_TOKENS,
                        },
                    )
            # Try responses.create
            elif hasattr(client, "responses") and hasattr(client.responses, "create"):
                logger.info("Using responses.create")
                try:
                    return client.responses.create(
                        model=model_name,
                        contents=prompt,
                        config={
                            "temperature": 0.0,
                            "maxOutputTokens": DEFAULT_MAX_OUTPUT_TOKENS,
                            "responseMimeType": "application/json",
                            "responseSchema": _build_response_schema(),
                        },
                    )
                except Exception as e:
                    logger.warning("Schema-based responses.create failed: %s", e)
                    return client.responses.create(
                        model=model_name,
                        contents=prompt,
                    )
            # Try generate_text
            elif hasattr(client, "generate_text"):
                logger.info("Using generate_text")
                return client.generate_text(
                    model=model_name,
                    prompt=prompt,
                    temperature=0.0,
                    max_output_tokens=DEFAULT_MAX_OUTPUT_TOKENS,
                )
            else:
                raise RuntimeError(
                    "genai client does not expose supported generation methods."
                )

        # Legacy google.generativeai SDK
        elif legacy_genai is not None and client is legacy_genai:
            logger.info("Using legacy google.generativeai client")
            model_obj = legacy_genai.GenerativeModel(
                model_name=model_name,
                generation_config=legacy_genai.types.GenerationConfig(
                    temperature=0.0,
                    max_output_tokens=DEFAULT_MAX_OUTPUT_TOKENS,
                    response_mime_type="application/json",
                    response_schema=_build_response_schema(),
                ),
            )
            logger.info("Created GenerativeModel: %s", model_obj)
            return model_obj.generate_content(contents=[prompt])

        # Fallback: try generate_text if available
        else:
            if hasattr(client, "generate_text"):
                logger.info("Using fallback generate_text")
                return client.generate_text(
                    model=model_name,
                    prompt=prompt,
                    temperature=0.0,
                    max_output_tokens=DEFAULT_MAX_OUTPUT_TOKENS,
                )
            else:
                raise RuntimeError(
                    "Configured Gemini client does not provide a supported generation method."
                )
    
    # Execute the API call with a timeout
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_api_call)
        try:
            response = future.result(timeout=DEFAULT_API_TIMEOUT)
            logger.info("Gemini API call completed successfully")
            return response
        except FutureTimeoutError:
            logger.error("Gemini API call timed out after %s seconds", DEFAULT_API_TIMEOUT)
            raise TimeoutError(
                f"Gemini API call timed out after {DEFAULT_API_TIMEOUT} seconds. "
                "The API may be overloaded or unresponsive."
            ) from None


def generate_candidate_profile(resume_text: str, model: Optional[str] = None) -> Dict[str, Any]:
    """Generate a normalized candidate profile from raw resume text using Gemini."""
    if not resume_text or not resume_text.strip():
        raise ValueError("resume_text must contain the resume content.")

    client = _configure_gemini_client()
    model_name = model or DEFAULT_GEMINI_MODEL
    prompt = _build_resume_prompt(resume_text)

    logger.info("Configured Gemini client. Using model: %s", model_name)
    logger.info("GEMINI_API_KEY set: %s", bool(GEMINI_API_KEY))
    logger.info("Client type: %s", type(client).__name__)
    logger.info("API timeout: %s seconds", DEFAULT_API_TIMEOUT)
    
    # Wrap the generation call with retries for transient errors (503, timeouts, etc.)
    max_attempts = DEFAULT_MAX_ATTEMPTS
    backoff = 1.0
    response = None
    last_exc = None

    for attempt in range(1, max_attempts + 1):
        try:
            logger.info("Starting Gemini API call (attempt %s/%s)...", attempt, max_attempts)
            response = _call_gemini_api_with_timeout(client, model_name, prompt)

            # If we got here, generation succeeded; break out of retry loop
            last_exc = None
            break

        except Exception as exc:
            last_exc = exc
            logger.exception("Gemini text generation attempt %s failed: %s", attempt, exc)
            # Inspect message to decide whether to retry
            msg = str(exc)
            if any(code in msg for code in ("API key not valid", "API_KEY_INVALID", "UNAUTHENTICATED", "401")):
                # unrecoverable auth error
                raise RuntimeError(
                    "Gemini API key is invalid or not authorized. \n"
                    "Update GEMINI_API_KEY in your .env with a valid key from https://aistudio.google.com/app/apikey"
                ) from exc

            # If final attempt, raise detailed error
            if attempt == max_attempts:
                raise RuntimeError(f"Gemini text generation failed after {max_attempts} attempts: {exc}") from exc

            # Try to extract a recommended retry delay from the exception (RetryInfo)
            retry_seconds = None

            # Helper: recursively search for retryDelay in a JSON-like structure
            def _search_retry(obj):
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        if isinstance(k, str) and "retry" in k.lower() and isinstance(v, str):
                            m = re.search(r"(\d+(?:\.\d+)?)s", v)
                            if m:
                                return float(m.group(1))
                        found = _search_retry(v)
                        if found:
                            return found
                elif isinstance(obj, list):
                    for item in obj:
                        found = _search_retry(item)
                        if found:
                            return found
                return None

            # Try structured attributes on the exception
            try:
                # Some google-genai errors include a response_json-like attribute
                resp_json = None
                if hasattr(exc, "response") and exc.response is not None:
                    try:
                        resp_json = exc.response.json()
                    except Exception:
                        resp_json = None

                if resp_json:
                    retry_seconds = _search_retry(resp_json)
                else:
                    # Try to search exc.args for embedded dicts
                    for arg in getattr(exc, "args", []) or []:
                        try:
                            if isinstance(arg, (str, bytes)):
                                text = arg.decode() if isinstance(arg, bytes) else arg
                                m = re.search(r"retryDelay\W*[:=]\W*['\"]?(\d+(?:\.\d+)?)s", text)
                                if m:
                                    retry_seconds = float(m.group(1))
                                    break
                        except Exception:
                            continue
            except Exception:
                retry_seconds = None

            # Fallback: attempt to parse retryDelay from the exception string
            if retry_seconds is None:
                m = re.search(r"retryDelay\W*[:=]\W*['\"]?(\d+(?:\.\d+)?)s", msg)
                if m:
                    retry_seconds = float(m.group(1))

            # If we found a recommended delay, respect it (but cap to a reasonable maximum)
            if retry_seconds is not None:
                sleep_time = min(max(retry_seconds, 1.0), 120.0)
                logger.info(
                    "Gemini returned RetryInfo recommending %s seconds; sleeping %s seconds before retrying",
                    retry_seconds,
                    sleep_time,
                )
                time.sleep(sleep_time)
            else:
                # Otherwise wait with exponential backoff and retry
                time.sleep(backoff)
                backoff *= 2

    raw_text = _extract_response_text(response)
    logger.info("Extracted response text length: %s", len(raw_text) if raw_text else 0)
    
    if not raw_text:
        logger.error("No text extracted from Gemini response. Response object: %s", response)
        raise RuntimeError("Gemini returned an empty response.")

    logger.debug("Raw Gemini response (first 500 chars): %s", raw_text[:500])
    profile = _parse_json_response(raw_text)
    normalized = _normalize_profile(profile)
    logger.info("Parsed and normalized Gemini profile: %s", normalized)
    return normalized
