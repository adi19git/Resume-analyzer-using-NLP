# 🤖 AI Resume Analyzer

An AI-powered resume analysis tool that scores resumes against job descriptions using NLP, providing ATS scores, skill gap analysis, and actionable improvement suggestions.

## ✨ Features

- **Resume Parsing** — Extracts text from PDF/DOCX files
- **NLP Analysis** — Identifies name, email, phone, skills, education, experience using spaCy NER
- **Keyword Matching** — TF-IDF cosine similarity between resume and job description
- **ATS Scoring** — Composite score (0-100) based on keywords, sections, formatting, experience
- **Skill Gap Analysis** — Identifies missing skills from the job description
- **Feedback Generator** — Actionable suggestions prioritized by importance
- **Analysis History** — PostgreSQL-backed history of past analyses

## 🛠 Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | FastAPI + Python 3.10+ |
| NLP | spaCy (en_core_web_sm) |
| ML | scikit-learn (TF-IDF + Cosine Similarity) |
| Database | PostgreSQL + SQLAlchemy |
| File Parsing | PyMuPDF (PDF) + python-docx (DOCX) |
| Frontend | Vanilla HTML/CSS/JS |

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- PostgreSQL installed and running

### 1. Create the PostgreSQL database

```sql
CREATE DATABASE resume_analyzer;
```

### 2. Configure environment

Edit `backend/.env` with your PostgreSQL credentials:

```
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/resume_analyzer
```

### 3. Install Python dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 4. Download spaCy model (auto-downloads on first run too)

```bash
python -m spacy download en_core_web_sm
```

### 5. Start the backend server

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Open the frontend

Open `frontend/index.html` in your browser, or serve it:

```bash
cd frontend
python -m http.server 5500
```

Then visit `http://localhost:5500`

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/analyze` | Upload resume + job description → full analysis |
| GET | `/api/history` | List past analyses |
| GET | `/api/analysis/{id}` | Get specific analysis result |
| GET | `/api/health` | Health check |
| GET | `/docs` | Swagger API documentation |

## 📁 Project Structure

```
ai resume analyser/
├── backend/
│   ├── main.py              # FastAPI app + routes
│   ├── config.py            # Configuration
│   ├── database.py          # PostgreSQL models
│   ├── .env                 # Environment variables
│   ├── requirements.txt     # Dependencies
│   └── modules/
│       ├── file_parser.py       # PDF/DOCX extraction
│       ├── nlp_engine.py        # spaCy NER + extraction
│       ├── keyword_matcher.py   # TF-IDF similarity
│       ├── ats_scorer.py        # ATS scoring engine
│       ├── feedback_generator.py # Suggestions
│       └── skills_data.py       # Skills database
├── frontend/
│   ├── index.html
│   ├── css/styles.css
│   └── js/app.js
└── sample_data/
    └── sample_job_description.txt
```

## 🧪 Testing

Use the sample job description in `sample_data/` and upload any PDF/DOCX resume.

## 🌐 Deployment

| Platform | Frontend | Backend |
|----------|----------|---------|
| **Render** | Static Site | Web Service (Python) |
| **Railway** | Static | Python service |
| **Vercel + Render** | Vercel | Render |
