# ClaimPilot — Tech Stack

Every tool in this stack is free and open source unless noted otherwise.
Where a free tier applies, the tier limits are documented.

---

## Language & Runtime

### Python 3.11+
- Primary language for all backend components
- Chosen for its ecosystem dominance in AI/ML tooling
- All libraries below have first-class Python support

---

## LLM Inference

### Groq API — Llama 3.1 8B
- **Purpose:** Powers Intent Classifier, Query Router, QueryResponder Agent
- **Why Groq:** Fastest inference available on free tier — sub-second latency
- **Why Llama 3.1 8B:** Strong instruction following, good structured JSON output,
  sufficient capability for classification and RAG-based answer generation
- **Free Tier Limits:** ~30 requests/minute, 14,400 requests/day
- **API Key:** Required — obtain at console.groq.com (free)
- **Model string:** `llama-3.1-8b-instant`

---

## Embeddings

### sentence-transformers — all-MiniLM-L6-v2
- **Purpose:** Converts text chunks into 384-dimensional vectors for ChromaDB storage
- **Why:** Completely free, runs locally, no API calls, no rate limits
- **Performance:** Strong semantic similarity quality for RAG pipelines
- **Size:** ~80MB model download on first run, cached locally after
- **Library:** `sentence-transformers` (pip installable)

---

## Vector Store

### ChromaDB
- **Purpose:** Stores and retrieves document embeddings
- **Two collections:**
  - `user_{user_id}` — per-user document vectors (user-namespaced)
  - `irdai_knowledge_base` — shared IRDAI regulatory document vectors
- **Why:** Free, open source, runs locally, native Python integration,
  supports metadata filtering for user and case isolation
- **Persistence:** Local disk storage — data survives restarts
- **Deletion:** Metadata filter-based deletion synced with PostgreSQL

---

## Orchestration

### LangChain
- **Purpose:** Chains LLM calls, manages prompts, integrates tools
- **Why:** Industry standard for LLM application development,
  extensive documentation, native Groq and ChromaDB integrations
- **Library:** `langchain`, `langchain-groq`, `langchain-community`

### LangGraph
- **Purpose:** Manages stateful multi-step conversation flows
- **Why:** Built specifically for agent state machines,
  native PostgreSQL checkpointer for state persistence,
  enables conversation resumption across sessions
- **Key feature used:** PostgreSQL checkpointer — serializes
  full conversation state to database after every turn
- **Library:** `langgraph`

---

## Database

### PostgreSQL (Local Installation)
- **Purpose:** Stores user profiles, document metadata, case information,
  LangGraph serialized conversation state
- **Why:** Relational integrity via foreign keys (user → case → document),
  LangGraph has native PostgreSQL checkpointer support,
  free and open source, production-grade reliability
- **Installation:** Direct local install — no Docker, no cloud service
  ```
  sudo apt install postgresql postgresql-contrib    # Ubuntu/Linux
  brew install postgresql                           # Mac
  ```
- **ORM:** SQLAlchemy for Python ↔ PostgreSQL interaction

---

## PDF Processing

### pdfplumber
- **Purpose:** Primary PDF text extraction for digitally created PDFs
- **Why:** More accurate than PyPDF2 for complex layouts,
  handles tables and multi-column text better,
  returns character-level metadata useful for quality detection
- **Detection logic:** If extracted characters > 100 per page
  → confirmed digital PDF → use pdfplumber output

### PyPDF2
- **Purpose:** PDF metadata extraction and initial file validation
- **Why:** Lightweight, fast for metadata-only operations

### Tesseract OCR
- **Purpose:** Fallback text extraction for scanned/image PDFs
- **Why:** Free, open source, industry standard OCR engine
- **Trigger:** When pdfplumber extracts < 100 characters per page
- **Python binding:** `pytesseract`
- **System install required:**
  ```
  sudo apt install tesseract-ocr    # Ubuntu/Linux
  brew install tesseract            # Mac
  ```
- **Implementation:** Discussed in detail during development phase

---

## Guardrails

### NeMo Guardrails (NVIDIA)
- **Purpose:** Input and output validation for insurance domain compliance
- **Why:** Free, open source, native LangChain integration,
  YAML-based configuration — easy to define topic taxonomy,
  supports both input and output rail definitions
- **Configuration:** Defined in `guardrails/config.yml` and `guardrails/flows.co`
- **Library:** `nemoguardrails`

---

## Web Framework

### FastAPI
- **Purpose:** REST API backend serving all frontend requests
- **Why:** Fast, async-native, automatic OpenAPI documentation,
  Python type hints for request/response validation,
  production-grade performance
- **Key endpoints:**
  - `POST /auth/register` — user registration
  - `POST /auth/login` — user login
  - `POST /chat` — main conversation endpoint
  - `POST /upload` — PDF document upload
  - `GET /cases` — fetch user's active cases

### Uvicorn
- **Purpose:** ASGI server for running FastAPI
- **Library:** `uvicorn`

---

## Frontend

### HTML / CSS / JavaScript
- **Purpose:** Chat interface served by FastAPI
- **Why:** No framework overhead, simple to build and maintain,
  sufficient for a demo-grade chat UI
- **Key features:**
  - Text message input and send
  - PDF file upload with drag-and-drop
  - Conversation history display
  - Case status indicator

---

## Semantic Chunking

### Custom Implementation (LangChain Text Splitters)
- **Purpose:** Splits extracted PDF text into semantically meaningful chunks
- **Strategy:** Sentence boundary detection with overlap
- **Parameters:**
  - Chunk size: ~500 tokens
  - Overlap: ~50 tokens
- **Library:** `langchain.text_splitter.RecursiveCharacterTextSplitter`
  with custom sentence-aware separators

---

## Knowledge Base — IRDAI Documents

### Source
- All documents publicly available at irdai.gov.in
- Downloaded as PDFs — processed through same ingestion pipeline
- Stored in `irdai_knowledge_base` ChromaDB collection

### Documents to Include
| Document | Coverage |
|----------|----------|
| IRDAI Master Circular on Health Insurance | Health claim timelines, cashless procedures, exclusions |
| IRDAI Master Circular on Motor Insurance | Motor claim process, third party vs comprehensive |
| IRDAI Master Circular on Life Insurance | Policy terms, nominee procedures, surrender values |
| IRDAI Guidelines on Travel Insurance | Trip cancellation, baggage loss, medical abroad |
| IRDAI Guidelines on Home/Property Insurance | Fire, flood, natural disaster claims |
| IRDAI Guidelines on Personal Accident Insurance | Disability, accidental death, workplace injury |
| IRDAI Policyholder Protection Guidelines | Customer rights, documentation requirements |
| IRDAI Insurance Ombudsman Guidelines | Grievance redressal, escalation timelines |

---

## Environment & Configuration

### python-dotenv
- **Purpose:** Loads environment variables from `.env` file
- **Library:** `python-dotenv`

### Key Environment Variables
```
GROQ_API_KEY=
POSTGRES_HOST=
POSTGRES_PORT=
POSTGRES_DB=
POSTGRES_USER=
POSTGRES_PASSWORD=
CHROMA_PERSIST_PATH=
```

---

## Complete Dependency Summary

```
# LLM & Orchestration
langchain
langchain-groq
langchain-community
langgraph
groq

# Embeddings
sentence-transformers

# Vector Store
chromadb

# Database
psycopg2-binary
sqlalchemy

# PDF Processing
pdfplumber
PyPDF2
pytesseract
Pillow

# Web Framework
fastapi
uvicorn

# Guardrails
nemoguardrails

# Utilities
python-dotenv
pydantic
```

---

## Why This Stack Is Fully Free

| Component | Cost |
|-----------|------|
| Groq API | Free tier — 14,400 req/day |
| sentence-transformers | Free — runs locally |
| ChromaDB | Free — open source, local |
| LangChain + LangGraph | Free — open source |
| PostgreSQL | Free — open source, local |
| pdfplumber + PyPDF2 | Free — open source |
| Tesseract OCR | Free — open source |
| NeMo Guardrails | Free — open source |
| FastAPI | Free — open source |

Total infrastructure cost for development and demo: **₹0**
