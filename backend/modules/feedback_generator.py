"""
Feedback Generator for the AI Resume Analyzer.

Produces actionable, prioritized improvement suggestions based on
the ATS score breakdown, missing skills, and resume content analysis.
Each suggestion has a category, priority level, and human-readable message.
"""

from modules.skills_data import get_skill_category


def generate_feedback(
    resume_data: dict,
    ats_result: dict,
    missing_keywords: list[str],
    matched_keywords: list[str],
) -> list[dict]:
    """
    Generate a list of improvement suggestions.

    Each suggestion:
    {
        "category": str,       # e.g., "Missing Skills", "Formatting"
        "priority": str,       # "high", "medium", or "low"
        "icon": str,           # Emoji for UI display
        "message": str,        # Human-readable suggestion
    }
    """
    suggestions = []
    breakdown = ats_result.get("breakdown", {})

    # ── 1. Missing Skills Feedback ────────────────────────────────────
    if missing_keywords:
        # Group missing keywords by category
        categorized = {}
        for kw in missing_keywords[:15]:  # Limit to top 15
            cat = get_skill_category(kw)
            categorized.setdefault(cat, []).append(kw)

        for cat, skills in categorized.items():
            skills_str = ", ".join(s.title() for s in skills[:5])
            suggestions.append({
                "category": "Missing Skills",
                "priority": "high",
                "icon": "🎯",
                "message": (
                    f"Add these {cat} skills mentioned in the job description: "
                    f"{skills_str}"
                ),
            })

    # ── 2. Section Completeness Feedback ──────────────────────────────
    section_info = breakdown.get("section_completeness", {})
    missing_sections = section_info.get("missing_sections", [])

    section_messages = {
        "summary": (
            "Add a Professional Summary at the top of your resume. "
            "A 2-3 sentence summary helps recruiters quickly understand your profile."
        ),
        "skills": (
            "Add a dedicated Skills section. "
            "List your technical skills in a scannable format for ATS systems."
        ),
        "experience": (
            "Add a Work Experience section with your job history. "
            "Include job title, company, dates, and bullet-point achievements."
        ),
        "education": (
            "Add an Education section with your degree, institution, and graduation year."
        ),
        "contact": (
            "Ensure your contact information (email, phone) is clearly visible "
            "at the top of your resume."
        ),
        "projects": (
            "Consider adding a Projects section to showcase hands-on work, "
            "especially if you have limited work experience."
        ),
        "certifications": (
            "Add relevant certifications to strengthen your candidacy."
        ),
    }

    for section in missing_sections:
        msg = section_messages.get(section)
        if msg:
            priority = "high" if section in {"summary", "skills", "experience", "education"} else "medium"
            suggestions.append({
                "category": "Missing Section",
                "priority": priority,
                "icon": "📋",
                "message": msg,
            })

    # ── 3. Formatting Feedback ────────────────────────────────────────
    fmt_info = breakdown.get("formatting_quality", {})
    for penalty in fmt_info.get("penalties", []):
        suggestions.append({
            "category": "Formatting",
            "priority": "medium",
            "icon": "📐",
            "message": penalty,
        })

    # ── 4. Experience Quality Feedback ────────────────────────────────
    exp_info = breakdown.get("experience_relevance", {})
    exp_score = exp_info.get("score", 0)

    # Action verbs
    verb_count = len(exp_info.get("action_verbs_found", []))
    if verb_count < 5:
        suggestions.append({
            "category": "Action Verbs",
            "priority": "high" if verb_count < 2 else "medium",
            "icon": "💪",
            "message": (
                "Use more strong action verbs to begin your bullet points. "
                "Examples: 'Architected', 'Spearheaded', 'Optimized', "
                "'Streamlined', 'Delivered', 'Automated'."
            ),
        })

    # Quantifiable achievements
    quant_count = exp_info.get("quantified_achievements", 0)
    if quant_count < 3:
        suggestions.append({
            "category": "Achievements",
            "priority": "high",
            "icon": "📊",
            "message": (
                "Include more measurable achievements with numbers. "
                "Examples: 'Reduced page load time by 40%', "
                "'Managed a team of 8 engineers', "
                "'Increased revenue by $500K annually'."
            ),
        })

    # ── 5. Keyword Match Feedback ─────────────────────────────────────
    kw_info = breakdown.get("keyword_match", {})
    overlap = kw_info.get("overlap_percentage", 0)

    if overlap < 30:
        suggestions.append({
            "category": "Keyword Optimization",
            "priority": "high",
            "icon": "🔑",
            "message": (
                f"Your resume matches only {overlap:.0f}% of job description keywords. "
                "Tailor your resume to include relevant terms from the job posting."
            ),
        })
    elif overlap < 60:
        suggestions.append({
            "category": "Keyword Optimization",
            "priority": "medium",
            "icon": "🔑",
            "message": (
                f"Keyword coverage is {overlap:.0f}%. Good start, but try to "
                "weave in more job-specific terms naturally throughout your resume."
            ),
        })

    # ── 6. General Best Practices ─────────────────────────────────────
    word_count = resume_data.get("word_count", 0)

    if not resume_data.get("email"):
        suggestions.append({
            "category": "Contact Info",
            "priority": "high",
            "icon": "📧",
            "message": "No email address detected. Add a professional email address.",
        })

    if not resume_data.get("phone"):
        suggestions.append({
            "category": "Contact Info",
            "priority": "medium",
            "icon": "📱",
            "message": "No phone number detected. Consider adding a phone number.",
        })

    if matched_keywords:
        suggestions.append({
            "category": "Strengths",
            "priority": "low",
            "icon": "✅",
            "message": (
                f"Great job! Your resume includes {len(matched_keywords)} "
                f"matching keywords: {', '.join(k.title() for k in matched_keywords[:8])}..."
            ),
        })

    # Sort: high priority first, then medium, then low
    priority_order = {"high": 0, "medium": 1, "low": 2}
    suggestions.sort(key=lambda s: priority_order.get(s["priority"], 1))

    return suggestions
