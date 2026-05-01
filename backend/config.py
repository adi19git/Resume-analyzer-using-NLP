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
# In production, restrict this to your actual frontend domain.
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5500",
    "http://localhost:8080",
    "http://127.0.0.1:5500",
    "http://127.0.0.1:8080",
    "null",  # For file:// protocol during local development
]

# ── spaCy Model ───────────────────────────────────────────────────────
SPACY_MODEL = "en_core_web_sm"
