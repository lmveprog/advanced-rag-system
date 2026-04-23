import duckdb
import chromadb
from sentence_transformers import SentenceTransformer
from openai import OpenAI
from pathlib import Path
from dotenv import load_dotenv
import os
import re

from glossary import glossary_lookup

load_dotenv()

DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))
DB_PATH = DATA_DIR / "master.duckdb"

# LLM client pointed at Mistral
mistral = OpenAI(base_url="https://api.mistral.ai/v1", api_key=os.getenv("MISTRAL_API_KEY"))
LLM_MODEL = os.getenv("LLM_MODEL", "mistral-small-latest")

# embedding model for vector search
embed_model = SentenceTransformer("Qwen/Qwen3-Embedding-0.6B")
chroma = chromadb.PersistentClient(path=str(DATA_DIR / "chroma"))
collection = chroma.get_or_create_collection("licenses")

LICENSE_ID_RE = re.compile(r'[A-Z]{2}-[A-Z]-[A-Z0-9]+-\d+')

SCHEMA = """
Table DuckDB: licenses

COLONNES PRINCIPALES:
- "License ID"         : identifiant unique (ex: EU-A-A1-000003, US-B-B2-000123)
- "License Key"        : clé de licence
- "Status"             : Active | Expired | Pending Renewal | Revoked | Suspended | Under Review
- "Company Name"       : nom de la société
- "Contact Name"       : nom du contact
- "Contact Email"      : email du contact
- "Contact Phone"      : téléphone
- "Country"            : Austria | Belgium | Croatia | Czech Republic | Denmark | Estonia | Finland | France | Germany | Greece | Hungary | Ireland | Italy | Luxembourg | Netherlands | Poland | Portugal | Romania | Spain | Sweden | United States
- "source_region"      : EU | US
- "Department"         : Compliance | Design | Engineering | Executive | Finance | HR | IT | Legal | Marketing | Operations | Product | R&D | Sales | Security | Support
- "License Type"       : Software - Desktop | Software - Cloud SaaS | Software - API | Software - Mobile | Software - Server | Software - Embedded | GDPR Compliant - Software | GDPR Compliant - Analytics | GDPR Compliant - Cloud Services | GDPR Compliant - Data Processing | GDPR Compliant - Communication | GDPR Compliant - AI/ML Models | Hardware - * | Service - * | Data - * | CE Marked - *
- "License Category"   : A | B | C | D
- "Risk Rating"        : Critical | High | Medium-High | Medium | Low
- "Tier"               : Free | Starter | Professional | Business | Enterprise | Unlimited
- "Compliance Level"   : Level 1 - Basic | Level 2 - Standard | Level 3 - Enhanced | Level 4 - Premium | Level 5 - Enterprise
- "GDPR Compliance Status" : Fully Compliant | Partially Compliant | Non-Compliant | Under Assessment | Remediation In Progress
- "SLA Level"          : Bronze | Silver | Gold | Platinum | Diamond
- "Seats Licensed"     : INTEGER
- "Seats Used"         : INTEGER
- "Annual Fee"         : frais annuels EU en EUR (VARCHAR)
- "Annual Fee (USD)"   : frais annuels US en USD (VARCHAR)
- "Currency"           : devise
- "Payment Method"     : mode de paiement
- "Payment Status"     : Paid | Pending | Overdue | Partial | Waived
- "Invoice Number"     : numéro de facture
- "Issue Date"         : date d'émission (VARCHAR)
- "Expiration Date"    : date d'expiration (VARCHAR)
- "Last Renewed"       : dernière date de renouvellement (VARCHAR)
- "Next Review Date"   : prochaine date de révision (VARCHAR)
- "Renewal Frequency"  : Annual | Semi-Annual | Quarterly | Monthly | Biennial | Perpetual
- "Auto-Renew"         : Yes | No
- "Uptime Guarantee (%)" : pourcentage de disponibilité garantie
- "Support Hours"      : ex: 24x7, 8x5
- "Audit Frequency"    : fréquence d'audit
- "Audit Result"       : Pass | Conditional Pass | Pass with Observations | Fail - Minor | Fail - Major | Pending
- "Cancellation Notice (Days)" : préavis d'annulation en jours
- "Software Version"   : version du logiciel
- "Repository"         : dépôt
- "Sub-Repository"     : sous-dépôt

COLONNES EU UNIQUEMENT:
- "VAT Number", "Postal Code", "Region", "Data Protection Officer", "DPO Email"
- "Support Language", "Data Residency", "Cross-Border Transfer", "Encryption Standard"
- "Last Audit Date", "CE Marking", "Environmental Compliance"

COLONNES US UNIQUEMENT:
- "State", "ZIP Code", "Data Classification", "Encryption Required"

RÈGLES SQL:
1. Toujours mettre les noms de colonnes entre guillemets doubles.

2. ILIKE est un OPÉRATEUR infix, jamais une fonction :
   CORRECT   → "Contact Name" ILIKE '%Mary Brown%'
   INCORRECT → ILIKE("Contact Name", '%Mary Brown%')

3. Pour les noms de personnes, chercher le nom complet en une seule expression.
   NE JAMAIS séparer prénom et nom en deux conditions ILIKE.

4. Les colonnes de dates sont VARCHAR — utiliser CAST pour les comparer :
   CORRECT   → CAST("Expiration Date" AS DATE) < CURRENT_DATE
   Pour un statut expiré, préférer → "Status" = 'Expired'

5. GROUP BY : toute colonne dans SELECT ou ORDER BY non agrégée doit être dans GROUP BY.

6. Pour les nombres : CAST("Seats Licensed" AS INTEGER)

7. Pour trier par frais sur toutes les licences (EU + US), utiliser COALESCE :
   ORDER BY TRY_CAST(REGEXP_REPLACE(COALESCE("Annual Fee","Annual Fee (USD)",'0'),'[^0-9.]','','g') AS DOUBLE) DESC
   Ne jamais trier uniquement sur "Annual Fee" : cela exclut les licences US.

8. LIMIT 20 par défaut sauf agrégat total. Si la question cherche UN résultat → LIMIT 1.
   Pour les listes → ORDER BY "License ID".

9. Pour chercher plusieurs valeurs : "Status" IN ('Active', 'Pending Renewal')
"""


def classify(question: str) -> str:
    resp = mistral.chat.completions.create(
        model=LLM_MODEL,
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": """Tu es un router pour un système RAG sur des licences logicielles.
Classifie la question en UNE seule catégorie :

LOOKUP  → récupérer tous les champs d'une licence dont on connaît le License ID exact (format XX-X-XX-XXXXXX)
          Ex: "Quel est le contact de EU-A-A1-000003 ?" / "Montre-moi EU-B-B2-000010"
          ⚠ LOOKUP uniquement si la question contient un License ID au format XX-X-XX-XXXXXX

SQL     → recherche, filtre, comptage, tri — y compris recherche par N'IMPORTE QUEL autre champ
          Ex: "Combien de licences expirées ?" / "Liste les licences Gold SLA du département IT"
          Ex: "Quelle licence a le VAT number HR296110703 ?"
          Ex: "Trouve la licence avec l'email john@acme.com" / "Licence avec l'invoice INV-EU-000042"
          Ex: "Quelle licence appartient à la société Acme Corp ?"

VECTOR  → contenu textuel des contrats PDF (sujet, clauses, conditions, termes, résiliation...)
          Ex: "De quoi parle EU-A-A1-000003 ?" / "What does the contract say about cancellation?"

HYBRID  → nécessite données structurées ET contenu des contrats
          Ex: "Les licences High Risk ont-elles des clauses d'audit ?"

GLOSSARY → définition ou explication d'un champ / concept du système de licences
           Ex: "Que signifie le Risk Rating ?" / "What is the SLA level?" / "C'est quoi le tier ?"

RÈGLE : License ID (XX-X-XX-XXXXXX) + question sur le CONTENU du contrat → VECTOR
        License ID (XX-X-XX-XXXXXX) + question sur des CHAMPS → LOOKUP
        Recherche par tout autre identifiant ou valeur (VAT, email, société, facture...) → SQL
        Question sur la définition d'un champ ou d'une valeur → GLOSSARY

Réponds UNIQUEMENT avec : LOOKUP, SQL, VECTOR, HYBRID ou GLOSSARY"""
            },
            {"role": "user", "content": question}
        ],
    )
    return resp.choices[0].message.content.strip()


def sql_tool(question: str) -> tuple[str, str]:
    resp = mistral.chat.completions.create(
        model=LLM_MODEL,
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": f"""Tu es un expert SQL sur des licences logicielles.
{SCHEMA}
Génère UNE requête SQL valide.
Réponds UNIQUEMENT avec la requête SQL brute, sans markdown."""
            },
            {"role": "user", "content": question}
        ],
    )
    query = resp.choices[0].message.content.strip().replace("```sql", "").replace("```", "").strip()

    #correct a sql request always failed
    query = re.sub(
        r"ILIKE\(([^,]+),\s*('[^']*')\)",
        lambda m: f"{m.group(1).strip()} ILIKE {m.group(2)}",
        query, flags=re.IGNORECASE,
    )

    try:
        con = duckdb.connect(str(DB_PATH))
        result = con.execute(query).fetchdf()
        con.close()
        return result.to_string(index=False), query
    except Exception as e:
        return f"Erreur SQL: {e}", query


def generate_sub_queries(question: str) -> list[str]:
    # multi-query: generate alternative phrasings to improve vector recall
    resp = mistral.chat.completions.create(
        model=LLM_MODEL,
        temperature=0.4,
        messages=[
            {
                "role": "system",
                "content": """Génère 3 reformulations de la question pour la recherche dans des contrats PDF.
Chaque reformulation doit aborder un angle différent (synonymes, termes juridiques, perspective différente).
Réponds avec UNIQUEMENT les 3 reformulations, une par ligne, sans numérotation."""
            },
            {"role": "user", "content": question}
        ],
    )
    lines = resp.choices[0].message.content.strip().splitlines()
    return [l.strip() for l in lines if l.strip()][:3]


def vector_tool(question: str, filter_ids: list[str] = None, multi_query: bool = True) -> tuple[str, list[dict]]:
    where = {"license_id": {"$in": filter_ids}} if filter_ids else None
    queries = [question] + (generate_sub_queries(question) if multi_query else [])
    embeddings = embed_model.encode(queries).tolist()

    seen_chunks: set[tuple] = set()
    seen_ids: set[str] = set()
    all_chunks: list[tuple[str, dict, float]] = []

    for emb in embeddings:
        results = collection.query(
            query_embeddings=[emb],
            n_results=5,
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        for chunk, meta, dist in zip(results["documents"][0], results["metadatas"][0], results["distances"][0]):
            key = (meta["license_id"], meta.get("chunk_index", chunk[:40]))
            if key not in seen_chunks:
                seen_chunks.add(key)
                all_chunks.append((chunk, meta, dist))

    all_chunks.sort(key=lambda x: x[2])
    all_chunks = all_chunks[:10]

    output = ""
    sources = []
    for chunk, meta, _ in all_chunks:
        lid = meta["license_id"]
        output += f"\n[{lid} — {meta.get('company', '')}]\n{chunk}\n"
        if lid not in seen_ids:
            seen_ids.add(lid)
            sources.append({"license_id": lid, "company": meta.get("company", ""), "region": meta.get("region", "")})

    return output, sources


def lookup_tool(question: str) -> tuple[str, str]:
    match = LICENSE_ID_RE.search(question)
    if not match:
        return "Aucun License ID trouvé.", ""

    license_id = match.group()
    con = duckdb.connect(str(DB_PATH))
    result = con.execute('SELECT * FROM licenses WHERE "License ID" = ?', [license_id]).fetchdf()
    con.close()

    if result.empty:
        return f"Licence {license_id} non trouvée.", license_id
    return result.T.to_string(), license_id


def get_pdf_links(license_ids: list[str]) -> list[dict]:
    if not license_ids:
        return []
    unique_ids = list(dict.fromkeys(license_ids))[:15]
    placeholders = ", ".join(["?"] * len(unique_ids))
    try:
        con = duckdb.connect(str(DB_PATH))
        rows = con.execute(
            f'SELECT "License ID", "Company Name", source_region, pdf_path FROM licenses WHERE "License ID" IN ({placeholders})',
            unique_ids
        ).fetchall()
        con.close()
    except Exception:
        return []

    return [
        {"license_id": lid, "company": company or "", "region": region or "", "url": f"/pdf/{region}/{Path(pdf_path).name}"}
        for lid, company, region, pdf_path in rows if pdf_path
    ]


def compute_confidence(category: str, context: str, pdf_links_count: int, answer: str) -> int:
    if not context.strip():
        return 5
    if "Erreur SQL" in context:
        return 8

    negative_signals = [
        "aucune correspondance", "non trouvée", "non mentionnée", "insuffisant",
        "pas d'information", "no information", "not found", "not mentioned",
        "aucune donnée", "aucune licence", "aucune mention",
    ]
    negative_hits = sum(1 for s in negative_signals if s in answer.lower())

    if category == "LOOKUP":
        score = 92 if len(context) > 200 else 15
    elif category == "SQL":
        score = min(75 + context.strip().count("\n") * 2, 92)
    elif category == "VECTOR":
        score = min(55 + pdf_links_count * 7, 90)
    elif category == "HYBRID":
        score = min(65 + pdf_links_count * 4, 93)
    else:
        score = 40

    score -= negative_hits * 18
    if pdf_links_count == 0 and category in ("VECTOR", "HYBRID"):
        score -= 25

    return max(5, min(score, 98))


def synthesize(question: str, context: str, category: str, history: list[dict] | None = None) -> str:
    system = """Tu es MatheusBot, un assistant expert en management de licences.
RÈGLE ABSOLUE : réponds TOUJOURS dans la même langue que la question de l'utilisateur. Si la question est en anglais, réponds en anglais. Si elle est en français, réponds en français. Peu importe la langue du contexte.

Base ta réponse UNIQUEMENT sur le contexte fourni. Cite toujours les License ID sources.
Utilise le markdown pour structurer ta réponse quand c'est pertinent (listes, gras, tableaux).

- Vérifie que chaque résultat correspond EXACTEMENT à ce qui est demandé.
- Ne jamais inventer ni approximer des données absentes du contexte.
- Si le contexte est vide ou sans correspondance exacte, dis-le clairement."""

    messages = [{"role": "system", "content": system}]
    if history:
        messages.extend(history[-6:])  # max 3 échanges précédents
    messages.append({"role": "user", "content": f"Question: {question}\n\nContexte:\n{context}"})

    resp = mistral.chat.completions.create(
        model=LLM_MODEL,
        temperature=0.1,
        messages=messages,
    )
    return resp.choices[0].message.content.strip()


def route(question: str, history: list[dict] | None = None) -> dict:
    question_ids = LICENSE_ID_RE.findall(question)
    category = classify(question)
    print(f"[router] {category}")

    context = ""
    all_ids: list[str] = []
    sources = []

    if category == "GLOSSARY":
        context = glossary_lookup(question)
        if not context:
            context = "Aucune définition trouvée pour ce champ dans le glossaire."

    elif category == "LOOKUP":
        context, license_id = lookup_tool(question)
        if license_id:
            all_ids.append(license_id)
            sources.append(license_id)

    elif category == "SQL":
        context, query = sql_tool(question)
        all_ids = LICENSE_ID_RE.findall(context)
        sources.append(f"SQL: {query}")

    elif category == "VECTOR":
        filter_ids = question_ids or None
        # skip multi-query when the question already targets a specific license
        context, vec_sources = vector_tool(question, filter_ids=filter_ids, multi_query=not question_ids)
        all_ids = [s["license_id"] for s in vec_sources]
        if not all_ids and filter_ids:
            context, vec_sources = vector_tool(question, multi_query=False)
            all_ids = [s["license_id"] for s in vec_sources]

    elif category == "HYBRID":
        sql_context, query = sql_tool(question)
        sql_ids = LICENSE_ID_RE.findall(sql_context)
        filter_ids = question_ids or sql_ids or None
        vec_context, vec_sources = vector_tool(question, filter_ids=filter_ids, multi_query=True)
        context = f"=== Données ===\n{sql_context}\n\n=== Contrats ===\n{vec_context}"
        all_ids = sql_ids + [s["license_id"] for s in vec_sources]
        sources.append(f"SQL: {query}")

    answer = synthesize(question, context, category, history)

    # show only the relevant PDF: one ID in question → that one, one ID in answer → that one, else all
    if len(question_ids) == 1:
        pdf_links = get_pdf_links(question_ids)
    else:
        answer_ids = LICENSE_ID_RE.findall(answer)
        pdf_links = get_pdf_links(answer_ids if len(answer_ids) == 1 else all_ids)

    return {
        "question": question,
        "category": category,
        "answer": answer,
        "context": context,
        "sources": sources,
        "pdf_links": pdf_links,
        "confidence": compute_confidence(category, context, len(pdf_links), answer),
    }
