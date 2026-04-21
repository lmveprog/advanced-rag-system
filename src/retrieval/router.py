import duckdb
import chromadb
from sentence_transformers import SentenceTransformer
from openai import OpenAI
from pathlib import Path
from dotenv import load_dotenv
import os
import re

load_dotenv()

DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))
DB_PATH = DATA_DIR / "master.duckdb"

mistral = OpenAI(
    base_url="https://api.mistral.ai/v1",
    api_key=os.getenv("MISTRAL_API_KEY")
)
LLM_MODEL = os.getenv("LLM_MODEL", "mistral-small-latest")

embed_model = SentenceTransformer("Qwen/Qwen3-Embedding-0.6B")
chroma = chromadb.PersistentClient(path=str(DATA_DIR / "chroma"))
collection = chroma.get_or_create_collection("licenses")

SCHEMA = """
Table DuckDB: licenses
Toutes les colonnes utilisent des guillemets doubles.

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
- "Seats Licensed"     : nombre de sièges autorisés (INTEGER)
- "Seats Used"         : nombre de sièges utilisés (INTEGER)
- "Annual Fee"         : montant annuel EU (VARCHAR)
- "Annual Fee (USD)"   : montant annuel US (VARCHAR)
- "Currency"           : devise EU
- "Payment Method"     : mode de paiement
- "Payment Status"     : Paid | Pending | Overdue | Partial | Waived
- "Invoice Number"     : numéro de facture
- "Issue Date"         : date d'émission
- "Expiration Date"    : date d'expiration
- "Last Renewed"       : dernière date de renouvellement
- "Next Review Date"   : prochaine date de révision
- "Renewal Frequency"  : Annual | Semi-Annual | Quarterly | Monthly | Biennial | Perpetual
- "Auto-Renew"         : Yes | No
- "SLA Level"          : Bronze | Silver | Gold | Platinum | Diamond
- "Uptime Guarantee (%)" : pourcentage de disponibilité garantie
- "Support Hours"      : heures de support (ex: 24x7, 8x5)
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
1. Toujours mettre les noms de colonnes entre guillemets doubles
2. Utiliser ILIKE pour les recherches textuelles (insensible à la casse)
3. Pour les nombres: CAST("Seats Licensed" AS INTEGER)
4. Pour les dates: "Expiration Date" > '2025-01-01'
5. Toujours ajouter ORDER BY et LIMIT 20 par défaut sauf si agrégat
6. Pour chercher plusieurs valeurs: "Status" IN ('Active', 'Pending Renewal')
"""

def classify(question: str) -> str:
    resp = mistral.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {
                "role": "system",
                "content": """Tu es un router pour un système RAG sur des licences logicielles.
Classifie la question en UNE seule catégorie :

LOOKUP  → contient un License ID explicite (format: XX-X-XX-XXXXXX)
SQL     → recherche, filtre, comptage, tri sur les données structurées des licences
VECTOR  → question sur le contenu textuel des contrats PDF (clauses, conditions, termes)
HYBRID  → nécessite données structurées ET contenu des contrats

Réponds UNIQUEMENT avec : LOOKUP, SQL, VECTOR ou HYBRID"""
            },
            {"role": "user", "content": question}
        ],
        temperature=0
    )
    return resp.choices[0].message.content.strip()

def sql_tool(question: str) -> tuple[str, str]:
    """Génère et exécute une requête SQL. Retourne (résultat, requête)."""
    resp = mistral.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {
                "role": "system",
                "content": f"""Tu es MatheusBot un expert.
{SCHEMA}
Génère UNE requête SQL valide pour répondre à la question.
Réponds UNIQUEMENT avec la requête SQL brute, sans markdown, sans explication."""
            },
            {"role": "user", "content": question}
        ],
        temperature=0
    )

    query = resp.choices[0].message.content.strip()
    query = query.replace("```sql", "").replace("```", "").strip()

    try:
        con = duckdb.connect(str(DB_PATH))
        result = con.execute(query).fetchdf()
        con.close()
        return result.to_string(index=False), query
    except Exception as e:
        return f"Erreur SQL: {e}", query

def vector_tool(question: str, filter_ids: list[str] = None) -> str:
    """Recherche sémantique dans ChromaDB."""
    embedding = embed_model.encode([question]).tolist()[0]

    where = None
    if filter_ids:
        where = {"license_id": {"$in": filter_ids}}

    results = collection.query(
        query_embeddings=[embedding],
        n_results=5,
        where=where
    )

    output = ""
    for chunk, meta in zip(results["documents"][0], results["metadatas"][0]):
        output += f"\n[{meta['license_id']} — {meta['company']}]\n{chunk}\n"
    return output

def lookup_tool(question: str) -> tuple[str, str]:
    """Lookup direct par License ID."""
    match = re.search(r'[A-Z]{2}-[A-Z]-[A-Z0-9]+-\d+', question)
    if not match:
        return "Aucun License ID trouvé.", ""

    license_id = match.group()
    con = duckdb.connect(str(DB_PATH))
    result = con.execute("""
        SELECT * FROM licenses WHERE "License ID" = ?
    """, [license_id]).fetchdf()
    con.close()

    if result.empty:
        return f"Licence {license_id} non trouvée.", license_id

    return result.T.to_string(), license_id

def synthesize(question: str, context: str, category: str) -> str:
    """LLM synthétise la réponse finale avec sources."""
    lang = "français" if any(w in question.lower() for w in ["quel", "quelle", "quels", "combien", "liste", "donne", "trouve", "cherche"]) else "the same language as the question"

    resp = mistral.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {
                "role": "system",
                "content": f"""Tu es MatheusBot, un assistant expert en management de licences.
    Tu aides les équipes internes à trouver, analyser et comprendre les licences de leur organisation.
    Réponds en {lang}, de façon claire, professionnelle et concise.
    Base ta réponse UNIQUEMENT sur le contexte fourni.
    Cite toujours les License ID sources.
    Si le contexte est vide ou insuffisant, dis-le clairement."""
            },
            {
                "role": "user",
                "content": f"Question: {question}\n\nContexte:\n{context}"
            }
        ],
        temperature=0.1
    )
    return resp.choices[0].message.content.strip()

def route(question: str) -> dict:
    """Point d'entrée principal. Retourne réponse + metadata."""
    category = classify(question)
    print(f"  [Router] → {category}")

    context = ""
    sources = []

    if category == "LOOKUP":
        context, source = lookup_tool(question)
        if source:
            sources.append(source)

    elif category == "SQL":
        context, query = sql_tool(question)
        sources.append(f"SQL: {query}")

    elif category == "VECTOR":
        context = vector_tool(question)

    elif category == "HYBRID":
        sql_context, query = sql_tool(question)
        ids = re.findall(r'[A-Z]{2}-[A-Z]-[A-Z0-9]+-\d+', sql_context)
        vector_context = vector_tool(question, filter_ids=ids if ids else None)
        context = f"=== Données ===\n{sql_context}\n\n=== Contrats ===\n{vector_context}"
        sources.append(f"SQL: {query}")

    answer = synthesize(question, context, category)

    return {
        "question": question,
        "category": category,
        "answer": answer,
        "context": context,
        "sources": sources
    }

if __name__ == "__main__":
    questions = [
        "Quel est le contact de EU-A-A1-000003 ?",
        "Combien de licences sont expirées en EU ?",
        "Show me all active Gold SLA licenses for the IT department",
        "Quelles licences High Risk ont un paiement en retard ?",
        "Find licenses expiring before 2025 with more than 100 seats",
    ]

    for q in questions:
        print(f"\n{'='*60}")
        print(f"Q: {q}")
        result = route(q)
        print(f"Réponse:\n{result['answer']}")
