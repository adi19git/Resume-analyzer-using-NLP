"""
Configuration module for the AI Resume Analyzer.

Centralizes all application settings including database connection,
file upload limits, CORS origins, and path configurations.
All sensitive values are loaded from environment variables with safe defaults.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

# ── Paths ─────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# ── File Upload Settings ──────────────────────────────────────────────
MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".docx"}

# ── Database ──────────────────────────────────────────────────────────
# Default uses localhost PostgreSQL. Override with DATABASE_URL env var.
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/resume_analyzer"
)

# ── CORS ──────────────────────────────────────────────────────────────
# In production the frontend is served from the same origin as the API,
# so we allow all origins. Override with CORS_ORIGINS env var if needed.
_cors_env = os.getenv("CORS_ORIGINS", "")
CORS_ORIGINS = (
    [o.strip() for o in _cors_env.split(",") if o.strip()]
    if _cors_env
    else ["*"]
)

# ── spaCy Model ───────────────────────────────────────────────────────
SPACY_MODEL = "en_core_web_sm"
