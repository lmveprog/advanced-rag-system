import duckdb
import chromadb
from sentence_transformers import SentenceTransformer
from pathlib import Path
from dotenv import load_dotenv
from src.ingestion.extract import extract_text
from rich import print
import os

load_dotenv()

DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))
DB_PATH = DATA_DIR / "master.duckdb"

print("[dim]Chargement modèle embedding...[/dim]")
model = SentenceTransformer("Qwen/Qwen3-Embedding-0.6B")

chroma = chromadb.PersistentClient(path=str(DATA_DIR / "chroma"))
collection = chroma.get_or_create_collection("licenses")

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunks.append(" ".join(words[i:i + chunk_size]))
        i += chunk_size - overlap
    return chunks

def safe_str(val) -> str:
    return str(val) if val else ""

def index_all():
    con = duckdb.connect(str(DB_PATH))
    rows = con.execute("""
        SELECT "License ID", source_region, pdf_path, "Company Name"
        FROM licenses
        WHERE pdf_path IS NOT NULL
        AND pdf_indexed = false
    """).fetchall()
    con.close()

    print(f"[bold]PDFs à indexer : {len(rows)}[/bold]")

    for i, (license_id, source_region, pdf_path, company) in enumerate(rows):
        print(f"[{i+1}/{len(rows)}] {license_id} — {company}")

        text, method = extract_text(pdf_path)
        if not text:
            print(f"  [red]Texte vide, skip[/red]")
            continue

        print(f"  [dim]{method} | {len(text)} chars[/dim]")

        chunks = chunk_text(text)
        embeddings = model.encode(chunks, batch_size=64, show_progress_bar=False).tolist()

        collection.add(
            ids=[f"{safe_str(license_id)}_chunk_{j}" for j in range(len(chunks))],
            embeddings=embeddings,
            documents=chunks,
            metadatas=[
                {
                    "license_id": safe_str(license_id),
                    "region": safe_str(source_region),
                    "company": safe_str(company),
                    "chunk": j
                }
                for j in range(len(chunks))
            ]
        )

        con = duckdb.connect(str(DB_PATH))
        con.execute("UPDATE licenses SET pdf_indexed = true WHERE \"License ID\" = ?", [license_id])
        con.close()

    print("[bold green]Indexation terminée[/bold green]")

if __name__ == "__main__":
    index_all()
