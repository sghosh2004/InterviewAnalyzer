import json
import logging
import textwrap
import time
import urllib.parse
import re
from io import BytesIO

import streamlit as st
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from services.document_service import build_document_record, extract_text_from_pdf
from services.gemini_service import generate_candidate_profile

st.set_page_config(page_title="Resume Analyzer", layout="wide")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

MAX_UPLOAD_SIZE = 10 * 1024 * 1024


def show_toast(message: str, level: str = "info") -> None:
    if hasattr(st, "toast"):
        st.toast(message)
        return

    if level == "success":
        st.success(message)
    elif level == "warning":
        st.warning(message)
    elif level == "error":
        st.error(message)
    else:
        st.info(message)


def add_debug(message: str) -> None:
    logger.debug(message)
    if "debug_messages" not in st.session_state:
        st.session_state.debug_messages = []
    st.session_state.debug_messages.append(message)


def build_export_report(profile: dict, document_record: dict | None = None) -> str:
    lines = [
        "Resume Analyzer Report",
        "========================",
        f"Candidate Name: {profile.get('candidate_name', '')}",
        f"ATS Score: {profile.get('ats_score', '')}",
        "",
        "Skills:",
    ]
    for skill in profile.get("skills", []):
        lines.append(f"- {skill}")

    lines.extend([
        "",
        "Experience:",
        profile.get("experience", ""),
        "",
        "Education:",
    ])
    for edu in profile.get("education", []):
        lines.append(f"- {edu}")

    lines.extend([
        "",
        "Recommendations:",
    ])
    for rec in profile.get("recommendations", []):
        lines.append(f"- {rec}")

    if document_record and document_record.get("extracted_text"):
        lines.extend([
            "",
            "Extracted Resume Text:",
            document_record.get("extracted_text", ""),
        ])

    return "\n".join(lines)


def build_export_pdf(profile: dict, document_record: dict | None = None) -> bytes:
    buffer = BytesIO()
    page_width, page_height = letter
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setFont("Helvetica", 11)

    text_lines = [
        "Resume Analyzer Report",
        "========================",
        f"Candidate Name: {profile.get('candidate_name', '')}",
        f"ATS Score: {profile.get('ats_score', '')}",
        "",
        "Skills:",
    ]
    for skill in profile.get("skills", []):
        text_lines.append(f"- {skill}")

    text_lines.extend([
        "",
        "Experience:",
        profile.get("experience", ""),
        "",
        "Education:",
    ])
    for edu in profile.get("education", []):
        text_lines.append(f"- {edu}")

    text_lines.extend([
        "",
        "Recommendations:",
    ])
    for rec in profile.get("recommendations", []):
        text_lines.append(f"- {rec}")

    if document_record and document_record.get("extracted_text"):
        text_lines.extend([
            "",
            "Extracted Resume Text:",
            document_record.get("extracted_text", ""),
        ])

    margin = 72
    y = page_height - margin
    line_height = 14
    for raw_line in text_lines:
        wrapped = textwrap.wrap(raw_line, width=90) or [""]
        for line in wrapped:
            if y < margin + line_height:
                pdf.showPage()
                pdf.setFont("Helvetica", 11)
                y = page_height - margin
            pdf.drawString(margin, y, line)
            y -= line_height

    pdf.save()
    buffer.seek(0)
    return buffer.getvalue()


def build_export_filename(profile: dict) -> str:
    name = profile.get("candidate_name") or "resume_analysis"
    safe_name = "_".join(str(name).strip().split())
    return f"{safe_name}_report.pdf"


def build_share_text(profile: dict, document_record: dict | None = None) -> str:
    lines = [
        f"Resume Analyzer Report for {profile.get('candidate_name', 'Candidate')}",
        f"ATS Score: {profile.get('ats_score', 'N/A')}",
        "",
        "Skills:",
    ]
    for skill in profile.get("skills", []):
        lines.append(f"- {skill}")

    if profile.get("experience"):
        lines.extend(["", "Experience:", profile.get("experience", "")])

    if profile.get("education"):
        lines.extend(["", "Education:"])
        for edu in profile.get("education", []):
            lines.append(f"- {edu}")

    if profile.get("recommendations"):
        lines.extend(["", "Recommendations:"])
        for rec in profile.get("recommendations", []):
            lines.append(f"- {rec}")

    if document_record and document_record.get("extracted_text"):
        lines.extend([
            "",
            "Extracted Resume Text:",
            document_record.get("extracted_text", ""),
        ])

    return "\n".join(lines)


def build_email_share_link(profile: dict, document_record: dict | None = None) -> str:
    subject = f"Resume Analysis Report: {profile.get('candidate_name', 'Candidate')}"
    body = build_share_text(profile, document_record)
    return "mailto:?subject={}&body={}".format(
        urllib.parse.quote(subject),
        urllib.parse.quote(body),
    )


def build_whatsapp_share_link(profile: dict, document_record: dict | None = None) -> str:
    text = build_share_text(profile, document_record)
    return "https://api.whatsapp.com/send?text={}".format(urllib.parse.quote(text))


def validate_upload(uploaded_file) -> str:
    if uploaded_file is None:
        return ""
    if not uploaded_file.name.lower().endswith(".pdf"):
        return "Only PDF resumes are supported."
    if getattr(uploaded_file, "size", 0) > MAX_UPLOAD_SIZE:
        return "The uploaded file exceeds the 10MB maximum size limit."
    return ""


# Styling
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    :root {
        color-scheme: light;
        font-family: 'Inter', sans-serif;
    }
    body {
        background: linear-gradient(180deg, #f2f7fb 0%, #eef4f9 100%);
    }
    .app-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1.15rem 0.5rem 1rem;
        margin-bottom: 1.5rem;
    }
    .brand {
        display: flex;
        flex-direction: column;
        gap: 0.12rem;
    }
    .brand-title {
        font-size: 1.55rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.03em;
        color: #0f172a;
    }
    .brand-subtitle {
        color: #64748b;
        font-size: 0.95rem;
        margin: 0;
    }
    .nav-items {
        display: flex;
        gap: 1.5rem;
        align-items: center;
        font-size: 0.98rem;
    }
    .nav-item {
        color: #475569;
        text-decoration: none;
        padding: 0.45rem 0.6rem;
        border-radius: 999px;
        transition: all 0.2s ease;
    }
    .nav-item:hover {
        color: #0f172a;
        background: rgba(15, 118, 110, 0.08);
    }
    .nav-item.active {
        color: #0f172a;
        font-weight: 700;
        background: rgba(15, 118, 110, 0.14);
        box-shadow: inset 0 0 0 1px rgba(15, 118, 110, 0.16);
    }
    .nav-item.disabled {
        color: #94a3b8;
        cursor: not-allowed;
        background: transparent;
    }
    .nav-item.disabled:hover {
        color: #94a3b8;
        background: transparent;
    }
    .user-actions {
        display: flex;
        align-items: center;
        gap: 1rem;
        justify-content: flex-end;
    }
    .user-actions span {
        font-size: 1.2rem;
        color: #334155;
        cursor: pointer;
    }
    .user-avatar {
        background-color: #0f766e;
        color: #ffffff;
        border-radius: 50%;
        width: 2.6rem;
        height: 2.6rem;
        display: grid;
        place-items: center;
        font-weight: 700;
        box-shadow: 0 12px 30px rgba(15, 118, 110, 0.18);
    }
    .dashboard-card {
        background: #ffffff;
        border: 1px solid rgba(148, 163, 184, 0.18);
        border-radius: 28px;
        padding: 1.6rem;
        box-shadow: 0 28px 70px rgba(15, 23, 42, 0.06);
        margin-bottom: 1.3rem;
    }
    .section-title {
        font-size: 1.1rem;
        font-weight: 800;
        margin-bottom: 1.2rem;
        color: #0f172a;
    }
    .upload-dropzone {
        border: 1px dashed rgba(99, 102, 241, 0.35);
        border-radius: 24px;
        padding: 2.4rem 1.4rem;
        text-align: center;
        color: #334155;
        background: linear-gradient(180deg, rgba(241, 245, 249, 0.95), #ffffff);
        transition: transform 0.25s ease, box-shadow 0.25s ease;
    }
    .upload-dropzone:hover {
        transform: translateY(-2px);
        box-shadow: 0 18px 40px rgba(15, 23, 42, 0.08);
    }
    .upload-dropzone div {
        max-width: 24rem;
        margin: 0 auto;
    }
    .upload-button {
        margin-top: 1rem;
        padding: 0.85rem 1.6rem;
        border-radius: 999px;
        background-color: #0f766e;
        color: #ffffff;
        text-decoration: none;
        display: inline-block;
        font-weight: 700;
        letter-spacing: 0.01em;
        box-shadow: 0 18px 30px rgba(15, 118, 110, 0.18);
    }
    .metric-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 1rem;
        margin-bottom: 1rem;
        min-height: 3rem;
    }
    .metric-info {
        min-width: 11rem;
        color: #475569;
        font-size: 0.95rem;
        font-weight: 600;
    }
    .progress-wrap {
        width: 100%;
        border-radius: 999px;
        background: #e2e8f0;
        height: 0.95rem;
        overflow: hidden;
        box-shadow: inset 0 1px 2px rgba(15, 23, 42, 0.08);
    }
    .progress-bar {
        height: 100%;
        border-radius: 999px;
        transition: width 0.4s ease;
    }
    .progress-green { background: linear-gradient(90deg, #14b8a6, #0f766e); }
    .progress-yellow { background: linear-gradient(90deg, #f97316, #f59e0b); }
    .small-note {
        color: #64748b;
        font-size: 0.9rem;
    }
    .tag-grid {
        display: flex;
        flex-wrap: wrap;
        gap: 0.65rem;
        margin-bottom: 1rem;
    }
    .tag-pill {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 0.65rem 0.95rem;
        border-radius: 999px;
        font-size: 0.87rem;
        font-weight: 700;
    }
    .tag-technical { background: rgba(16, 185, 129, 0.12); color: #0f766e; }
    .tag-soft { background: rgba(59, 130, 246, 0.12); color: #1d4ed8; }
    .report-actions {
        display: flex;
        gap: 0.8rem;
        justify-content: flex-end;
        flex-wrap: wrap;
        margin-bottom: 1.4rem;
    }
    .action-button {
        border-radius: 50%;
        width: 3.5rem;
        height: 3.5rem;
        border: 1px solid transparent;
        font-size: 1.5rem;
        cursor: pointer;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        text-decoration: none;
    }
    .action-button:hover {
        transform: translateY(-2px);
    }
    .btn-export {
        background: linear-gradient(90deg, #10b981, #08967e);
        color: #ffffff;
        border-color: transparent;
        box-shadow: 0 18px 30px rgba(16, 185, 129, 0.18);
    }
    .btn-export:hover {
        box-shadow: 0 20px 36px rgba(16, 185, 129, 0.24);
    }
    .btn-share {
        background: linear-gradient(90deg, #10b981, #08967e);
        color: #ffffff;
        border-color: transparent;
        box-shadow: 0 18px 30px rgba(16, 185, 129, 0.18);
    }
    .btn-share:hover {
        box-shadow: 0 20px 36px rgba(16, 185, 129, 0.24);
    }
    .stDownloadButton button {
        width: 3.5rem !important;
        height: 3.5rem !important;
        min-width: 3.5rem !important;
        min-height: 3.5rem !important;
        padding: 0 !important;
        border-radius: 50% !important;
        background: linear-gradient(90deg, #10b981, #08967e) !important;
        color: #ffffff !important;
        border: 1px solid transparent !important;
        box-shadow: 0 18px 30px rgba(16, 185, 129, 0.18) !important;
        font-size: 1.5rem !important;
        font-weight: 400 !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease !important;
        cursor: pointer !important;
    }
    .stDownloadButton button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 20px 36px rgba(16, 185, 129, 0.24) !important;
    }
    .circle-score {
        width: 7rem;
        height: 7rem;
        border-radius: 50%;
        border: 10px solid rgba(16, 185, 129, 0.18);
        display: grid;
        place-items: center;
        font-size: 2.2rem;
        font-weight: 800;
        color: #064e3b;
        margin: 0 auto 0.9rem;
        background: radial-gradient(circle at top left, rgba(79, 70, 229, 0.08), transparent 40%);
    }
    .sub-metric-list {
        list-style: none;
        padding: 0;
        margin: 0;
        color: #475569;
        font-size: 0.95rem;
    }
    .sub-metric-list li {
        display: flex;
        justify-content: space-between;
        padding: 0.85rem 0;
        border-bottom: 1px solid rgba(148, 163, 184, 0.18);
    }
    .sub-metric-list li:last-child { border-bottom: none; }
    .recent-item {
        border-radius: 20px;
        padding: 1rem 1rem;
        background: #f8fbff;
        margin-bottom: 0.9rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 1rem;
        border: 1px solid rgba(59, 130, 246, 0.12);
    }
    .recent-item-title {
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 0.25rem;
    }
    .recent-meta {
        color: #64748b;
        font-size: 0.9rem;
    }
    .recent-score {
        background: rgba(16, 185, 129, 0.14);
        color: #0f766e;
        border-radius: 999px;
        padding: 0.5rem 0.95rem;
        font-weight: 800;
        min-width: 4.5rem;
        text-align: center;
    }
    .view-all {
        color: #0f766e;
        font-weight: 700;
        text-decoration: none;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Page header
header_col1, header_col2 = st.columns([1, 1])
with header_col1:
    st.markdown(
        """
        <div class='app-header'>
            <div class='brand'>
                <span class='brand-title'>Resume Analyzer</span>
                <span class='brand-subtitle'>Enterprise HR Platform</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with header_col2:
    st.markdown(
        """
        <div class='app-header'>
            <div class='nav-items'>
                <a class='nav-item active'>Dashboard</a>
                <a class='nav-item disabled'>Analytics</a>
                <a class='nav-item disabled'>Candidates</a>
                <a class='nav-item disabled'>Settings</a>
            </div>
            <div class='user-actions'>
                <span>🔔</span>
                <div class='user-avatar'>JD</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def classify_skills(skills):
    soft_keywords = {
        "leadership",
        "team",
        "collaboration",
        "communication",
        "problem solving",
        "project management",
        "adaptability",
        "creativity",
        "critical thinking",
        "ownership",
        "empathy",
        "stakeholder",
    }
    technical = []
    soft = []
    for skill in skills:
        normalized = skill.lower()
        if any(keyword in normalized for keyword in soft_keywords):
            soft.append(skill)
        else:
            technical.append(skill)
    return technical, soft


def calculate_dashboard_scores(profile):
    ats_score = float(profile.get("ats_score", 0) or 0)
    skills = profile.get("skills", []) or []
    experience_text = profile.get("experience", "") or ""
    education = profile.get("education", []) or []
    recommendations = profile.get("recommendations", []) or []

    skills_score = min(100, int(30 + len(skills) * 8)) if skills else 10
    experience_word_count = len(experience_text.split())
    experience_score = min(100, max(20, int(30 + experience_word_count * 0.8))) if experience_text else 18
    formatting_score = min(
        100,
        60 + (10 if education else 0) + (10 if recommendations else 0) + (10 if experience_text else 0),
    )

    overall_score = round((ats_score + skills_score + experience_score + formatting_score) / 4)
    status = (
        "Excellent"
        if overall_score >= 90
        else "Strong"
        if overall_score >= 75
        else "Good"
        if overall_score >= 60
        else "Needs Improvement"
    )

    return {
        "overall_score": overall_score,
        "ats_score": ats_score,
        "skills_score": skills_score,
        "experience_score": experience_score,
        "formatting_score": formatting_score,
        "status": status,
    }


if "document_record" not in st.session_state:
    st.session_state.document_record = None
if "candidate_profile" not in st.session_state:
    st.session_state.candidate_profile = None
if "debug_messages" not in st.session_state:
    st.session_state.debug_messages = []
if "recent_analyses" not in st.session_state:
    st.session_state.recent_analyses = []

# Main layout
left_col, right_col = st.columns([1.1, 1.9], gap="large")

with left_col:
    with st.container():
        st.markdown("<div class='dashboard-card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>Upload Resume</div>", unsafe_allow_html=True)
        st.markdown(
            """
            <div class='upload-dropzone'>
                <div style='font-size:2rem; margin-bottom: 0.9rem;'>📄</div>
                <div style='font-weight:700; font-size:1rem;'>Upload a PDF resume to extract text</div>
                <div style='color:#6b7280; margin:0.35rem 0 1rem;'>Drag and drop your file, or use the uploader below</div>
                <div class='small-note' style='margin-top:1rem;'>Supports PDF only (Max 10MB)</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        uploaded_file = st.file_uploader(
            "Upload resume PDF",
            type=["pdf"],
            help="Upload a PDF resume for extraction",
            label_visibility="collapsed",
        )

        if uploaded_file is None:
            if st.session_state.document_record is not None or st.session_state.candidate_profile is not None:
                st.session_state.document_record = None
                st.session_state.candidate_profile = None
                st.session_state.debug_messages = []
            st.markdown(
                "<div style='margin-top:1rem; color:#64748b;'>No file uploaded. Upload a PDF to begin the analysis.</div>",
                unsafe_allow_html=True,
            )
        else:
            validation_error = validate_upload(uploaded_file)
            if validation_error:
                show_toast(validation_error, level="warning")
                st.session_state.candidate_profile = None
            else:
                file_name = uploaded_file.name
                upload_progress = st.progress(0)
                logger.info("Starting resume extraction for %s", file_name)
                add_debug(f"Starting resume extraction for {file_name}")
                with st.spinner("Extracting text from your resume..."):
                    try:
                        extracted_text = extract_text_from_pdf(uploaded_file)
                        upload_progress.progress(25)
                        time.sleep(0.1)
                        add_debug(f"Extracted {len(extracted_text)} characters from PDF")
                        logger.info("Extracted text length %s", len(extracted_text))
                    except Exception as exc:
                        logger.exception("PDF extraction failed")
                        show_toast(f"PDF extraction failed: {exc}", level="error")
                        add_debug(f"PDF extraction failed: {exc}")
                        st.session_state.candidate_profile = None
                        upload_progress.empty()
                        extracted_text = ""

                if not extracted_text:
                    show_toast(
                        "No text could be extracted from the PDF. "
                        "The resume may be image-based or encrypted.",
                        level="error",
                    )
                    st.session_state.candidate_profile = None
                    st.session_state.document_record = build_document_record(file_name, extracted_text)
                    upload_progress.empty()
                else:
                    st.session_state.document_record = build_document_record(file_name, extracted_text)
                    with st.spinner("Analyzing resume with Gemini..."):
                        try:
                            upload_progress.progress(50)
                            add_debug("Sending resume text to Gemini for profile generation")
                            st.session_state.candidate_profile = generate_candidate_profile(extracted_text)
                            upload_progress.progress(90)
                            time.sleep(0.1)
                            show_toast(f"Resume uploaded and profile generated: {file_name}", level="success")
                            add_debug(f"Candidate profile keys: {list(st.session_state.candidate_profile.keys())}")
                            logger.info("Candidate profile generated for %s", file_name)
                            recent_entry = {
                                "title": file_name,
                                "score": calculate_dashboard_scores(st.session_state.candidate_profile)["overall_score"],
                                "time": "Just now",
                            }
                            st.session_state.recent_analyses.insert(0, recent_entry)
                            if len(st.session_state.recent_analyses) > 5:
                                st.session_state.recent_analyses = st.session_state.recent_analyses[:5]
                        except Exception as exc:
                            logger.exception("Candidate profile generation failed")
                            retry_seconds = None
                            try:
                                text = str(exc)
                                m = re.search(r"retryDelay\W*[:=]\W*['\"]?(\d+(?:\.\d+)?)s", text, flags=re.IGNORECASE)
                                if not m:
                                    m = re.search(r"Please retry in\s*(\d+(?:\.\d+)?)s", text, flags=re.IGNORECASE)
                                if m:
                                    retry_seconds = float(m.group(1))
                            except Exception:
                                retry_seconds = None

                            if retry_seconds:
                                show_toast(
                                    f"Gemini is rate-limited. Try again in ~{int(retry_seconds)}s.",
                                    level="warning",
                                )
                                add_debug(f"Gemini recommended retry delay: {retry_seconds}s")
                            else:
                                show_toast(f"Failed to generate candidate profile: {exc}", level="error")
                                add_debug(f"Failed to generate candidate profile: {exc}")

                            st.session_state.candidate_profile = None
                        finally:
                            upload_progress.progress(100)
                            time.sleep(0.1)
                            upload_progress.empty()

        if st.session_state.document_record:
            st.markdown(
                f"<div class='small-note' style='margin-top:1rem; color:#0f172a;'>"
                f"<strong>File:</strong> {st.session_state.document_record['file_name']}</div>",
                unsafe_allow_html=True,
            )
            st.text_area(
                "Extracted Resume Text",
                value=st.session_state.document_record["extracted_text"],
                height=220,
            )

        st.markdown("</div>", unsafe_allow_html=True)

    with st.container():
        st.markdown("<div class='dashboard-card'>", unsafe_allow_html=True)
        st.markdown(
            "<div class='section-title'>Recent Analyses "
            "<span style='float:right; font-size:0.92rem;'><a class='view-all'>View All</a></span>"
            "</div>",
            unsafe_allow_html=True,
        )
        if st.session_state.recent_analyses:
            for item in st.session_state.recent_analyses:
                st.markdown(
                    f"""
                    <div class='recent-item'>
                        <div>
                            <div class='recent-item-title'>{item['title']}</div>
                            <div class='recent-meta'>{item['time']}</div>
                        </div>
                        <div class='recent-score'>{item['score']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                "<div class='recent-item'>"
                "<div style='color:#64748b;'>No recent analyses yet. Upload a resume to get started.</div>"
                "</div>",
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

with right_col:
    with st.container():
        st.markdown("<div class='dashboard-card'>", unsafe_allow_html=True)
        st.markdown(
            "<div class='section-title'>Analysis Report</div>",
            unsafe_allow_html=True,
        )

        profile = st.session_state.candidate_profile or {}
        metrics = calculate_dashboard_scores(profile) if profile else {
            "overall_score": 0,
            "status": "Awaiting Upload",
            "ats_score": 0,
            "skills_score": 0,
            "experience_score": 0,
            "formatting_score": 0,
        }
        candidate_title = profile.get("candidate_name") or "Resume Analyzer"
        candidate_subtitle = (
            "Resume analysis summary"
            if profile
            else "Upload a PDF to generate a candidate profile"
        )

        if profile:
            email_link = build_email_share_link(profile, st.session_state.document_record)
            whatsapp_link = build_whatsapp_share_link(profile, st.session_state.document_record)

            left, right = st.columns([3, 2])
            with left:
                st.markdown(
                    f"<div style='margin-bottom:0.5rem;'>"
                    f"<div style='font-size:1rem; font-weight:700;'>{candidate_title}</div>"
                    f"<div style='color:#6b7280; margin-top:0.35rem;'>{candidate_subtitle}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
            with right:
                st.markdown(
                    f"<a class='action-button btn-share' href='{email_link}' target='_blank'>✉️</a>",
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f"<a class='action-button btn-share' href='{whatsapp_link}' target='_blank'>💬</a>",
                    unsafe_allow_html=True,
                )
                export_content = build_export_pdf(profile, st.session_state.document_record)
                export_filename = build_export_filename(profile)
                st.download_button(
                    label="📥",
                    data=export_content,
                    file_name=export_filename,
                    mime="application/pdf",
                    key="export_report",
                )
        else:
            st.markdown(
                f"<div style='display:flex; justify-content:space-between; flex-wrap:wrap; gap:1rem; margin-bottom:1.5rem;'>"
                f"<div><div style='font-size:1rem; font-weight:700;'>{candidate_title}</div>"
                f"<div style='color:#6b7280; margin-top:0.35rem;'>{candidate_subtitle}</div></div>"
                f"<div class='report-actions'>"
                f"<span class='action-button btn-share' style='cursor:not-allowed; opacity:0.65;'>Share</span>"
                f"</div></div>",
                unsafe_allow_html=True,
            )

        st.markdown(
            f"<div class='circle-score'>{metrics['overall_score']}</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div style='text-align:center; color:#374151; font-weight:600; margin-bottom:1rem;'>{metrics['status']}</div>"
            f"<div style='display:grid; gap:1rem;'>"
            f"<div class='metric-row'><div class='metric-info'>ATS Compatibility</div>"
            f"<div class='progress-wrap'><div class='progress-bar progress-green' style='width:{metrics['ats_score']}%;'></div></div>"
            f"<div style='min-width:3rem; font-weight:700;'>{metrics['ats_score']}%</div></div>"
            f"<div class='metric-row'><div class='metric-info'>Skills Match</div>"
            f"<div class='progress-wrap'><div class='progress-bar progress-green' style='width:{metrics['skills_score']}%;'></div></div>"
            f"<div style='min-width:3rem; font-weight:700;'>{metrics['skills_score']}%</div></div>"
            f"<div class='metric-row'><div class='metric-info'>Experience</div>"
            f"<div class='progress-wrap'><div class='progress-bar progress-yellow' style='width:{metrics['experience_score']}%;'></div></div>"
            f"<div style='min-width:3rem; font-weight:700;'>{metrics['experience_score']}%</div></div>"
            f"<div class='metric-row'><div class='metric-info'>Formatting</div>"
            f"<div class='progress-wrap'><div class='progress-bar progress-green' style='width:{metrics['formatting_score']}%;'></div></div>"
            f"<div style='min-width:3rem; font-weight:700;'>{metrics['formatting_score']}%</div></div>"
            f"</div>",
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.candidate_profile:
        profile = st.session_state.candidate_profile
        with st.container():
            st.markdown("<div class='dashboard-card'>", unsafe_allow_html=True)
            st.markdown("<div class='section-title'>Candidate Profile</div>", unsafe_allow_html=True)
            st.markdown(
                f"<div style='display:flex; justify-content:space-between; flex-wrap:wrap; gap:1.5rem;'>"
                f"<div style='min-width:16rem;'>"
                f"<div style='font-size:1rem; font-weight:700; color:#0f172a;'>{profile['candidate_name']}</div>"
                f"<div style='color:#475569; margin-top:0.35rem;'>ATS Score: <strong>{profile['ats_score']}</strong></div>"
                f"</div>"
                f"<div style='flex:1 1 16rem; min-width:16rem;'>"
                f"<div style='font-weight:600; color:#475569; margin-bottom:0.5rem;'>Skills</div>"
                f"<div class='tag-grid'>"
                + "".join([
                    f"<span class='tag-pill tag-technical'>{skill}</span>"
                    for skill in profile.get("skills", [])
                ])
                + "</div>"
                f"</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                "<div style='margin-top:1rem;'>"
                f"<div style='font-weight:700; color:#0f172a; margin-bottom:0.55rem;'>Experience Summary</div>"
                f"<div style='color:#475569; line-height:1.65;'>{profile.get('experience', '')}</div>"
                "</div>"
                "<div style='margin-top:1rem;'>"
                f"<div style='font-weight:700; color:#0f172a; margin-bottom:0.55rem;'>Education</div>"
                + "".join([
                    f"<div style='color:#475569; line-height:1.6;'>• {edu}</div>"
                    for edu in profile.get("education", [])
                ])
                + "</div>"
                "<div style='margin-top:1rem;'>"
                f"<div style='font-weight:700; color:#0f172a; margin-bottom:0.55rem;'>Recommendations</div>"
                + (
                    "<div style='color:#475569; line-height:1.6;'>NA</div>"
                    if not profile.get("recommendations")
                    else "".join([
                        f"<div style='color:#475569; line-height:1.6;'>• {rec}</div>"
                        for rec in profile.get("recommendations", [])
                    ])
                )
                + "</div>",
                unsafe_allow_html=True,
            )
            st.markdown("</div>", unsafe_allow_html=True)

    with st.container():
        st.markdown("<div class='dashboard-card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>Skills Assessment</div>", unsafe_allow_html=True)

        profile = st.session_state.candidate_profile or {}
        skills = profile.get("skills", []) or []
        technical_skills, soft_skills = classify_skills(skills)

        if not skills:
            st.markdown(
                "<div style='color:#64748b; margin-bottom:1rem;'>"
                "Upload a resume to extract skills and populate the assessment."
                "</div>",
                unsafe_allow_html=True,
            )

        st.markdown("<div style='display:flex; gap:2rem; flex-wrap:wrap;'>", unsafe_allow_html=True)
        st.markdown(
            "<div style='flex:1 1 20rem;'>"
            "<div style='font-weight:700; margin-bottom:0.8rem;'>Technical Skills Detected</div>"
            "<div class='tag-grid'>"
            + (
                "<span style='color:#475569;'>NA</span>"
                if not technical_skills
                else "".join([
                    f"<span class='tag-pill tag-technical'>{skill}</span>"
                    for skill in technical_skills
                ])
            )
            + "</div></div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div style='flex:1 1 20rem;'>"
            "<div style='font-weight:700; margin-bottom:0.8rem;'>Soft Skills Identified</div>"
            "<div class='tag-grid'>"
            + (
                "<span style='color:#475569;'>NA</span>"
                if not soft_skills
                else "".join([
                    f"<span class='tag-pill tag-soft'>{skill}</span>"
                    for skill in soft_skills
                ])
            )
            + "</div></div>",
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

        required_count = len(technical_skills)
        preferred_count = len(soft_skills)
        extra_skills_count = max(0, len(skills) - 5)

        st.markdown(
            "<ul class='sub-metric-list'>"
            f"<li><span>Required Skills Present</span><span>{required_count} detected</span></li>"
            f"<li><span>Preferred Skills Present</span><span>{preferred_count} detected</span></li>"
            f"<li><span>Additional Relevant Skills</span><span>{extra_skills_count}</span></li>"
            "</ul>",
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with st.expander("Debug / Diagnostics", expanded=False):
        if st.session_state.debug_messages:
            for message in st.session_state.debug_messages:
                st.write(message)
        else:
            st.write("No debug messages yet. Upload a resume to begin diagnostics.")