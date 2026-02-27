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

    st.title("📄 Resume Refiner")
    st.caption("AI-Powered Resume Intelligence Dashboard")

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

        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
            ["📊 Dashboard", "🔎 Keyword Visual", "🧠 Analysis", "💡 Suggestions", "🧾 JSON", "✍ Rewritten Resume"]
        )

        # ================= DASHBOARD =================

        with tab1:

            st.markdown("## 🎯 ATS Score Overview")

            color = "green" if score > 70 else "orange" if score > 40 else "red"

            st.markdown(
                f"""
                <div style="text-align:center;padding:30px;border-radius:15px;
                background-color:#f0f2f6;">
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
                df.set_index("keyword")[["job_count", "resume_count"]]
            )

            if missing_keywords:
                st.warning("Missing Keywords: " + ", ".join(missing_keywords[:10]))

        # ================= ANALYSIS =================

        with tab3:
            st.json(st.session_state.resume_analysis)

        # ================= SUGGESTIONS =================

        with tab4:
            st.json(st.session_state.optimization_suggestions)

        # ================= JSON =================

        with tab5:
            st.json(st.session_state.last_result)

        # ================= REWRITE =================

        with tab6:

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

                with open(st.session_state.rewritten_pdf, "rb") as f:
                    st.download_button(
                        "⬇ Download ATS Resume PDF",
                        f,
                        file_name="ATS_Resume.pdf",
                        mime="application/pdf"
                    )


if __name__ == "__main__":
    main()