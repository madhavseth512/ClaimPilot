# ClaimPilot

**An internal AI-powered claim assistant that guides insurance customers through document submission via a conversational chat interface.**

Built for insurance companies to deploy to their claimants — ClaimPilot understands the customer's situation in natural language, identifies the correct claim type, collects all IRDAI-mandated documents one by one, and answers regulatory queries grounded in official IRDAI Master Circulars.

---

![ClaimPilot Demo](assets/demo.png)

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Supported Intents](#supported-intents)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Test Suite](#test-suite)
- [Setup & Installation](#setup--installation)
- [Running the Application](#running-the-application)
- [API Reference](#api-reference)
- [Knowledge Base](#knowledge-base)
- [Design Decisions](#design-decisions)
- [Future Scope](#future-scope)
- [Disclaimer](#disclaimer)

---

## Overview

ClaimPilot is an internal tool deployed by insurance companies to collect required claim documents from customers. Instead of asking claimants to fill forms or navigate portals, ClaimPilot conducts a structured conversation:

1. Customer describes their situation in plain language
2. ClaimPilot identifies the claim type (motor, health, life, travel, home, personal accident)
3. The system requests each required document one at a time, following IRDAI guidelines
4. Uploaded PDFs are processed, chunked, and stored as searchable vectors
5. The customer can ask general insurance queries at any point — answered from IRDAI regulatory documents
6. Session state persists — customers can return and continue where they left off

---

## Key Features

- **Conversational document collection** — requests one document at a time, acknowledges each upload before asking for the next
- **6 supported claim intents** — with IRDAI-sourced document checklists and conditional sub-type documents
- **Dual-rail guardrails** — input filtering (blocks off-topic, medical advice, investment advice, legal advice) and output validation (hallucination check, jurisdiction check, insurer recommendation check)
- **RAG over IRDAI documents** — general queries answered from real IRDAI Master Circulars and Handbooks, not LLM memory
- **Session persistence** — LangGraph state machine backed by PostgreSQL; users resume exactly where they left off
- **Multi-case support** — each user can have multiple active claim cases simultaneously
- **Sub-type detection** — motor: theft / third-party / own damage; health: cashless / reimbursement; life: accidental / illness; travel: baggage / cancellation / medical / passport; home: fire / flood / burglary; personal accident: temporary / permanent disability

---

## Supported Intents

| Intent | Example Triggers | IRDAI Source |
|---|---|---|
| Motor Claim | "My car was stolen", "Someone hit my bike", "I bumped into a pole" | IRDAI Motor Insurance Master Circular |
| Health Claim | "I was hospitalised", "I had surgery", "My father was diagnosed with cancer" | IRDAI Health Insurance Master Circular |
| Life Insurance | "My husband passed away and had a life policy", "I want to file a death claim" | IRDAI Life Insurance Master Circular |
| Travel Insurance | "My luggage was lost at the airport", "I fell sick while travelling abroad" | IRDAI Travel Insurance Guidelines |
| Home / Property | "My house caught fire", "Flood damage to my property", "Burglary at my home" | IRDAI Property Insurance Guidelines |
| Personal Accident | "I fell from stairs and fractured my arm", "Workplace accident" | IRDAI Personal Accident Guidelines |

---

## Architecture

```
                        ┌────────────────────────────────┐
                        │         React Frontend          │
                        │  (3-panel: cases / chat / docs) │
                        └────────────────┬───────────────┘
                                         │ HTTP
                        ┌────────────────▼───────────────┐
                        │         FastAPI Backend         │
                        │  /auth  /chat  /upload  /cases  │
                        └──┬─────────────────────────┬───┘
                           │                         │
               ┌───────────▼──────────┐   ┌──────────▼──────────┐
               │   Input Guardrail    │   │  Auth + Token Store  │
               │  (Groq LLM classify) │   │  (bcrypt + secrets)  │
               └───────────┬──────────┘   └─────────────────────┘
                           │
               ┌───────────▼──────────────────────────────────┐
               │            LangGraph State Machine            │
               │                                               │
               │  onboarding → intent_classification           │
               │      → document_collection                    │
               │      → query_handling                         │
               │      → document_processing                    │
               │      → session_resume                         │
               │                                               │
               │  Checkpointer: PostgreSQL (session persist)   │
               └───┬────────────────────────────┬─────────────┘
                   │                            │
     ┌─────────────▼──────────┐    ┌────────────▼─────────────┐
     │    DocProcessor Agent   │    │   QueryResponder Agent    │
     │                         │    │                           │
     │  pdfplumber → text      │    │  Query Router (classify)  │
     │  Tesseract OCR fallback │    │  personal_doc │ general   │
     │  Semantic chunking      │    │       │              │    │
     │  all-MiniLM-L6-v2      │    │  User ChromaDB   IRDAI KB │
     │  ChromaDB (per-user)   │    │  (user_{id})  (shared)    │
     └─────────────────────────┘    └────────────┬─────────────┘
                                                 │
                                    ┌────────────▼─────────────┐
                                    │    Output Guardrail       │
                                    │  hallucination / jurisd.  │
                                    │  / insurer recommend.     │
                                    └──────────────────────────┘
```

### Component Breakdown

| Component | Responsibility |
|---|---|
| **LangGraph State Machine** | Orchestrates the full conversation flow. Each node (onboarding, intent classification, document collection, query handling) runs as a named graph node with typed state. |
| **Intent Classifier** | Sends user description to Groq LLM with a structured prompt. Returns intent + confidence score. Routes to clarification if confidence < 0.75. |
| **Query Router** | Classifies mid-conversation queries into `personal_doc`, `general_insurance`, `ambiguous`, or `off_topic`. |
| **DocProcessor Agent** | Extracts text from PDFs (pdfplumber first, Tesseract OCR fallback for scanned docs), chunks with 500-token windows / 50-token overlap, embeds with sentence-transformers, stores in per-user ChromaDB collection. |
| **QueryResponder Agent** | Retrieves relevant chunks from ChromaDB and feeds them to the LLM with a grounded-answer prompt. Always cites the IRDAI source document when answering regulatory queries. |
| **Guardrails** | Dual-rail implementation. Input: Groq LLM classifies into ALLOWED / BLOCK_OFFTOPIC / BLOCK_MEDICAL / BLOCK_INVEST / BLOCK_LEGAL. Output: three async checks — hallucination, non-Indian jurisdiction, insurer recommendation. |
| **PostgreSQL** | Stores users, cases, and documents. Also acts as LangGraph checkpointer for session persistence. |
| **ChromaDB** | Two collections: `user_{user_id}` (per-user uploaded documents) and `irdai_knowledge_base` (shared regulatory knowledge). |

---

## Tech Stack

| Layer | Tool | Reason |
|---|---|---|
| LLM Inference | Groq API — Llama 3.1 8B (`llama-3.1-8b-instant`) | Free tier, fast inference, strong instruction following |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` | Local, free, 384-dim, strong semantic similarity |
| Vector Store | ChromaDB (local) | Zero-cost, persistent, supports per-collection isolation |
| Agent Orchestration | LangGraph 0.4 | Built for stateful multi-step agent conversations |
| LLM Framework | LangChain 0.3 | Tooling for prompt management, retrieval chains |
| Session Persistence | LangGraph PostgreSQL Checkpointer | Native LangGraph integration, reliable state replay |
| Database | PostgreSQL + SQLAlchemy + Alembic | Structured data (users, cases, documents) + migrations |
| PDF Extraction | pdfplumber | Accurate text extraction from digital PDFs |
| OCR Fallback | Tesseract + pytesseract + Pillow | Handles scanned / image-based PDFs |
| Guardrails | NeMo Guardrails 0.11 + custom runner | Dual-rail input/output filtering |
| Web Framework | FastAPI 0.115 | Async, auto-documented, Pydantic validation |
| Auth | bcrypt + `secrets.token_hex` | Secure password hashing, cryptographically random tokens |
| Frontend | React 18 + Vite 6 + Tailwind CSS 3 | Component-based UI, fast build, utility-first styling |
| Routing | React Router v6 | Client-side routing with protected route guard |
| Backend Tests | pytest + pytest-asyncio | Standard Python testing |
| Frontend Tests | Vitest + React Testing Library | Vite-native test runner, RTL for component behaviour |
| Knowledge Base | IRDAI Master Circulars (5 PDFs) | Authoritative Indian insurance regulatory source |

**Total infrastructure cost: ₹0** — fully free stack for development and demo.

---

## Project Structure

```
ClaimPilot/
├── main.py                        # FastAPI app entry point
├── requirements.txt
├── pytest.ini
├── alembic.ini
├── .env.example
│
├── agents/
│   ├── doc_processor.py           # PDF ingestion + ChromaDB storage
│   └── query_responder.py         # RAG query answering (user docs + IRDAI KB)
│
├── core/
│   ├── intent_classifier.py       # Groq LLM intent classification
│   ├── query_router.py            # Classifies mid-chat queries
│   ├── semantic_chunker.py        # RecursiveCharacterTextSplitter
│   ├── embedding_generator.py     # sentence-transformers embeddings
│   ├── state_manager.py           # LangGraph graph definition + nodes
│   └── security.py                # bcrypt password hashing + token management
│
├── db/
│   ├── postgres.py                # SQLAlchemy models + session + checkpointer
│   └── chroma.py                  # ChromaDB client + collection helpers
│
├── routes/
│   ├── auth.py                    # POST /auth/register  POST /auth/login
│   ├── chat.py                    # POST /chat/  POST /chat/resume
│   ├── upload.py                  # POST /upload/
│   └── cases.py                   # GET /cases/  GET /cases/{case_id}
│
├── guardrails/
│   ├── config.yml                 # NeMo Guardrails config
│   ├── flows.co                   # Colang flow definitions
│   ├── actions.py                 # Custom output rail actions
│   └── runner.py                  # check_input() / check_output() interface
│
├── ingestion/
│   ├── pdf_extractor.py           # pdfplumber + Tesseract OCR pipeline
│   └── ingestion_interface.py     # DocProcessor.process() entry point
│
├── knowledge_base/
│   ├── ingest_irdai.py            # One-time IRDAI PDF ingestion script
│   └── irdai_docs/                # 5 IRDAI Master Circulars (PDFs)
│
├── migrations/                    # Alembic migration files
│
├── frontend/
│   ├── index.html
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── package.json
│   └── src/
│       ├── main.jsx               # React entry point + BrowserRouter
│       ├── App.jsx                # Routes + PrivateRoute guard
│       ├── index.css              # Tailwind directives + component classes
│       ├── api/client.js          # All API calls (auth, chat, upload, cases)
│       ├── context/AuthContext.jsx
│       ├── pages/
│       │   ├── Login.jsx
│       │   ├── Register.jsx
│       │   └── Dashboard.jsx      # Main 3-panel orchestrator
│       ├── components/
│       │   ├── Navbar.jsx
│       │   ├── ProfileDropdown.jsx
│       │   ├── CasesSidebar.jsx   # Left panel — case list + New Case
│       │   ├── ChatArea.jsx       # Center panel — messages + input
│       │   ├── MessageBubble.jsx
│       │   └── DocumentPanel.jsx  # Right panel — checklist + upload
│       └── __tests__/             # Vitest component tests
│
├── tests/
│   ├── conftest.py                # Shared pytest fixtures
│   ├── test_api.py                # Auth matrix + input validation (mock-based)
│   ├── test_e2e.py                # Full conversation flows (live stack)
│   ├── test_guardrails.py         # Guardrail true/false positive suite
│   ├── run_eval.py                # Eval accuracy measurement script
│   └── eval_set.json              # 50 labelled inputs for accuracy scoring
│
└── assets/
    └── demo.png                   # UI screenshot (add manually)
```

---

## Test Suite

### Running Tests

```bash
# API tests — mock-based, no external dependencies
pytest tests/test_api.py -v

# Guardrail tests — requires GROQ_API_KEY
pytest tests/test_guardrails.py -v

# End-to-end conversation tests — requires PostgreSQL + GROQ_API_KEY
pytest tests/test_e2e.py -v -s

# Frontend component tests
cd frontend && npm test

# Eval accuracy measurement
python tests/run_eval.py
```

### Test Results

| Suite | Tests | Result | Description |
|---|---|---|---|
| `test_api.py` | 38 / 38 | All pass | Auth matrix, input validation, upload validation, response shape contracts |
| `test_guardrails.py` | 44 / 44 | All pass | 30 must-allow (false positive regression) + 14 must-block |
| `test_e2e.py` | 22 / 22 | All pass | Onboarding, all 6 intents, edge cases, session resumption, multi-case |
| Frontend Vitest | 41 / 41 | All pass | MessageBubble, ChatArea, DocumentPanel, CasesSidebar, AuthContext |
| **Total** | **145 / 145** | **All pass** | |

### Eval Accuracy

```
Intent Classifier : 26 / 26  (100.0%)
Query Router      : 24 / 24  (100.0%)
Total             : 50 / 50  (100.0%)
```

Evaluated against a labelled set of 50 inputs covering all 6 intents and all 4 query categories.

### Guardrail Coverage

| Category | Must Allow | Must Block |
|---|---|---|
| Greetings & passthrough | 7 | — |
| Claim situation descriptions (motor, health, life, travel, home, PA) | 16 | — |
| General insurance queries | 7 | — |
| Medical advice requests | — | 4 |
| Off-topic queries | — | 5 |
| Insurer comparison / investment advice | — | 3 |
| Legal advice (non-insurance) | — | 2 |

---

## Setup & Installation

### Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.11+ | |
| PostgreSQL | 14+ | Running locally |
| Tesseract OCR | 5.x | Required for scanned PDF fallback |
| Node.js | 18+ | For frontend build |
| Groq API key | — | Free at [console.groq.com](https://console.groq.com) |

### 1. Clone the Repository

```bash
git clone https://github.com/madhavseth512/ClaimPilot.git
cd ClaimPilot
```

### 2. Python Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / Mac
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Install System Dependencies

```bash
# Ubuntu / Debian
sudo apt install postgresql postgresql-contrib tesseract-ocr

# Mac
brew install postgresql tesseract

# Windows — install Tesseract from:
# https://github.com/UB-Mannheim/tesseract/wiki
```

### 4. Environment Variables

```bash
cp .env.example .env
```

Edit `.env`:

```env
GROQ_API_KEY=your_groq_api_key_here
DATABASE_URL=postgresql://postgres:password@localhost:5432/claimpilot
APP_HOST=0.0.0.0
APP_PORT=8000
INTENT_CONFIDENCE_THRESHOLD=0.75
```

### 5. Database Setup

```bash
# Create the database
createdb claimpilot

# Run migrations
alembic upgrade head
```

### 6. Ingest IRDAI Knowledge Base

```bash
# Place IRDAI PDF documents in knowledge_base/irdai_docs/
# Then run the one-time ingestion script:
python knowledge_base/ingest_irdai.py
```

### 7. Frontend Build

```bash
cd frontend
npm install
npm run build
cd ..
```

---

## Running the Application

### Production (FastAPI serves built frontend)

```bash
python main.py
```

Open [http://localhost:8000](http://localhost:8000)

### Development (hot reload on both sides)

```bash
# Terminal 1 — Backend
python main.py

# Terminal 2 — Frontend dev server (with proxy to backend)
cd frontend
npm run dev
```

Open [http://localhost:5173](http://localhost:5173)

---

## API Reference

All endpoints except `/auth/register` and `/auth/login` require:
```
Authorization: Bearer <token>
```

### Auth

| Method | Endpoint | Body | Response |
|---|---|---|---|
| POST | `/auth/register` | `{name, email, password}` | `{user_id, token, message}` |
| POST | `/auth/login` | `{email, password}` | `{user_id, token, message}` |

### Chat

| Method | Endpoint | Body / Params | Response |
|---|---|---|---|
| POST | `/chat/` | `{message, case_id?}` | `{response, case_id, pending_docs, case_status}` |
| POST | `/chat/resume` | `?case_id=<id>` | `{response, case_id, pending_docs, case_status}` |

### Upload

| Method | Endpoint | Form Data | Response |
|---|---|---|---|
| POST | `/upload/` | `file (PDF), case_id, document_type` | `{success, document_id, message, pending_docs, collected_docs, case_status}` |

### Cases

| Method | Endpoint | Response |
|---|---|---|
| GET | `/cases/` | `[{case_id, intent, case_status, pending_docs, collected_docs, total_docs}]` |
| GET | `/cases/{case_id}` | `{case_id, intent, case_status, pending_docs, collected_docs, total_docs}` |

---

## Knowledge Base

ClaimPilot's regulatory knowledge is sourced from official IRDAI documents:

| Document | Coverage |
|---|---|
| IRDAI Master Circular — Health Insurance | Health claim requirements, cashless process, reimbursement, pre-authorisation |
| IRDAI Master Circular — Motor Insurance | Motor claim process, theft, third-party, own damage, FIR requirements |
| IRDAI Master Circular — Life Insurance | Death claims, nominee process, surrender, maturity |
| IRDAI Master Circular — Protection of Policyholders' Interests | Customer rights, claim timelines, grievance redressal, ombudsman |
| IRDAI Handbook on Insurance | General insurance principles, policy types, IRDAI regulatory framework |

All documents are chunked (500 tokens, 50-token overlap), embedded with `all-MiniLM-L6-v2`, and stored in a shared ChromaDB collection. Query responses always cite the source document.

---

## Design Decisions

**One document at a time** — The conversation design spec requires asking for documents sequentially. Dumping the full list creates cognitive overload for claimants.

**IRDAI knowledge base over web search** — Eliminates hallucination risk and jurisdiction mismatch. All regulatory answers are grounded in official Indian insurance documents, not LLM memory.

**Separate ChromaDB collection per user** — Prevents cross-user data leakage and enables clean deletion when a case is closed.

**LangGraph for state management** — Built specifically for stateful multi-step agent conversations with native PostgreSQL checkpointer for session persistence across browser sessions.

**Dual guardrails** — Input filtering prevents abuse; output validation catches hallucination, non-Indian regulatory references, and insurer recommendations. Both rails fail-open on timeout.

**bcrypt for password hashing** — SHA-256 is fast and brute-forceable; bcrypt is adaptive and resistant to GPU-based attacks.

**Groq + Llama 3.1 8B** — Free tier, sub-second latency, sufficient reasoning for insurance intent classification and query answering.

**case_id alongside user_id** — Supports multiple simultaneous active cases per user without state mixing.

---

## Future Scope

### 1. Entity Slot Filling

Currently, ClaimPilot identifies the claim intent and collects documents — but it does not extract the specific data values mentioned within the conversation. The next evolution is **dynamic entity slot filling**: as the customer describes their situation, the system would automatically identify and capture structured data points — date of incident, location, vehicle registration number, hospital name, policy number, claim amount, and other intent-specific fields — directly from the conversation without asking the customer to fill a separate form.

This extracted data would populate a structured slot schema for each intent, creating a machine-readable summary of the claim alongside the collected documents. This eliminates manual data entry by insurance staff and makes the downstream integration significantly more powerful.

### 2. Direct Integration with Insurer Core Systems

Once entity slots are populated and all documents are collected, ClaimPilot could automatically compose and dispatch a structured **FNOL (First Notice of Loss) payload** to the insurer's core policy administration system — without any human intervention.

The payload would be formatted to the target system's API spec (for example, DuckCreek or Guidewire — the two dominant platforms used by Indian and global insurers) and submitted via a secure API call at the point of case completion. This would:

- Eliminate the manual re-keying of claim data by back-office staff
- Trigger the insurer's internal claim workflow automatically
- Provide the claimant with a real claim reference number in the chat interface
- Reduce claim registration time from days to seconds

This integration would position ClaimPilot as a full **straight-through processing** front-end for insurance claims, not just a document collection assistant.

---

## Disclaimer

ClaimPilot is a demonstration project built as a proof of concept. It is not affiliated with any insurance company or the Insurance Regulatory and Development Authority of India (IRDAI). All regulatory information is sourced from publicly available IRDAI documents. Users and deploying organisations should verify all claim requirements directly with the relevant insurer.
