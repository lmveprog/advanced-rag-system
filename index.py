import duckdb
import chromadb
import pdfplumber
import pytesseract
import re
from pdf2image import convert_from_path
from sentence_transformers import SentenceTransformer
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))
DB_PATH = DATA_DIR / "master.duckdb"

model = SentenceTransformer("Qwen/Qwen3-Embedding-0.6B")
chroma = chromadb.PersistentClient(path=str(DATA_DIR / "chroma"))
collection = chroma.get_or_create_collection("licenses")


def clean(text: str) -> str:
    text = re.sub(r'\(cid:\d+\)', '', text)
    return re.sub(r'\s+', ' ', text).strip()


def extract(pdf_path: str) -> str:
    # scanned PDFs use OCR, native PDFs use pdfplumber
    if "_SCAN" in pdf_path:
        text = ""
        for img in convert_from_path(pdf_path, dpi=300):
            text += pytesseract.image_to_string(img, lang="eng+fra") + "\n"
        return clean(text)

    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
    return clean(text)


def chunk(text: str, size: int = 500, overlap: int = 50) -> list[str]:
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunks.append(" ".join(words[i:i + size]))
        i += size - overlap
    return chunks


def index_all():
    con = duckdb.connect(str(DB_PATH))
    rows = con.execute("""
        SELECT "License ID", source_region, pdf_path, "Company Name"
        FROM licenses
        WHERE pdf_path IS NOT NULL AND pdf_indexed = false
    """).fetchall()
    con.close()

    print(f"{len(rows)} PDFs to index")

    for i, (license_id, region, pdf_path, company) in enumerate(rows):
        print(f"[{i+1}/{len(rows)}] {license_id}")

        text = extract(pdf_path)
        if not text:
            print(f"  empty, skipping")
            continue

        chunks = chunk(text)
        embeddings = model.encode(chunks, batch_size=64, show_progress_bar=False).tolist()

        collection.add(
            ids=[f"{license_id}_chunk_{j}" for j in range(len(chunks))],
            embeddings=embeddings,
            documents=chunks,
            metadatas=[
                {"license_id": str(license_id), "region": str(region), "company": str(company or ""), "chunk_index": j}
                for j in range(len(chunks))
            ]
        )

        con = duckdb.connect(str(DB_PATH))
        con.execute('UPDATE licenses SET pdf_indexed = true WHERE "License ID" = ?', [license_id])
        con.close()

    print("done")


if __name__ == "__main__":
    index_all()
