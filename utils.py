import base64
import re
import difflib
from collections import Counter

from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import ChatOpenAI
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from reportlab.platypus import SimpleDocTemplate, Preformatted
from reportlab.lib.styles import ParagraphStyle


# =========================
# PDF PREVIEW
# =========================

def display_pdf_preview(pdf_file):

    base64_pdf = base64.b64encode(
        pdf_file.getvalue()
    ).decode("utf-8")

    iframe = f"""
    <iframe
    src="data:application/pdf;base64,{base64_pdf}"
    width="100%"
    height="600px"
    type="application/pdf">
    </iframe>
    """

    return iframe


# =========================
# LOAD RESUME (CLEANED)
# =========================

def load_resume_documents(pdf_path):

    loader = PyPDFLoader(pdf_path)
    documents = loader.load()

    for doc in documents:
        text = doc.page_content
        text = text.replace("■", "")
        text = text.replace("�", "")
        text = text.encode("utf-8", "ignore").decode("utf-8")
        doc.page_content = text

    return documents


# =========================
# PROMPTS
# =========================

OPTIMIZATION_PROMPTS = {
    "ATS Keyword Optimizer": "Optimize resume for ATS",
    "Experience Section Enhancer": "Improve experience section",
    "Skills Hierarchy Creator": "Improve skills section",
    "Professional Summary Crafter": "Improve summary",
    "Education Optimizer": "Improve education",
    "Technical Skills Showcase": "Improve tech skills",
    "Career Gap Framing": "Improve career gap"
}


# =========================
# ATS SCORE
# =========================

ats_model = SentenceTransformer("all-MiniLM-L6-v2")


def calculate_ats_score(resume_analysis, job_description):

    if not resume_analysis or not job_description:
        return 0

    resume_text = " ".join(
        resume_analysis.get("key_skills", [])
        + resume_analysis.get("professional_experience", [])
        + resume_analysis.get("education", [])
        + resume_analysis.get("notable_projects", [])
    )

    emb1 = ats_model.encode([resume_text])
    emb2 = ats_model.encode([job_description])

    similarity = cosine_similarity(emb1, emb2)[0][0]
    semantic_score = similarity * 60

    job_words = set(re.findall(r'\b\w+\b', job_description.lower()))
    resume_words = set(re.findall(r'\b\w+\b', resume_text.lower()))

    keyword_score = (
        len(job_words.intersection(resume_words)) / len(job_words)
    ) * 25

    skill_match = sum(
        1 for skill in resume_analysis.get("key_skills", [])
        if skill.lower() in job_description.lower()
    )

    skill_score = min(skill_match * 3, 15)

    final_score = semantic_score + keyword_score + skill_score

    return min(round(final_score), 100)


# 🔥 NEW: Breakdown for Dashboard

def calculate_score_breakdown(resume_analysis, job_description):

    if not resume_analysis or not job_description:
        return 0, 0, 0

    resume_text = " ".join(
        resume_analysis.get("key_skills", [])
        + resume_analysis.get("professional_experience", [])
        + resume_analysis.get("education", [])
        + resume_analysis.get("notable_projects", [])
    )

    emb1 = ats_model.encode([resume_text])
    emb2 = ats_model.encode([job_description])

    similarity = cosine_similarity(emb1, emb2)[0][0]
    semantic_score = round(similarity * 60)

    job_words = set(re.findall(r'\b\w+\b', job_description.lower()))
    resume_words = set(re.findall(r'\b\w+\b', resume_text.lower()))

    keyword_score = round(
        (len(job_words.intersection(resume_words)) / len(job_words)) * 25
    ) if job_words else 0

    skill_match = sum(
        1 for skill in resume_analysis.get("key_skills", [])
        if skill.lower() in job_description.lower()
    )

    skill_score = min(skill_match * 3, 15)

    return semantic_score, keyword_score, skill_score


# =========================
# KEYWORD ANALYSIS
# =========================

def extract_keyword_data(resume_analysis, job_description):

    resume_text = " ".join(
        resume_analysis.get("key_skills", [])
        + resume_analysis.get("professional_experience", [])
        + resume_analysis.get("education", [])
        + resume_analysis.get("notable_projects", [])
    ).lower()

    job_words = re.findall(r'\b\w+\b', job_description.lower())

    filtered = [w for w in job_words if len(w) > 3]

    freq = Counter(filtered)

    keyword_data = []
    missing_keywords = []

    for word, count in freq.most_common(15):
        presence = resume_text.count(word)
        keyword_data.append({
            "keyword": word,
            "Required in Job": count,
            "Found in Resume": presence
        })

        if presence == 0:
            missing_keywords.append(word)

    return keyword_data, missing_keywords


# =========================
# REWRITE
# =========================

def generate_rewritten_resume(original_resume_text, job_description, model_name="gpt-4o-mini"):

    prompt = f"""
You are an expert ATS Resume Optimizer.

STRICT RULES:
1. Keep EXACT same layout
2. Keep EXACT same headings
3. Do NOT remove content
4. Only improve bullet points
5. Add missing ATS keywords
6. Add extra tech stack inside existing Skills section
7. Do NOT add explanation

Resume:
{original_resume_text}

Job Description:
{job_description}

Return ONLY the improved resume.
"""

    llm = ChatOpenAI(model=model_name, temperature=0)
    response = llm.invoke(prompt)
    return response.content


# =========================
# HIGHLIGHT
# =========================

def highlight_new_content(original_text, rewritten_text):

    original_lines = [line.strip() for line in original_text.splitlines() if line.strip()]
    rewritten_lines = rewritten_text.splitlines()

    highlighted_lines = []

    for new_line in rewritten_lines:
        clean_new = new_line.strip()

        matches = difflib.get_close_matches(clean_new, original_lines, n=1, cutoff=0.85)

        if matches:
            highlighted_lines.append(new_line)
        else:
            highlighted_lines.append(
                f"<span style='background-color:#1e3a8a; color:#ffffff; font-weight:600'>{new_line}</span>"
            )

    return "<br>".join(highlighted_lines)


# =========================
# PDF
# =========================

def create_resume_pdf(content):

    file_path = "ATS_Optimized_Resume.pdf"

    doc = SimpleDocTemplate(file_path)

    style = ParagraphStyle(
        name="ModernResume",
        fontName="Helvetica",
        fontSize=10.5,
        leading=13
    )

    elements = []
    elements.append(Preformatted(content.strip(), style))
    doc.build(elements)

    return file_path