# Advanced RAG System — Intelligent Chatbot

> Ask questions about ~2000 software licenses in plain language.

---

## The idea

A company manages roughly thousand of software licenses split between EU and US clients. Each license has two layers of information:

- **Structured metadata** in CSV files — company name, contact, status, expiration date, SLA level, payment status, department, risk rating, etc.
- **A PDF contract** with the actual legal text — termination clauses, audit terms, data residency, etc.

Before this, finding anything meant opening a spreadsheet, filtering columns, then manually opening PDFs. This chatbot replaces that whole process with a single text input.

You type something like *"which licenses in the engineering department expire this year?"* or *"what does EU-A-A1-000003 say about cancellation?"* — and it figures out where to look, retrieves the data, and writes a plain-language answer.

---

## How the routing works

The interesting part is that not every question is answered the same way. There are 5 routes:

| Route | When it triggers | What happens |
|-------|-----------------|--------------|
| `LOOKUP` | Question contains a License ID (`EU-A-A1-000003`) and asks about its fields | Direct `SELECT *` on DuckDB |
| `SQL` | Filter, count, sort, or search by any field (VAT number, email, company…) | LLM generates a SQL query → runs on DuckDB |
| `VECTOR` | Question is about the *content* of a contract | Semantic search in ChromaDB over PDF chunks |
| `HYBRID` | Needs both structured data and contract content | SQL + vector search combined |
| `GLOSSARY` | Asking what a field means ("what is Risk Rating?") | Answered from a static dictionary detailed by internal team |

The classification itself is done by calling Mistral with a short prompt. It's not a fancy classifier — just a zero-shot LLM call that's surprisingly reliable once the examples in the prompt are specific enough.

For vector searches, the system generates 3 rephrased versions of the question before searching (multi-query RAG). This increases recall because the same concept can be phrased differently across contracts.

---

## Architecture

```
User question
    │
    ▼
classify()          ← the LLM decides the route
    │
    ├─ LOOKUP   → DuckDB: SELECT * WHERE "License ID" = ?
    ├─ SQL      → Mistral generates SQL → DuckDB
    ├─ VECTOR   → embed question (×4 with rephrasing) → ChromaDB top-10 chunks
    ├─ HYBRID   → SQL + VECTOR combined
    └─ GLOSSARY → static dict lookup
    │
    ▼
synthesize()        ← Mistral writes the final answer in the user's language
    │
    ▼
JSON response:  answer · category · pdf_links · confidence · raw context
```

---

## My Stack

| What | Tool |
|------|------|
| API | FastAPI |
| Structured DB | DuckDB |
| Vector DB | ChromaDB |
| Embeddings | `Qwen/Qwen3-Embedding-0.6B` via SentenceTransformers |
| LLM | Mistral API (`mistral-small-latest`) — via OpenAI-compatible client |
| PDF extraction | pdfplumber (native) + pytesseract (scanned PDFs) |
| Frontend | Vanilla HTML/CSS/JS, embedded directly in `app.py` |

No frontend framework, no separate build step — the entire UI is served from a single Python string. It keeps deployment simple.

---

## Project structure

```
.
├── app.py          # FastAPI server + the entire HTML/JS UI as a string
├── router.py       # Core logic: classify, retrieve, synthesize, confidence
├── build_db.py     # One-time script: merges EU_ALL.csv + US_ALL.csv into DuckDB
├── index.py        # One-time script: extracts PDF text, chunks it, embeds + stores in ChromaDB
├── glossary.py     # Static field definitions + alias map for GLOSSARY route
├── data/
│   ├── table/
│   │   ├── EU_ALL.csv      # ~600 EU license records
│   │   └── US_ALL.csv      # ~1400 US license records
│   ├── pdf/
│   │   ├── EU/             # Contract PDFs named by License ID
│   │   └── US/
│   ├── master.duckdb       # Built by build_db.py
│   └── chroma/             # Vector index built by index.py
├── .env
└── requirements.txt
```

---

## Setup

**1. Clone and install**
```bash
git clone https://github.com/lmveprog/advanced-rag-system
cd advanced-rag-system
python -m venv .venv
source .venv/bin/activate  # on windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**2. Configure `.env`**
```
MISTRAL_API_KEY=your_key_here 
LLM_MODEL=mistral-small-latest
DATA_DIR=./data
```

# https://console.mistral.ai/upgrade/plans you can firstly setup your project on Mistral AI Studio with experiment plan (Free)

**3. Build the database** — only needed once, or when CSVs change
```bash
python build_db.py
```

**4. Index the PDFs** — only needed once, or when new PDFs are added
```bash
python index.py
```

**5. Start**
```bash
uvicorn app:app --reload
```

Open `http://localhost:8000`.

---

## A few things worth knowing

**License ID format** — IDs follow the pattern `XX-X-XX-XXXXXX` (e.g. `EU-A-A1-000003`). Mentioning one in your question routes it directly to a lookup or filters the vector search to that specific contract.

**Scanned PDFs** — Files ending in `_SCAN` are processed with OCR (pytesseract) instead of pdfplumber. Both go through the same chunking and embedding pipeline afterward.

**SQL generation** — Mistral writes the SQL queries at runtime. The router auto-corrects a few common mistakes the model makes: wrong `ILIKE` syntax, treating date columns as dates instead of VARCHAR, missing `GROUP BY` columns. It's not perfect — complex queries can still fail — but it handles most natural language filters correctly.

**Confidence score** — Every response includes a score from 5 to 98. It's a heuristic based on the route, how much context was retrieved, and whether the answer contains phrases like "not found" or "no data". It's useful as a rough signal, not a calibrated probability.

**Conversation history** — The UI keeps the last 6 exchanges and sends them to the LLM on each call, so you can ask follow-up questions without repeating context.
