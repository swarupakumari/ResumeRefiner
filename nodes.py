import streamlit as st
import json
from typing import List
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.output_parsers import PydanticOutputParser
from dotenv import load_dotenv
import re

load_dotenv()


# ----------------------------
# Utility Functions
# ----------------------------

def strip_think_tags(text: str) -> str:
    """Remove <think>...</think> blocks from LLM output."""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def clean_llm_output(text):
    """Remove markdown code blocks like ```json ... ```"""
    cleaned = re.sub(r"```json|```", "", text, flags=re.IGNORECASE)
    return cleaned.strip()


# ----------------------------
# Schemas
# ----------------------------

class ResumeAnalysisSchema(BaseModel):
    key_skills: List[str] = Field(default_factory=list)
    professional_experience: List[str] = Field(default_factory=list)
    education: List[str] = Field(default_factory=list)
    notable_projects: List[str] = Field(default_factory=list)
    career_progression: str = ""


class SuggestionsSchema(BaseModel):
    key_findings: List[str] = Field(default_factory=list)
    specific_improvements: List[str] = Field(default_factory=list)
    action_items: List[str] = Field(default_factory=list)


resume_parser = PydanticOutputParser(pydantic_object=ResumeAnalysisSchema)
suggestions_parser = PydanticOutputParser(pydantic_object=SuggestionsSchema)


# ----------------------------
# Nodes
# ----------------------------

def embed_documents(state):
    try:
        st.write("Running embed_documents node...")
        documents = state.get("documents", [])

        if not documents:
            raise ValueError("No documents to embed")

        embedder = OpenAIEmbeddings(model="text-embedding-3-small")
        vectorstore = FAISS.from_documents(documents, embedder)

        st.write("Embedding complete")
        state["vectorstore"] = vectorstore
        return state

    except Exception as e:
        st.error(f"Error in embed_documents: {e}")
        state["vectorstore"] = None
        return state


def analyze_resume(state):
    try:
        st.write("Running analyze_resume node...")

        vectorstore = state.get("vectorstore")
        if vectorstore is None:
            raise ValueError("Vectorstore missing")

        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0
        )

        retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

        query = state.get("job_description") or state.get("job_title") or "resume"
        st.write(f"Retrieving documents for query: {query[:80]}...")

        context_docs = retriever.invoke(query)

        if hasattr(context_docs, "docs"):
            context_docs = context_docs.docs

        context_text = "\n\n".join(doc.page_content for doc in context_docs)

        prompt = f"""
Please provide a JSON object strictly matching the schema below.
Do not include any explanations or other text.

{resume_parser.get_format_instructions()}

Resume Content:
{context_text}
"""

        response = llm.invoke([{"role": "user", "content": prompt}])
        raw_text = clean_llm_output(response.content)

        try:
            parsed = resume_parser.parse(raw_text)
            state["resume_analysis"] = parsed.model_dump()   # ✅ FIXED
        except Exception as e:
            st.error(f"Failed to parse resume analysis output: {e}")
            state["resume_analysis"] = ResumeAnalysisSchema().model_dump()  # ✅ FIXED

        st.write("Got structured analysis response")
        return state

    except Exception as e:
        st.error(f"Error in analyze_resume: {e}")
        state["resume_analysis"] = ResumeAnalysisSchema().model_dump()  # ✅ FIXED
        return state


def generate_suggestions(state):
    try:
        st.write("Running generate_suggestions node...")

        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0
        )

        resume_analysis_obj = state.get("resume_analysis", ResumeAnalysisSchema())

        if hasattr(resume_analysis_obj, "model_dump"):
            analysis_dict = resume_analysis_obj.model_dump()
        else:
            analysis_dict = resume_analysis_obj

        resume_analysis_json = json.dumps(analysis_dict)

        job_title = state.get("job_title", "")
        job_description = state.get("job_description", "")
        optimization_query = state.get("optimization_query", "")

        prompt = f"""
Please provide a JSON object strictly matching the schema below.
Do not include any explanations or other text.

{suggestions_parser.get_format_instructions()}

Resume Analysis:
{resume_analysis_json}

Job Title: {job_title}
Job Description: {job_description}

Optimization Request: {optimization_query}
"""

        response = llm.invoke([{"role": "user", "content": prompt}])
        raw_text = clean_llm_output(response.content)

        try:
            parsed = suggestions_parser.parse(raw_text)
            state["optimization_suggestions"] = parsed.model_dump()   # ✅ FIXED
        except Exception as e:
            st.error(f"Failed to parse suggestions output: {e}")
            state["optimization_suggestions"] = SuggestionsSchema().model_dump()  # ✅ FIXED

        st.write("Got structured suggestions response")
        return state

    except Exception as e:
        st.error(f"Error in generate_suggestions: {e}")
        state["optimization_suggestions"] = SuggestionsSchema().model_dump()  # ✅ FIXED
        return state


def check_reanalyze(state):
    try:
        trigger_reanalyze = state.get("trigger_reanalyze", False)
        st.write(f"check_reanalyze node: trigger_reanalyze={trigger_reanalyze}")
        state["reanalyze"] = trigger_reanalyze
        return state

    except Exception as e:
        st.error(f"Error in check_reanalyze: {e}")
        state["reanalyze"] = False
        return state