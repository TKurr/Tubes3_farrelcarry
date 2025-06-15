import re

# Define section headers
skill_sections = ["skills", "skill highlights", "summary of skills", "competencies"]
experience_sections = ["work history", "work experience", "experience", "professional experience", "employment history"]
education_sections = ["education", "educational background", "education and training"]

# Digabungkan
all_known_sections = skill_sections + experience_sections + education_sections + [
    "summary", "career overview", "core strengths", "accomplishments", "certifications and trainings", "certifications",
    "profile", "core qualifications", "highlights", "qualifications", "training", "languages"
]

def extract_section(text: str, section_headers: list[str]) -> str:
    pattern = f"({'|'.join(map(re.escape, section_headers))})\\s*\\n?(.*?)(?=\\n({'|'.join(map(re.escape, all_known_sections))})\\s*\\n|$)"
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(2).strip()
    return ""

def extract_skills(text: str) -> list[str]:
    content = extract_section(text, skill_sections)
    # Split by commas or newlines or bullets
    return [s.strip() for s in re.split(r",|\n|•|-", content) if s.strip()]

# def extract_experience(text: str) -> list[str]:
#     pattern = r"(Work Experience|Experience|Professional Experience)(.*?)(?=(Career Overview|Core Strengths|Accomplishments|Education|$))"
#     match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
#     if match:
#         body = match.group(2).strip()
#         return [line.strip() for line in body.splitlines() if line.strip()]
#     return []

def extract_experience(text: str) -> list[dict]:
    entries = re.split(
        r"(?=(?:[A-Z][a-z/& ]{2,50}\d{4}))", flat_text  # Contoh: "Shift Supervisor Jun 2007"
    )

    result = []

    for entry in entries:
        lines = [line.strip() for line in entry.strip().split(". ") if len(line.strip()) > 10]
        if not lines:
            continue
        title = lines[0]
        descs = lines[1:]
        result.append({
            "title": title,
            "descriptions": descs
        })

    return result

def extract_education(text: str) -> list[str]:
    patterns = [
        r"[a-zA-Z]+ university",
        r"university of [a-zA-Z ]+",
        r"[a-zA-Z ]+ college",
        r"college of [a-zA-Z ]+",
        r"[a-zA-Z ]* institute of [a-zA-Z ]+",
        r"bachelor of [a-zA-Z ]+",
        r"master of [a-zA-Z ]+",
        r"ph\.?d\.? in [a-zA-Z ]+"
    ]
    results = []
    for pat in patterns:
        results += re.findall(pat, text, flags=re.IGNORECASE)
    return sorted(set([r.strip() for r in results if r.strip()]))

def extract_summary(text: str) -> str:
    pattern = r"(Career Overview|Professional Summary|Summary)(.*?)(?=(Core Strengths|Accomplishments|Education|$))"
    match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(2).strip().replace("\n", " ")
    return "No summary available."

def extract_cv_summary(text: str) -> dict:
    lower_text = "\n" + text + "\n"
    return {
        "skills": extract_skills(lower_text),
        "experience": extract_experience(lower_text),
        "education": extract_education(lower_text),
        "summary": extract_summary(lower_text),
    }
