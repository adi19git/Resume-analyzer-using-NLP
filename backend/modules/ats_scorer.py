"""
ATS Scoring Engine for the AI Resume Analyzer.

Calculates a composite ATS score (0-100) based on four weighted components:
  1. Keyword Match (40%) - How well resume matches the job description
  2. Section Completeness (25%) - Are all standard sections present
  3. Formatting Quality (15%) - Resume structure and readability
  4. Experience Relevance (20%) - Action verbs, achievements, JD alignment
"""

import re
from modules.skills_data import ACTION_VERBS


def calculate_keyword_score(
    similarity: float, matched_count: int, total_keywords: int
) -> dict:
    """
    Score based on cosine similarity + keyword overlap percentage.
    similarity: TF-IDF cosine similarity (0.0-1.0)
    matched_count: number of JD keywords found in resume
    total_keywords: total JD keywords extracted
    """
    # Cosine similarity contributes 60% of this sub-score
    sim_score = min(similarity * 100 * 2, 100) * 0.6  # Scale up since raw sim is often low

    # Keyword overlap contributes 40%
    if total_keywords > 0:
        overlap_pct = (matched_count / total_keywords) * 100
    else:
        overlap_pct = 0
    overlap_score = min(overlap_pct, 100) * 0.4

    score = round(sim_score + overlap_score, 1)
    return {
        "score": min(score, 100),
        "similarity": similarity,
        "matched_count": matched_count,
        "total_keywords": total_keywords,
        "overlap_percentage": round(overlap_pct, 1),
    }


def calculate_section_score(sections: dict[str, bool]) -> dict:
    """
    Score based on presence of standard resume sections.
    Essential sections are weighted more heavily.
    """
    weights = {
        "contact": 20,         # Must have contact info
        "experience": 25,      # Must have work experience
        "education": 20,       # Must have education
        "skills": 20,          # Must have skills section
        "summary": 10,         # Should have a summary/objective
        "projects": 3,         # Nice to have
        "certifications": 2,   # Nice to have
    }

    earned = 0
    total = sum(weights.values())
    present = []
    missing = []

    for section, weight in weights.items():
        if sections.get(section, False):
            earned += weight
            present.append(section)
        else:
            missing.append(section)

    score = round((earned / total) * 100, 1)
    return {
        "score": score,
        "present_sections": present,
        "missing_sections": missing,
    }


def calculate_formatting_score(text: str) -> dict:
    """
    Score based on formatting quality indicators.
    Checks: word count, bullet points, line length, consistency.
    """
    lines = text.strip().split("\n")
    word_count = len(text.split())
    penalties = []
    score = 100.0

    # Word count check (ideal: 300-800 words for 1-2 page resume)
    if word_count < 150:
        penalty = 25
        score -= penalty
        penalties.append(f"Too short ({word_count} words). Aim for 300-800 words.")
    elif word_count < 300:
        penalty = 10
        score -= penalty
        penalties.append(f"Somewhat short ({word_count} words). Consider adding more detail.")
    elif word_count > 1200:
        penalty = 15
        score -= penalty
        penalties.append(f"Too long ({word_count} words). Keep to 1-2 pages.")

    # Bullet point usage (resumes should use bullets)
    bullet_patterns = r"^[\s]*[•\-\*\▪\►\➤\→]"
    bullet_lines = sum(1 for l in lines if re.match(bullet_patterns, l))
    if bullet_lines < 3:
        score -= 10
        penalties.append("Low use of bullet points. Use bullets for experience entries.")

    # Check for very long lines (might indicate poor formatting)
    long_lines = sum(1 for l in lines if len(l.strip()) > 120)
    if long_lines > len(lines) * 0.3:
        score -= 10
        penalties.append("Many lines are too long. Break content into shorter bullet points.")

    # Check for ALL CAPS abuse
    caps_lines = sum(1 for l in lines if l.strip().isupper() and len(l.strip()) > 10)
    if caps_lines > 5:
        score -= 5
        penalties.append("Excessive use of ALL CAPS. Use title case for headings.")

    return {
        "score": max(round(score, 1), 0),
        "word_count": word_count,
        "bullet_count": bullet_lines,
        "penalties": penalties,
    }


def calculate_experience_score(text: str, job_keywords: list[str]) -> dict:
    """
    Score based on experience quality indicators.
    Checks: action verbs, quantifiable achievements, keyword usage.
    """
    text_lower = text.lower()
    words = set(text_lower.split())
    score = 0.0
    details = []

    # Action verb usage (out of 40 points)
    found_verbs = words.intersection(ACTION_VERBS)
    verb_count = len(found_verbs)
    if verb_count >= 8:
        score += 40
        details.append(f"Excellent action verb usage ({verb_count} found)")
    elif verb_count >= 5:
        score += 30
        details.append(f"Good action verb usage ({verb_count} found)")
    elif verb_count >= 2:
        score += 15
        details.append(f"Some action verbs found ({verb_count}). Add more.")
    else:
        details.append("Very few action verbs. Use verbs like 'Led', 'Developed', 'Optimized'.")

    # Quantifiable achievements (out of 30 points)
    # Look for numbers with context (%, $, x, etc.)
    quant_patterns = [
        r"\d+\s*%",           # Percentages
        r"\$\s*[\d,]+",       # Dollar amounts
        r"\d+\s*x\b",        # Multipliers
        r"\d+\+?\s*(users?|customers?|clients?|team|people|members?)",
        r"(increased|decreased|reduced|improved|grew|saved)\s.*\d+",
    ]
    quant_count = sum(
        len(re.findall(p, text_lower)) for p in quant_patterns
    )
    if quant_count >= 5:
        score += 30
        details.append(f"Great use of metrics ({quant_count} quantified achievements)")
    elif quant_count >= 2:
        score += 20
        details.append(f"Some metrics found ({quant_count}). Add more numbers.")
    elif quant_count >= 1:
        score += 10
        details.append("Few metrics. Quantify your impact (e.g., 'reduced costs by 30%').")
    else:
        details.append("No quantified achievements found. Add measurable impact statements.")

    # JD keyword relevance in experience context (out of 30 points)
    if job_keywords:
        relevant = sum(1 for kw in job_keywords if kw.lower() in text_lower)
        relevance_pct = relevant / len(job_keywords) if job_keywords else 0
        kw_score = min(relevance_pct * 100, 100) * 0.3
        score += kw_score
        details.append(f"JD keyword coverage: {round(relevance_pct * 100, 1)}%")

    return {
        "score": min(round(score, 1), 100),
        "action_verbs_found": sorted(found_verbs)[:10],
        "quantified_achievements": quant_count,
        "details": details,
    }


def calculate_ats_score(
    resume_data: dict,
    similarity: float,
    matched_keywords: list[str],
    missing_keywords: list[str],
    resume_text: str,
    job_keywords: list[str],
    has_jd: bool = True,
) -> dict:
    """
    Main ATS scoring function. Combines all sub-scores with weights.

    With JD:    Keyword 40% | Sections 25% | Formatting 15% | Experience 20%
    Without JD: Sections 40% | Formatting 25% | Experience 35%  (keyword skipped)
    """
    total_kw = len(matched_keywords) + len(missing_keywords)

    keyword = calculate_keyword_score(similarity, len(matched_keywords), total_kw)
    section = calculate_section_score(resume_data.get("sections", {}))
    formatting = calculate_formatting_score(resume_text)
    experience = calculate_experience_score(resume_text, job_keywords)

    if has_jd:
        # Full scoring with JD-based keyword match
        overall = round(
            keyword["score"] * 0.40
            + section["score"] * 0.25
            + formatting["score"] * 0.15
            + experience["score"] * 0.20,
            1
        )
    else:
        # Resume-quality-only scoring (no JD comparison)
        overall = round(
            section["score"] * 0.40
            + formatting["score"] * 0.25
            + experience["score"] * 0.35,
            1
        )

    # Determine grade
    if overall >= 80:
        grade = "A"
        grade_label = "Excellent"
    elif overall >= 65:
        grade = "B"
        grade_label = "Good"
    elif overall >= 50:
        grade = "C"
        grade_label = "Fair"
    elif overall >= 35:
        grade = "D"
        grade_label = "Needs Improvement"
    else:
        grade = "F"
        grade_label = "Poor"

    breakdown = {
        "section_completeness": {"weight": "40%" if not has_jd else "25%", **section},
        "formatting_quality": {"weight": "25%" if not has_jd else "15%", **formatting},
        "experience_relevance": {"weight": "35%" if not has_jd else "20%", **experience},
    }

    if has_jd:
        breakdown["keyword_match"] = {"weight": "40%", **keyword}

    return {
        "overall_score": min(overall, 100),
        "grade": grade,
        "grade_label": grade_label,
        "has_jd": has_jd,
        "breakdown": breakdown,
    }

