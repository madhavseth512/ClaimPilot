# ClaimPilot 🛡️

**A conversational multi-agent AI system that acts as a virtual insurance assistant for Indian customers.**

ClaimPilot guides users through the insurance claim process via a natural language chat interface — collecting required documents, answering regulatory queries grounded in IRDAI documentation, and maintaining persistent user context across sessions.

---

## What ClaimPilot Does

- Understands the user's situation in natural language and identifies the insurance intent
- Drives the conversation to collect all required documents — one at a time
- Processes uploaded PDFs and stores them as searchable vectors linked to the user
- Answers general insurance queries grounded in IRDAI Master Circulars and Handbooks
- Maintains full conversation state across sessions — resumes where the user left off
- Supports multiple simultaneous active cases per user
- Enforces insurance-domain guardrails on both input and output

---

## Supported Insurance Intents

| Intent | Example Trigger |
|--------|----------------|
| Motor Claim | "I had a car accident", "My bike was stolen" |
| Health Claim | "I was hospitalised", "I was diagnosed with cancer" |
| Life Insurance | "My father passed away and had a life policy" |
| Travel Insurance | "My luggage was lost at the airport" |
| Home / Property Insurance | "My house caught fire", "Flood damage to my property" |
| Personal Accident | "I fell and fractured my arm", "Workplace injury" |

---

## Tech Stack

| Component | Tool |
|-----------|------|
| LLM | Groq API — Llama 3.1 8B |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) — local |
| Vector Store | ChromaDB — local |
| Orchestration | LangChain + LangGraph |
| Database | PostgreSQL (local) |
| State Persistence | LangGraph PostgreSQL Checkpointer |
| PDF Processing | pdfplumber + Tesseract OCR (fallback) |
| Guardrails | NeMo Guardrails |
| Web Framework | FastAPI |
| Frontend | HTML / CSS / JavaScript |
| Knowledge Base | IRDAI Master Circulars and Handbooks |

**Total infrastructure cost: ₹0** — fully free stack for development and demo.

---

## Architecture Overview

```
User → FastAPI → Guardrails → Intent Classifier → LangGraph State Manager
                                                          │
                              ┌───────────────────────────┤
                              │                           │
                      Document Upload               Query Asked
                              │                           │
                    Document Ingestion            Query Router
                    Interface                           │
                              │                ┌─────────┴──────────┐
                    pdfplumber / OCR       User Docs          IRDAI KB
                              │            (ChromaDB)        (ChromaDB)
                    Semantic Chunker            │                  │
                              │                └─────────┬─────────┘
                    Embedding Generator    QueryResponder Agent
                              │                          │
                    DocProcessor Agent         Output Guardrails
                              │                          │
                    ChromaDB + PostgreSQL       Final Response
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full detailed breakdown.

---

## Project Structure

```
claimpilot/
├── main.py
├── requirements.txt
├── .env.example
├── README.md
├── ARCHITECTURE.md
├── TECHSTACK.md
├── CLAUDE.md
├── TODO.md
├── agents/
│   ├── doc_processor.py
│   └── query_responder.py
├── core/
│   ├── intent_classifier.py
│   ├── query_router.py
│   ├── semantic_chunker.py
│   ├── embedding_generator.py
│   └── state_manager.py
├── db/
│   ├── postgres.py
│   └── chroma.py
├── ingestion/
│   ├── pdf_extractor.py
│   └── ingestion_interface.py
├── guardrails/
│   ├── config.yml
│   └── flows.co
├── knowledge_base/
│   ├── ingest_irdai.py
│   └── irdai_docs/
├── routes/
│   ├── auth.py
│   ├── chat.py
│   └── upload.py
└── frontend/
    ├── index.html
    ├── style.css
    └── app.js
```

---

## Setup Instructions

### Prerequisites
- Python 3.11+
- PostgreSQL installed locally
- Tesseract OCR installed
- Groq API key (free at console.groq.com)

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/ClaimPilot.git
cd ClaimPilot
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate        # Linux / Mac
venv\Scripts\activate           # Windows
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Install System Dependencies
```bash
# Ubuntu / Linux
sudo apt install postgresql postgresql-contrib tesseract-ocr

# Mac
brew install postgresql tesseract
```

### 5. Configure Environment
```bash
cp .env.example .env
# Edit .env and fill in your Groq API key and PostgreSQL credentials
```

### 6. Set Up Database
```bash
# Create PostgreSQL database
createdb claimpilot

# Run migrations
alembic upgrade head
```

### 7. Populate IRDAI Knowledge Base
```bash
# Download IRDAI documents to knowledge_base/irdai_docs/
# Then run the ingestion script
python knowledge_base/ingest_irdai.py
```

### 8. Run the Application
```bash
uvicorn main:app --reload
```

Open `http://localhost:8000` in your browser.

---

## Key Design Decisions

**PDF only in v1** — Reduces ingestion complexity. Most insurance documents in India are submitted as PDFs.

**IRDAI knowledge base over web search** — Eliminates hallucination risk and jurisdiction mismatch. All regulatory answers are grounded in official Indian insurance documents.

**Semantic chunking with overlap** — Preserves context across chunk boundaries for more accurate RAG retrieval.

**Separate ChromaDB collection per user** — Prevents cross-user data leakage and enables clean deletion when a document is removed.

**LangGraph for state management** — Built specifically for stateful multi-step agent conversations with native PostgreSQL checkpointer for session persistence.

**Dual guardrails** — Input filtering and output validation both applied. Necessary in a high-stakes domain like insurance.

**case_id alongside user_id** — Supports multiple simultaneous active cases per user without state mixing.

---

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) — Full system design and component interaction
- [TECHSTACK.md](TECHSTACK.md) — Every tool, why it was chosen, free tier details
- [CLAUDE.md](CLAUDE.md) — Agent behaviour, guardrails taxonomy, intent definitions, conversation design
- [TODO.md](TODO.md) — Phased build plan with milestones

---

## Status

🚧 **Active Development** — See [TODO.md](TODO.md) for current progress.

---

## Disclaimer

ClaimPilot is a demonstration project. It is not affiliated with any insurance company or IRDAI. All regulatory information is sourced from publicly available IRDAI documents. Users should verify claim requirements directly with their insurer.
