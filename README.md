# CareerForge AI Pro — Agentic Career Intelligence Platform

**Author: Rehan Shaikh**

CareerForge AI Pro is a full-stack career intelligence project that goes beyond an ATS checker. It analyzes resumes against job descriptions, recommends suitable roles and companies to research, creates skill-gap roadmaps, provides safe resume rewrite guidance, generates interview questions, analyzes public GitHub profiles, compares resume versions, tracks job applications in SQLite, provides CV templates/guidelines, and exports a PDF career report.

## Features
- Resume PDF/TXT analysis and ATS scoring
- Job-description skill matching and missing-skill detection
- Role recommendations + company research shortlist
- Personalized learning roadmap
- Resume bullet rewrite guidance (does not invent achievements)
- Interview coach with role/skill-specific questions
- Public GitHub profile analyzer
- Resume V1 vs V2 comparison
- CV Template Lab: ATS Pro, Student Launch, Engineer Impact, Research CV
- Strong-CV checklist and writing guidance
- Local account authentication + SQLite job tracker
- Career dashboard with charts
- PDF career intelligence report export
- Modern responsive dark/glass UI

> Company suggestions are a research shortlist based on broad role fit, not live vacancies or guarantees. Always verify current openings on official career pages.

## Run on Windows / VS Code
### 1. Open project folder in VS Code
Open the `careerforge-ai` folder.

### 2. Start backend
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```
Backend: `http://127.0.0.1:8000`
API docs: `http://127.0.0.1:8000/docs`

### 3. Start frontend
```bash
cd frontend
python -m http.server 5500
```
Open `http://127.0.0.1:5500`

## Important
This educational project uses deterministic NLP/keyword intelligence locally. The AI features do not require a paid API key. A future production version can add an LLM provider, embeddings/vector search, live job feeds, OAuth and production-grade authentication.
