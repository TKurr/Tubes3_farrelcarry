# src/core/pdf_processor.py

import os
import re
import json
from typing import Iterator, Dict, Any

import pdfplumber
import pytesseract
from PIL import Image


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extracts all text from a single PDF, using OCR as a fallback."""
    all_text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    all_text += text + "\n"
                else:
                    # fallback to OCR if no text is extracted
                    im = page.to_image(
                        resolution=300
                    ).original  # Ensure Image is imported from PIL
                    ocr_text = pytesseract.image_to_string(im)
                    all_text += ocr_text + "\n"
    except Exception as e:
        print(f"[PdfProcessor] Failed to process {pdf_path}: {e}")
    return all_text


def clean_text(
    text: str,
) -> str:
    """Removes newlines, specific chars, and normalizes whitespace."""
    text = (
        text.strip()
        .replace("\n", " ")
        .replace("\r", "")
        .replace("Â", "")
        .replace("ï¼", "")
    )
    text = re.sub(r"\s+", " ", text)
    return text


# --- Flat Text Formatting ---
def format_flat_text(text: str) -> str:
    """
    Flattens text for pattern matching by removing special chars and making it lowercase.
    Operates on the raw text to preserve as much original content as possible before flattening.
    """
    temp_text = re.sub(r"[^\w\s-]", "", text)  # Keep hyphens
    temp_text = re.sub(r"\s+", " ", temp_text)
    return temp_text.lower().strip()


# --- Detailed Information Extractor ---
def extract_detailed_info(text: str) -> Dict[str, Any]:
    """
    This is the primary function for getting detailed summary data.
    It expects text that has preserved its original structure (newlines, etc.).
    """
    flags = re.DOTALL | re.IGNORECASE

    name_pattern = re.findall(r"([A-Z][a-z]+(?: [A-Z][a-z]+)+)", text)
    name = name_pattern[0] if name_pattern else "Unknown Name"

    summary_pattern = re.findall(
        r"(Summary|Objective|Profile)(.*?)(Certifications|Skills|Experience|Education|Projects|$)",
        text,
        flags=flags,
    )
    summary = (
        summary_pattern[0][1].strip().replace("\n", " ")
        if summary_pattern
        else "No summary available"
    )

    certifications_pattern = re.findall(
        r"(Certifications|Licenses)(.*?)(Skills|Experience|Education|Projects|$)",
        text,
        flags=flags,
    )
    certifications = (
        certifications_pattern[0][1].strip().replace("\n", " ")
        if certifications_pattern
        else "No certifications available"
    )

    skills_pattern = re.findall(
        r"(Skills|Highlights|Competencies)(.*?)(Experience|Education|Projects|$)",
        text,
        flags=flags,
    )
    skills_text = skills_pattern[0][1].strip() if skills_pattern else ""
    skills = (
        sorted(
            list(
                set(
                    [
                        s.strip()
                        for s in re.split(r"[\n,;•*-]+", skills_text)
                        if s.strip() and len(s.strip()) > 1
                    ]
                )
            )
        )
        if skills_text
        else ["No skills available"]
    )

    experience_pattern = re.findall(
        r"(Experience|Work History|Employment)(.*?)(Education|Skills|Projects|$)",
        text,
        flags=flags,
    )
    experience_text = experience_pattern[0][1].strip() if experience_pattern else ""
    experience_entries = re.split(r"\n\s*\n+", experience_text)
    experience = [
        exp.replace("\n", " ").strip() for exp in experience_entries if exp.strip()
    ]
    if not experience:
        experience = ["No experience listed"]

    education_pattern = re.findall(
        r"(Education|Academic Background)(.*?)(Skills|Experience|Projects|$)",
        text,
        flags=flags,
    )
    education_text = education_pattern[0][1].strip() if education_pattern else ""
    education_entries = [
        edu.replace("\n", " ").strip()
        for edu in education_text.split("\n")
        if edu.strip()
    ]
    if not education_entries:
        education_entries = ["No education listed"]

    projects_pattern = re.findall(
        r"(Projects|Personal Projects)(.*?)(Skills|Experience|Education|$)",
        text,
        flags=flags,
    )
    projects_text = projects_pattern[0][1].strip() if projects_pattern else ""
    project_entries = re.split(r"\n\s*\n+", projects_text)
    projects = [
        proj.replace("\n", " ").strip() for proj in project_entries if proj.strip()
    ]
    if not projects:
        projects = ["No projects listed"]

    # Contact Info (using your new regex's approach)
    contact_pattern_header = re.findall(
        r"(Contact Information|Contact)(.*?)(PROFILE|SUMMARY|OBJECTIVE|EXPERIENCE|SKILLS|EDUCATION|PROJECTS|CERTIFICATIONS|$)",
        text,
        flags=flags,
    )
    contact_info_block = (
        contact_pattern_header[0][1].strip() if contact_pattern_header else ""
    )

    # Try to find specific details within the block or globally if no block
    email_match = re.search(
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", contact_info_block or text
    )
    phone_match = re.search(
        r"\(?\b\d{3}\b\)?[-.\s]?\b\d{3}\b[-.\s]?\b\d{4}\b", contact_info_block or text
    )

    contact_details_list = []
    if email_match:
        contact_details_list.append(f"Email: {email_match.group(0)}")
    if phone_match:
        contact_details_list.append(f"Phone: {phone_match.group(0)}")
    contact_info_str = (
        " | ".join(contact_details_list)
        if contact_details_list
        else "No contact info found"
    )

    return {
        "Full Name": name,
        "Summary": summary,
        "Certifications": certifications,
        "Skills": skills,
        "Experience": experience,  # List of strings (experience blocks)
        "Education": education_entries,  # List of strings (education lines/blocks)
        "Projects": projects,  # List of strings (project blocks)
        "Contact Info": contact_info_str,
    }


# --- Hybrid function will now use your new extract_detailed_info ---
def extract_hybrid_info(text: str) -> Dict[str, Any]:
    """
    The 'text' input should be the raw text from the PDF (output of extract_text_from_pdf),
    as extract_detailed_info uses regex that benefits from original document structure.
    """
    return extract_detailed_info(text)


# --- Helper Function for finding files (if needed by background_parser fallback) ---
def find_pdf_files(data_directory: str) -> Iterator[str]:
    """
    A helper to discover all PDF files.
    Yields the full path for each PDF file found in the specified data_directory.
    """
    if not os.path.isdir(data_directory):
        print(f"[PdfProcessor] Error: Data directory not found at '{data_directory}'")
        return
    for root, _, files in os.walk(data_directory):
        for file_name in files:  # Renamed 'file' to 'file_name' to avoid conflict
            if file_name.lower().endswith(".pdf"):
                yield os.path.join(root, file_name)


if __name__ == "__main__":
    current_file_path = os.path.abspath(__file__)
    core_dir = os.path.dirname(current_file_path)
    src_dir = os.path.dirname(core_dir)
    project_root = os.path.dirname(src_dir)

    test_pdf_filename = "10984392.pdf"  # Example filename
    test_pdf_path = os.path.join(project_root, "data", test_pdf_filename)

    if not os.path.exists(test_pdf_path):
        print(f"Test PDF not found at: {test_pdf_path}")
        print(
            "Please ensure a PDF (e.g., 10984392.pdf) exists in the 'data' directory at the project root, or update the path."
        )
    else:
        print(f"Testing with PDF: {test_pdf_path}")

        raw_content = extract_text_from_pdf(test_pdf_path)
        print("\n--- Raw Extracted Text (first 500 chars) ---")
        print(raw_content[:500] + "..." if len(raw_content) > 500 else raw_content)

        print("\n--- Testing YOUR NEW extract_detailed_info with raw_text ---")
        detailed_info_output = extract_detailed_info(raw_content)

        for key, value in detailed_info_output.items():
            print(f"\n{key}:")
            if isinstance(value, list):
                for item in value:
                    print(f"- {item}")
            else:
                print(value)

        # 3. Test format_flat_text (for search) using the raw_content
        print("\n--- Testing format_flat_text with raw_text (first 500 chars) ---")
        flat_output = format_flat_text(raw_content)
        print(flat_output[:500] + "..." if len(flat_output) > 500 else flat_output)
