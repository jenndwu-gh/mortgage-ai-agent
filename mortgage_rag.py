"""
Mortgage Pre-approval Agent with RAG
=====================================
Two embedding approaches:
  - Approach A: OpenAI text-embedding-3-small  (requires OPENAI_API_KEY)
  - Approach B: sentence-transformers           (fully local, no API key)

Switch by setting: EMBEDDING_APPROACH = "openai"  or  "local"
"""

import os
import json
import chromadb
import anthropic

# ── Choose your approach ────────────────────────────────────────
EMBEDDING_APPROACH = "openai"   # change to "local" for no-API-key version

# ── Clients ─────────────────────────────────────────────────────
anthropic_client = anthropic.Anthropic()          # reads ANTHROPIC_API_KEY
chroma_client    = chromadb.Client()              # in-memory, resets on restart
                                                  # use chromadb.PersistentClient(path="./chroma_db")
                                                  # to persist across sessions

# ────────────────────────────────────────────────────────────────
# PHASE 1 — Knowledge base
# In production: load real Fannie Mae / FHA guidelines PDF
# Here: mock guidelines that cover real underwriting rules
# ────────────────────────────────────────────────────────────────

GUIDELINES = [
    # Credit score rules
    {
        "id": "credit_001",
        "topic": "minimum credit score conventional loan",
        "text": (
            "Conventional loan minimum FICO score requirements: "
            "620 minimum for all conventional loan programs. "
            "Scores 740+ receive best pricing tiers. "
            "Scores 620-639 require additional compensating factors such as "
            "lower DTI or higher reserves. "
            "Scores below 620 are ineligible for conventional financing."
        )
    },
    {
        "id": "credit_002",
        "topic": "FHA loan credit score",
        "text": (
            "FHA loan credit requirements: minimum 580 FICO for 3.5% down payment. "
            "Scores 500-579 require 10% down payment. "
            "Scores below 500 are ineligible for FHA financing. "
            "FHA is more flexible than conventional for borrowers with prior derogatory credit."
        )
    },

    # DTI rules
    {
        "id": "dti_001",
        "topic": "debt to income ratio limit conventional",
        "text": (
            "Debt-to-income (DTI) ratio limits for conventional loans: "
            "Maximum total DTI is 45% for most programs. "
            "DTI up to 50% is allowed with strong compensating factors: "
            "FICO 720+, reserves of 12+ months, or LTV below 75%. "
            "Front-end DTI (housing expense only) should not exceed 28%. "
            "DTI is calculated as (all monthly debts + proposed housing payment) / gross monthly income."
        )
    },
    {
        "id": "dti_002",
        "topic": "compensating factors high DTI",
        "text": (
            "Compensating factors that allow higher DTI ratios: "
            "1. Significant cash reserves (12+ months PITI). "
            "2. Minimal payment shock (new payment within 5% of current housing expense). "
            "3. High residual income exceeding guidelines by 20%+. "
            "4. FICO score of 720 or higher. "
            "Maximum DTI with compensating factors is 50% for conventional, 57% for FHA."
        )
    },

    # LTV rules
    {
        "id": "ltv_001",
        "topic": "loan to value ratio LTV requirements",
        "text": (
            "Loan-to-value (LTV) ratio requirements: "
            "Maximum LTV for conventional purchase: 97% (3% down). "
            "LTV above 80% requires private mortgage insurance (PMI). "
            "PMI can be removed when LTV reaches 80% through payments or appreciation. "
            "LTV above 95% requires FICO 660+. "
            "Investment properties: maximum LTV 85%."
        )
    },

    # Reserve requirements
    {
        "id": "reserves_001",
        "topic": "cash reserves requirements months",
        "text": (
            "Cash reserve requirements after closing: "
            "Minimum 2 months PITI (principal, interest, taxes, insurance) for primary residence. "
            "6 months reserves required if DTI exceeds 43%. "
            "12 months reserves required for LTV above 95% with FICO below 680. "
            "Reserves must be in liquid accounts: checking, savings, or money market. "
            "401k and IRA count at 60% of vested balance. "
            "Gift funds cannot be counted as reserves."
        )
    },

    # Income verification
    {
        "id": "income_001",
        "topic": "income documentation requirements",
        "text": (
            "Income documentation requirements: "
            "W-2 employees: 2 years W-2s and 30 days recent pay stubs. "
            "Self-employed: 2 years federal tax returns, business and personal. "
            "Income must be stable and likely to continue for 3+ years. "
            "Overtime and bonus income: 2-year history required, averaged over 24 months. "
            "Rental income: 75% of gross rental income counted after vacancy factor."
        )
    },

    # Decline reasons
    {
        "id": "decline_001",
        "topic": "automatic decline disqualifying factors",
        "text": (
            "Automatic disqualifying factors for mortgage pre-approval: "
            "1. FICO below 620 for conventional (below 500 for FHA). "
            "2. Foreclosure within past 7 years (3 years for FHA). "
            "3. Bankruptcy Chapter 7 within 4 years (2 years for FHA). "
            "4. Active delinquency on any mortgage account. "
            "5. DTI exceeding 50% with no compensating factors. "
            "6. Insufficient income to document (cannot verify employment)."
        )
    },

    # Property rules
    {
        "id": "property_001",
        "topic": "property value appraisal requirements",
        "text": (
            "Property eligibility and appraisal requirements: "
            "Property must be primary residence, second home, or investment property. "
            "Appraisal required for all purchase transactions. "
            "Property must meet minimum condition standards (no deferred maintenance). "
            "Condos require project approval — warrantable condos only for conventional. "
            "Maximum loan amount for conforming loans: $766,550 (2024 baseline)."
        )
    },
]


# ────────────────────────────────────────────────────────────────
# PHASE 1 — Embedding functions (two approaches)
# ────────────────────────────────────────────────────────────────

def embed_openai(texts: list[str]) -> list[list[float]]:
    """Approach A: OpenAI API — fast, accurate, costs ~$0.00002/1K tokens"""
    from openai import OpenAI
    oai = OpenAI()   # reads OPENAI_API_KEY
    response = oai.embeddings.create(
        model="text-embedding-3-small",
        input=texts
    )
    return [item.embedding for item in response.data]


def embed_local(texts: list[str]) -> list[list[float]]:
    """Approach B: sentence-transformers — fully local, free, slightly less accurate
    First run downloads ~90MB model. pip install sentence-transformers first.
    """
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("all-MiniLM-L6-v2")
    return model.encode(texts).tolist()


def get_embeddings(texts: list[str]) -> list[list[float]]:
    """Router — switch via EMBEDDING_APPROACH at top of file"""
    if EMBEDDING_APPROACH == "openai":
        return embed_openai(texts)
    else:
        return embed_local(texts)


# ────────────────────────────────────────────────────────────────
# PHASE 1 — Build vector database
# ────────────────────────────────────────────────────────────────

def build_knowledge_base() -> chromadb.Collection:
    """Chunk → embed → store. Run once (or at startup)."""
    collection = chroma_client.get_or_create_collection("underwriting_guidelines")

    # Skip if already populated
    if collection.count() > 0:
        print(f"Knowledge base already loaded ({collection.count()} chunks)")
        return collection

    print("Building knowledge base...")
    texts = [g["text"] for g in GUIDELINES]
    ids   = [g["id"]   for g in GUIDELINES]

    embeddings = get_embeddings(texts)

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=[{"topic": g["topic"]} for g in GUIDELINES]
    )
    print(f"Loaded {collection.count()} guideline chunks into vector DB")
    return collection


# ────────────────────────────────────────────────────────────────
# PHASE 2 — Retrieval tool
# ────────────────────────────────────────────────────────────────

def search_guidelines(query: str, collection: chromadb.Collection, n=3) -> str:
    """Embed the query, find top-N closest guideline chunks."""
    query_embedding = get_embeddings([query])[0]
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n
    )
    chunks = results["documents"][0]
    topics = [m["topic"] for m in results["metadatas"][0]]

    output = []
    for i, (chunk, topic) in enumerate(zip(chunks, topics)):
        output.append(f"[Guideline {i+1} — {topic}]\n{chunk}")
    return "\n\n".join(output)


# ────────────────────────────────────────────────────────────────
# Mock applicant data (same as before)
# ────────────────────────────────────────────────────────────────

MOCK_APPLICANTS = {
    "A001": {
        "name": "Sarah Chen", "fico": 740,
        "monthly_income": 8500, "monthly_debts": 800,
        "assets": 45000, "loan_amount": 400000, "property_value": 500000,
    },
    "A002": {
        "name": "Tom Rivera", "fico": 580,
        "monthly_income": 5000, "monthly_debts": 2200,
        "assets": 8000, "loan_amount": 300000, "property_value": 320000,
    },
    "A003": {
        "name": "Maria Santos", "fico": 635,  # borderline — needs compensating factors
        "monthly_income": 7000, "monthly_debts": 1200,
        "assets": 30000, "loan_amount": 350000, "property_value": 400000,
    },
}


# ────────────────────────────────────────────────────────────────
# Tool definitions — same structure as before, one new tool added
# ────────────────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "get_credit_report",
        "description": "Get credit bureau data and loan details for an applicant. Call this first.",
        "input_schema": {
            "type": "object",
            "properties": {
                "applicant_id": {"type": "string", "description": "e.g. A001"}
            },
            "required": ["applicant_id"]
        }
    },
    {
        "name": "parse_financials",
        "description": "Parse bank statement PDF to get monthly income, debts, and assets.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pdf_path": {"type": "string", "description": "Path to bank statement PDF"}
            },
            "required": ["pdf_path"]
        }
    },
    {
        "name": "calculate_ratios",
        "description": "Calculate DTI, LTV, and reserve months from financial data.",
        "input_schema": {
            "type": "object",
            "properties": {
                "monthly_income":   {"type": "number"},
                "monthly_debts":    {"type": "number"},
                "loan_amount":      {"type": "number"},
                "property_value":   {"type": "number"},
                "assets":           {"type": "number"}
            },
            "required": ["monthly_income", "monthly_debts", "loan_amount", "property_value", "assets"]
        }
    },
    # ── NEW TOOL ────────────────────────────────────────────────
    {
        "name": "search_guidelines",
        "description": (
            "Search the underwriting policy knowledge base for relevant guidelines. "
            "Use when you need to verify: credit score thresholds, DTI limits, "
            "LTV requirements, reserve requirements, or disqualifying factors. "
            "Always search before making a final decision."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "e.g. 'minimum FICO score conventional loan' or 'DTI limit compensating factors'"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "generate_letter",
        "description": "Generate pre-approval or decline letter after all data collected and guidelines checked.",
        "input_schema": {
            "type": "object",
            "properties": {
                "applicant_name": {"type": "string"},
                "decision":       {"type": "string", "enum": ["approved", "declined"]},
                "loan_amount":    {"type": "number"},
                "fico":           {"type": "number"},
                "dti":            {"type": "number"},
                "reasons":        {"type": "string"}
            },
            "required": ["applicant_name", "decision", "loan_amount", "fico", "dti", "reasons"]
        }
    }
]


# ────────────────────────────────────────────────────────────────
# Tool execution functions
# ────────────────────────────────────────────────────────────────

def get_credit_report(applicant_id):
    a = MOCK_APPLICANTS[applicant_id]
    return {
        "name": a["name"], "fico": a["fico"],
        "loan_amount": a["loan_amount"], "property_value": a["property_value"]
    }

def parse_financials(pdf_path):
    # Reuse your real PDF parser from Option B
    # For now falling back to mock so this file runs standalone
    import pdfplumber, re
    try:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = "\n".join(p.extract_text() for p in pdf.pages if p.extract_text())
        deposits = re.findall(r'DIRECT DEPOSIT.*?([\d,]+\.\d{2})', full_text)
        monthly_income = sum(float(d.replace(",", "")) for d in deposits)
        debt_keywords = ['LOAN', 'CREDIT CARD', 'MORTGAGE', 'BNPL', 'AFFIRM', 'PAYDAY']
        debts = []
        for line in full_text.split('\n'):
            if any(k in line.upper() for k in debt_keywords):
                amounts = re.findall(r'([\d,]+\.\d{2})', line)
                if amounts:
                    debts.append(float(amounts[0].replace(",", "")))
        closing = re.search(r'Closing Balance.*?\$([\d,]+\.?\d*)', full_text)
        assets = float(closing.group(1).replace(",", "")) if closing else 0.0
        return {"monthly_income": monthly_income, "monthly_debts": sum(debts), "assets": assets}
    except Exception:
        # Fallback to mock if PDF not found
        for aid, a in MOCK_APPLICANTS.items():
            if aid in pdf_path:
                return {"monthly_income": a["monthly_income"],
                        "monthly_debts": a["monthly_debts"], "assets": a["assets"]}
        return {"monthly_income": 0, "monthly_debts": 0, "assets": 0}

def calculate_ratios(monthly_income, monthly_debts, loan_amount, property_value, assets):
    monthly_payment = loan_amount * 0.005
    dti = (monthly_debts + monthly_payment) / monthly_income
    ltv = loan_amount / property_value
    reserve_months = assets / (monthly_debts + monthly_payment)
    return {
        "dti": round(dti, 3), "ltv": round(ltv, 3),
        "reserve_months": round(reserve_months, 1),
        "monthly_payment": round(monthly_payment, 2)
    }

def generate_letter(applicant_name, decision, loan_amount, fico, dti, reasons):
    if decision == "approved":
        return {"letter": (
            f"PRE-APPROVAL LETTER\n\nDear {applicant_name},\n\n"
            f"We are pleased to pre-approve your mortgage application.\n"
            f"Approved amount: ${loan_amount:,} | FICO: {fico} | DTI: {dti:.1%}\n\n{reasons}"
        )}
    else:
        return {"letter": (
            f"DECLINE NOTICE\n\nDear {applicant_name},\n\n"
            f"We are unable to approve your application at this time.\n\nReasons: {reasons}"
        )}

def run_tool(name, inputs, collection):
    if name == "get_credit_report":  return get_credit_report(**inputs)
    if name == "parse_financials":   return parse_financials(**inputs)
    if name == "calculate_ratios":   return calculate_ratios(**inputs)
    if name == "search_guidelines":  return {"guidelines": search_guidelines(inputs["query"], collection)}
    if name == "generate_letter":    return generate_letter(**inputs)


# ────────────────────────────────────────────────────────────────
# Agent loop — identical structure, one extra tool
# ────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a senior mortgage underwriter at a US bank.
Given an applicant ID and their bank statement PDF path, evaluate their mortgage application.

Your workflow:
1. get_credit_report      — get FICO, loan amount, property value
2. parse_financials       — get income, debts, assets from PDF
3. calculate_ratios       — compute DTI, LTV, reserve months
4. search_guidelines      — look up relevant policies BEFORE deciding
   (search for: credit score requirements, DTI limits, reserve requirements)
5. generate_letter        — approve or decline with specific policy references

You MUST call search_guidelines before making a final decision.
Cite the specific guideline that supports your decision in the letter."""


def run_agent(applicant_id: str, pdf_path: str, collection: chromadb.Collection):
    print(f"\n{'='*55}")
    print(f"Processing: {applicant_id}")
    print(f"{'='*55}")

    messages = [{
        "role": "user",
        "content": (
            f"Process mortgage application for applicant {applicant_id}. "
            f"Bank statement PDF is at: {pdf_path}"
        )
    }]

    while True:
        response = anthropic_client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1500,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages
        )

        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    print("\n", block.text)
            break

        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"→ {block.name}({block.input})")
                    result = run_tool(block.name, block.input, collection)
                    # Truncate guideline output in console so it doesn't flood
                    display = str(result)[:120] + "..." if len(str(result)) > 120 else str(result)
                    print(f"  ← {display}")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result)
                    })
            messages.append({"role": "user", "content": tool_results})


# ────────────────────────────────────────────────────────────────
# Run
# ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Build knowledge base once
    collection = build_knowledge_base()

    # Test retrieval before running agent
    print("\n--- Retrieval test ---")
    result = search_guidelines("minimum credit score conventional loan", collection)
    print(result[:300], "...\n")

    # Run all three applicants
    # Update paths to your local PDF location
    PDF_DIR = "./sample_docs"
    run_agent("A001", f"{PDF_DIR}/bank_statement_A001.pdf", collection)
    run_agent("A002", f"{PDF_DIR}/bank_statement_A002.pdf", collection)
    run_agent("A003", f"{PDF_DIR}/bank_statement_A001.pdf", collection)  # A003 reuses A001 PDF for now
