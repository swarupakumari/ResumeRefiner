# 🚀 ResumeRefiner

AI-Powered Resume Optimization Tool that analyzes resumes against job descriptions and improves ATS (Applicant Tracking System) compatibility.

---

## 📌 Overview

ResumeRefiner helps candidates optimize their resumes by:

- 📊 Calculating ATS Match Score
- 🔍 Extracting and comparing keywords
- 🧠 Generating intelligent suggestions
- ✍️ Rewriting resume content
- 🎯 Highlighting improvements clearly

This project demonstrates practical implementation of LLM workflows using LangChain-style graph orchestration.

---

## ✨ Features

### 1️⃣ ATS Score Dashboard
- Overall Match Score
- Visual Score Breakdown
- Keyword comparison chart

### 2️⃣ Keyword Analysis
- Extracts job description keywords
- Compares with resume keywords
- Displays missing keywords

### 3️⃣ Smart Suggestions
- Key findings
- Specific improvements
- Actionable items

### 4️⃣ Resume Rewriting
- AI-generated optimized summary
- Tailored content based on job role
- Improved keyword alignment

### 5️⃣ Highlighted Changes View
- Clearly shows differences between original and optimized resume

---

## 🛠️ Tech Stack

- Python
- Streamlit (Frontend UI)
- LangChain-style Graph Workflow
- LLM Integration
- Matplotlib / Visualization
- JSON structured output

---

## 🧠 How It Works

1. Upload Resume (PDF)
2. Enter Job Title & Job Description
3. System:
   - Extracts text
   - Generates keyword analysis
   - Calculates ATS score
   - Produces structured improvement suggestions
4. Displays:
   - Dashboard
   - Visual Charts
   - JSON Output
   - Rewritten Resume

---

## 📂 Project Structure
app.py # Main application
graph.py # Workflow graph logic
nodes.py # Processing nodes
utils.py # Helper functions
test_nodes.py # Unit testing
requirements.txt # Dependencies


