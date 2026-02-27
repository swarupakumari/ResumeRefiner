import streamlit as st
import shutil
import tempfile
import pandas as pd

from utils import (
    display_pdf_preview,
    load_resume_documents,
    OPTIMIZATION_PROMPTS,
    calculate_ats_score,
    calculate_score_breakdown,
    generate_rewritten_resume,
    create_resume_pdf,
    highlight_new_content,
    extract_keyword_data
)

from graph import create_resume_graph


def main():

    st.set_page_config(
        page_title="Resume Refiner",
        page_icon="📄",
        layout="wide"
    )

# ===== PREMIUM DARK UI POLISH =====
    st.markdown("""
<style>

/* Remove Top White Bar */
header {visibility: hidden;}
.block-container {padding-top: 1.5rem;}

/* Main Background */
.stApp {
    background: linear-gradient(135deg, #0b0f1c, #0f172a);
    color: #e5e7eb;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0b1a2a, #0f1117);
}
                /* Upload Resume text color */
section[data-testid="stSidebar"] h3 {
     color: #94a3b8 !important;
    font-weight: 600;
}

/* ===== MAIN TITLE (Resume Refiner) ===== */
h1 {
    font-size: 42px !important;
    font-weight: 700 !important;
    background: linear-gradient(90deg, #0066ff, #00f5d4);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: 1px;
}

/* Sub text */
.stCaption {
    color: #9ca3af !important;
}

/* Section Labels (Job Title, Job Description etc.) */
label {
    color: #cbd5e1 !important;
    font-weight: 500;
}

/* Input Containers Darker */
div[data-testid="stTextInput"],
div[data-testid="stTextArea"],
div[data-testid="stFileUploader"] {
    background-color: #111827 !important;
    padding: 15px !important;
    border-radius: 14px !important;
    border: 1px solid #1f2937 !important;
    margin-bottom: 15px;
}

/* Input Fields */
input, textarea {
    background-color: #1e293b !important;
    color: #ffffff !important;
    border-radius: 10px !important;
    border: 1px solid #334155 !important;
}

/* File Upload Area */
section[data-testid="stFileUploader"] > div {
    background-color: #1e293b !important;
    border-radius: 12px !important;
    border: 1px dashed #00f5d4 !important;
}

/* Buttons */
/* Optimize Button - Eye Soothing */
.stButton>button {
    background: linear-gradient(90deg, #3b82f6, #14b8a6);
    color: white;
    border-radius: 12px;
    border: none;
    padding: 0.6em 1.2em;
    font-weight: 600;
    transition: all 0.3s ease;
}

/* Softer hover */
.stButton>button:hover {
    transform: translateY(-2px);
    box-shadow: 0px 4px 12px rgba(59, 130, 246, 0.25);
}

/* Tabs */
button[data-baseweb="tab"] {
    background-color: #1e293b !important;
    color: #d1d5db !important;
    border-radius: 10px !important;
    padding: 10px 18px !important;
    margin-right: 6px;
    font-weight: 500;
    border: 1px solid #2d3748 !important;
}

button[data-baseweb="tab"][aria-selected="true"] {
    background: linear-gradient(90deg, #0066ff, #00f5d4) !important;
    color: white !important;
    font-weight: 600;
    box-shadow: 0px 0px 12px rgba(0, 245, 212, 0.6);
}

button[data-baseweb="tab"] span {
    color: inherit !important;
}

/* Cards */
div[data-testid="stVerticalBlock"] > div {
    background-color: #111827;
    border-radius: 14px;
    padding: 15px;
}
                /* Input Focus Effect */
input:focus, textarea:focus {
    border: 1px solid #3b82f6 !important;
    box-shadow: 0px 0px 8px rgba(59, 130, 246, 0.35) !important;
    outline: none !important;
}
                /* Background Depth Effect */
body {
    background: radial-gradient(
        circle at 20% 20%,
        rgba(59, 130, 246, 0.08),
        transparent 40%
    ),
    radial-gradient(
        circle at 80% 80%,
        rgba(20, 184, 166, 0.06),
        transparent 40%
    ),
    #0f1117;
                

}

</style>
""", unsafe_allow_html=True)

    st.title("📄 Resume Refiner")
    st.caption("Craft Your Career - Built by Swarupa")

    defaults = {
        "resume_analysis": {},
        "optimization_suggestions": {},
        "documents": None,
        "temp_dir": None,
        "last_result": None,
        "rewritten_resume": "",
        "rewritten_pdf": "",
        "job_description": "",
        "original_resume_text": ""
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # Sidebar Upload
    with st.sidebar:
        st.image("./img/rrr.png", width=700)
        st.subheader("Upload Resume")
        uploaded_file = st.file_uploader("PDF only", type=["pdf"])

        if uploaded_file:
            st.session_state.temp_dir = tempfile.mkdtemp()
            path = f"{st.session_state.temp_dir}/{uploaded_file.name}"

            with open(path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            st.session_state.documents = load_resume_documents(path)

            full_resume_text = ""
            for doc in st.session_state.documents:
                full_resume_text += doc.page_content + "\n"

            st.session_state.original_resume_text = full_resume_text

            st.markdown(display_pdf_preview(uploaded_file), unsafe_allow_html=True)
            st.success("Resume uploaded successfully")

    job_title = st.text_input("Job Title")
    job_description = st.text_area("Job Description", height=200)

    if st.button("🚀 Optimize Resume"):

        graph = create_resume_graph()

        state = {
            "documents": st.session_state.documents,
            "job_title": job_title,
            "job_description": job_description,
            "optimization_query": OPTIMIZATION_PROMPTS["ATS Keyword Optimizer"],
        }

        result = graph.invoke(state)

        st.session_state.last_result = result
        st.session_state.resume_analysis = result.get("resume_analysis", {})
        st.session_state.optimization_suggestions = result.get("optimization_suggestions", {})
        st.session_state.job_description = job_description

        st.success("Optimization Completed ✅")

    if st.session_state.resume_analysis:

        score = calculate_ats_score(
            st.session_state.resume_analysis,
            st.session_state.job_description
        )

        semantic, keyword, skill = calculate_score_breakdown(
            st.session_state.resume_analysis,
            st.session_state.job_description
        )

        tab1, tab2, tab3, tab4, tab5 = st.tabs(
            ["📊 Dashboard", "🔎 Keyword Visual", "🧠 Analysis", "💡 Suggestions", "✍ Rewritten Resume"]
        )

        # ================= DASHBOARD =================
        with tab1:

            st.markdown("## 🎯 ATS Score Overview")

            color = "green" if score > 70 else "orange" if score > 40 else "red"

            st.markdown(
                f"""
                <div style="text-align:center;padding:30px;border-radius:15px;
                background-color:#1e293b;">
                    <h1 style="font-size:60px;color:{color};">{score}%</h1>
                    <h3>Overall Match Score</h3>
                </div>
                """,
                unsafe_allow_html=True
            )

            st.markdown("### 📊 Score Breakdown")

            breakdown_df = pd.DataFrame({
                "Metric": ["Semantic Match", "Keyword Coverage", "Skill Match"],
                "Score": [semantic, keyword, skill]
            })

            st.bar_chart(breakdown_df.set_index("Metric"))

        # ================= KEYWORD =================
        with tab2:

            keyword_data, missing_keywords = extract_keyword_data(
                st.session_state.resume_analysis,
                st.session_state.job_description
            )

            df = pd.DataFrame(keyword_data)

            st.bar_chart(
                df.set_index("keyword")[["Required in Job", "Found in Resume"]]
            )

            if missing_keywords:
                st.warning("Missing Keywords: " + ", ".join(missing_keywords[:10]))

        # ================= ANALYSIS =================
        with tab3:
            st.json(st.session_state.resume_analysis)

        # ================= SUGGESTIONS =================
        with tab4:
            st.json(st.session_state.optimization_suggestions)

       

        # ================= REWRITE =================
        with tab5:

            if st.button("Generate Resume"):

                rewritten = generate_rewritten_resume(
                    st.session_state.original_resume_text,
                    st.session_state.job_description
                )

                st.session_state.rewritten_resume = rewritten
                st.session_state.rewritten_pdf = create_resume_pdf(rewritten)

            if st.session_state.rewritten_resume:

                sub1, sub2 = st.tabs(["Optimized Resume", "Highlighted Changes"])

                with sub1:
                    st.text_area("Resume", st.session_state.rewritten_resume, height=400)

                with sub2:
                    highlighted = highlight_new_content(
                        st.session_state.original_resume_text,
                        st.session_state.rewritten_resume
                    )
                    st.markdown(highlighted, unsafe_allow_html=True)

                


if __name__ == "__main__":
    main()