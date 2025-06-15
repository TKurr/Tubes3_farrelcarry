# src/core/pdf_processor.py

# This module contains all functions for PDF processing, including text
# extraction with OCR, cleaning, and structured information extraction.

import os
import re
from typing import Iterator, Dict, Any
from pdfminer.high_level import extract_text

from config import DATA_DIR

# --- Text Extraction and Cleaning ---


def extract_pdf_text(pdf_path: str) -> str:
    """Extracts text from a PDF file using pdfminer.six."""
    try:
        return extract_text(pdf_path)
    except Exception as e:
        print(f"[PdfProcessor] Error reading {pdf_path}: {e}")
        return ""


def clean_text(text: str) -> str:
    """Cleans raw text by removing unwanted characters and normalizing whitespace."""
    text = text.strip().replace("\n", " ").replace("\r", "")
    text = re.sub(r"\s+", " ", text)
    return text


def format_flat_text(text: str) -> str:
    """Flattens text for pattern matching by removing special chars and making it lowercase."""
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.lower().strip()


# --- Structured Information Extraction ---


def extract_hybrid_info(text: str) -> dict:
    """
    Extracts structured information from the full text of a resume using Regex.
    This is the primary function for getting detailed summary data.
    """
    flags = re.DOTALL | re.IGNORECASE

    # Extract Summary
    summary_pattern = re.findall(
        r"(Summary|Objective|Profile)(.*?)(Certifications|Skills|Experience|Education|$)",
        text,
        flags=flags,
    )
    summary = (
        summary_pattern[0][1].strip().replace("\n", " ")
        if summary_pattern
        else "No summary available"
    )

    # Extract Skills
    skills_pattern = re.findall(
        r"(Skills|Highlights|Competencies)(.*?)(Experience|Education|Projects|$)",
        text,
        flags=flags,
    )
    skills_text = skills_pattern[0][1].strip() if skills_pattern else ""
    skills = sorted(
        list(
            set(
                [
                    s.strip()
                    for s in re.split(r"[\n,;•*-]", skills_text)
                    if s.strip() and len(s.strip()) > 1
                ]
            )
        )
    )

    # Extract Experience
    experience_pattern = re.findall(
        r"(Experience|Work History|Employment)(.*?)(Education|Skills|Projects|$)",
        text,
        flags=flags,
    )
    experience_text = experience_pattern[0][1].strip() if experience_pattern else ""
    experience_entries = re.split(r"\n\s*\n", experience_text)  # Split by blank lines
    experience = [
        exp.replace("\n", " ").strip() for exp in experience_entries if exp.strip()
    ]

    # Extract Education
    education_pattern = re.findall(
        r"(Education|Academic Background)(.*?)(Skills|Experience|$)", text, flags=flags
    )
    education_text = education_pattern[0][1].strip() if education_pattern else ""
    education_entries = [
        edu.replace("\n", " ").strip()
        for edu in education_text.split("\n")
        if edu.strip()
    ]

    # Extract Name (simple heuristic)
    name_match = re.match(r"^[A-Z][a-z]+(?:\s[A-Z][a-z]+)+", text)
    name = name_match.group(0) if name_match else "Unknown Name"

    return {
        "Full Name": name,
        "Summary": summary,
        "Skills": skills,
        "Experience": experience,
        "Education": education_entries,
    }


# --- Helper Function for finding files ---


def find_pdf_files() -> Iterator[str]:
    """
    A helper to discover all PDF files for the SearchService to iterate over.
    Yields the full path for each PDF file found in the DATA_DIR.
    """
    if not os.path.isdir(DATA_DIR):
        print(f"[PdfProcessor] Error: Data directory not found at '{DATA_DIR}'")
        return
    for root, _, files in os.walk(DATA_DIR):
        for file in files:
            if file.lower().endswith(".pdf"):
                yield os.path.join(root, file)
