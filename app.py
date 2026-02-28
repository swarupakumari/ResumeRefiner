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

    # ===== PREMIUM DARK UI =====
    st.markdown("""
    <style>
    header {visibility: hidden;}
    .block-container {padding-top: 1.5rem;}

    .stApp {
        background: linear-gradient(135deg, #0b0f1c, #0f172a);
        color: #e5e7eb;
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0b1a2a, #0f1117);
    }

    h1 {
        font-size: 42px !important;
        font-weight: 700 !important;
        background: linear-gradient(90deg, #0066ff, #00f5d4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    div[data-testid="stTextInput"],
    div[data-testid="stTextArea"],
    div[data-testid="stFileUploader"] {
        background-color: #111827 !important;
        padding: 15px !important;
        border-radius: 14px !important;
        border: 1px solid #1f2937 !important;
        margin-bottom: 15px;
    }

    input, textarea {
        background-color: #1e293b !important;
        color: #ffffff !important;
        border-radius: 10px !important;
        border: 1px solid #334155 !important;
    }

    .stButton>button {
        background: linear-gradient(90deg, #3b82f6, #14b8a6);
        color: white;
        border-radius: 12px;
        border: none;
        padding: 0.6em 1.2em;
        font-weight: 600;
    }

    .stButton>button:disabled {
        background: #334155 !important;
        color: #94a3b8 !important;
    }
                
                /* ===== CUSTOM TABS - MATCH OPTIMIZE BUTTON ===== */

button[data-baseweb="tab"] {
    background: #1e293b !important;
    color: #d1d5db !important;
    border-radius: 12px !important;
    padding: 10px 18px !important;
    margin-right: 6px !important;
    font-weight: 500 !important;
    border: 1px solid #2d3748 !important;
    transition: all 0.3s ease !important;
}

/* Active Tab - SAME AS OPTIMIZE BUTTON */
button[data-baseweb="tab"][aria-selected="true"] {
    background: linear-gradient(90deg, #3b82f6, #14b8a6) !important;
    color: white !important;
    font-weight: 600 !important;
    box-shadow: 0px 4px 12px rgba(59, 130, 246, 0.35) !important;
    border: none !important;
}

/* Hover Effect */
button[data-baseweb="tab"]:hover {
    transform: translateY(-2px);
    box-shadow: 0px 4px 12px rgba(59, 130, 246, 0.25);
}
    </style>
    """, unsafe_allow_html=True)

    st.title("📄 Resume Refiner")
    st.caption("Craft Your Career - Built by Swarupa")

    # ===== SESSION STATE DEFAULTS =====
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

    # ===== SIDEBAR =====
    with st.sidebar:
        st.image("img/rrr.png", width=700)

        st.markdown(
            '<h3 style="color:#94a3b8;">Upload Resume <span style="color:#ef4444;">*</span></h3>',
            unsafe_allow_html=True
        )

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

    # ===== MAIN INPUTS =====
    st.markdown("### Job Details")

    # Job Title with red *
    st.markdown(
        '<label style="color:#cbd5e1;font-weight:500;">Job Title <span style="color:#ef4444;">*</span></label>',
        unsafe_allow_html=True
    )
    job_title = st.text_input("", key="job_title_input")

    # Job Description with red *
    st.markdown(
        '<label style="color:#cbd5e1;font-weight:500;">Job Description <span style="color:#ef4444;">*</span></label>',
        unsafe_allow_html=True
    )
    job_description = st.text_area("", height=200, key="job_desc_input")

    # ===== DISABLE BUTTON LOGIC =====
    optimize_disabled = (
        not job_title.strip()
        or not job_description.strip()
        or not st.session_state.documents
    )

    if st.button("🚀 Optimize Resume", disabled=optimize_disabled):

        if not st.session_state.documents:
            st.error("⚠ Please upload your resume.")
            return

        if not job_title.strip():
            st.error("⚠ Job Title is required.")
            return

        if not job_description.strip():
            st.error("⚠ Job Description is required.")
            return
 
        graph = create_resume_graph()

        state = {
            "documents": st.session_state.documents,
            "job_title": job_title,
            "job_description": job_description,
            "optimization_query": OPTIMIZATION_PROMPTS["ATS Keyword Optimizer"],
        }

        with st.spinner("Optimizing your resume..."):
            result = graph.invoke(state)

        st.session_state.last_result = result
        st.session_state.resume_analysis = result.get("resume_analysis", {})
        st.session_state.optimization_suggestions = result.get("optimization_suggestions", {})
        st.session_state.job_description = job_description

        st.success("Optimization Completed ✅")

    # ===== RESULTS SECTION =====
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

        with tab1:
            st.markdown("## 🎯 ATS Score Overview")
            color = "green" if score > 70 else "orange" if score > 40 else "red"

            st.markdown(
                f"""
                <div style="text-align:center;padding:30px;border-radius:15px;background-color:#1e293b;">
                    <h1 style="font-size:60px;color:{color};">{score}%</h1>
                    <h3>Overall Match Score</h3>
                </div>
                """,
                unsafe_allow_html=True
            )

            breakdown_df = pd.DataFrame({
                "Metric": ["Semantic Match", "Keyword Coverage", "Skill Match"],
                "Score": [semantic, keyword, skill]
            })

            st.bar_chart(breakdown_df.set_index("Metric"))

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

        with tab3:
            st.json(st.session_state.resume_analysis)

        with tab4:
            st.json(st.session_state.optimization_suggestions)

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