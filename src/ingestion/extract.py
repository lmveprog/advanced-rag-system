import pdfplumber
import pytesseract
from pdf2image import convert_from_path
from rich import print
import re

def clean_text(text: str) -> str:
    text = re.sub(r'\(cid:\d+\)', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_native(pdf_path: str) -> str:
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text += t + "\n"
    except Exception as e:
        print(f"[red]pdfplumber error: {e}[/red]")
    return clean_text(text)

def extract_ocr(pdf_path: str) -> str:
    text = ""
    try:
        images = convert_from_path(pdf_path, dpi=300)
        for img in images:
            t = pytesseract.image_to_string(img, lang="eng+fra")
            if t:
                text += t + "\n"
    except Exception as e:
        print(f"[red]OCR error: {e}[/red]")
    return clean_text(text)

def extract_text(pdf_path: str) -> tuple[str, str]:
    if "_SCAN" in pdf_path:
        return extract_ocr(pdf_path), "ocr"
    return extract_native(pdf_path), "native"
