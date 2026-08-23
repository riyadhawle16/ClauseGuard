# ClauseGuard

**Understand. Protect. Negotiate.**

An AI-powered rental agreement analyzer for renters. Upload a lease PDF and it extracts clauses, flags terms worth your attention, identifies missing information, and answers your questions — all grounded strictly in your own document.

🔗 **Live demo:** [clause-guard-ruddy.vercel.app](https://clause-guard-ruddy.vercel.app)

> ClauseGuard is a document-analysis tool, not a legal-advice platform. All analysis uses predefined rules and retrieved document content only.

---

## Features

- **Clause Extraction** — Deterministic, page-aware extraction of clauses from uploaded PDFs
- **Semantic Search & Q&A** — RAG pipeline (ChromaDB + Groq LLM) answers questions grounded in the document, with citations generated from the database, not the LLM
- **Attention Analysis** — Flags 10 predefined risk categories (deposit, notice period, lock-in, penalties, etc.) via deterministic rules + optional LLM classification — the LLM can't invent categories or make legal conclusions
- **Missing Information Detection** — Marks each category `PRESENT`, `UNCLEAR`, or `NOT_IDENTIFIED`
- **Auth** — JWT-based, with every document/session scoped to its owning user

---

## Tech Stack

React, Vite, Tailwind · FastAPI, Python, SQLAlchemy · PostgreSQL · ChromaDB · sentence-transformers · Groq LLM (llama3) · JWT · pytest · Docker · GitHub Actions (CI/CD) · Vercel + Render (deployment)

---

## Architecture

```
React (Vite/Tailwind) → FastAPI Backend → PostgreSQL + ChromaDB → Groq LLM
```

**RAG flow:** Question → Embedding → Semantic Search → Grounded Context → LLM → Answer + Citation (from DB, not the model)

---

## Legal Safety Design

The LLM never makes legal judgments. Instead of *"this clause is illegal,"* it says *"this may be worth reviewing — the agreement contains a penalty condition."* The 10 risk categories are hardcoded; the LLM classifies within them but can't invent new ones or apply legal thresholds. This deterministic-rules + LLM split was a deliberate choice for predictability and safety.

---

## Security

JWT auth + bcrypt · ownership isolation on every query (cross-user access → 404) · PDF validation (size/type/magic bytes) + UUID file storage · secrets server-side only · no stack traces exposed to clients.

---

## Running Locally

```bash
# Backend
cd backend && cp .env.example .env   # add DATABASE_URL, JWT_SECRET_KEY, GROQ_API_KEY
pip install -r requirements.txt && alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend && cp .env.example .env && npm install && npm run dev

# Or, everything via Docker
docker-compose up --build
```

**Tests:** `pytest app/tests/ -v` — covers auth, upload, PDF processing, RAG retrieval, attention analysis, and missing-info detection. Runs automatically via GitHub Actions on every push/PR to `main`.

---



*ClauseGuard provides document analysis and general informational insights. It is not a substitute for professional legal advice.*
