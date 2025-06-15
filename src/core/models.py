from typing import List, Dict
from dataclasses import dataclass, field
from datetime import date


@dataclass
class Applicant:
    applicant_id: int
    first_name: str
    last_name: str
    date_of_birth: date
    address: str
    phone_number: str

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


@dataclass
class Application:
    detail_id: int
    applicant_id: int
    application_role: str
    cv_path: str


@dataclass
class CVDocument:
    cv_id: int 
    raw_pdf_path: str
    text_for_pattern_matching: str
    text_for_regex: str
    extracted_skills: List[str] = field(default_factory=list)
    extracted_job_history: List[Dict[str, str]] = field(default_factory=list)
    extracted_education: List[Dict[str, str]] = field(default_factory=list)
    extracted_summary_overview: str = ""

    def apply_regex_extraction(self, extractor):
        self.extracted_skills = extractor.extract_skills(self.text_for_pattern_matching)
        self.extracted_job_history = extractor.extract_job_history(self.text_for_pattern_matching)
        self.extracted_education = extractor.extract_education(self.text_for_pattern_matching)
        self.extracted_summary_overview = extractor.extract_summary(self.text_for_pattern_matching)


@dataclass
class SearchResult:
    applicant_id: int
    detail_id: int
    applicant_name: str
    application_role: str
    matched_keywords: Dict[str, int]

    @property
    def total_matches(self) -> int:
        return sum(self.matched_keywords.values())

    def to_dict(self) -> Dict:
        return {
            "applicant_id": self.applicant_id,
            "detail_id": self.detail_id,
            "applicant_name": self.applicant_name,
            "application_role": self.application_role,
            "matched_keywords": self.matched_keywords,
            "total_matches": self.total_matches,
        }


@dataclass
class CVSummary:
    applicant_name: str
    birthdate: date
    address: str
    phone_number: str
    skills: List[str]
    job_history: List[Dict[str, str]]
    education: List[Dict[str, str]]
    overall_summary: str
    cv_path: str
