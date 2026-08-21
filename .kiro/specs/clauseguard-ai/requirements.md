# Requirements Document

## Introduction

ClauseGuard is an AI-powered rental agreement analysis platform that helps renters understand dense contractual language before signing. Users upload a rental/lease agreement PDF, and the platform extracts its contents, enables natural language Q&A grounded strictly in the uploaded document, automatically flags predefined clause categories that deserve attention, and identifies information that is missing or unclear. All analysis is document-scoped and non-legal in nature — ClauseGuard does not give legal advice, invent legal rules, or classify clauses as unlawful.

The MVP delivers: user authentication, PDF upload and processing, clause extraction, vector-based RAG Q&A with citations, predefined attention analysis across 10 categories, missing/unclear information detection, and a dashboard — running in Docker with pytest-based testing and GitHub Actions CI/CD.

---

## Glossary

- **System**: The ClauseGuard full-stack application (FastAPI backend + React frontend).
- **User**: An authenticated renter using the platform.
- **Document**: A rental agreement PDF uploaded by a User.
- **Clause**: A discrete section or provision extracted from a Document.
- **Chunk**: A text segment derived from a Clause or page boundary, used for embedding and retrieval.
- **Embedding**: A dense vector representation of a Chunk produced by the Embedding_Service.
- **Vector_Store**: The Chroma vector database that stores and retrieves Embeddings scoped per user and document.
- **RAG_Pipeline**: Retrieval-Augmented Generation pipeline that combines Vector_Store retrieval with LLM generation.
- **LLM**: The Groq-hosted Llama language model used for text generation and classification tasks.
- **LLM_Response**: Structured JSON output returned by the LLM for analysis tasks.
- **Attention_Category**: One of the 10 predefined categories used to flag clauses deserving attention.
- **Attention_Level**: One of four values — HIGH, MEDIUM, LOW, NO_DEFINED_RISK — assigned to a flagged clause.
- **Risk_Flag**: A record linking a Document and optionally a Clause to an Attention_Category and Attention_Level with supporting evidence.
- **Missing_Item**: A predefined information item expected in a rental agreement that is absent or unclear in a given Document.
- **Chat_Session**: A conversation context scoped to a single User and Document.
- **Chat_Message**: A single turn (user or assistant) within a Chat_Session.
- **Processing_Status**: The current state of Document processing: PENDING, PROCESSING, COMPLETED, FAILED.
- **Citation**: A reference in the format "Source: Page X, Clause Y" linking an answer to its document location.
- **Auth_Service**: The backend service responsible for user registration, login, and JWT management.
- **Document_Service**: The backend service orchestrating Document upload, storage metadata, and processing lifecycle.
- **PDF_Service**: The backend service responsible for extracting text from uploaded PDFs with page-awareness.
- **Clause_Service**: The backend service responsible for detecting and extracting Clause boundaries from extracted text.
- **Embedding_Service**: The backend service responsible for generating Embeddings from Chunks.
- **Vector_Service**: The backend service responsible for storing and querying Embeddings in the Vector_Store.
- **RAG_Service**: The backend service orchestrating retrieval and grounded answer generation.
- **LLM_Service**: The backend service responsible for issuing prompts to the LLM and parsing responses.
- **Risk_Service**: The backend service responsible for deterministic and LLM-based Attention_Category detection.
- **Analysis_Service**: The backend service orchestrating the full document analysis pipeline.
- **JWT**: JSON Web Token used for stateless authentication.
- **CI_CD_Pipeline**: The GitHub Actions workflow that runs tests and validates the build on each push.

---

## Requirements

---

### Requirement 1: User Registration

**User Story:** As a new visitor, I want to create an account with my email and password, so that I can securely access my uploaded agreements.

#### Acceptance Criteria

1. WHEN a registration request is received with a valid email and password, THE Auth_Service SHALL create a User record with a bcrypt-hashed password and return a JWT.
2. WHEN a registration request is received with an email that already exists, THE Auth_Service SHALL return an error response with HTTP status 409 and a message indicating the email is already in use.
3. WHEN a registration request is received with an invalid email format, THE Auth_Service SHALL return an error response with HTTP status 422.
4. WHEN a registration request is received with a password shorter than 8 characters, THE Auth_Service SHALL return an error response with HTTP status 422.
5. THE Auth_Service SHALL store only the bcrypt hash of the password and SHALL NOT store the plaintext password.

---

### Requirement 2: User Login

**User Story:** As a registered user, I want to log in with my email and password, so that I can access my documents and analysis.

#### Acceptance Criteria

1. WHEN a login request is received with a valid email and correct password, THE Auth_Service SHALL return a signed JWT with a configurable expiry.
2. WHEN a login request is received with an email that does not exist, THE Auth_Service SHALL return an error response with HTTP status 401.
3. WHEN a login request is received with an incorrect password, THE Auth_Service SHALL return an error response with HTTP status 401.
4. THE Auth_Service SHALL NOT distinguish between "email not found" and "wrong password" in the error message, returning a generic credential error for both cases.

---

### Requirement 3: Authenticated Session Management

**User Story:** As a logged-in user, I want my session to be maintained securely, so that I do not need to re-authenticate on every action.

#### Acceptance Criteria

1. THE System SHALL require a valid JWT in the Authorization header for all protected API endpoints.
2. WHEN a request is received on a protected endpoint with a missing or malformed JWT, THE System SHALL return HTTP status 401.
3. WHEN a request is received on a protected endpoint with an expired JWT, THE System SHALL return HTTP status 401.
4. WHEN a request is received on a protected endpoint with a valid JWT, THE System SHALL extract the user identity from the token and scope all operations to that User.

---

### Requirement 4: PDF Upload

**User Story:** As a user, I want to upload a rental agreement PDF, so that the platform can analyze its contents.

#### Acceptance Criteria

1. WHEN an authenticated user submits a PDF file to the upload endpoint, THE Document_Service SHALL create a Document record with Processing_Status PENDING and return the document ID.
2. WHEN a file is submitted that is not a PDF, THE Document_Service SHALL return an error response with HTTP status 422 indicating an unsupported file type.
3. WHEN a PDF file exceeding 20 MB is submitted, THE Document_Service SHALL return an error response with HTTP status 413.
4. THE Document_Service SHALL associate the uploaded Document with the authenticated User and SHALL NOT allow other users to access it.
5. WHEN a Document record is created, THE Document_Service SHALL enqueue the Document for asynchronous processing and update Processing_Status to PROCESSING.

---

### Requirement 5: PDF Text Extraction

**User Story:** As a user, I want my uploaded PDF to be parsed accurately, so that analysis is based on the actual document content.

#### Acceptance Criteria

1. WHEN a Document with Processing_Status PROCESSING is received, THE PDF_Service SHALL extract all text content from the PDF preserving page boundaries.
2. WHEN text extraction produces at least one non-empty page, THE PDF_Service SHALL return a page-indexed text structure where each page is identified by its 1-based page number.
3. WHEN a PDF contains no extractable text (e.g., a scanned image-only PDF), THE PDF_Service SHALL mark the Document Processing_Status as FAILED and record the reason.
4. IF text extraction raises an unhandled exception, THEN THE PDF_Service SHALL mark the Document Processing_Status as FAILED and record the error details.

---

### Requirement 6: Clause and Section Extraction

**User Story:** As a user, I want the system to identify individual clauses and sections in my agreement, so that analysis and citations are precise.

#### Acceptance Criteria

1. WHEN page-indexed text is available for a Document, THE Clause_Service SHALL detect clause and section boundaries using heading patterns, numbered lists, and paragraph structure.
2. WHEN a Clause is detected, THE Clause_Service SHALL create a Clause record containing: document_id, clause_number, section name, page_number, and the extracted text.
3. WHEN no clause boundaries are detected in the text, THE Clause_Service SHALL treat each page as a single Clause to preserve coverage.
4. THE Clause_Service SHALL preserve the original text of each Clause without modification or summarization.

---

### Requirement 7: Chunking and Embedding

**User Story:** As a user, I want my agreement indexed for search, so that questions can retrieve relevant passages accurately.

#### Acceptance Criteria

1. WHEN Clause records are available for a Document, THE Embedding_Service SHALL split each Clause into Chunks that do not exceed 512 tokens, with a 50-token overlap between consecutive Chunks.
2. WHEN a Chunk is created, THE Embedding_Service SHALL generate a vector Embedding for the Chunk using the configured sentence-transformer model.
3. WHEN an Embedding is generated for a Chunk, THE Vector_Service SHALL store the Embedding in the Vector_Store with metadata: user_id, document_id, page_number, clause_number, section, and the Chunk text.
4. THE Vector_Service SHALL scope all Vector_Store collections by user_id and document_id to prevent cross-user data access.
5. IF embedding generation fails for a Chunk, THEN THE Embedding_Service SHALL log the failure, skip that Chunk, and continue processing remaining Chunks.

---

### Requirement 8: Processing Pipeline Completion

**User Story:** As a user, I want to know when my document is ready, so that I can start using the analysis features.

#### Acceptance Criteria

1. WHEN all Clauses have been embedded and stored, THE Document_Service SHALL update Processing_Status to COMPLETED.
2. WHEN any unrecoverable error occurs during the processing pipeline, THE Document_Service SHALL update Processing_Status to FAILED with a reason recorded.
3. WHEN an authenticated user requests the status of a Document, THE Document_Service SHALL return the current Processing_Status.
4. THE Document_Service SHALL NOT expose Documents belonging to other Users.

---

### Requirement 9: RAG Question Answering

**User Story:** As a user, I want to ask questions about my rental agreement in natural language, so that I can understand specific terms without reading every page.

#### Acceptance Criteria

1. WHEN an authenticated user submits a question for a Document with Processing_Status COMPLETED, THE RAG_Service SHALL embed the question and retrieve the top-5 most semantically similar Chunks from the Vector_Store scoped to that document.
2. WHEN relevant Chunks are retrieved, THE RAG_Service SHALL construct a prompt containing only the retrieved Chunks and submit it to the LLM_Service to generate a grounded answer.
3. WHEN the LLM generates an answer, THE RAG_Service SHALL return the answer together with Citations referencing the page and clause of each supporting Chunk.
4. WHEN the retrieved Chunks do not contain information sufficient to answer the question, THE RAG_Service SHALL return the response: "I couldn't find a clear answer to this in your agreement." and SHALL NOT generate a speculative answer.
5. THE RAG_Service SHALL NOT include information outside the retrieved Chunks in the generated answer.
6. WHEN a question is submitted for a Document with Processing_Status other than COMPLETED, THE RAG_Service SHALL return an error response with HTTP status 409 indicating the document is not ready.

---

### Requirement 10: Chat Session Management

**User Story:** As a user, I want my conversation about a document to be preserved, so that I can review past questions and answers.

#### Acceptance Criteria

1. WHEN an authenticated user initiates a conversation for a Document, THE System SHALL create a Chat_Session record linked to the User and Document.
2. WHEN a Chat_Message is sent or received, THE System SHALL persist it as a Chat_Message record with role (user or assistant), content, and timestamp.
3. WHEN an authenticated user requests the message history for a Chat_Session, THE System SHALL return all Chat_Messages for that session in chronological order.
4. THE System SHALL NOT return Chat_Sessions or Chat_Messages belonging to other Users.

---

### Requirement 11: Citation Format

**User Story:** As a user, I want every answer to cite the specific page and clause it came from, so that I can verify the information in my original document.

#### Acceptance Criteria

1. WHEN the RAG_Service returns an answer, THE System SHALL include at least one Citation for each answer that is grounded in retrieved content.
2. THE System SHALL format each Citation as "Source: Page X, Clause Y" where X is the 1-based page number and Y is the clause identifier extracted from Chunk metadata.
3. WHEN multiple Chunks from different pages or clauses support an answer, THE System SHALL include a Citation for each distinct source.

---

### Requirement 12: Automated Attention Analysis — Deterministic Detection

**User Story:** As a user, I want the system to automatically find clauses in specific categories that deserve my attention, so that I don't miss important provisions.

#### Acceptance Criteria

1. WHEN a Document reaches Processing_Status COMPLETED, THE Risk_Service SHALL scan all Clause records for the Document using keyword patterns, regex, and section heading matching to identify candidate Clauses for each of the 10 Attention_Categories.
2. THE Risk_Service SHALL evaluate the following Attention_Categories: SECURITY_DEPOSIT, LOCK_IN, NOTICE_PERIOD, MAINTENANCE, TERMINATION, PENALTIES, RENT_ESCALATION, SUBLETTING, RENEWAL, DISPUTE_RESOLUTION.
3. THE Risk_Service SHALL NOT create a Risk_Flag based on keyword presence alone — a candidate Clause must be passed to the LLM for classification before a Risk_Flag is created.
4. WHEN no candidate Clauses are found for an Attention_Category, THE Risk_Service SHALL record that category with Attention_Level NO_DEFINED_RISK for the Document.

---

### Requirement 13: Automated Attention Analysis — LLM Classification

**User Story:** As a user, I want the attention flags to reflect the actual content of the clause, not just keyword matches, so that the analysis is meaningful.

#### Acceptance Criteria

1. WHEN a candidate Clause is identified by deterministic detection, THE LLM_Service SHALL classify it using a structured prompt that outputs a JSON object with fields: category, attention_level, reason, tenant_impact, evidence, confidence.
2. THE LLM_Service SHALL instruct the LLM to assign attention_level from only these values: HIGH, MEDIUM, LOW, NO_DEFINED_RISK.
3. WHEN the LLM returns a valid structured JSON response, THE Risk_Service SHALL create a Risk_Flag record from the response fields.
4. WHEN the LLM returns a response that fails JSON validation or contains unexpected field values, THE Risk_Service SHALL mark the result as ANALYSIS_REQUIRES_REVIEW and SHALL NOT create a Risk_Flag from the invalid data.
5. THE LLM_Service SHALL NOT instruct the LLM to assess legality, enforceability, or compliance with any law or jurisdiction.
6. THE LLM_Service SHALL instruct the LLM to base its classification strictly on the content of the provided Clause text.

---

### Requirement 14: Missing and Unclear Information Detection

**User Story:** As a user, I want to know if important information is missing from my agreement, so that I can ask for clarification before signing.

#### Acceptance Criteria

1. WHEN a Document reaches Processing_Status COMPLETED, THE Analysis_Service SHALL check for the presence and clarity of each of the following items in the Document's Clauses: rent amount, security deposit, deposit refund conditions, deposit deduction conditions, notice period, lock-in period, termination conditions, maintenance responsibility, repair responsibility, utilities, rent escalation, renewal conditions, subletting restrictions, dispute resolution procedure, property details, parties to the agreement, agreement duration.
2. WHEN an expected item is not found in any Clause of the Document, THE Analysis_Service SHALL record that item as absent.
3. WHEN an expected item is present but expressed in vague or undefined terms, THE Analysis_Service SHALL record that item as unclear.
4. THE Analysis_Service SHALL return the list of absent and unclear items as part of the Document analysis result.
5. THE Analysis_Service SHALL NOT invent or infer values for missing items — it SHALL only report their absence or ambiguity.

---

### Requirement 15: Document Analysis Dashboard

**User Story:** As a user, I want a single page that shows me all analysis results for my agreement, so that I can quickly understand its key terms and risks.

#### Acceptance Criteria

1. WHEN an authenticated user navigates to the document detail page for a COMPLETED Document, THE System SHALL display: a document summary, the list of Risk_Flags with their Attention_Level and reason, the list of Missing_Items, and the Chat interface.
2. WHEN Risk_Flags are displayed, THE System SHALL visually distinguish Attention_Levels: HIGH, MEDIUM, LOW, and NO_DEFINED_RISK.
3. WHEN Missing_Items are displayed, THE System SHALL indicate whether each item is absent or unclear.
4. WHEN a Document has Processing_Status PENDING or PROCESSING, THE System SHALL display a processing indicator and SHALL NOT show analysis results.
5. WHEN a Document has Processing_Status FAILED, THE System SHALL display an error message informing the User that processing was unsuccessful.

---

### Requirement 16: Legal Disclaimer

**User Story:** As a user, I want to be clearly informed that ClauseGuard is not legal advice, so that I understand the scope of what I am receiving.

#### Acceptance Criteria

1. THE System SHALL display the following disclaimer on every page that presents analysis results: "ClauseGuard provides document analysis and general informational insights. It is not a substitute for professional legal advice. Attention indicators are based on predefined document-analysis rules and should not be interpreted as legal conclusions."
2. THE System SHALL display the disclaimer on the registration and login pages.
3. THE System SHALL NOT use language such as "illegal", "unlawful", "unenforceable", or "legally invalid" in any generated output.

---

### Requirement 17: User Document List

**User Story:** As a user, I want to see all my uploaded agreements in one place, so that I can navigate to any document quickly.

#### Acceptance Criteria

1. WHEN an authenticated user navigates to the dashboard, THE System SHALL display a list of all Documents belonging to that User, showing the document title, original filename, Processing_Status, and upload date.
2. WHEN a User has no uploaded Documents, THE System SHALL display an empty-state message and a prompt to upload their first agreement.
3. THE System SHALL NOT display Documents belonging to other Users.

---

### Requirement 18: Frontend Routing

**User Story:** As a user, I want clear navigation between sections of the application, so that I can move between features without confusion.

#### Acceptance Criteria

1. THE System SHALL provide the following client-side routes: / (landing/home), /login (login form), /register (registration form), /dashboard (document list), /documents/new (upload page), /documents/:id (document analysis page).
2. WHEN an unauthenticated user attempts to access /dashboard, /documents/new, or /documents/:id, THE System SHALL redirect the user to /login.
3. WHEN an authenticated user navigates to / or /login, THE System SHALL redirect the user to /dashboard.

---

### Requirement 19: Non-Hallucination Guarantee

**User Story:** As a user, I want all answers to be based only on my agreement, so that I am not misled by invented information.

#### Acceptance Criteria

1. THE RAG_Service SHALL construct every LLM prompt to include an explicit instruction that the LLM must answer only from the provided document excerpts and must not use external knowledge.
2. WHEN the LLM_Service receives a response that contains content not traceable to the retrieved Chunks, THE RAG_Service SHALL discard the response and return the fallback message: "I couldn't find a clear answer to this in your agreement."
3. THE System SHALL NOT present any analysis result derived from external knowledge, inferred legal rules, or fabricated content.

---

### Requirement 20: Containerization

**User Story:** As a developer, I want the application to run in Docker containers, so that the environment is reproducible and deployment is consistent.

#### Acceptance Criteria

1. THE System SHALL provide a Dockerfile for the backend that installs all Python dependencies and starts the FastAPI application.
2. THE System SHALL provide a Dockerfile for the frontend that builds the React application and serves it.
3. THE System SHALL provide a docker-compose.yml that starts the backend, frontend, PostgreSQL, and Chroma services together with a single command.
4. WHEN the docker-compose stack is started, THE System SHALL apply database migrations automatically before the backend accepts requests.
5. THE System SHALL provide environment variable configuration for all secrets and deployment-specific values, with no hardcoded credentials in any Dockerfile or source file.

---

### Requirement 21: Automated Testing

**User Story:** As a developer, I want a pytest test suite, so that regressions are caught before deployment.

#### Acceptance Criteria

1. THE System SHALL include pytest tests covering: Auth_Service registration and login logic, Document_Service upload validation, PDF_Service text extraction, Clause_Service boundary detection, Embedding_Service chunk sizing, RAG_Service grounded response and fallback behavior, Risk_Service deterministic detection and LLM classification validation, Analysis_Service missing item detection.
2. WHEN the test suite is executed, THE System SHALL achieve a minimum of 80% line coverage as measured by pytest-cov.
3. THE System SHALL provide mock implementations for LLM_Service and Vector_Service calls within the test suite so that tests do not require live Groq API or Chroma instances.
4. FOR ALL valid serialization and deserialization of LLM_Response JSON objects, parsing then re-serializing SHALL produce an equivalent object (round-trip property).

---

### Requirement 22: CI/CD Pipeline

**User Story:** As a developer, I want GitHub Actions to run tests on every push, so that broken code is caught before it can be merged.

#### Acceptance Criteria

1. WHEN a commit is pushed to any branch, THE CI_CD_Pipeline SHALL install dependencies, run the pytest suite, and report pass or fail status.
2. WHEN any test in the pytest suite fails, THE CI_CD_Pipeline SHALL mark the workflow run as failed and SHALL NOT proceed to deployment steps.
3. THE CI_CD_Pipeline SHALL use environment variable secrets for any API keys or credentials required during testing, and SHALL NOT hardcode credentials in workflow files.

---

### Requirement 23: Deployment-Ready Configuration

**User Story:** As a developer, I want the application to be configurable for production deployment, so that it can be hosted on Vercel and Render/Railway without code changes.

#### Acceptance Criteria

1. THE System SHALL read all configuration values (database URL, JWT secret, Groq API key, Chroma host, CORS origins) from environment variables at startup.
2. WHEN a required environment variable is missing at startup, THE System SHALL raise a configuration error and refuse to start.
3. THE System SHALL configure CORS to allow only origins specified in the CORS_ORIGINS environment variable.
4. THE System SHALL provide a sample .env.example file listing all required environment variables with placeholder values and no real secrets.

---

### Requirement 24: Data Isolation and Security

**User Story:** As a user, I want my documents and conversations to be private, so that other users cannot access my data.

#### Acceptance Criteria

1. THE System SHALL scope all database queries for Documents, Clauses, Risk_Flags, Chat_Sessions, and Chat_Messages to the authenticated User's ID.
2. WHEN an authenticated user requests a resource that belongs to a different User, THE System SHALL return HTTP status 404 rather than 403, to avoid confirming the existence of the resource.
3. THE Vector_Service SHALL include user_id as a mandatory filter on all Vector_Store queries.
4. THE System SHALL validate that the document_id in any chat or analysis request belongs to the authenticated User before processing the request.
