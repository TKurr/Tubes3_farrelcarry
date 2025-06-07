import pdfplumber
import pytesseract
from PIL import Image
import re
import json

def extract_text_from_pdf(pdf_path):
    all_text = ""
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
    return all_text

def clean_text(text):
    text = text.replace('•', '-').replace('–', '-')
    text = re.sub(r'\n+', '\n', text)
    return text.strip()

def format_sectioned_text(text):
    section_titles = ['Skills', 'Summary', 'Highlights', 'Accomplishments', 'Experience', 'Education']
    lines = text.split('\n')
    output = {}
    current_section = 'Header'
    output[current_section] = []

    for line in lines:
        clean_line = line.strip()
        if not clean_line:
            continue
        title_match = next((title for title in section_titles if title.lower() in clean_line.lower()), None)
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

def format_flat_text(text):
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.lower().strip()

def convert_pdf_to_json(pdf_path, json_output_path):
    raw_text = extract_text_from_pdf(pdf_path)
    cleaned = clean_text(raw_text)
    structured = format_sectioned_text(cleaned)
    flat = format_flat_text(cleaned)

    result = {
        "structured": structured,
        "flattened": flat
    }

    with open(json_output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"JSON saved to: {json_output_path}")

# Contoh pemanggilan
convert_pdf_to_json("10554236.pdf", "cv_output.json")
# Cetak hasil JSON
with open("cv_output.json", "r", encoding="utf-8") as f:
    cv_json = json.load(f)

print("=== Structured ===\n")
print(cv_json["structured"])