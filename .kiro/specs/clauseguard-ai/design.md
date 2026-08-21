# Technical Design Document — ClauseGuard

## Overview

ClauseGuard is a full-stack web application that allows renters to upload rental agreement PDFs, receive automated clause-level attention analysis, ask natural language questions grounded strictly in the document, and identify missing or unclear information. This document describes the technical design for the MVP.

---

## 1. System Architecture

```
┌─────────────────────────────────────────┐
│           React Frontend (Vite)         │
│   Tailwind CSS · React Router · Axios   │
└────────────────────┬────────────────────┘
                     │ REST API (HTTPS)
                     ▼
┌─────────────────────────────────────────┐
│         FastAPI Backend (Python)        │
│   Pydantic · SQLAlchemy · JWT Auth      │
├──────────────┬──────────────────────────┤
│  PostgreSQL  │        Chroma            │
│  (app data)  │  (vector store, scoped)  │
└──────────────┴──────────────────────────┘
                     │
          ┌──────────┴──────────┐
          │   Document Pipeline │
          │  PDF → Chunks →     │
          │  Embeddings →       │
          │  Chroma             │
          └──────────┬──────────┘
                     │
          ┌──────────┴──────────┐
          │   Groq LLM (API)    │
          │  RAG Q&A            │
          │  Clause Analysis    │
          └─────────────────────┘
```

---

## 2. Backend Structure

```
backend/
  app/
    main.py                    # FastAPI app, CORS, router registration
    config.py                  # Pydantic settings from env vars
    database.py                # SQLAlchemy engine, session factory
    dependencies.py            # FastAPI dependencies (get_db, get_current_user)

    api/
      auth.py                  # POST /auth/register, POST /auth/login
      documents.py             # POST /documents, GET /documents, GET /documents/{id}
      chat.py                  # POST /chat/sessions, GET /chat/sessions/{id}/messages, POST /chat/sessions/{id}/messages
      analysis.py              # GET /documents/{id}/analysis, GET /documents/{id}/missing-items

    models/
      user.py                  # User ORM model
      document.py              # Document ORM model
      clause.py                # Clause ORM model
      risk_flag.py             # RiskFlag ORM model
      chat.py                  # ChatSession + ChatMessage ORM models

    schemas/
      auth.py                  # RegisterRequest, LoginRequest, TokenResponse
      document.py              # DocumentCreate, DocumentResponse, DocumentStatus
      chat.py                  # SessionCreate, MessageCreate, MessageResponse
      analysis.py              # RiskFlagResponse, MissingItemResponse, AnalysisResponse

    services/
      auth_service.py          # register_user(), login_user(), hash_password(), verify_password()
      document_service.py      # create_document(), get_document(), list_documents(), update_status()
      pdf_service.py           # extract_text_by_page(file_bytes) -> List[PageText]
      clause_service.py        # extract_clauses(pages, document_id) -> List[Clause]
      embedding_service.py     # chunk_clause(clause) -> List[Chunk], embed_chunks(chunks) -> List[Vector]
      vector_service.py        # store_embeddings(), query_similar_chunks()
      rag_service.py           # answer_question(question, document_id, user_id) -> AnswerWithCitations
      llm_service.py           # complete(prompt) -> str, classify_clause(clause, category) -> LLMClassification
      risk_service.py          # detect_candidates(clauses) -> List[Candidate], analyze_document(document_id)
      analysis_service.py      # detect_missing_items(clauses) -> List[MissingItem], run_full_analysis(document_id)

    repositories/
      user_repo.py
      document_repo.py
      clause_repo.py
      risk_flag_repo.py
      chat_repo.py

    rules/
      risk_rules.py            # CATEGORY_KEYWORDS, CATEGORY_CRITERIA (the only source of risk definitions)

    utils/
      jwt_utils.py             # create_token(), decode_token()
      pdf_validator.py         # validate_pdf(file) -> bool
      response_validator.py    # validate_llm_classification(raw) -> LLMClassification | None

    tests/
      test_auth.py
      test_documents.py
      test_pdf_service.py
      test_clause_service.py
      test_embedding_service.py
      test_rag_service.py
      test_risk_service.py
      test_analysis_service.py
      conftest.py
```

---

## 3. Database Schema

### User
| Column        | Type         | Constraints              |
|---------------|--------------|--------------------------|
| id            | UUID (PK)    | default gen_random_uuid()|
| email         | VARCHAR(255) | UNIQUE, NOT NULL         |
| password_hash | VARCHAR(255) | NOT NULL                 |
| created_at    | TIMESTAMP    | default now()            |

### Document
| Column            | Type         | Constraints              |
|-------------------|--------------|--------------------------|
| id                | UUID (PK)    |                          |
| user_id           | UUID (FK)    | → User.id, NOT NULL      |
| title             | VARCHAR(500) | NOT NULL                 |
| original_filename | VARCHAR(500) | NOT NULL                 |
| processing_status | VARCHAR(20)  | default 'PENDING'        |
| processing_error  | TEXT         | nullable                 |
| created_at        | TIMESTAMP    | default now()            |
| updated_at        | TIMESTAMP    | default now()            |

Processing_Status enum: `PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`

### Clause
| Column        | Type      | Constraints         |
|---------------|-----------|---------------------|
| id            | UUID (PK) |                     |
| document_id   | UUID (FK) | → Document.id       |
| clause_number | INTEGER   |                     |
| section       | TEXT      | nullable            |
| page_number   | INTEGER   | NOT NULL            |
| text          | TEXT      | NOT NULL            |

Index: `(document_id, clause_number)`

### RiskFlag
| Column          | Type         | Constraints         |
|-----------------|--------------|---------------------|
| id              | UUID (PK)    |                     |
| document_id     | UUID (FK)    | → Document.id       |
| clause_id       | UUID (FK)    | → Clause.id, nullable|
| category        | VARCHAR(50)  | NOT NULL            |
| attention_level | VARCHAR(20)  | NOT NULL            |
| reason          | TEXT         | nullable            |
| tenant_impact   | TEXT         | nullable            |
| evidence        | TEXT         | nullable            |
| confidence      | FLOAT        | nullable            |
| created_at      | TIMESTAMP    | default now()       |

### ChatSession
| Column      | Type      | Constraints         |
|-------------|-----------|---------------------|
| id          | UUID (PK) |                     |
| user_id     | UUID (FK) | → User.id           |
| document_id | UUID (FK) | → Document.id       |
| created_at  | TIMESTAMP | default now()       |

### ChatMessage
| Column     | Type         | Constraints         |
|------------|--------------|---------------------|
| id         | UUID (PK)    |                     |
| session_id | UUID (FK)    | → ChatSession.id    |
| role       | VARCHAR(10)  | 'user' or 'assistant'|
| content    | TEXT         | NOT NULL            |
| created_at | TIMESTAMP    | default now()       |

---

## 4. API Design

### Auth Endpoints
```
POST /api/v1/auth/register
  Body: { email, password }
  Response: { access_token, token_type }

POST /api/v1/auth/login
  Body: { email, password }
  Response: { access_token, token_type }
```

### Document Endpoints
```
POST /api/v1/documents
  Auth: required
  Body: multipart/form-data (file: PDF, title: string)
  Response: { id, title, processing_status, created_at }

GET /api/v1/documents
  Auth: required
  Response: [{ id, title, original_filename, processing_status, created_at }]

GET /api/v1/documents/{document_id}
  Auth: required
  Response: { id, title, processing_status, created_at, ... }
```

### Analysis Endpoints
```
GET /api/v1/documents/{document_id}/analysis
  Auth: required
  Response: {
    document_id,
    risk_flags: [{ category, attention_level, reason, tenant_impact, evidence, confidence, clause_id }],
    missing_items: [{ item, status }]  // status: absent | unclear
  }
```

### Chat Endpoints
```
POST /api/v1/chat/sessions
  Auth: required
  Body: { document_id }
  Response: { id, document_id, created_at }

GET /api/v1/chat/sessions/{session_id}/messages
  Auth: required
  Response: [{ id, role, content, citations, created_at }]

POST /api/v1/chat/sessions/{session_id}/messages
  Auth: required
  Body: { content: string }
  Response: { id, role, content, citations: [{ page, clause, text }], created_at }
```

---

## 5. Document Processing Pipeline

```
1. Upload handler receives PDF bytes
2. PDF_Service.extract_text_by_page(bytes) → List[{page_number, text}]
3. Clause_Service.extract_clauses(pages) → List[Clause]
4. For each Clause:
   a. Embedding_Service.chunk_clause(clause) → List[Chunk]
   b. For each Chunk: Embedding_Service.embed(chunk.text) → vector
   c. Vector_Service.store(chunk, vector, metadata)
5. Document status → COMPLETED
6. Analysis_Service.run_full_analysis(document_id) [runs after COMPLETED]
```

Processing runs synchronously in a background task (FastAPI `BackgroundTasks`). No message queue needed for MVP.

---

## 6. Document Processing — Implementation Details

### PDF Service
- Library: `pdfplumber` (handles text extraction with page awareness)
- Output: `List[PageText]` where `PageText = {page_number: int, text: str}`
- Fallback: if all pages return empty text → raise `ExtractionError`

### Clause Service
Detection strategy (in order):
1. Numbered clause pattern: `^\s*(\d+\.[\d\.]*)\s+[A-Z]` → numbered clause
2. ALL-CAPS heading: `^\s*[A-Z][A-Z\s]{3,}\s*$` → section heading
3. Title-case heading followed by body text
4. Fallback: treat each page as one clause

Each clause stores: `clause_number`, `section` (nearest heading), `page_number`, `text`.

### Chunking
- Max chunk size: 512 tokens (approximated as 400 words)
- Overlap: 50 tokens (approximated as 40 words)
- Use `langchain.text_splitter.RecursiveCharacterTextSplitter`

### Embedding Model
- Model: `sentence-transformers/all-MiniLM-L6-v2`
- Loaded once at startup, reused via singleton
- Produces 384-dimensional vectors

### Chroma
- Collection name: `clauseguard_{user_id}_{document_id}` (or use metadata filtering)
- Preferred approach: single collection `clauseguard_documents`, filter on metadata
- Metadata stored per chunk: `user_id`, `document_id`, `page_number`, `clause_number`, `section`, `text`
- Isolation: every query includes `where={"user_id": user_id, "document_id": document_id}`

---

## 7. RAG Pipeline

```
1. User submits question
2. Embed question → query vector
3. Vector_Service.query(vector, user_id, document_id, top_k=5)
4. If 0 chunks returned → return fallback message
5. Build prompt:
   - System: "Answer only from the provided document excerpts. If not found, say so."
   - Context: top-5 chunks with page/clause metadata
   - User question
6. LLM_Service.complete(prompt) → answer text
7. Extract citations from chunk metadata
8. Return { answer, citations: [{page, clause, text}] }
```

### Anti-hallucination prompt
```
System: You are a document analysis assistant. Answer ONLY based on the provided document excerpts below.
Do NOT use any external knowledge. Do NOT invent information.
If the answer is not in the excerpts, respond exactly:
"I couldn't find a clear answer to this in your agreement."

Document excerpts:
[CHUNK 1 — Page X, Clause Y]
{text}
...
```

---

## 8. Risk Analysis

### risk_rules.py structure
```python
ATTENTION_CATEGORIES = [
    "SECURITY_DEPOSIT", "LOCK_IN", "NOTICE_PERIOD", "MAINTENANCE",
    "TERMINATION", "PENALTIES", "RENT_ESCALATION", "SUBLETTING",
    "RENEWAL", "DISPUTE_RESOLUTION"
]

CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    "SECURITY_DEPOSIT": ["security deposit", "caution deposit", "refundable deposit", ...],
    "LOCK_IN": ["lock-in", "lock in", "minimum period", "early exit", ...],
    # ... etc
}

CATEGORY_CRITERIA: Dict[str, str] = {
    "SECURITY_DEPOSIT": """
        Evaluate whether the clause clearly states:
        - The deposit amount
        - Conditions under which deductions can be made
        - The process for returning the deposit
        Attention may be appropriate if deduction conditions are broad or undefined.
        Do NOT assess legality or statutory compliance.
    """,
    # ... etc
}
```

### Detection flow
```
1. For each clause in document:
   For each category in ATTENTION_CATEGORIES:
     If any keyword in CATEGORY_KEYWORDS[category] found in clause.text (case-insensitive):
       Add (clause, category) to candidates

2. For each (clause, category) candidate:
   prompt = build_classification_prompt(clause.text, category, CATEGORY_CRITERIA[category])
   raw = LLM_Service.complete(prompt)
   result = response_validator.validate_llm_classification(raw)
   If result valid:
     Create RiskFlag from result
   Else:
     Create RiskFlag with attention_level=ANALYSIS_REQUIRES_REVIEW

3. For each category with no candidates found:
   Create RiskFlag(category=category, attention_level=NO_DEFINED_RISK)
```

### Classification prompt
```
Analyze the following rental agreement clause for the category: {category}

Category criteria:
{criteria}

Clause text:
{clause_text}

Return ONLY a JSON object with these exact fields:
{
  "category": "{category}",
  "attention_level": "HIGH" | "MEDIUM" | "LOW" | "NO_DEFINED_RISK",
  "reason": "...",
  "tenant_impact": "...",
  "evidence": "...",
  "confidence": 0.0 to 1.0
}

Rules:
- Do NOT assess legality or enforceability
- Do NOT reference any laws, statutes, or legal thresholds
- Base your classification ONLY on the clause text provided
- Use only the allowed attention_level values
```

---

## 9. Missing / Unclear Items Detection

### Items checked (17 total)
```python
MISSING_ITEMS = [
    "rent_amount", "security_deposit", "deposit_refund", "deposit_deductions",
    "notice_period", "lock_in_period", "termination_conditions",
    "maintenance_responsibility", "repair_responsibility", "utilities",
    "rent_escalation", "renewal_conditions", "subletting_restrictions",
    "dispute_resolution", "property_details", "parties", "agreement_duration"
]
```

### Detection approach
For each item, use a hybrid approach:
1. Keyword matching to find candidate clauses for the item
2. If no candidates found → `absent`
3. If candidates found → pass to LLM with a focused prompt:
   "Does this text clearly specify {item_description}? Answer: PRESENT, UNCLEAR, or ABSENT. Explain briefly."
4. If LLM says PRESENT → skip
5. If LLM says UNCLEAR or ABSENT → record accordingly

---

## 10. Frontend Structure

```
frontend/
  src/
    main.jsx
    App.jsx                    # Router setup
    
    pages/
      LandingPage.jsx          # / route
      LoginPage.jsx            # /login
      RegisterPage.jsx         # /register
      DashboardPage.jsx        # /dashboard
      UploadPage.jsx           # /documents/new
      DocumentPage.jsx         # /documents/:id

    components/
      layout/
        Navbar.jsx
        Footer.jsx
        ProtectedRoute.jsx
        Disclaimer.jsx

      dashboard/
        DocumentCard.jsx
        EmptyState.jsx

      document/
        ProcessingIndicator.jsx
        DocumentSummary.jsx
        AttentionFlags.jsx
        AttentionFlagCard.jsx
        MissingItems.jsx
        ChatPanel.jsx
        CitationBadge.jsx

      ui/
        Button.jsx
        Input.jsx
        Badge.jsx
        Spinner.jsx
        ErrorMessage.jsx

    hooks/
      useAuth.js
      useDocuments.js
      useChat.js

    context/
      AuthContext.jsx

    services/
      api.js                   # Axios instance with base URL + auth interceptor
      authApi.js
      documentsApi.js
      chatApi.js
      analysisApi.js

    utils/
      formatDate.js
      attentionLevelColor.js
```

---

## 11. Authentication Flow

```
Register:
  POST /auth/register → { access_token }
  Store token in localStorage
  Redirect to /dashboard

Login:
  POST /auth/login → { access_token }
  Store token in localStorage
  Redirect to /dashboard

Protected routes:
  Axios interceptor adds Authorization: Bearer {token} to all requests
  ProtectedRoute component reads AuthContext — if no token, redirect to /login
  On 401 response → clear token, redirect to /login
```

---

## 12. Configuration and Secrets

All configuration read from environment variables via Pydantic `BaseSettings`:

```python
class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    GROQ_API_KEY: str
    GROQ_MODEL: str = "llama3-8b-8192"
    CHROMA_HOST: str = "chroma"
    CHROMA_PORT: int = 8000
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    MAX_FILE_SIZE_MB: int = 20
    CORS_ORIGINS: str = "http://localhost:5173"
    
    class Config:
        env_file = ".env"
```

---

## 13. Docker Configuration

```yaml
# docker-compose.yml services:
services:
  db:
    image: postgres:15
    environment: POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
    volumes: postgres_data:/var/lib/postgresql/data
    healthcheck: pg_isready

  chroma:
    image: chromadb/chroma:latest
    ports: 8001:8000
    volumes: chroma_data:/chroma/chroma

  backend:
    build: ./backend
    depends_on: [db, chroma]
    environment: (all Settings vars)
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000

  frontend:
    build: ./frontend
    depends_on: [backend]
    ports: 3000:80
    environment: VITE_API_URL
```

Backend Dockerfile: Python 3.11 slim, pip install, uvicorn start
Frontend Dockerfile: Node 18, npm build, nginx serve

---

## 14. CI/CD Pipeline

```yaml
# .github/workflows/ci.yml
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres: (postgres:15)
    steps:
      - checkout
      - setup python 3.11
      - pip install -r requirements.txt
      - run: pytest --cov=app --cov-report=xml --cov-fail-under=80
      - upload coverage report

  lint:
    runs-on: ubuntu-latest
    steps:
      - checkout
      - setup python 3.11
      - pip install ruff
      - run: ruff check app/

  build-frontend:
    runs-on: ubuntu-latest
    steps:
      - checkout
      - setup node 18
      - npm ci
      - npm run build
```

---

## 15. Security Measures

- Passwords hashed with bcrypt (passlib), cost factor 12
- JWT signed with HS256, 24-hour expiry, secret from env var
- All protected endpoints require `Depends(get_current_user)`
- Document ownership checked in every repository query (user_id filter)
- PDF validation: MIME type check + magic bytes check + 20MB size limit
- Chroma queries always include `user_id` + `document_id` filter
- CORS restricted to configured origins
- No API keys in source code or Docker files
- No full document text logged

---

## 16. Key Design Decisions

| Decision | Choice | Reason |
|---|---|---|
| Async processing | FastAPI `BackgroundTasks` | Sufficient for MVP; no queue infra needed |
| Vector isolation | Metadata filter on single collection | Simpler than per-user collections; equally secure |
| Embedding model | all-MiniLM-L6-v2 | Fast, small, good for semantic search |
| PDF library | pdfplumber | Best page-aware text extraction for rental agreements |
| Risk rules | rules/risk_rules.py only | Single source of truth, prevents rule invention |
| LLM provider | Groq (Llama 3) | Fast inference, free tier, no GPU needed |
| Token counting | word-count approximation | Avoids tiktoken dependency in MVP |
