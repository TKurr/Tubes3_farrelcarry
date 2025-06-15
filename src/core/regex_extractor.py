# src/core/regex_extractor.py

# This module contains the advanced logic for extracting structured
# information from a cleaned CV text string using Regex.

import re

# --- Section Keyword Definitions ---

skill_sections = ["skills", "skill highlights", "summary of skills", "competencies"]

experience_sections = [
    "work history",
    "work experience",
    "experience",
    "professional experience",
    "professional history",
    "employment history",
]

education_sections = ["education", "education and training", "educational background"]

# A comprehensive list to identify the start of the *next* section,
# which helps find the end of the current section.
all_known_sections = (
    skill_sections
    + experience_sections
    + education_sections
    + [
        "summary",
        "highlights",
        "professional summary",
        "core qualifications",
        "languages",
        "professional profile",
        "relevant experience",
        "affiliations",
        "certifications",
        "qualifications",
        "accomplishments",
        "additional information",
        "core accomplishments",
        "career overview",
        "core strengths",
        "interests",
        "professional affiliations",
        "online profile",
        "certifications and trainings",
        "credentials",
        "personal information",
        "career focus",
        "executive profile",
        "military experience",
        "community service",
        "presentations",
        "publications",
        "community leadership positions",
        "license",
        "computer skills",
        "volunteer work",
        "awards and publications",
        "activities and honors",
        "volunteer associations",
    ]
)

# --- Extraction Functions ---


def extract_skills(text: str) -> list[str]:
    """Extracts a list of skills from the text."""
    # Pattern to find a skill section header and capture everything until the next known header
    pattern = f"\\n({'|'.join(map(re.escape, skill_sections))})\\n(.*?)(?=\\n({'|'.join(map(re.escape, all_known_sections))})\\n|$)"
    match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
    if match:
        body = match.group(2).strip()
        # Split by common delimiters and clean up the results
        skills = [s.strip() for s in re.split(r",|\n|;|•|-", body) if s.strip()]
        return skills
    return []


def extract_education(text: str) -> list[str]:
    """Extracts a list of education entries from the text."""
    # This uses a different approach: looks for keywords related to institutions.
    patterns = [
        r"university of [a-zA-Z ]+",
        r"[a-zA-Z ]+ university",
        r"[a-zA-Z ]+ college",
        r"college of [a-zA-Z ]+",
        r"[a-zA-Z ]* institute of [a-zA-Z ]+",
        r"[a-zA-Z ]+ institute",
        r"[a-zA-Z ]+ high school",
        r"bachelor of [a-zA-Z ]+",
        r"master of [a-zA-Z ]+",
        r"ph\.d\. in [a-zA-Z ]+",
    ]
    education_matches = []
    for pattern in patterns:
        matches = re.findall(pattern, text, flags=re.IGNORECASE)
        education_matches.extend(matches)

    # Return a unique, cleaned list
    return sorted(list({match.strip() for match in education_matches if match.strip()}))


def extract_experience(text: str) -> list[str]:
    """Extracts job titles or experience entries from the text."""
    # Pattern to find an experience section header and capture the body
    pattern = f"\\n({'|'.join(map(re.escape, experience_sections))})\\n(.*?)(?=\\n({'|'.join(map(re.escape, all_known_sections))})\\n|$)"
    match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return []

    body = match.group(2).strip()
    # For simplicity, we'll treat each line in the experience section as a separate entry.
    # A more complex parser could be built here to find dates, companies, etc.
    experiences = [line.strip() for line in body.splitlines() if line.strip()]
    return experiences


def extract_summary(text: str) -> str:
    """Extracts the summary section from the text."""
    pattern = f"\\n(summary|objective|professional summary|profile)\\n(.*?)(?=\\n({'|'.join(map(re.escape, all_known_sections))})\\n|$)"
    match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(2).strip().replace("\n", " ")
    return "No summary available."


def extract_cv_summary(text: str) -> dict:
    """
    The main extraction orchestrator. Runs all other extraction functions.
    """
    # Use the original text (with newlines) for section-based parsing
    # We add newlines at start/end to help the regex anchors (^)
    formatted_text = "\n" + text.lower() + "\n"

    return {
        "skills": extract_skills(formatted_text),
        "experience": extract_experience(formatted_text),
        "education": extract_education(formatted_text),
        "summary": extract_summary(formatted_text),
    }
