"""
NLP Engine for the AI Resume Analyzer.

Uses spaCy NER + regex to extract structured data from resume text:
name, email, phone, skills, education, experience, and sections.
"""

import re
import logging
import spacy
from modules.skills_data import (
    ALL_SKILLS, DEGREE_KEYWORDS, EDUCATION_INSTITUTIONS_KEYWORDS
)

logger = logging.getLogger(__name__)

# Load spaCy model (will be downloaded on first run via main.py)
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    logger.warning("spaCy model not found. Run: python -m spacy download en_core_web_sm")
    nlp = None


def extract_email(text: str) -> str | None:
    """Extract email address using regex."""
    pattern = r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
    match = re.search(pattern, text)
    return match.group(0) if match else None


def extract_phone(text: str) -> str | None:
    """Extract phone number using regex (supports international formats)."""
    patterns = [
        r"[\+]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{1,4}[-\s\.]?[0-9]{4,6}",
        r"\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}",
        r"\+91[-\s]?[0-9]{10}",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            phone = match.group(0).strip()
            # Only return if it looks like a real phone number (7+ digits)
            digits = re.sub(r"\D", "", phone)
            if len(digits) >= 7:
                return phone
    return None


def extract_name(text: str) -> str | None:
    """
    Extract candidate name using spaCy NER.
    Looks for PERSON entities in the first few lines of the resume,
    since the name is almost always at the top.
    """
    if nlp is None:
        return None

    # Only process the first 500 chars (name is at the top)
    first_chunk = text[:500]
    doc = nlp(first_chunk)

    for ent in doc.ents:
        if ent.label_ == "PERSON":
            name = ent.text.strip()
            # Filter out single-word "names" that are likely false positives
            if len(name.split()) >= 2:
                return name

    # Fallback: first line that looks like a name (2-4 capitalized words)
    for line in text.split("\n")[:5]:
        line = line.strip()
        words = line.split()
        if 2 <= len(words) <= 4 and all(w[0].isupper() for w in words if w):
            # Check it's not a section header
            lower = line.lower()
            if not any(kw in lower for kw in [
                "resume", "curriculum", "objective", "summary", "experience"
            ]):
                return line
    return None


def extract_skills(text: str) -> list[str]:
    """
    Extract skills by matching against the curated skills database.
    Uses case-insensitive word-boundary matching for accuracy.
    """
    found_skills = set()
    text_lower = text.lower()

    for skill in ALL_SKILLS:
        # Use word boundary regex to avoid partial matches
        # e.g., "c" shouldn't match inside "communication"
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, text_lower):
            found_skills.add(skill.title() if len(skill) > 3 else skill.upper())

    return sorted(found_skills)


def extract_education(text: str) -> list[dict]:
    """
    Extract education entries from resume text.
    Looks for degree keywords near institution keywords.
    """
    education = []
    lines = text.split("\n")

    # Find the education section
    edu_start = None
    for i, line in enumerate(lines):
        if re.search(r"\b(education|academic|qualification)\b", line, re.IGNORECASE):
            edu_start = i
            break

    if edu_start is None:
        # Try to find education entries anywhere
        search_lines = lines
    else:
        # Search from education section header to next section or 20 lines
        search_lines = lines[edu_start:edu_start + 20]

    current_entry = {}
    for line in search_lines:
        line_lower = line.lower().strip()
        if not line_lower:
            if current_entry:
                education.append(current_entry)
                current_entry = {}
            continue

        # Check for degree keywords
        for kw in DEGREE_KEYWORDS:
            if kw in line_lower:
                current_entry["degree"] = line.strip()
                break

        # Check for institution keywords
        for kw in EDUCATION_INSTITUTIONS_KEYWORDS:
            if kw in line_lower:
                current_entry["institution"] = line.strip()
                break

        # Check for years (e.g., 2018-2022, 2020)
        year_match = re.search(r"(19|20)\d{2}", line)
        if year_match:
            current_entry.setdefault("year", line.strip())

    if current_entry:
        education.append(current_entry)

    return education


def extract_experience(text: str) -> list[dict]:
    """
    Extract work experience entries from resume text.
    Identifies job titles, companies, and duration.
    """
    experience = []
    lines = text.split("\n")

    # Find experience section
    exp_start = None
    for i, line in enumerate(lines):
        if re.search(
            r"\b(experience|employment|work\s*history|professional)\b",
            line, re.IGNORECASE
        ):
            exp_start = i
            break

    if exp_start is None:
        return experience

    # Common job title patterns
    title_patterns = [
        r"(senior|junior|lead|staff|principal|chief)?\s*(software|data|web|full[\-\s]?stack|front[\-\s]?end|back[\-\s]?end|devops|cloud|ml|ai|product|project|program|quality|systems?|network|database|security)\s*(engineer|developer|architect|manager|analyst|scientist|designer|administrator|specialist|consultant|director|lead|intern)",
        r"(cto|ceo|cfo|coo|vp|svp|evp|avp)\b",
    ]

    search_lines = lines[exp_start:exp_start + 50]
    current_entry = {}

    for line in search_lines:
        line_stripped = line.strip()
        if not line_stripped:
            if current_entry:
                experience.append(current_entry)
                current_entry = {}
            continue

        # Check for job title
        for pattern in title_patterns:
            if re.search(pattern, line_stripped, re.IGNORECASE):
                current_entry["title"] = line_stripped
                break

        # Check for date ranges (e.g., "Jan 2020 - Present")
        date_match = re.search(
            r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*\d{4}|"
            r"\d{4})\s*[-–—to]+\s*"
            r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*\d{4}|"
            r"\d{4}|present|current)",
            line_stripped, re.IGNORECASE
        )
        if date_match:
            current_entry["duration"] = date_match.group(0)

    if current_entry:
        experience.append(current_entry)

    return experience


def extract_sections(text: str) -> dict[str, bool]:
    """
    Detect which standard resume sections are present.
    Returns a dict of section_name -> True/False.
    """
    section_patterns = {
        "summary": r"\b(summary|objective|profile|about\s*me)\b",
        "experience": r"\b(experience|employment|work\s*history|professional)\b",
        "education": r"\b(education|academic|qualification|degree)\b",
        "skills": r"\b(skills|technical\s*skills|core\s*competencies|technologies)\b",
        "projects": r"\b(projects|portfolio)\b",
        "certifications": r"\b(certification|certificate|licensed|accredit)\b",
        "awards": r"\b(awards?|honors?|achievements?)\b",
        "publications": r"\b(publications?|papers?|research)\b",
        "contact": None,  # Checked separately
    }

    sections = {}
    text_lower = text.lower()

    for section, pattern in section_patterns.items():
        if pattern:
            sections[section] = bool(re.search(pattern, text_lower))
        else:
            # Contact info: check for email or phone
            has_email = extract_email(text) is not None
            has_phone = extract_phone(text) is not None
            sections[section] = has_email or has_phone

    return sections


def analyze_resume(text: str) -> dict:
    """
    Main orchestrator: runs all extraction functions and returns
    a structured dict with all parsed resume data.
    """
    return {
        "name": extract_name(text),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "skills": extract_skills(text),
        "education": extract_education(text),
        "experience": extract_experience(text),
        "sections": extract_sections(text),
        "word_count": len(text.split()),
        "line_count": len(text.strip().split("\n")),
    }
