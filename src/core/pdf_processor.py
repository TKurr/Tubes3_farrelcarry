# src/core/pdf_processor.py

# This module contains functions for PDF processing, including text extraction
# with an OCR fallback, and various text formatting utilities.
# The core functions were provided by a teammate.

import os
import re
import json
from typing import Iterator
import pdfplumber
import pytesseract
from PIL import Image

from config import DATA_DIR

# --- Original Functions from Teammate ---


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
                    im = page.to_image(resolution=300).original
                    ocr_text = pytesseract.image_to_string(im)
                    all_text += ocr_text + "\n"
    except Exception as e:
        print(f"[PdfProcessor] Failed to process {pdf_path}: {e}")
    return all_text


def clean_text(text: str) -> str:
    """Performs basic cleaning on the raw extracted text."""
    text = text.replace("•", "-").replace("–", "-")
    text = re.sub(r"\n+", "\n", text)
    return text.strip()


def format_sectioned_text(text: str) -> str:
    """Formats the cleaned text into a structured, sectioned string."""
    section_titles = [
        "Skills",
        "Summary",
        "Highlights",
        "Accomplishments",
        "Experience",
        "Education",
    ]
    lines = text.split("\n")
    output = {}
    current_section = "Header"
    output[current_section] = []

    for line in lines:
        clean_line = line.strip()
        if not clean_line:
            continue
        title_match = next(
            (title for title in section_titles if title.lower() in clean_line.lower()),
            None,
        )
        if title_match:
            current_section = title_match
            output[current_section] = []
            continue
        output[current_section].append(clean_line)

    result = ""
    for section, items in output.items():
        result += f"{section}\n\n"
        for item in items:
            result += f"{item}\n"
        result += "\n"
    return result.strip()


def format_flat_text(text: str) -> str:
    """Flattens text for pattern matching by removing special chars and extra spaces."""
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.lower().strip()


def convert_pdf_to_json(pdf_path: str, json_output_path: str):
    """Utility function to process a single PDF and save the output as JSON."""
    raw_text = extract_text_from_pdf(pdf_path)
    cleaned = clean_text(raw_text)
    structured = format_sectioned_text(cleaned)
    flat = format_flat_text(cleaned)

    result = {"structured": structured, "flattened": flat}

    with open(json_output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"JSON saved to: {json_output_path}")


# --- Helper Function for SearchService ---


def find_pdf_files() -> Iterator[str]:
    """
    A necessary helper to discover all PDF files for the SearchService to iterate over.
    Yields the full path for each PDF file found in the DATA_DIR.
    """
    if not os.path.isdir(DATA_DIR):
        print(f"[PdfProcessor] Error: Data directory not found at '{DATA_DIR}'")
        return
    for root, _, files in os.walk(DATA_DIR):
        for file in files:
            if file.lower().endswith(".pdf"):
                yield os.path.join(root, file)
