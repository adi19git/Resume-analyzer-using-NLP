"""
Keyword Matcher module for the AI Resume Analyzer.

Uses TF-IDF vectorization + cosine similarity to score how well
a resume matches a job description. Also extracts top keywords
from the JD and identifies which ones are present/missing.

WHY TF-IDF over raw keyword counting?
- TF-IDF weights rare, meaningful terms higher (e.g., "Kubernetes")
  and common terms lower (e.g., "team", "work").
- Cosine similarity is direction-based, so it's robust to document length.
"""

import re
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.corpus import stopwords

logger = logging.getLogger(__name__)

# Download NLTK stopwords (only needed once)
try:
    nltk.data.find("corpora/stopwords")
except LookupError:
    nltk.download("stopwords", quiet=True)

STOP_WORDS = set(stopwords.words("english"))


def preprocess_text(text: str) -> str:
    """
    Clean text for TF-IDF vectorization.
    - Lowercase everything
    - Remove special characters and extra whitespace
    - Remove stopwords
    """
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s\+\#\.]", " ", text)  # Keep +, #, . for C++, C#, etc.
    text = re.sub(r"\s+", " ", text).strip()
    words = [w for w in text.split() if w not in STOP_WORDS and len(w) > 1]
    return " ".join(words)


def calculate_similarity(resume_text: str, job_description: str) -> float:
    """
    Calculate cosine similarity between resume and job description
    using TF-IDF vectors. Returns a float between 0.0 and 1.0.
    """
    cleaned_resume = preprocess_text(resume_text)
    cleaned_jd = preprocess_text(job_description)

    if not cleaned_resume or not cleaned_jd:
        return 0.0

    vectorizer = TfidfVectorizer(
        max_features=5000,      # Limit vocabulary to top 5000 terms
        ngram_range=(1, 2),     # Include bigrams (e.g., "machine learning")
        stop_words="english",
    )

    try:
        tfidf_matrix = vectorizer.fit_transform([cleaned_jd, cleaned_resume])
        score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])[0][0]
        return round(float(score), 4)
    except ValueError:
        return 0.0


def extract_job_keywords(job_description: str, top_n: int = 30) -> list[str]:
    """
    Extract the top N most important keywords from a job description
    using TF-IDF feature importance scores.
    """
    cleaned = preprocess_text(job_description)
    if not cleaned:
        return []

    vectorizer = TfidfVectorizer(
        max_features=200,
        ngram_range=(1, 2),
        stop_words="english",
    )

    try:
        tfidf_matrix = vectorizer.fit_transform([cleaned])
        feature_names = vectorizer.get_feature_names_out()
        scores = tfidf_matrix.toarray()[0]
        # Sort by TF-IDF score descending
        ranked = sorted(
            zip(feature_names, scores), key=lambda x: x[1], reverse=True
        )
        return [word for word, score in ranked[:top_n] if score > 0]
    except ValueError:
        return []


def find_matching_keywords(
    resume_text: str, job_keywords: list[str]
) -> tuple[list[str], list[str]]:
    """
    Check which job keywords appear in the resume.
    Returns (matched_keywords, missing_keywords).
    """
    resume_lower = resume_text.lower()
    matched = []
    missing = []

    for keyword in job_keywords:
        # Use word boundary matching
        pattern = r"\b" + re.escape(keyword.lower()) + r"\b"
        if re.search(pattern, resume_lower):
            matched.append(keyword)
        else:
            missing.append(keyword)

    return matched, missing
