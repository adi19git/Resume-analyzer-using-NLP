"""
Database module for the AI Resume Analyzer.

Sets up PostgreSQL connection via SQLAlchemy with connection pooling.
Defines the AnalysisResult model that stores every resume analysis.
Gracefully handles missing PostgreSQL — the app still works without DB.
"""

from datetime import datetime, timezone
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, DateTime, Text
)
from sqlalchemy.orm import sessionmaker, declarative_base
from config import DATABASE_URL
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()

# Try to connect; set to None if PostgreSQL is unavailable
try:
    engine = create_engine(
        DATABASE_URL,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        echo=False,
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    DB_AVAILABLE = True
except Exception as e:
    logger.warning(f"Could not create DB engine: {e}")
    engine = None
    SessionLocal = None
    DB_AVAILABLE = False


class AnalysisResult(Base):
    """Stores the result of each resume analysis."""
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    upload_date = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    overall_score = Column(Float, nullable=False, default=0.0)
    analysis_json = Column(Text, nullable=False)

    def __repr__(self):
        return f"<AnalysisResult(id={self.id}, file='{self.filename}', score={self.overall_score})>"


def init_db():
    """Create all tables if DB is available."""
    if engine:
        Base.metadata.create_all(bind=engine)
        return True
    return False


def get_db():
    """FastAPI dependency — yields a session or None if DB unavailable."""
    if SessionLocal is None:
        yield None
        return
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
