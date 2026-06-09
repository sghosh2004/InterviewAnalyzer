import traceback
from services.gemini_service import (
    _configure_gemini_client,
    DEFAULT_GEMINI_MODEL,
    _build_resume_prompt,
    _extract_response_text,
)

sample_resume = '''John Doe

Experienced Software Engineer with 5 years of experience in Python, Flask, and cloud deployments. Proven track record building scalable REST APIs and working with PostgreSQL and Redis. Led a small team of developers to deliver features on schedule. Skilled in unit testing, CI/CD, Docker, and AWS.

Education:
B.S. in Computer Science

Work Experience:
Software Engineer at Acme Corp (2019-2023): Developed backend services, improved system performance by 30%.
Junior Developer at WebStart (2017-2019): Assisted in frontend and backend development.

Skills: Python, Flask, SQL, PostgreSQL, Redis, Docker, AWS, Kubernetes, REST APIs, Testing, CI/CD, Leadership

'''

try:
    client = _configure_gemini_client()
    model_name = DEFAULT_GEMINI_MODEL
    prompt = _build_resume_prompt(sample_resume)
    print('Using model:', model_name)

    response = None
    if hasattr(client, 'responses') and hasattr(client.responses, 'create'):
        response = client.responses.create(model=model_name, input=prompt, temperature=0.0, max_output_tokens=800)
    elif hasattr(client, 'models') and hasattr(client.models, 'generate_content'):
        response = client.models.generate_content(model=model_name, contents=[prompt], config={"temperature":0.0, "maxOutputTokens":800})
    elif hasattr(client, 'generate_text'):
        response = client.generate_text(model=model_name, prompt=prompt, temperature=0.0, max_output_tokens=800)
    else:
        raise RuntimeError('No supported client method found')

    print('Response object type:', type(response))
    try:
        raw = _extract_response_text(response)
        print('---- RAW RESPONSE START ----')
        print(repr(raw))
        print('---- RAW RESPONSE END ----')
    except Exception as e:
        print('Failed to extract text:', e)
        traceback.print_exc()

except Exception as e:
    traceback.print_exc()
    print('ERROR:', e)
