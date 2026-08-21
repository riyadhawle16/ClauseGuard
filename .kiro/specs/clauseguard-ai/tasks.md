# Tasks

## Phase 1: Project Foundation

- [x] 1. Initialize backend project structure
  - Create `backend/` directory with `app/` package
  - Create `app/main.py` with FastAPI app instance, health check endpoint (`GET /health`), and CORS middleware skeleton
  - Create `app/config.py` with Pydantic `BaseSettings` reading all env vars: `DATABASE_URL`, `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `JWT_EXPIRE_MINUTES`, `GROQ_API_KEY`, `GROQ_MODEL`, `CHROMA_HOST`, `CHROMA_PORT`, `EMBEDDING_MODEL`, `MAX_FILE_SIZE_MB`, `CORS_ORIGINS`
  - Create `app/database.py` with SQLAlchemy engine, `SessionLocal`, and `Base`
  - Create `app/dependencies.py` with `get_db` dependency
  - Create empty `__init__.py` in all package directories
  - Create `backend/requirements.txt` with pinned versions: fastapi, uvicorn, sqlalchemy, psycopg2-binary, pydantic-settings, python-jose, passlib[bcrypt], python-multipart, pdfplumber, langchain, langchain-community, chromadb, sentence-transformers, groq, pytest, pytest-cov, pytest-asyncio, httpx, ruff
  - Create `backend/.env.example` listing all required env vars with placeholder values
  - Verify: `python -c "from app.main import app"` succeeds
  - _Requirements: 23_

- [x] 2. Initialize frontend project structure
  - Scaffold with `npm create vite@latest frontend -- --template react`
  - Install dependencies: tailwindcss, postcss, autoprefixer, react-router-dom, axios
  - Configure Tailwind CSS (`tailwind.config.js`, `postcss.config.js`, import in `index.css`)
  - Create `src/services/api.js` with Axios instance pointing to `VITE_API_URL` env var
  - Create `frontend/.env.example` with `VITE_API_URL=http://localhost:8000`
  - Create `src/App.jsx` with `BrowserRouter` and placeholder routes for `/`, `/login`, `/register`, `/dashboard`, `/documents/new`, `/documents/:id`
  - Create stub page components (`LandingPage`, `LoginPage`, `RegisterPage`, `DashboardPage`, `UploadPage`, `DocumentPage`) that render a heading only
  - Verify: `npm run dev` starts without errors, all routes render stubs
  - _Requirements: 18_

---

## Phase 2: Authentication

- [-] 3. Implement User model and database migration
  - Create `app/models/user.py` with `User` SQLAlchemy model: `id` (UUID PK), `email` (VARCHAR 255, UNIQUE), `password_hash` (VARCHAR 255), `created_at` (TIMESTAMP default now)
  - Create `app/models/__init__.py` importing all models
  - Add Alembic for migrations: `alembic init migrations`, configure `env.py` to use `Base.metadata` and `DATABASE_URL`
  - Generate initial migration: `alembic revision --autogenerate -m "create_users_table"`
  - Verify migration applies cleanly against a test PostgreSQL instance
  - _Requirements: 1, 2_

- [ ] 4. Implement auth schemas and JWT utilities
  - Create `app/schemas/auth.py`: `RegisterRequest` (email, password with min length 8 validation), `LoginRequest`, `TokenResponse` (access_token, token_type)
  - Create `app/utils/jwt_utils.py`: `create_access_token(data: dict) -> str` and `decode_access_token(token: str) -> dict` using `python-jose`, reading secret and algorithm from `Settings`
  - Add `get_current_user` dependency to `app/dependencies.py` that reads the Bearer token from the Authorization header, decodes it, and returns the user_id
  - _Requirements: 1, 2, 3_

- [ ] 5. Implement auth service and repository
  - Create `app/repositories/user_repo.py`: `get_by_email(db, email)`, `create_user(db, email, password_hash)`
  - Create `app/services/auth_service.py`: `register_user(db, email, password) -> TokenResponse` (checks duplicate email → 409, hashes password, creates user, returns JWT), `login_user(db, email, password) -> TokenResponse` (verifies credentials → 401 on any failure, returns JWT)
  - _Requirements: 1, 2_

- [ ] 6. Implement auth API endpoints
  - Create `app/api/auth.py` with `POST /api/v1/auth/register` and `POST /api/v1/auth/login`
  - Register router in `app/main.py` with prefix `/api/v1`
  - _Requirements: 1, 2_

- [ ] 7. Implement frontend authentication
  - Create `src/context/AuthContext.jsx` with `AuthProvider` storing JWT in localStorage, providing `login()`, `logout()`, `isAuthenticated`, `token`
  - Create `src/hooks/useAuth.js` consuming AuthContext
  - Create `src/services/authApi.js` with `register(email, password)` and `login(email, password)` functions
  - Update Axios instance in `api.js` to add `Authorization: Bearer {token}` header interceptor and 401 response interceptor (clear token + redirect to /login)
  - Implement `src/components/layout/ProtectedRoute.jsx` redirecting unauthenticated users to `/login`
  - Implement `LoginPage.jsx`: form with email/password, calls `authApi.login`, stores token, redirects to `/dashboard`
  - Implement `RegisterPage.jsx`: form with email/password, calls `authApi.register`, stores token, redirects to `/dashboard`
  - Implement `LandingPage.jsx`: marketing page with links to `/login` and `/register`, and the legal disclaimer
  - Wrap `/dashboard`, `/documents/new`, `/documents/:id` routes in `ProtectedRoute`
  - Add redirect from `/` and `/login` to `/dashboard` when already authenticated
  - _Requirements: 2, 3, 16, 18_

- [ ] 8. Write auth tests
  - Create `backend/app/tests/conftest.py` with test database setup (SQLite in-memory), `TestClient` fixture
  - Create `backend/app/tests/test_auth.py` testing: successful registration returns JWT, duplicate email returns 409, short password returns 422, successful login returns JWT, wrong password returns 401, unknown email returns 401, protected endpoint without token returns 401, protected endpoint with valid token succeeds
  - _Requirements: 1, 2, 3, 21_

---

## Phase 3: PDF Upload

- [ ] 9. Implement Document model and migration
  - Create `app/models/document.py` with `Document` SQLAlchemy model: `id` (UUID PK), `user_id` (UUID FK → User.id), `title` (VARCHAR 500), `original_filename` (VARCHAR 500), `processing_status` (VARCHAR 20 default 'PENDING'), `processing_error` (TEXT nullable), `created_at`, `updated_at`
  - Generate and apply migration: `alembic revision --autogenerate -m "create_documents_table"`
  - _Requirements: 4, 8_

- [ ] 10. Implement document schemas and repository
  - Create `app/schemas/document.py`: `DocumentCreate`, `DocumentResponse` (id, title, original_filename, processing_status, created_at), `DocumentListResponse`
  - Create `app/repositories/document_repo.py`: `create_document()`, `get_document_by_id(db, doc_id, user_id)` (returns None if not owned by user), `list_documents_by_user(db, user_id)`, `update_processing_status(db, doc_id, status, error=None)`
  - _Requirements: 4, 8, 17, 24_

- [ ] 11. Implement PDF upload endpoint
  - Create `app/utils/pdf_validator.py`: `validate_pdf(file_bytes, filename, max_size_mb) -> None` — checks file size ≤ MAX_FILE_SIZE_MB (raises 413 if exceeded), checks MIME type is `application/pdf` or filename ends in `.pdf` (raises 422 if not), checks first 4 bytes are `%PDF` magic bytes (raises 422 if not)
  - Create `app/services/document_service.py`: `create_document(db, user_id, title, original_filename) -> Document`, `get_document(db, doc_id, user_id) -> Document`, `list_documents(db, user_id) -> List[Document]`
  - Create `app/api/documents.py` with:
    - `POST /api/v1/documents` — accepts `multipart/form-data` (file + title), validates PDF, creates Document record (status PENDING), saves file bytes to `uploads/{document_id}.pdf`, returns DocumentResponse
    - `GET /api/v1/documents` — returns user's document list
    - `GET /api/v1/documents/{document_id}` — returns single document (404 if not owned)
  - Register router in `main.py`
  - _Requirements: 4, 8, 17, 24_

- [ ] 12. Implement frontend upload page
  - Implement `src/services/documentsApi.js` with `uploadDocument(file, title)`, `listDocuments()`, `getDocument(id)`, `getAnalysis(id)`
  - Implement `UploadPage.jsx`: drag-and-drop or file-picker for PDF, title input, submit calls `documentsApi.uploadDocument`, shows upload progress/success, redirects to `/documents/:id` on success
  - Implement `DashboardPage.jsx`: fetches and displays user's documents using `DocumentCard` component (title, filename, status badge, date), `EmptyState` when no documents, link to `/documents/new`
  - Create `src/components/dashboard/DocumentCard.jsx` and `EmptyState.jsx`
  - _Requirements: 4, 15, 17, 18_

- [ ] 13. Write document upload tests
  - Test: successful PDF upload creates document and returns 201, non-PDF file returns 422, file > 20MB returns 413, upload without auth returns 401, other user cannot access document (returns 404)
  - _Requirements: 4, 21, 24_

---

## Phase 4: PDF Processing and Clause Extraction

- [ ] 14. Implement Clause model and migration
  - Create `app/models/clause.py`: `id` (UUID PK), `document_id` (UUID FK), `clause_number` (INTEGER), `section` (TEXT nullable), `page_number` (INTEGER), `text` (TEXT)
  - Add index on `(document_id, clause_number)`
  - Generate and apply migration
  - Create `app/repositories/clause_repo.py`: `create_clauses_bulk(db, clauses)`, `get_clauses_by_document(db, doc_id) -> List[Clause]`
  - _Requirements: 6_

- [ ] 15. Implement PDF service
  - Create `app/services/pdf_service.py`
  - Implement `extract_text_by_page(file_bytes: bytes) -> List[PageText]` using `pdfplumber`
  - `PageText` is a dataclass/TypedDict: `{page_number: int, text: str}`
  - If all pages return empty text → raise `ExtractionError("No extractable text found — document may be image-only")`
  - Catch all `pdfplumber` exceptions and re-raise as `ExtractionError`
  - _Requirements: 5_

- [ ] 16. Implement clause service
  - Create `app/services/clause_service.py`
  - Implement `extract_clauses(pages: List[PageText], document_id: str) -> List[ClauseData]`
  - Detection strategy (apply in order):
    1. Regex for numbered clauses: `r'^\s*(\d+\.[\d\.]*)\s+[A-Z]'`
    2. ALL-CAPS section headings: `r'^\s*[A-Z][A-Z\s]{3,}\s*$'`
    3. Title-case heading lines (line is ≤ 60 chars, title-cased, followed by body text)
    4. Fallback: entire page text as one clause
  - Each detected clause gets: `clause_number` (sequential), `section` (most recent heading), `page_number`, `text`
  - `ClauseData` is a TypedDict matching Clause model fields
  - _Requirements: 6_

- [ ] 17. Wire processing pipeline as background task
  - Create `app/services/document_service.py` method `process_document(document_id: str, db_session_factory)`:
    1. Update status → PROCESSING
    2. Load file bytes from `uploads/{document_id}.pdf`
    3. Call `pdf_service.extract_text_by_page(bytes)`
    4. Call `clause_service.extract_clauses(pages, document_id)`
    5. Bulk-insert Clause records
    6. Update status → COMPLETED (or FAILED on exception, recording error)
  - In `POST /api/v1/documents` endpoint, after creating the Document record, use FastAPI `BackgroundTasks` to call `process_document`
  - _Requirements: 4, 5, 6, 8_

- [ ] 18. Write PDF and clause extraction tests
  - Test `pdf_service`: valid PDF returns page-indexed text, image-only PDF raises ExtractionError, corrupted bytes raises ExtractionError
  - Test `clause_service`: numbered clauses detected correctly, ALL-CAPS headings detected, fallback to page-level clause when no headings, clause_number is sequential, page_number preserved
  - Use sample PDF fixtures (create minimal test PDFs programmatically with `fpdf2`)
  - _Requirements: 5, 6, 21_

---

## Phase 5: Embeddings and Chroma

- [ ] 19. Implement embedding service
  - Create `app/services/embedding_service.py`
  - Load `sentence-transformers/all-MiniLM-L6-v2` as a module-level singleton on first import
  - Implement `chunk_clause(clause: ClauseData, max_words: int = 400, overlap_words: int = 40) -> List[ChunkData]`
    - Use `langchain.text_splitter.RecursiveCharacterTextSplitter` with `chunk_size=400*5` (chars), `chunk_overlap=40*5`
    - Each `ChunkData` carries all parent clause metadata plus `chunk_index`
  - Implement `embed_text(text: str) -> List[float]` returning the embedding vector
  - _Requirements: 7_

- [ ] 20. Implement vector service
  - Create `app/services/vector_service.py`
  - Connect to Chroma using `chromadb.HttpClient(host=settings.CHROMA_HOST, port=settings.CHROMA_PORT)` (or `EphemeralClient` in tests)
  - Use a single collection named `clauseguard_documents`
  - Implement `store_chunks(chunks: List[ChunkData], embeddings: List[List[float]])` — upserts to Chroma with metadata: `user_id`, `document_id`, `page_number`, `clause_number`, `section`, `text`
  - Implement `query_similar_chunks(query_vector: List[float], user_id: str, document_id: str, top_k: int = 5) -> List[ChunkResult]`
    - Always include `where={"$and": [{"user_id": user_id}, {"document_id": document_id}]}`
    - Returns `ChunkResult` with `text`, `page_number`, `clause_number`, `section`, `distance`
  - Implement `delete_document_chunks(user_id: str, document_id: str)` for future document deletion
  - _Requirements: 7, 24_

- [ ] 21. Integrate embeddings into processing pipeline
  - Update `document_service.process_document` to add after clause extraction:
    5. For each clause, call `embedding_service.chunk_clause(clause)`
    6. For each chunk, call `embedding_service.embed_text(chunk.text)`
    7. Call `vector_service.store_chunks(chunks, embeddings)`
  - If embedding fails for a chunk, log the error, skip the chunk, continue
  - Only update status to COMPLETED after all successful embeddings are stored
  - _Requirements: 7, 8_

- [ ] 22. Write embedding and vector tests
  - Test `embedding_service.chunk_clause`: clause longer than 400 words is split, overlap preserved, metadata carried through, short clause returns single chunk
  - Test `embedding_service.embed_text`: returns list of floats with length 384
  - Test `vector_service`: stored chunks are retrievable, query returns only chunks matching user_id + document_id (not other user's chunks), delete removes all chunks for document
  - Use `chromadb.EphemeralClient()` in tests (no external Chroma needed)
  - _Requirements: 7, 21, 24_

---

## Phase 6: RAG Q&A and Citations

- [ ] 23. Implement LLM service
  - Create `app/services/llm_service.py`
  - Initialize Groq client using `settings.GROQ_API_KEY`
  - Implement `complete(prompt: str, system_prompt: str = None) -> str` — sends chat completion request to `settings.GROQ_MODEL`, returns content string
  - Handle Groq API errors with logging; re-raise as `LLMError`
  - _Requirements: 9, 13_

- [ ] 24. Implement RAG service
  - Create `app/services/rag_service.py`
  - Implement `answer_question(question: str, document_id: str, user_id: str, db) -> AnswerResponse`
    1. Check document exists and belongs to user (raise 404 if not, 409 if not COMPLETED)
    2. `query_vector = embedding_service.embed_text(question)`
    3. `chunks = vector_service.query_similar_chunks(query_vector, user_id, document_id, top_k=5)`
    4. If no chunks → return fallback `AnswerResponse`
    5. Build context string from chunks with page/clause labels
    6. Build system prompt with anti-hallucination instruction
    7. `answer = llm_service.complete(question, system_prompt=system_prompt_with_context)`
    8. Build `citations` from chunk metadata
    9. Return `AnswerResponse(answer=answer, citations=citations)`
  - Fallback message: `"I couldn't find a clear answer to this in your agreement."`
  - `AnswerResponse`: `{answer: str, citations: List[Citation]}`
  - `Citation`: `{page_number: int, clause_number: int, section: str, source_text: str}`
  - _Requirements: 9, 11, 19_

- [ ] 25. Implement Chat Session model, schemas, repository
  - Create `app/models/chat.py`: `ChatSession` (id, user_id, document_id, created_at), `ChatMessage` (id, session_id, role, content, citations_json TEXT, created_at)
  - `citations_json` stores serialized citation list as JSON string
  - Create `app/schemas/chat.py`: `SessionResponse`, `MessageCreate`, `MessageResponse` (includes parsed `citations: List[Citation]`)
  - Create `app/repositories/chat_repo.py`: `create_session()`, `get_session(db, session_id, user_id)`, `create_message()`, `get_messages_by_session()`
  - Generate and apply migration
  - _Requirements: 10_

- [ ] 26. Implement chat API endpoints
  - Create `app/api/chat.py`:
    - `POST /api/v1/chat/sessions` — creates ChatSession for authenticated user + document_id (validates document ownership)
    - `GET /api/v1/chat/sessions/{session_id}/messages` — returns messages for session (validates session ownership)
    - `POST /api/v1/chat/sessions/{session_id}/messages` — receives user message, calls `rag_service.answer_question`, persists both user message and assistant message, returns assistant `MessageResponse`
  - Register router in `main.py`
  - _Requirements: 9, 10, 11_

- [ ] 27. Implement frontend chat panel
  - Create `src/services/chatApi.js` with `createSession(documentId)`, `getMessages(sessionId)`, `sendMessage(sessionId, content)`
  - Create `src/hooks/useChat.js` managing session lifecycle and message state
  - Implement `src/components/document/ChatPanel.jsx`:
    - Creates session on mount (or loads existing)
    - Displays message history (user bubbles right, assistant bubbles left)
    - Input box + send button
    - Renders citations below each assistant message using `CitationBadge`
    - Fallback message styled distinctly
  - Implement `src/components/document/CitationBadge.jsx`: shows "Source: Page X, Clause Y" as a small badge
  - _Requirements: 9, 10, 11_

- [ ] 28. Write RAG and chat tests
  - Test `rag_service`: question returns answer + citations, no relevant chunks returns fallback, wrong user cannot access document chunks
  - Test `chat` endpoints: session creation, message persistence, history retrieval, cross-user isolation
  - Mock `llm_service.complete` and `vector_service.query_similar_chunks` in tests
  - _Requirements: 9, 10, 11, 21, 24_

---

## Phase 7: Automated Attention Analysis

- [ ] 29. Implement risk rules
  - Create `app/rules/risk_rules.py` with:
    - `ATTENTION_CATEGORIES: List[str]` — exactly the 10 allowed categories
    - `CATEGORY_KEYWORDS: Dict[str, List[str]]` — keyword lists for each category
    - `CATEGORY_CRITERIA: Dict[str, str]` — criteria descriptions for each category per the design doc
  - This file is the ONLY source of risk category definitions
  - _Requirements: 12, 13_

- [ ] 30. Implement RiskFlag model, schemas, repository
  - Create `app/models/risk_flag.py`: `id`, `document_id` (FK), `clause_id` (FK nullable), `category`, `attention_level`, `reason`, `tenant_impact`, `evidence`, `confidence`, `created_at`
  - Create `app/schemas/analysis.py`: `RiskFlagResponse`, `MissingItemResponse`, `AnalysisResponse`
  - Create `app/repositories/risk_flag_repo.py`: `create_risk_flag()`, `get_risk_flags_by_document()`
  - Generate and apply migration
  - _Requirements: 12, 13_

- [ ] 31. Implement response validator
  - Create `app/utils/response_validator.py`
  - Implement `validate_llm_classification(raw: str) -> LLMClassification | None`:
    - Parse JSON from raw string (handle markdown code blocks)
    - Validate all required fields present: `category`, `attention_level`, `reason`, `tenant_impact`, `evidence`, `confidence`
    - Validate `category` is in `ATTENTION_CATEGORIES`
    - Validate `attention_level` is in `["HIGH", "MEDIUM", "LOW", "NO_DEFINED_RISK"]`
    - Validate `confidence` is a float between 0.0 and 1.0
    - Return `None` if any validation fails
  - `LLMClassification` is a Pydantic model with the above fields
  - _Requirements: 13, 16_

- [ ] 32. Implement risk service
  - Create `app/services/risk_service.py`
  - Implement `detect_candidates(clauses: List[Clause]) -> Dict[str, List[Clause]]`
    - For each clause, check each category's keywords (case-insensitive substring match)
    - Returns dict mapping category → list of matching clauses
  - Implement `classify_clause(clause: Clause, category: str) -> LLMClassification | None`
    - Builds classification prompt using `CATEGORY_CRITERIA[category]` and clause text
    - Calls `llm_service.complete(prompt)`
    - Calls `response_validator.validate_llm_classification(raw)`
    - Returns validated result or None
  - Implement `analyze_document(document_id: str, db) -> List[RiskFlag]`
    - Loads all clauses for document
    - Calls `detect_candidates(clauses)`
    - For each category with candidates: calls `classify_clause` for best-matching clause, creates RiskFlag
    - For each category with NO candidates: creates RiskFlag with `attention_level=NO_DEFINED_RISK`, `clause_id=None`
    - Returns all created RiskFlag records
  - _Requirements: 12, 13_

- [ ] 33. Integrate risk analysis into processing pipeline
  - After document status is set to COMPLETED in `process_document`, call `risk_service.analyze_document(document_id, db)`
  - If risk analysis fails, log error but do NOT set document status to FAILED (core processing already succeeded)
  - _Requirements: 12_

- [ ] 34. Implement analysis API endpoint
  - Create `app/api/analysis.py`:
    - `GET /api/v1/documents/{document_id}/analysis` — validates ownership, checks COMPLETED status (return 409 if not), returns `AnalysisResponse` with `risk_flags` and `missing_items`
  - Register router in `main.py`
  - _Requirements: 12, 13, 15_

- [ ] 35. Write risk service tests
  - Test `detect_candidates`: keyword matching works case-insensitively, returns correct categories for sample clauses, no false positives for unrelated text
  - Test `response_validator`: valid JSON passes, invalid attention_level rejected, missing fields rejected, invalid category rejected, confidence out of range rejected
  - Test `risk_service.analyze_document`: produces one RiskFlag per category, NO_DEFINED_RISK for categories with no matching clauses, invalid LLM response creates ANALYSIS_REQUIRES_REVIEW flag (not NO_DEFINED_RISK)
  - Mock `llm_service.complete` in all tests
  - _Requirements: 12, 13, 21_

---

## Phase 8: Missing / Unclear Information Detection

- [ ] 36. Implement missing items detection
  - Create `app/services/analysis_service.py`
  - Define `MISSING_ITEMS: List[str]` — the 17 items from requirements
  - Define `ITEM_KEYWORDS: Dict[str, List[str]]` — keyword lists per item
  - Define `ITEM_DESCRIPTIONS: Dict[str, str]` — human-readable descriptions for prompts
  - Implement `detect_missing_items(clauses: List[Clause], db) -> List[MissingItemResult]`
    - For each item:
      1. Find clauses containing any item keyword
      2. If no clauses found → record as `absent`
      3. If clauses found → call LLM with focused prompt: "Does this text clearly specify {description}? Reply with exactly: PRESENT, UNCLEAR, or ABSENT. Then explain briefly."
      4. Parse response: PRESENT → skip, UNCLEAR → record as `unclear`, ABSENT → record as `absent`
      5. If LLM response parse fails → record as `unclear` (safe fallback)
    - Returns `List[MissingItemResult(item, status)]` where status is `absent` or `unclear`
    - Items with status PRESENT are excluded from the list
  - `MissingItemResult`: `{item: str, status: str, description: str}`
  - _Requirements: 14_

- [ ] 37. Integrate missing items detection into processing pipeline
  - After `risk_service.analyze_document` completes, call `analysis_service.detect_missing_items(clauses, db)`
  - Store results — decide: either persist to a `MissingItem` DB table OR compute on-demand
  - Decision: compute on-demand and cache on first call (store results in a new `missing_item` table for performance)
  - Create `MissingItem` model: `id`, `document_id`, `item_key`, `status` (absent/unclear), `created_at`
  - Generate and apply migration
  - _Requirements: 14_

- [ ] 38. Expose missing items in analysis endpoint
  - Update `GET /api/v1/documents/{document_id}/analysis` to include `missing_items: List[MissingItemResponse]` in the response
  - `MissingItemResponse`: `{item: str, status: str, label: str}` where `label` is a human-readable name
  - _Requirements: 14, 15_

- [ ] 39. Write missing items tests
  - Test: item present and clear → not in result list, item absent → `absent` in result, item present but vague → `unclear` in result
  - Test: all 17 items have keyword entries (completeness check)
  - Mock `llm_service.complete` in tests
  - _Requirements: 14, 21_

---

## Phase 9: Dashboard Integration

- [ ] 40. Implement DocumentPage frontend
  - Implement `src/components/layout/Disclaimer.jsx` — renders the exact legal disclaimer text
  - Implement `src/hooks/useDocuments.js` with `useDocument(id)` that polls `GET /documents/{id}` every 3 seconds while status is PENDING or PROCESSING
  - Implement `DocumentPage.jsx` with:
    - While PENDING/PROCESSING: show `ProcessingIndicator` with status label, poll for updates
    - On FAILED: show error message
    - On COMPLETED: show full analysis dashboard
  - Implement `src/components/document/ProcessingIndicator.jsx` — spinner with status text
  - _Requirements: 8, 15, 18_

- [ ] 41. Implement analysis dashboard components
  - Implement `src/components/document/AttentionFlags.jsx` — groups RiskFlags by attention level, renders each as `AttentionFlagCard`
  - Implement `src/components/document/AttentionFlagCard.jsx` — shows category, attention level badge (color-coded: HIGH=red, MEDIUM=amber, LOW=blue, NO_DEFINED_RISK=gray), reason, tenant_impact
  - Implement `src/components/document/MissingItems.jsx` — lists missing/unclear items, labels each as "Not found" or "Unclear"
  - Implement `src/utils/attentionLevelColor.js` — maps attention level to Tailwind color classes
  - _Requirements: 15_

- [ ] 42. Implement Navbar and layout
  - Implement `src/components/layout/Navbar.jsx` — shows app name/logo, links, logout button
  - Implement `src/components/layout/Footer.jsx` — shows disclaimer text
  - Wrap all pages in consistent layout with Navbar and Footer
  - Ensure disclaimer appears on every page showing analysis results and on login/register pages
  - _Requirements: 16_

- [ ] 43. Complete DashboardPage integration
  - Finalize `DashboardPage.jsx` to use real API data
  - Processing status badge colors: PENDING=gray, PROCESSING=blue (animated), COMPLETED=green, FAILED=red
  - Each document card links to `/documents/:id`
  - _Requirements: 15, 17_

---

## Phase 10: Testing, Docker, CI/CD, and Deployment

- [ ] 44. Complete backend test suite
  - Ensure all test files exist and pass: `test_auth.py`, `test_documents.py`, `test_pdf_service.py`, `test_clause_service.py`, `test_embedding_service.py`, `test_rag_service.py`, `test_risk_service.py`, `test_analysis_service.py`
  - Add cross-user isolation tests: user A cannot read user B's documents, clauses, flags, chat sessions, or Chroma chunks
  - Add end-to-end processing pipeline integration test (using in-memory SQLite, mock LLM, EphemeralClient Chroma)
  - Run `pytest --cov=app --cov-report=term-missing --cov-fail-under=80` and fix until passing
  - _Requirements: 21, 24_

- [ ] 45. Create Docker configuration
  - Create `backend/Dockerfile`: `FROM python:3.11-slim`, copy requirements.txt, pip install, copy app, CMD uvicorn
  - Create `frontend/Dockerfile` (multi-stage): stage 1 `node:18-slim` builds with `npm run build`, stage 2 `nginx:alpine` serves from `/usr/share/nginx/html`
  - Create `frontend/nginx.conf` for SPA routing (all paths → `index.html`)
  - Create `docker-compose.yml` with services: `db` (postgres:15), `chroma` (chromadb/chroma), `backend`, `frontend`
  - Add `backend/docker-compose.override.yml` command to run `alembic upgrade head && uvicorn ...`
  - Create `docker-compose.yml` healthchecks for db and chroma
  - Create root `.env.example` combining all env vars needed
  - Verify: `docker-compose up` starts all services, `GET /health` returns 200
  - _Requirements: 20_

- [ ] 46. Create GitHub Actions CI/CD pipeline
  - Create `.github/workflows/ci.yml`
  - Jobs:
    - `lint`: checkout, setup python 3.11, `pip install ruff`, `ruff check backend/app`
    - `test`: checkout, setup python 3.11, `pip install -r backend/requirements.txt`, start postgres service container, run `pytest --cov=app --cov-fail-under=80`, upload coverage artifact
    - `build-frontend`: checkout, setup node 18, `npm ci` in frontend/, `npm run build`
  - All jobs run on push and pull_request to any branch
  - Secrets: `TEST_DATABASE_URL`, `GROQ_API_KEY` (mocked in tests), `JWT_SECRET_KEY`
  - Verify the workflow runs and passes (fix any CI-specific issues)
  - _Requirements: 22_

- [ ] 47. Deployment configuration
  - Create `backend/render.yaml` (or `railway.toml`) with service config: build command `pip install -r requirements.txt`, start command `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
  - Create `frontend/vercel.json` with rewrite rule `{ "source": "/(.*)", "destination": "/" }` for SPA routing
  - Update `Settings` to handle `DATABASE_URL` with `postgresql+psycopg2://` scheme correction (Render provides `postgres://`)
  - Create `DEPLOYMENT.md` documenting required env vars for Render/Railway and Vercel
  - Verify all secrets are env-var-driven with no hardcoded values
  - _Requirements: 23_
