# Mortgage Pre-Approval AI Agent

An AI-powered mortgage underwriting agent that automates pre-approval decisions using LLM reasoning, RAG-based policy lookup, and real document parsing.

Built by a credit risk professional with 10+ years of Basel II/III and consumer lending experience — combining domain expertise with modern AI engineering.

---

## What It Does

Given an applicant ID and bank statement PDF, the agent autonomously:

1. Retrieves credit bureau data (FICO score, loan details)
2. Parses bank statement PDF to extract income, debts, and assets
3. Calculates key underwriting ratios (DTI, LTV, reserve months)
4. Queries a RAG knowledge base of underwriting guidelines to inform its decision
5. Generates a pre-approval letter or decline notice with specific policy citations

**The agent makes policy-grounded decisions** — it doesn't rely on hardcoded thresholds. Instead it retrieves relevant guidelines from a vector database at decision time, the same way a real underwriter references policy manuals.

---

## Architecture

```
Applicant ID + Bank Statement PDF
        │
        ▼
┌─────────────────────────────────┐
│         LLM (Claude)            │  ← Brain: reasoning + orchestration
│     Tool Orchestration          │
└──────────┬──────────────────────┘
           │ calls tools as needed
    ┌──────┴───────────────────────────────┐
    │              │             │         │
    ▼              ▼             ▼         ▼
get_credit    parse_         calculate  search_
_report()    financials()    _ratios()  guidelines()
    │         (pdfplumber)   DTI/LTV    (ChromaDB RAG)
    │              │             │         │
    └──────────────┴─────────────┴─────────┘
                        │
                        ▼
              generate_letter()
           Pre-Approval / Decline
```

---

## Key Technical Concepts Demonstrated

**Multi-tool Agent**: LLM autonomously decides which tools to call, in what order, based on what information it needs — not a fixed pipeline.

**RAG (Retrieval-Augmented Generation)**: Underwriting guidelines are chunked, embedded, and stored in ChromaDB. At decision time, the agent retrieves the most relevant policy sections using semantic search, grounding decisions in real policy text rather than hardcoded rules.

**Real Document Parsing**: Bank statement PDFs are parsed with `pdfplumber` using regex to extract income (direct deposits), recurring debts (loan payments, credit cards), and closing balance.

**Domain-Grounded System Prompt**: System prompt encodes real underwriting workflow — not generic instructions. Reflects actual mortgage underwriting sequence used at major financial institutions.

---

## Underwriting Logic

The agent evaluates applications against Fannie Mae / FHA style guidelines retrieved from the knowledge base:

| Factor | Conventional | FHA |
|--------|-------------|-----|
| Min FICO | 620 | 580 |
| Max DTI | 45% (50% with compensating factors) | 57% |
| Max LTV | 97% | 96.5% |
| Min Reserves | 2 months PITI | 1 month PITI |

Borderline cases (e.g. FICO 620-639) trigger compensating factor analysis — the agent searches guidelines for scenarios where exceptions apply, mirroring real underwriter judgment.

---

## Stack

| Component | Technology |
|-----------|-----------|
| LLM | Anthropic Claude (claude-sonnet) |
| Agent framework | Anthropic Tool Use API (no LangChain) |
| Vector DB | ChromaDB (persistent) |
| Embeddings | OpenAI text-embedding-3-small or sentence-transformers (local) |
| PDF parsing | pdfplumber + regex |
| Language | Python 3.11 |

---

## Project Structure

```
mortgage-ai-agent/
├── mortgage_rag.py          # Main agent — tool definitions, RAG, agent loop
├── create_bank_statement.py # Generates realistic mock bank statement PDFs
├── sample_docs/
│   ├── bank_statement_A001.pdf   # Sarah Chen — approved case
│   └── bank_statement_A002.pdf   # Tom Rivera — declined case
├── chroma_db/               # Persisted vector database (auto-created)
└── README.md
```

---

## Sample Output

**Approved case (Sarah Chen — FICO 740, DTI 38%)**
```
→ get_credit_report({'applicant_id': 'A001'})
→ parse_financials({'pdf_path': '...'})
→ calculate_ratios({...})
→ search_guidelines('minimum FICO score conventional loan')
→ search_guidelines('DTI ratio limits compensating factors')
→ generate_letter({'decision': 'approved', ...})

PRE-APPROVAL LETTER

Dear Sarah Chen,

We are pleased to pre-approve your mortgage application.
Approved amount: $400,000 | FICO: 740 | DTI: 38.2%

Per Fannie Mae guidelines (FICO 740+ qualifies for best pricing tier),
your application meets all conventional loan requirements...
```

**Declined case (Tom Rivera — FICO 580, DTI 64%)**
```
DECLINE NOTICE

Dear Tom Rivera,

We are unable to approve your application at this time.

Reasons:
1. FICO score 580 is below the 620 minimum for conventional loans.
   FHA financing requires minimum 580 with 10% down payment.
2. DTI of 64% exceeds maximum 50% even with compensating factors.
3. Reserves of 1.8 months fall below required 2 months PITI.
```

---

## Setup

```bash
pip install anthropic openai chromadb pdfplumber reportlab

export ANTHROPIC_API_KEY=your_key
export OPENAI_API_KEY=your_key      # or set EMBEDDING_APPROACH = "local"

python create_bank_statement.py     # generate sample PDFs
python mortgage_rag.py              # run the agent
```

---


