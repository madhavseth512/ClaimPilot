# ClaimPilot — System Architecture

## Overview

ClaimPilot is a multi-agent conversational AI system designed to automate insurance claim assistance for Indian customers. The system guides users through claim filing, collects required documents, answers regulatory queries grounded in IRDAI documentation, and maintains persistent user context across sessions.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER (Browser)                          │
│                     HTML / CSS / JS Chat UI                     │
└─────────────────────────────┬───────────────────────────────────┘
                              │ HTTP / REST
┌─────────────────────────────▼───────────────────────────────────┐
│                        FastAPI Backend                          │
│                     (API Gateway Layer)                         │
└──────┬──────────────────────┬──────────────────────┬────────────┘
       │                      │                      │
       ▼                      ▼                      ▼
┌─────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│  Auth &     │    │   Onboarding     │    │   Guardrails Layer  │
│  User Mgmt  │    │   Flow Handler   │    │   (NeMo Guardrails) │
│ (PostgreSQL)│    │                  │    │   Input Validation  │
└─────────────┘    └────────┬─────────┘    └──────────┬──────────┘
                            │                         │
                            ▼                         ▼
                  ┌──────────────────────────────────────────────┐
                  │            Intent Classifier                 │
                  │         (Groq API — Llama 3.1 8B)           │
                  │                                              │
                  │  Intents: Motor | Health | Life | Travel |  │
                  │           Home/Property | Personal Accident  │
                  └─────────────────────┬────────────────────────┘
                                        │
                                        ▼
                  ┌──────────────────────────────────────────────┐
                  │         LangGraph State Manager              │
                  │                                              │
                  │  - Loads document checklist per intent       │
                  │  - Tracks collected vs pending documents     │
                  │  - Manages case_id and user_id context       │
                  │  - Persists state to PostgreSQL              │
                  └──────────┬─────────────────┬────────────────┘
                             │                 │
               ┌─────────────▼──┐         ┌───▼──────────────────┐
               │ Document       │         │ Query Asked           │
               │ Uploaded       │         │                       │
               └────────┬───────┘         └───┬──────────────────┘
                        │                     │
                        ▼                     ▼
          ┌─────────────────────┐   ┌─────────────────────────────┐
          │  Document Ingestion │   │       Query Router          │
          │  Interface          │   │                             │
          │                     │   │  - Personal doc query       │
          │  Format Check:      │   │  - General insurance query  │
          │  Digitally created? │   │  - Ambiguous (low conf.)    │
          │  → pdfplumber       │   │  - Off-topic → Guardrails  │
          │  Scanned/Image PDF? │   └──────┬──────────┬───────────┘
          │  → Tesseract OCR    │          │          │
          └────────┬────────────┘          │          │
                   │                       │          │
                   ▼                       ▼          ▼
          ┌─────────────────┐   ┌──────────────┐  ┌──────────────────┐
          │ Semantic Chunker│   │ User ChromaDB│  │ IRDAI Knowledge  │
          │                 │   │ Collection   │  │ Base ChromaDB    │
          │ - Chunk text    │   │ (user_id +   │  │ Collection       │
          │ - Add overlap   │   │  case_id     │  │                  │
          │ - Normalize     │   │  namespaced) │  │ Master Circulars │
          └────────┬────────┘   └──────┬───────┘  │ Handbooks        │
                   │                   │           └────────┬─────────┘
                   ▼                   │                    │
          ┌─────────────────┐          │                    │
          │ Embedding       │          │                    │
          │ Generator       │          └─────────┬──────────┘
          │                 │                    │
          │ sentence-       │                    ▼
          │ transformers    │          ┌──────────────────────┐
          │ (all-MiniLM-L6) │          │  QueryResponder Agent│
          └────────┬────────┘          │  (Groq API)          │
                   │                   │                      │
                   ▼                   │  RAG over retrieved  │
          ┌─────────────────┐          │  chunks + LLM answer │
          │ DocProcessor    │          │  generation          │
          │ Agent           │          └──────────┬───────────┘
          │                 │                     │
          │ - Store vectors │                     ▼
          │   in ChromaDB   │          ┌──────────────────────┐
          │ - Store metadata│          │  Output Guardrails   │
          │   in PostgreSQL │          │  (NeMo Guardrails)   │
          │ - Update        │          │                      │
          │   checklist     │          │  Validates response  │
          │   state         │          │  before delivery     │
          └─────────────────┘          └──────────┬───────────┘
                                                   │
                                                   ▼
                                        ┌──────────────────────┐
                                        │   Final Response     │
                                        │   to User            │
                                        │                      │
                                        │ + IRDAI source cite  │
                                        │ + Next doc request   │
                                        │   if pending         │
                                        └──────────────────────┘
```

---

## Component Breakdown

### 1. Chat UI (Frontend)
- Simple HTML/CSS/JS single page chat interface
- Handles text input and PDF file upload
- Displays conversation history
- Communicates with FastAPI backend via REST

### 2. FastAPI Backend
- Single API gateway handling all incoming requests
- Routes to appropriate handlers:
  - `/auth` — user registration and login
  - `/chat` — main conversation endpoint
  - `/upload` — document upload endpoint
  - `/cases` — case management endpoint

### 3. Onboarding Flow Handler
- Triggered on first message from a new user
- Presents structured opening prompt:
  ```
  "Hello, I am your ClaimPilot insurance assistant.
  Are you here to:
  1. File a new insurance claim
  2. Check status of an existing claim
  3. Ask a general insurance query"
  ```
- Captures initial intent and routes accordingly

### 4. Guardrails Layer (NeMo Guardrails)
- **Input Guardrails** — runs before any processing
  - Validates query is insurance-domain related
  - Topic taxonomy: motor claims, health claims, life insurance,
    travel insurance, home/property insurance, personal accident,
    IRDAI regulations, policy terms, claim procedures
  - Blocks: medical advice, legal advice unrelated to insurance,
    financial investment advice, off-topic conversation
- **Output Guardrails** — runs before response delivery
  - Validates LLM response does not hallucinate policy terms
  - Ensures response does not contradict IRDAI regulations
  - Flags responses with unsupported claims

### 5. Intent Classifier
- Single LLM call to Groq API
- Input: user's natural language description of situation
- Output: structured JSON with intent + confidence score
  ```json
  {
    "intent": "motor_claim",
    "confidence": 0.92,
    "description": "User reporting vehicle accident damage"
  }
  ```
- Confidence threshold: 0.75
  - Above threshold → proceed to LangGraph
  - Below threshold → ask clarifying question

**Supported Intents:**
| Intent | Example Trigger |
|--------|----------------|
| motor_claim | "I had a car accident", "My bike was stolen" |
| health_claim | "I was hospitalised", "Cancer diagnosis" |
| life_insurance | "I want life cover", "Nominee claim after death" |
| travel_insurance | "Lost baggage abroad", "Trip cancellation" |
| home_property | "House fire", "Flood damage to property" |
| personal_accident | "Fell and fractured my arm", "Workplace injury" |

### 6. LangGraph State Manager
- Manages full conversation state as a directed graph
- State schema:
  ```python
  {
    "user_id": str,
    "case_id": str,
    "intent": str,
    "required_docs": List[str],     # from IRDAI checklist
    "collected_docs": List[str],    # submitted by user
    "pending_docs": List[str],      # yet to be submitted
    "conversation_history": List,
    "case_status": str              # active | complete | escalated
  }
  ```
- State persisted to PostgreSQL via LangGraph PostgreSQL checkpointer
- Resumes seamlessly if user returns after closing chat

### 7. Document Ingestion Interface
Unified entry point for all PDF uploads. Two path pipeline:

**Path A — Digital PDF:**
- Detected via pdfplumber character extraction threshold
- If extracted characters > 100 per page → digital PDF confirmed
- Processed via pdfplumber for clean text extraction

**Path B — Scanned/Image PDF:**
- Detected when extracted characters < 100 per page
- Fallback to Tesseract OCR
- Converts PDF pages to images → OCR extracts text
- Implementation details discussed during development phase

### 8. Semantic Chunker
- Takes raw extracted text
- Splits into semantically meaningful chunks
- Uses sentence boundary detection — no mid-sentence splits
- Chunk size: ~500 tokens
- Overlap: ~50 tokens between consecutive chunks
- Preserves document section context in chunk metadata

### 9. Embedding Generator
- Model: `sentence-transformers/all-MiniLM-L6-v2`
- Runs locally — no API calls
- Converts each chunk into 384-dimensional vector
- Vectors passed to ChromaDB for storage

### 10. DocProcessor Agent
- Orchestrates the full ingestion pipeline
- On successful processing:
  - Stores vectors in user's ChromaDB collection
  - Stores document metadata in PostgreSQL
  - Updates LangGraph state — moves document from pending to collected
  - Triggers next document request if checklist still has pending items

### 11. ChromaDB — Two Collections

**Collection 1: User Documents**
- One collection per user: `user_{user_id}`
- Each vector carries metadata:
  ```python
  {
    "user_id": str,
    "case_id": str,
    "document_type": str,
    "filename": str,
    "chunk_index": int,
    "upload_timestamp": str
  }
  ```
- Deletion pipeline: when document deleted from PostgreSQL,
  corresponding vectors deleted from ChromaDB by metadata filter

**Collection 2: IRDAI Knowledge Base**
- Single shared collection: `irdai_knowledge_base`
- Pre-populated with IRDAI Master Circulars and Handbooks
- Read-only during runtime
- Covers: motor, health, life, travel, home, personal accident

### 12. Query Router
- Classifies incoming query into one of four buckets:
  - `personal_doc` → RAG over user's ChromaDB collection
  - `general_insurance` → RAG over IRDAI knowledge base collection
  - `ambiguous` → confidence below 0.75 → ask clarifying question
  - `off_topic` → route to input guardrails → block
- Single LLM call with structured JSON output

### 13. QueryResponder Agent
- Receives relevant chunks from ChromaDB retrieval
- Constructs prompt with:
  - Retrieved chunks as context
  - Conversation history
  - User profile metadata
- Generates response via Groq API
- For IRDAI queries — appends source document citation

### 14. PostgreSQL Database Schema

```
users
├── user_id (PK)
├── name
├── email
├── password_hash
└── created_at

cases
├── case_id (PK)
├── user_id (FK → users)
├── intent
├── case_status
└── created_at

documents
├── document_id (PK)
├── case_id (FK → cases)
├── user_id (FK → users)
├── filename
├── document_type
├── upload_timestamp
└── chroma_collection_ref

conversation_state
├── state_id (PK)
├── case_id (FK → cases)
├── user_id (FK → users)
├── state_json           ← LangGraph serialized state
└── updated_at
```

---

## Data Flow — New User Filing a Motor Claim

```
1. User opens chat → Onboarding Flow presents options
2. User selects "File a new claim"
3. User types: "I bumped my car into a pole today"
4. Input Guardrails → insurance-related → pass
5. Intent Classifier → motor_claim (confidence: 0.91) → pass
6. LangGraph State Manager:
   - Creates new case_id
   - Loads IRDAI motor claim document checklist
   - required_docs: [FIR copy, RC book, Driving License,
                     Repair Estimate, Insurance Policy copy]
   - collected_docs: []
   - pending_docs: [all five]
7. Agent responds: "I'm sorry to hear that. To process your
   motor insurance claim, I'll need a few documents.
   Let's start with the FIR copy. Please upload it."
8. User uploads PDF → Document Ingestion Interface
9. pdfplumber extracts text → Semantic Chunker → Embeddings
10. DocProcessor stores in ChromaDB (user namespace)
    + metadata in PostgreSQL
11. LangGraph updates: collected_docs: [FIR copy]
                        pending_docs: [RC book, Driving License,
                                       Repair Estimate, Policy copy]
12. Agent responds: "FIR copy received. Next, please upload
    your RC book."
13. Process repeats until all documents collected
14. Agent confirms: "All documents received. Your claim
    has been submitted successfully."
```

---

## Data Flow — Returning User with General Query

```
1. User opens chat → session resumed from PostgreSQL state
2. User types: "How long will my claim take to process?"
3. Input Guardrails → insurance-related → pass
4. Query Router → general_insurance query
5. RAG over IRDAI Knowledge Base
6. Retrieved chunks: IRDAI motor claim settlement timeline circular
7. QueryResponder generates answer grounded in IRDAI content
8. Output Guardrails → validates response → pass
9. Response delivered with IRDAI circular citation
```

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| PDF only in v1 | Reduces ingestion complexity, most insurance docs are PDF |
| Semantic chunking with overlap | Preserves context across chunk boundaries for better RAG retrieval |
| Separate ChromaDB collections per user | Prevents cross-user data leakage, enables clean deletion |
| IRDAI knowledge base over web search | Eliminates hallucination, jurisdiction-correct (India), stable content |
| LangGraph for state management | Built for stateful multi-step agent conversations, native PostgreSQL checkpointer |
| Dual guardrails | Input filtering + output validation — both necessary in high-stakes insurance domain |
| Confidence threshold on router and classifier | Graceful degradation via clarifying questions rather than wrong answers |
| case_id alongside user_id | Supports multiple simultaneous active cases per user |
