# ClaimPilot — TODO.md
# Phased Build Plan

Each phase builds on the previous. Complete and test each phase
before moving to the next. Checkboxes track progress.

---

## Phase 1 — Project Setup & Infrastructure
*Goal: Working local environment with all dependencies installed*

- [ ] Create GitHub repository `ClaimPilot`
- [ ] Set up Python virtual environment (`python -m venv venv`)
- [ ] Install all dependencies from `requirements.txt`
- [ ] Install PostgreSQL locally and verify connection
- [ ] Install Tesseract OCR system package
- [ ] Create `.env` file from `.env.example` and add Groq API key
- [ ] Create PostgreSQL database and run schema migrations
- [ ] Initialise ChromaDB local persistence directory
- [ ] Verify Groq API connection with a test call
- [ ] Verify sentence-transformers embedding generation locally
- [ ] Set up project folder structure (see below)

### Folder Structure
```
claimpilot/
├── main.py                  # FastAPI app entry point
├── requirements.txt
├── .env.example
├── README.md
├── ARCHITECTURE.md
├── TECHSTACK.md
├── CLAUDE.md
├── TODO.md
├── agents/
│   ├── doc_processor.py     # DocProcessor Agent
│   └── query_responder.py   # QueryResponder Agent
├── core/
│   ├── intent_classifier.py
│   ├── query_router.py
│   ├── semantic_chunker.py
│   ├── embedding_generator.py
│   └── state_manager.py     # LangGraph state
├── db/
│   ├── postgres.py          # SQLAlchemy models and connection
│   └── chroma.py            # ChromaDB connection and helpers
├── ingestion/
│   ├── pdf_extractor.py     # pdfplumber + Tesseract fallback
│   └── ingestion_interface.py
├── guardrails/
│   ├── config.yml           # NeMo Guardrails config
│   └── flows.co             # NeMo conversation flows
├── knowledge_base/
│   ├── ingest_irdai.py      # Script to populate IRDAI collection
│   └── irdai_docs/          # Downloaded IRDAI PDF files
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

## Phase 2 — Database Layer
*Goal: PostgreSQL schema set up, SQLAlchemy models working*

- [ ] Define SQLAlchemy models for:
  - [ ] `users` table
  - [ ] `cases` table
  - [ ] `documents` table
  - [ ] `conversation_state` table
- [ ] Write and run Alembic migration scripts
- [ ] Test CRUD operations for each model
- [ ] Set up LangGraph PostgreSQL checkpointer connection
- [ ] Verify state serialization and deserialization round-trip

---

## Phase 3 — Document Ingestion Pipeline
*Goal: PDF uploaded → text extracted → chunked → embedded → stored in ChromaDB*

- [ ] Build `pdf_extractor.py`:
  - [ ] pdfplumber extraction for digital PDFs
  - [ ] Character count threshold detection (< 100 chars/page → scanned)
  - [ ] Tesseract OCR fallback path (implementation details in dev phase)
- [ ] Build `semantic_chunker.py`:
  - [ ] RecursiveCharacterTextSplitter with sentence-aware separators
  - [ ] Chunk size: ~500 tokens, overlap: ~50 tokens
  - [ ] Preserve section context in chunk metadata
- [ ] Build `embedding_generator.py`:
  - [ ] Load `all-MiniLM-L6-v2` model
  - [ ] Generate 384-dim vectors for each chunk
- [ ] Build `chroma.py`:
  - [ ] User collection creation: `user_{user_id}`
  - [ ] Vector storage with metadata (user_id, case_id, doc_type, chunk_index)
  - [ ] Metadata-filtered retrieval by user_id and case_id
  - [ ] Deletion pipeline: delete vectors by metadata filter
- [ ] Build `DocProcessor Agent`:
  - [ ] Orchestrates full ingestion pipeline
  - [ ] Updates document metadata in PostgreSQL on success
  - [ ] Updates LangGraph state checklist (collected_docs, pending_docs)
- [ ] End-to-end test: upload a sample PDF → verify vectors in ChromaDB

---

## Phase 4 — IRDAI Knowledge Base Population
*Goal: IRDAI documents downloaded, processed, stored in knowledge base collection*

- [ ] Download IRDAI Master Circulars and Guidelines PDFs from irdai.gov.in:
  - [ ] Master Circular on Health Insurance
  - [ ] Master Circular on Motor Insurance
  - [ ] Master Circular on Life Insurance
  - [ ] Guidelines on Travel Insurance
  - [ ] Guidelines on Home/Property Insurance
  - [ ] Guidelines on Personal Accident Insurance
  - [ ] Policyholder Protection Guidelines
  - [ ] Insurance Ombudsman Guidelines
- [ ] Build `ingest_irdai.py` script:
  - [ ] Runs same ingestion pipeline as user documents
  - [ ] Stores in `irdai_knowledge_base` ChromaDB collection
  - [ ] Tags each chunk with source document name for citation
- [ ] Run ingestion script and verify all documents stored
- [ ] Test RAG retrieval: query knowledge base, verify relevant chunks returned

---

## Phase 5 — Core Agent Logic
*Goal: Intent classifier, query router, and QueryResponder working*

- [ ] Build `intent_classifier.py`:
  - [ ] Groq API call with intent classification prompt from CLAUDE.md
  - [ ] JSON output parsing
  - [ ] Confidence threshold check (< 0.75 → clarifying question)
  - [ ] Test all 6 intents with example trigger phrases
- [ ] Build `query_router.py`:
  - [ ] Groq API call with query classification prompt from CLAUDE.md
  - [ ] Routes to: personal_doc | general_insurance | ambiguous | off_topic
  - [ ] Confidence threshold check for ambiguous routing
- [ ] Build `QueryResponder Agent`:
  - [ ] ChromaDB retrieval (user collection or IRDAI collection based on router)
  - [ ] Prompt construction with retrieved chunks + conversation history
  - [ ] Groq API call for answer generation
  - [ ] IRDAI source citation appended for general insurance queries
- [ ] Test QueryResponder with sample personal doc query
- [ ] Test QueryResponder with sample IRDAI knowledge base query

---

## Phase 6 — LangGraph State Management
*Goal: Full conversation state machine working with session persistence*

- [ ] Define LangGraph state schema (from ARCHITECTURE.md)
- [ ] Define graph nodes:
  - [ ] `onboarding_node` — new user first message
  - [ ] `intent_classification_node`
  - [ ] `document_request_node` — asks for next pending document
  - [ ] `document_processing_node` — triggers DocProcessor
  - [ ] `query_handling_node` — triggers QueryResponder
  - [ ] `session_resume_node` — returning user state reload
- [ ] Define graph edges and conditional routing
- [ ] Connect PostgreSQL checkpointer to LangGraph
- [ ] Test state persistence: mid-conversation → close browser → reopen → verify state resumed
- [ ] Test case isolation: two active cases for same user → verify no state mixing

---

## Phase 7 — Guardrails
*Goal: NeMo Guardrails filtering input and output*

- [ ] Install and configure NeMo Guardrails
- [ ] Write `guardrails/config.yml` with allowed topic taxonomy from CLAUDE.md
- [ ] Write `guardrails/flows.co` defining:
  - [ ] Input rail: block off-topic queries
  - [ ] Output rail: validate response before delivery
- [ ] Integrate guardrails into FastAPI chat endpoint
- [ ] Test input guardrails: send off-topic query → verify block response
- [ ] Test output guardrails: verify hallucinated amounts are flagged

---

## Phase 8 — FastAPI Backend & Routes
*Goal: All API endpoints working, frontend connected to backend*

- [ ] Build `routes/auth.py`:
  - [ ] `POST /auth/register` — create user in PostgreSQL
  - [ ] `POST /auth/login` — authenticate, return session token
- [ ] Build `routes/chat.py`:
  - [ ] `POST /chat` — receives message, runs full agent pipeline, returns response
  - [ ] Handles onboarding flow detection (new vs returning user)
  - [ ] Manages session token → user_id mapping
- [ ] Build `routes/upload.py`:
  - [ ] `POST /upload` — receives PDF, validates format, triggers DocProcessor
  - [ ] Returns upload status and checklist update
- [ ] Build `routes/cases.py`:
  - [ ] `GET /cases` — returns user's active cases and their status
- [ ] Integration test: full message → agent pipeline → response round trip

---

## Phase 9 — Frontend Chat UI
*Goal: Working chat interface connected to FastAPI backend*

- [ ] Build `frontend/index.html`:
  - [ ] Chat message display area
  - [ ] Text input and send button
  - [ ] PDF file upload with drag-and-drop
  - [ ] Case status indicator
- [ ] Build `frontend/style.css`:
  - [ ] Clean, professional chat UI styling
  - [ ] User message vs agent message visual distinction
  - [ ] Upload progress indicator
- [ ] Build `frontend/app.js`:
  - [ ] WebSocket or polling connection to FastAPI
  - [ ] Message send and receive handling
  - [ ] File upload handling
  - [ ] Session management (store token in memory)
- [ ] End-to-end test: complete claim flow through UI

---

## Phase 10 — Integration Testing & Demo Preparation
*Goal: Full system tested end-to-end across all 6 intents*

- [ ] Test complete flow for each intent:
  - [ ] Motor claim
  - [ ] Health claim
  - [ ] Life insurance
  - [ ] Travel insurance
  - [ ] Home/property insurance
  - [ ] Personal accident
- [ ] Test returning user session resumption
- [ ] Test multiple active cases for same user
- [ ] Test IRDAI knowledge base query answering
- [ ] Test ambiguous intent clarification flow
- [ ] Test guardrails on off-topic inputs
- [ ] Test OCR fallback with a scanned PDF sample
- [ ] Record metrics for resume:
  - [ ] Average document processing time
  - [ ] Embedding generation time per document
  - [ ] End-to-end query response latency
  - [ ] Number of IRDAI documents in knowledge base
  - [ ] Number of insurance intents supported
- [ ] Write demo script for placement interviews

---

## Metrics to Record (For Resume)
Once Phase 10 is complete, document these:

| Metric | Target | Actual |
|--------|--------|--------|
| Insurance intents supported | 6 | — |
| IRDAI documents in knowledge base | 8+ | — |
| Average PDF processing time | < 10s | — |
| End-to-end query response latency | < 5s | — |
| Embedding generation time | < 2s/doc | — |
| Supported document types per intent | 6-8 | — |

---

## Notes
- Work through phases sequentially — each phase depends on the previous
- Commit to GitHub at the end of each phase with a descriptive commit message
- Test each component in isolation before integrating
- Keep `.env` file out of git — only `.env.example` is committed
- Tesseract OCR implementation details will be discussed separately during Phase 3
