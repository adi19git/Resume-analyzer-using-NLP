"""
Main FastAPI application for the AI Resume Analyzer.

Endpoints:
  POST /api/analyze   – Upload resume + job description → full analysis
  GET  /api/history   – List past analysis results
  GET  /api/analysis/{id} – Get a specific analysis by ID
  GET  /api/health    – Health check

On startup:
  - Downloads spaCy model if missing
  - Downloads NLTK data if missing
  - Initializes the PostgreSQL database tables
"""

import os
import sys
import json
from typing import Optional
import logging
import subprocess
from datetime import datetime, timezone

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from config import CORS_ORIGINS, ALLOWED_EXTENSIONS, MAX_FILE_SIZE_BYTES, SPACY_MODEL, BASE_DIR
from database import init_db, get_db, AnalysisResult

from modules.file_parser import parse_resume
from modules.nlp_engine import analyze_resume
from modules.keyword_matcher import (
    calculate_similarity,
    extract_job_keywords,
    find_matching_keywords,
)
from modules.ats_scorer import calculate_ats_score
from modules.feedback_generator import generate_feedback

# ── Logging ───────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s",
)
logger = logging.getLogger("resume_analyzer")

# ── FastAPI App ───────────────────────────────────────────────────────
app = FastAPI(
    title="AI Resume Analyzer",
    description="Analyze resumes against job descriptions using NLP",
    version="1.0.0",
)

# CORS middleware so the frontend can call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Startup Event ─────────────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    """Run on server startup: download models and create DB tables."""
    # 1. Download spaCy model if not present
    try:
        import spacy
        spacy.load(SPACY_MODEL)
        logger.info(f"spaCy model '{SPACY_MODEL}' is ready.")
    except OSError:
        logger.info(f"Downloading spaCy model '{SPACY_MODEL}'...")
        subprocess.check_call([
            sys.executable, "-m", "spacy", "download", SPACY_MODEL
        ])
        logger.info("spaCy model downloaded successfully.")
        # Reload the nlp engine module to pick up the new model
        from modules import nlp_engine
        import importlib
        importlib.reload(nlp_engine)

    # 2. Download NLTK stopwords if not present
    import nltk
    try:
        nltk.data.find("corpora/stopwords")
    except LookupError:
        nltk.download("stopwords", quiet=True)

    # 3. Initialize database tables
    try:
        init_db()
        logger.info("Database tables initialized.")
    except Exception as e:
        logger.error(f"Database init failed: {e}")
        logger.warning(
            "Make sure PostgreSQL is running and DATABASE_URL is correct. "
            "Set the DATABASE_URL env variable or update config.py."
        )


# ── Helper ────────────────────────────────────────────────────────────
def validate_file(filename: str, file_size: int):
    """Validate uploaded file extension and size."""
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    if file_size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE_BYTES // (1024*1024)}MB"
        )


# ══════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ══════════════════════════════════════════════════════════════════════

@app.post("/api/analyze")
async def analyze(
    file: UploadFile = File(..., description="Resume file (PDF or DOCX)"),
    job_description: str = Form("", description="Job description text (optional)"),
    db: Optional[Session] = Depends(get_db),
):
    """
    Main analysis endpoint.
    Accepts a resume file + optional job description, returns full analysis.
    When no JD is provided, scores based on resume quality alone.
    """
    # 1. Read and validate file
    file_bytes = await file.read()
    validate_file(file.filename, len(file_bytes))
    has_jd = bool(job_description and job_description.strip())
    logger.info(f"Analyzing: {file.filename} ({len(file_bytes)} bytes, JD={'yes' if has_jd else 'no'})")

    # 2. Extract text from resume
    try:
        resume_text = parse_resume(file_bytes, file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 3. NLP analysis — extract structured data
    resume_data = analyze_resume(resume_text)

    # 4. Keyword matching — only if JD is provided
    if has_jd:
        similarity = calculate_similarity(resume_text, job_description)
        job_keywords = extract_job_keywords(job_description)
        matched_keywords, missing_keywords = find_matching_keywords(
            resume_text, job_keywords
        )
    else:
        similarity = 0.0
        job_keywords = []
        matched_keywords = []
        missing_keywords = []

    # 5. ATS scoring
    ats_result = calculate_ats_score(
        resume_data=resume_data,
        similarity=similarity,
        matched_keywords=matched_keywords,
        missing_keywords=missing_keywords,
        resume_text=resume_text,
        job_keywords=job_keywords,
        has_jd=has_jd,
    )

    # 6. Generate feedback
    suggestions = generate_feedback(
        resume_data=resume_data,
        ats_result=ats_result,
        missing_keywords=missing_keywords,
        matched_keywords=matched_keywords,
    )

    # 7. Build response
    result = {
        "filename": file.filename,
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
        "resume_data": resume_data,
        "similarity_score": similarity,
        "keywords": {
            "job_keywords": job_keywords,
            "matched": matched_keywords,
            "missing": missing_keywords,
        },
        "ats_score": ats_result,
        "suggestions": suggestions,
    }

    # 8. Save to database (best-effort, works without PostgreSQL)
    if db is not None:
        try:
            db_record = AnalysisResult(
                filename=file.filename,
                overall_score=ats_result["overall_score"],
                analysis_json=json.dumps(result, default=str),
            )
            db.add(db_record)
            db.commit()
            db.refresh(db_record)
            result["id"] = db_record.id
            logger.info(
                f"Analysis saved (id={db_record.id}, score={ats_result['overall_score']})"
            )
        except Exception as e:
            logger.warning(f"Could not save to database: {e}")
            result["id"] = None
    else:
        result["id"] = None

    return result


@app.get("/api/history")
async def get_history(
    limit: int = 20,
    db: Optional[Session] = Depends(get_db),
):
    """Get list of past analysis results (most recent first)."""
    if db is None:
        return []
    try:
        results = (
            db.query(AnalysisResult)
            .order_by(AnalysisResult.upload_date.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": r.id,
                "filename": r.filename,
                "upload_date": r.upload_date.isoformat(),
                "overall_score": r.overall_score,
            }
            for r in results
        ]
    except Exception as e:
        logger.error(f"History fetch failed: {e}")
        return []


@app.get("/api/analysis/{analysis_id}")
async def get_analysis(analysis_id: int, db: Optional[Session] = Depends(get_db)):
    """Get a specific analysis result by ID."""
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")
    result = db.query(AnalysisResult).filter(
        AnalysisResult.id == analysis_id
    ).first()

    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")

    return json.loads(result.analysis_json)


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "AI Resume Analyzer",
        "version": "1.0.0",
    }


# ── Serve Frontend Static Files ───────────────────────────────────────
FRONTEND_DIR = BASE_DIR.parent / "frontend"
if FRONTEND_DIR.exists():
    # Mount CSS and JS as static files
    app.mount("/css", StaticFiles(directory=str(FRONTEND_DIR / "css")), name="css")
    app.mount("/js", StaticFiles(directory=str(FRONTEND_DIR / "js")), name="js")

    @app.get("/")
    async def serve_frontend():
        """Serve the frontend index.html at root."""
        return FileResponse(str(FRONTEND_DIR / "index.html"))

    @app.get("/{path:path}")
    async def spa_catchall(path: str):
        """SPA catch-all: serve index.html for any non-API, non-static route."""
        return FileResponse(str(FRONTEND_DIR / "index.html"))
