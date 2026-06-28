# advanced-rag-system

a rag chatbot i built for a school project: you ask questions about ~2000
software licenses in plain language, and it figures out where to look and writes
the answer back.

## the idea

the setup is a company managing around two thousand software licenses split
between EU and US clients. each license has two layers of information:

- **structured metadata** in csv files - company name, contact, status,
  expiration date, sla level, payment status, department, risk rating, etc.
- **a pdf contract** with the actual legal text - termination clauses, audit
  terms, data residency, and so on.

before something like this, finding anything meant opening a spreadsheet,
filtering columns, then digging through pdfs by hand. the chatbot replaces that
whole thing with a single text box. you type *"which licenses in the engineering
department expire this year?"* or *"what does EU-A-A1-000003 say about
cancellation?"* and it works out where to look, pulls the data, and answers in
plain language.

## how the routing works

the interesting part is that not every question is answered the same way. there
are 5 routes:

| route | when it triggers | what happens |
|-------|-----------------|--------------|
| `LOOKUP` | the question contains a license id (`EU-A-A1-000003`) and asks about its fields | direct `SELECT *` on duckdb |
| `SQL` | filter, count, sort, or search by any field (vat number, email, company…) | the llm generates a sql query → runs on duckdb |
| `VECTOR` | the question is about the *content* of a contract | semantic search in chromadb over pdf chunks |
| `HYBRID` | needs both structured data and contract content | sql + vector search combined |
| `GLOSSARY` | asking what a field means ("what is risk rating?") | answered from a static dictionary |

the classification itself is a short prompt sent to mistral - not a fancy
classifier, just a zero-shot llm call that turned out surprisingly reliable once
the examples in the prompt got specific enough.

for vector searches the system generates 3 rephrased versions of the question
before searching (multi-query rag). that bumps recall, because the same concept
gets phrased differently across contracts.

## architecture

```
user question
    │
    ▼
classify()          ← the llm decides the route
    │
    ├─ LOOKUP   → duckdb: SELECT * WHERE "License ID" = ?
    ├─ SQL      → mistral generates sql → duckdb
    ├─ VECTOR   → embed question (×4 with rephrasing) → chromadb top-10 chunks
    ├─ HYBRID   → sql + vector combined
    └─ GLOSSARY → static dict lookup
    │
    ▼
synthesize()        ← mistral writes the final answer in the user's language
    │
    ▼
json response:  answer · category · pdf_links · confidence · raw context
```

## the stack

| what | tool |
|------|------|
| api | fastapi |
| structured db | duckdb |
| vector db | chromadb |
| embeddings | `Qwen/Qwen3-Embedding-0.6B` via sentence-transformers |
| llm | mistral api (`mistral-small-latest`), openai-compatible client |
| pdf extraction | pdfplumber (native) + pytesseract (scanned pdfs) |
| frontend | vanilla html/css/js, embedded directly in `app.py` |

no frontend framework, no separate build step - the whole ui is served from a
single python string, which keeps the thing simple.

## project structure

```
.
├── app.py          # fastapi server + the entire html/js ui as a string
├── router.py       # core logic: classify, retrieve, synthesize, confidence
├── build_db.py     # merges EU_ALL.csv + US_ALL.csv into duckdb
├── index.py        # extracts pdf text, chunks it, embeds + stores in chromadb
├── glossary.py     # static field definitions + alias map for the GLOSSARY route
└── data/
    ├── table/      # EU_ALL.csv (~600 records) + US_ALL.csv (~1400 records)
    ├── pdf/        # contract pdfs named by license id (EU/ and US/)
    ├── master.duckdb
    └── chroma/     # the vector index
```

## a few things worth knowing

**license id format** - ids follow `XX-X-XX-XXXXXX` (e.g. `EU-A-A1-000003`).
mentioning one in a question routes it straight to a lookup, or filters the
vector search down to that specific contract.

**scanned pdfs** - files ending in `_SCAN` go through ocr (pytesseract) instead of
pdfplumber, then hit the same chunking and embedding pipeline as everything else.

**sql generation** - mistral writes the queries at runtime, and the router
auto-corrects a few mistakes the model keeps making: wrong `ILIKE` syntax,
treating date columns as dates instead of varchar, missing `GROUP BY` columns.
not perfect - complex queries can still fail - but it handles most natural
language filters fine.

**confidence score** - every response carries a score from 5 to 98. it's a
heuristic based on the route, how much context got retrieved, and whether the
answer contains phrases like "not found". useful as a rough signal, not a
calibrated probability.

**conversation history** - the ui keeps the last 6 exchanges and sends them along
on each call, so follow-up questions work without repeating context.
