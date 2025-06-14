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


def extract_summary(text: str) -> str:
    pattern = re.compile(
        r"(?ms)^Summary\s*(.*?)\s*(?=^(?:Highlights|Skills|Experience|Education)\b)",
        re.MULTILINE
    )
    m = pattern.search(text)
    return m.group(1).strip() if m else ""

def extract_skills(text: str) -> list[str]:
    """
    Keahlian pelamar: daftar item di section 'Highlights' atau 'Skills'.
    """
    pattern = re.compile(
        r"(?ms)^(?:Highlights|Skills)\s*(.*?)\s*(?=^(?:Accomplishments|Experience|Education)\b)",
        re.MULTILINE
    )
    m = pattern.search(text)
    if not m:
        return []
    return [line.strip() for line in m.group(1).splitlines() if line.strip()]

def extract_experience(text: str) -> list[dict[str, str]]:
    # Pertama ambil section Experience
    sec = re.search(r"(?ms)^Experience\s*(.*?)\s*(?=^Education\b|\Z)", text, re.MULTILINE)
    if not sec:
        return []
    block = sec.group(1)
    # Regex untuk setiap entry
    entry_pattern = re.compile(
        r"^(?P<company>.+?)\s+"
        r"(?P<start>\w+\s+\d{4})\s+to\s+(?P<end>\w+\s+\d{4})\s+"
        r"(?P<position>.+)$",
        re.MULTILINE
    )
    return [m.groupdict() for m in entry_pattern.finditer(block)]

def extract_education(text: str) -> list[dict[str, str]]:
    sec = re.search(
        r"(?ms)^Education\s*(?:\r?\n){2,}(.*?)(?=(?:\r?\n){2,}\S|\Z)",
        text
    )
    if not sec:
        return []

    block = sec.group(1).strip()
    entries: list[dict[str, str]] = []

    # 2) Regex untuk tiap baris entry
    line_pattern = re.compile(
        r"^"
        r"(?P<degree>[^:]+?)\s*:\s*"              
        r"[^,]+?\s*,\s*"                          
        r"(?P<graduation_date>"
          r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}"
          r"|\d{4}"
        r")\s+"
        r"(?P<institution>.+)"                   
        r"$",
        re.MULTILINE
    )

    for line in block.splitlines():
        line = line.strip()
        if not line:
            continue
        m = line_pattern.match(line)
        if m:
            d = m.groupdict()
            d["degree"]          = d["degree"].strip()
            d["graduation_date"] = d["graduation_date"].strip()
            d["institution"]     = d["institution"].strip()
            entries.append(d)

    return entries





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

import re

def format_resume(text: str) -> str:
    header_keywords = {
        'summary':    ['summary', 'overview', 'profile'],
        'skills':     ['skill', 'competenc', 'ability'],
        'experience': ['experience', 'work experience', 'professional experience', 'employment'],
        'education':  ['education', 'educational background', 'academic', 'training']
    }

    # flatten semua keyword untuk deteksi header
    all_keys = [kw for kws in header_keywords.values() for kw in kws]
    # header: baris mana saja yang mengandung salah satu keyword
    header_re = re.compile(
        r'^(?P<header>.*\b(?:' + '|'.join(all_keys) + r')\b.*)$',
        re.IGNORECASE | re.MULTILINE
    )

    # 1) Split text ke list of (raw_header, body)
    sections = []
    last_hdr = None
    last_pos = 0
    for m in header_re.finditer(text):
        hdr = m.group('header').strip()
        if last_hdr is not None:
            body = text[last_pos:m.start()].strip()
            sections.append((last_hdr, body))
        last_hdr = hdr
        last_pos = m.end()
    # section terakhir
    if last_hdr is not None:
        body = text[last_pos:].strip()
        sections.append((last_hdr, body))

    # 2) Proses tiap section
    out = []
    for raw_hdr, body in sections:
        out.append(raw_hdr.upper())
        out.append('')

        low = raw_hdr.lower()
        # cari jenis section
        sect = None
        for key, kws in header_keywords.items():
            if any(kw in low for kw in kws):
                sect = key
                break

        if sect == 'experience':
            entry_re = re.compile(
                r'(?P<title>[^\n]+)\n'
                r'(?P<daterange>[A-Za-z]+ \d{4}\s+to\s+[A-Za-z]+ \d{4})(?:\s+(?P<company_loc>.*?))?\n'
                r'(?P<details>.*?)(?=(?:[^\n]+\n[A-Za-z]+ \d{4}\s+to\s+[A-Za-z]+ \d{4})|\Z)',
                re.DOTALL
            )
            for em in entry_re.finditer(body):
                title       = em.group('title').strip()
                date_range  = em.group('daterange').strip()
                comp_loc    = em.group('company_loc') or ''
                header_line = date_range + ((' ' + comp_loc.strip()) if comp_loc.strip() else '')

                out.append(title)
                out.append(header_line)
                out.append('')

                merged = em.group('details').replace('\n', ' ')
                for sent in re.split(r'\.\s+', merged):
                    s = sent.strip().rstrip('.')
                    if s:
                        out.append(s + '.')
                out.append('')

        elif sect == 'summary':
            for sent in re.split(r'\.\s+', body):
                s = sent.strip().rstrip('.')
                if s:
                    out.append(s + '.')
            out.append('')

        elif sect == 'skills':
            for item in re.split(r'[\n,;]+', body):
                it = item.strip('- ').strip()
                if it:
                    out.append(it)
            out.append('')

        elif sect == 'education':
            for line in body.splitlines():
                it = line.strip()
                if it:
                    out.append(it)
            out.append('')

        else:
            for line in body.splitlines():
                it = line.strip()
                if it:
                    out.append(it)
            out.append('')

    return '\n'.join(out).rstrip()



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

def extract_applicant_info(text: str) -> dict[str, object]:
    SECTION_PATTERN = re.compile(
        r'^\s*(?P<header>SUMMARY|SKILLS|EXPERIENCE|EDUCATION)\s*$\n+'  
        r'(?P<body>.*?)(?=\n+^\s*(?:SUMMARY|SKILLS|EXPERIENCE|EDUCATION)\s*$|\Z)',
        re.IGNORECASE | re.MULTILINE | re.DOTALL
    )
    data = {
        'summary': '',
        'skills': [],
        'experience': [],
        'education': []
    }

    for m in SECTION_PATTERN.finditer(text):
        header = m.group('header').strip().upper()
        body   = m.group('body').strip()

        if header == 'SUMMARY':
            data['summary'] = body.replace('\n', ' ').strip()

        elif header == 'SKILLS':
            items = re.split(r'[\n,;]+', body)
            data['skills'] = [s.strip() for s in items if s.strip()]

        elif header == 'EXPERIENCE':
            lines = body.splitlines()
            i = 0
            while i < len(lines) - 1:
                pos = lines[i].strip()
                dr  = lines[i+1].strip()
                if re.match(r'[A-Za-z]+ \d{4}\s+to\s+[A-Za-z]+ \d{4}', dr):
                    data['experience'].append({
                        'position': pos,
                        'date_range': dr
                    })
                    i += 2
                else:
                    i += 1

        elif header == 'EDUCATION':
            for line in body.splitlines():
                line = line.strip()
                if not line:
                    continue

                #graduation date
                date_m = re.search(r'([A-Za-z]+ \d{4})', line)
                if not date_m:
                    continue
                grad_date = date_m.group(1)

                #degree = teks sebelum tanggal
                degree = line[:date_m.start()].strip(' ,:-')

                #institution = cari kata kunci University/College/Institute/School/Edu
                inst_m = re.search(
                    r'\b(?:University|College|Institute|School|Edu)\b.*?(?=(?:,|City|State|\s{2,}|$))',
                    line[date_m.end():],
                    re.IGNORECASE
                )
                institution = inst_m.group(0).strip(' ,') if inst_m else ''

                data['education'].append({
                    'graduation_date': grad_date,
                    'institution': institution,
                    'degree': degree
                })

    return data


if __name__ == "__main__":
    pdf_path = "../../data/ACCOUNTANT/10674770.pdf" 
    content = extract_text_from_pdf(pdf_path)
    print("Extracted Text:\n", format_resume(content))

    teks = format_resume(content)
    print("\n--- Informasi Pelamar ---\n")

    info = extract_applicant_info(teks)

    print("Ringkasan:")
    print(info['summary'], "\n")

    print("Keahlian:")
    for s in info['skills']:
        print(f"- {s}")
    print()

    print("Pengalaman Kerja:")
    for e in info['experience']:
        print(f"- {e['date_range']}: {e['position']}")
    print()

    print("Pendidikan:")
    for ed in info['education']:
        print(f"- {ed['graduation_date']}: {ed['degree']} at {ed['institution']}")

    

