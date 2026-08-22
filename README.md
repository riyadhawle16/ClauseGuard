# ClauseGuard

> **Understand. Protect. Negotiate.**

ClauseGuard is an AI-powered rental agreement intelligence platform built for renters in India. Upload your rental agreement PDF and ClauseGuard will extract every clause, flag areas worth your attention, identify missing or unclear information, and answer your questions — all grounded strictly in your own document.

**ClauseGuard is not a legal-advice platform.** It is a document-analysis and decision-support tool. All analysis is based on predefined rules and retrieved document content only.

---

## Live Architecture

```
React Frontend (Vite + Tailwind)
        │
        │ REST API
        ▼
FastAPI Backend (Python)
        │
   ┌────┴────┐
   ▼         ▼
PostgreSQL  Chroma
(app data)  (vector store)
        │
        ▼
  Groq LLM (llama3)
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, Tailwind CSS, React Router, Axios |
| Backend | Python 3.11, FastAPI, Pydantic, SQLAlchemy |
| Database | PostgreSQL |
| Authentication | JWT, bcrypt/passlib |
| Vector Store | Chroma (persistent) |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`) |
| LLM | Groq API (llama3-8b-8192) |
| Testing | pytest, pytest-cov |
| Infrastructure | Docker, GitHub Actions |
| Deployment | Frontend → Vercel · Backend → Render/Railway |

---

## Implementation Phases

The project is implemented in 10 phases. **Phases 1–9 are complete.**

---

### ✅ Phase 1 — Project Foundation

**Status: Complete**

- FastAPI backend with health endpoint (`GET /health`)
- Modular backend structure (`api/`, `models/`, `schemas/`, `services/`, `repositories/`, `rules/`, `utils/`)
- Pydantic `BaseSettings` configuration (all values from environment variables)
- SQLAlchemy engine + `SessionLocal` + `Base`
- React + Vite + Tailwind CSS frontend scaffold
- All 6 routes stubbed (`/`, `/login`, `/register`, `/dashboard`, `/documents/new`, `/documents/:id`)
- Docker Compose with PostgreSQL
- `.env.example` for all required variables
- 2 tests passing

---

### ✅ Phase 2 — Authentication

**Status: Complete**

- User registration with bcrypt password hashing
- JWT login (configurable expiry)
- `GET /api/v1/auth/me` — returns safe user info (no password hash)
- `get_current_user` FastAPI dependency used by all protected endpoints
- Frontend: Login page, Register page, `AuthContext`, `ProtectedRoute`
- Token stored in `localStorage`; 401 → auto-redirect to `/login`
- Generic error messages (no user enumeration)
- Alembic migration: `users` table
- 17 tests passing (cumulative)

---

### ✅ Phase 3 — PDF Upload

**Status: Complete**

- `POST /api/v1/documents` — multipart PDF upload
- PDF validation: magic bytes check, extension check, 20 MB size limit
- Safe UUID-based file storage (original filename never used as path)
- `GET /api/v1/documents` — user's document list
- `GET /api/v1/documents/{id}` — single document (404 if not owned)
- `DELETE /api/v1/documents/{id}` — deletes record + stored file
- `processing_status` starts as `"uploaded"`
- User isolation: all queries scoped by JWT-derived user ID
- `storage_service.py` abstraction for filesystem operations
- Alembic migration: `documents` table
- Frontend: Upload page with drag & drop, Dashboard with document cards
- 35 tests passing (cumulative)

---

### ✅ Phase 4 — PDF Processing & Clause Extraction

**Status: Complete**

- `POST /api/v1/documents/{id}/process` — triggers processing
- PDF text extraction using `pypdf` (page-aware, 1-based page numbers)
- Text normalization utility (`normalize_text`, `is_effectively_empty`)
- Deterministic clause extraction (numbered headings, ALL-CAPS headings, title-case headings, page fallback)
- Bulk clause insert into PostgreSQL
- Status transitions: `uploaded → processing → ready` (or `failed`)
- Reprocessing safety: existing clauses replaced, never duplicated
- `GET /api/v1/documents/{id}/clauses` — returns extracted clauses
- Empty/image-only PDFs fail safely with a user-friendly message
- Alembic migration: `clauses` table
- Frontend: Process Document button, clause list display, processing states
- 59 tests passing (cumulative)

---

### ✅ Phase 5 — Embeddings & Chroma Vector Store

**Status: Complete**

- `sentence-transformers/all-MiniLM-L6-v2` — 384-dim embeddings (lazy-loaded singleton)
- Chroma persistent client — single collection `clauseguard_clauses`
- Deterministic vector IDs (= `clause_id`) — idempotent upsert
- Metadata per vector: `document_id`, `clause_id`, `clause_number`, `page_number`, `heading`
- `GET /api/v1/documents/{id}/search?q=...` — semantic search (no LLM, retrieval only)
- Reprocessing: old vectors deleted before new ones stored
- Document deletion: vectors cleaned up alongside DB records
- User isolation: all queries filtered by `document_id`
- `CHROMA_PERSIST_DIRECTORY` configurable via env var
- 80 tests passing (cumulative)

---

### ✅ Phase 6 — RAG Q&A with Citations

**Status: Complete**

- `POST /api/v1/documents/{id}/chat` — ask a question, receive a grounded answer + citations
- `GET /api/v1/documents/{id}/chat` — retrieve full chat history
- RAG pipeline:
  1. Embed question
  2. Semantic search (Chroma, filtered by `document_id`)
  3. Relevance threshold (distance ≤ 0.85) — fallback if no relevant clauses
  4. Build structured context (`[Clause N | Page P]`)
  5. Strict system prompt (no legal advice, untrusted document data instruction)
  6. Groq LLM (`llama3-8b-8192`)
  7. Backend-generated citations (never from LLM output)
- Chat sessions persisted (`chat_sessions`, `chat_messages` tables)
- Last 8 messages included as conversation context
- Groq API failures return safe generic message — no stack traces
- Prompt injection defence: document content marked as untrusted
- Alembic migration: `chat_sessions` + `chat_messages` tables
- Frontend: Chat panel with message history, citations, loading state
- 103 tests passing (cumulative)

---

### ✅ Phase 7 — Automated Attention Analysis

**Status: Complete**

- `POST /api/v1/documents/{id}/analyze-attention` — run attention analysis
- `GET /api/v1/documents/{id}/attention` — retrieve stored flags
- **Exactly 10 predefined categories** (defined in `app/rules/attention_rules.py`):

  | Category | Purpose |
  |---|---|
  | `SECURITY_DEPOSIT` | Deposit amount, refund, deduction terms |
  | `NOTICE_PERIOD` | Notice requirements for both parties |
  | `LOCK_IN_PERIOD` | Minimum stay, early exit restrictions |
  | `EARLY_TERMINATION` | Consequences of ending the agreement early |
  | `MAINTENANCE_RESPONSIBILITY` | Repair and upkeep assignment |
  | `RENT_INCREASE` | Escalation schedules and revision terms |
  | `LANDLORD_TERMINATION` | Landlord's right to terminate |
  | `TENANT_TERMINATION` | Tenant's right to terminate |
  | `PENALTIES_AND_LIQUIDATED_DAMAGES` | Monetary penalties and compensation |
  | `MAINTENANCE_AND_UTILITY_CHARGES` | Recurring charges assigned to tenant |

- **Two-layer detection:**
  - Layer 1 (deterministic): case-insensitive keyword/pattern matching — always runs
  - Layer 2 (optional LLM): confirms match, provides confidence score; never invents categories
- Severity: `review` or `important` — NOT a legal assessment
- Idempotent: re-running replaces previous flags
- Legal safety: no legal conclusions, no "illegal/unlawful/unenforceable" language
- Alembic migration: `attention_flags` table
- Frontend: Collapsible attention panel with category badges
- 140 tests passing (cumulative)

---

### ✅ Phase 8 — Missing / Unclear Information Detection

**Status: Complete**

- `POST /api/v1/documents/{id}/analyze-missing-info` — run information completeness check
- `GET /api/v1/documents/{id}/missing-info` — retrieve stored results
- Reuses all 10 Phase 7 attention categories
- **Three statuses:**
  - `PRESENT` — information clearly found
  - `UNCLEAR` — partial signal, not clearly stated
  - `NOT_IDENTIFIED` — not found at all
- **Two-layer detection:**
  - Layer 1 (deterministic): strong patterns (→ PRESENT) + weak patterns (→ UNCLEAR) + no match (→ NOT_IDENTIFIED)
  - Layer 2 (optional LLM): refines UNCLEAR/NOT_IDENTIFIED results; LLM failure → deterministic result kept
- Returns all 10 category results per analysis
- Evidence clause linked when found
- Idempotent: re-running replaces previous results
- Legal safety: "not clearly identified" framing only — never "missing illegally"
- Alembic migration: `missing_info_flags` table
- Frontend: Information completeness panel with PRESENT/UNCLEAR/NOT_IDENTIFIED chips
- 176 tests passing (cumulative)

---

### ✅ Phase 9 — Dashboard Integration & Product Polish

**Status: Complete**

- **Dashboard:** stats bar (total, ready, processing, uploaded), improved document cards with clause count and "Open Agreement" button, empty state with upload prompt
- **Document page:** reorganised into 6 sections in priority order — Agreement Overview → Processing → Attention Analysis → Missing Information → Ask Your Agreement → Extracted Clauses (collapsible)
- **Analysis summary:** compact card showing attention item count and missing-info breakdown appears at top of document page after analysis
- **Navbar:** shared sticky navigation with logo, Dashboard link, Upload shortcut, Sign out
- **Landing page:** polished hero + feature grid
- **Upload page:** drag-and-drop zone, file size display, improved error messages
- **Error handling:** specific messages for 401/403/422/413/503; no stack traces ever shown
- **Empty states:** all sections have friendly empty-state messages
- **Responsive:** all pages work on mobile, tablet, and desktop
- No backend changes were required for Phase 9
- 176 tests passing (unchanged — Phase 9 is frontend only)
- Frontend build: **110 modules, 2.62s**

---

### ⏳ Phase 10 — Testing, Docker, CI/CD & Deployment Preparation

**Status: Planned**

- Complete pytest coverage (≥ 80% line coverage)
- Docker Compose: backend + frontend + PostgreSQL + Chroma
- GitHub Actions CI/CD pipeline: lint → test → coverage → build
- Vercel deployment configuration for frontend
- Render/Railway deployment configuration for backend
- `DEPLOYMENT.md` with environment variable documentation
- Final security review

---

## Project Structure

```
ClauseGuard/
├── backend/
│   ├── app/
│   │   ├── api/            # Route handlers
│   │   ├── models/         # SQLAlchemy ORM models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   ├── repositories/   # Database access layer
│   │   ├── rules/          # Attention & missing-info rules (source of truth)
│   │   ├── utils/          # PDF validator, text normalizer, JWT utils
│   │   └── tests/          # pytest test suite
│   ├── migrations/         # Alembic migrations
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── pages/          # Route-level page components
│   │   ├── components/     # Reusable UI components
│   │   ├── services/       # Axios API clients
│   │   ├── context/        # AuthContext
│   │   └── hooks/
│   ├── package.json
│   ├── Dockerfile
│   └── nginx.conf
├── docker-compose.yml
└── .gitignore
```

---

## Quick Start (Local Development)

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+

### Backend

```bash
cd backend
cp .env.example .env
# Fill in DATABASE_URL, JWT_SECRET_KEY, GROQ_API_KEY
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

### Docker (all services)

```bash
docker-compose up --build
```

Backend: http://localhost:8000  
Frontend: http://localhost:3000  
API docs: http://localhost:8000/docs

---

## Environment Variables

Copy `backend/.env.example` and fill in:

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `JWT_SECRET_KEY` | Secret for JWT signing (keep private) |
| `GROQ_API_KEY` | Groq API key (get from console.groq.com) |
| `GROQ_MODEL` | Groq model ID (default: `llama3-8b-8192`) |
| `CHROMA_PERSIST_DIRECTORY` | Directory for Chroma data (default: `./chroma_data`) |
| `UPLOAD_DIR` | Directory for uploaded PDFs (default: `./uploads`) |
| `CORS_ORIGINS` | Allowed frontend origins |
| `MAX_FILE_SIZE_MB` | Max PDF upload size (default: `20`) |

---

## Running Tests

```bash
cd backend
pytest app/tests/ -v
pytest app/tests/ --cov=app --cov-report=term-missing
```

Current test count: **176 passing**

---

## Legal Disclaimer

ClauseGuard provides document analysis and general informational insights. It is not a substitute for professional legal advice. Attention indicators are based on predefined document-analysis rules and should not be interpreted as legal conclusions.

---

## License

This project is built as a portfolio project. All rights reserved.
