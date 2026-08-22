"""
Phase 6 tests — RAG pipeline, chat API, citations, and security.

All tests use:
  - mock_embed: fast deterministic embeddings (no real model)
  - mock_llm: patches chat_complete to return deterministic responses
  - tmp_uploads: isolated per-test PDF storage
  - shared_chroma_client: in-memory Chroma (from conftest)

No real Groq API key is required.
"""
import io
import json
import uuid
import pytest
from unittest.mock import patch, MagicMock
from fpdf import FPDF


# ── PDF / test helpers ────────────────────────────────────────────────────────

def make_text_pdf(pages: list) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=False)
    for page_text in pages:
        pdf.add_page()
        pdf.set_font("Helvetica", size=11)
        for line in page_text.splitlines():
            pdf.cell(0, 6, line, ln=True)
    return bytes(pdf.output())


def register_and_login(client, email, password="password123"):
    r = client.post("/api/v1/auth/register", json={"email": email, "password": password})
    assert r.status_code == 201, r.text
    return r.json()["access_token"]


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def upload_pdf(client, token, content: bytes, title="Test Agreement"):
    return client.post(
        "/api/v1/documents",
        files={"file": ("agreement.pdf", io.BytesIO(content), "application/pdf")},
        data={"title": title},
        headers=auth_headers(token),
    )


def upload_and_process(client, token, content: bytes, title="Test"):
    up = upload_pdf(client, token, content, title=title)
    assert up.status_code == 201, up.text
    doc_id = up.json()["id"]
    proc = client.post(
        f"/api/v1/documents/{doc_id}/process", headers=auth_headers(token)
    )
    assert proc.status_code == 200, proc.text
    return doc_id


# Agreement content used across tests — deterministic clauses
AGREEMENT_PAGES = [
    (
        "1. Security Deposit\n"
        "The tenant shall pay a security deposit of two months rent before occupancy.\n\n"
        "2. Notice Period\n"
        "Either party shall provide sixty days written notice before termination.\n\n"
        "3. Lock-in Period\n"
        "The tenant agrees to occupy the premises for a minimum of twelve months.\n\n"
        "4. Maintenance\n"
        "The tenant is responsible for minor repairs not exceeding five hundred rupees."
    )
]


# ── mock_llm fixture ──────────────────────────────────────────────────────────

@pytest.fixture
def mock_llm(monkeypatch):
    """Patch chat_complete to return a deterministic answer without calling Groq."""
    import app.services.llm_service as llm_svc
    mock = MagicMock(return_value="According to the agreement, the notice period is sixty days.")
    monkeypatch.setattr(llm_svc, "chat_complete", mock)
    return mock


@pytest.fixture
def mock_llm_empty(monkeypatch):
    """Patch chat_complete to return an empty string (simulate empty response)."""
    import app.services.llm_service as llm_svc
    monkeypatch.setattr(llm_svc, "chat_complete", MagicMock(return_value=""))


@pytest.fixture
def mock_llm_fail(monkeypatch):
    """Patch chat_complete to raise LLMError (simulate Groq failure)."""
    import app.services.llm_service as llm_svc
    from app.services.llm_service import LLMError
    monkeypatch.setattr(llm_svc, "chat_complete", MagicMock(side_effect=LLMError("API down")))


# ── RAG unit tests ────────────────────────────────────────────────────────────

def test_rag_system_prompt_present(mock_embed, mock_llm):
    """LLM must receive a system prompt."""
    from app.services import rag_service
    fake_hit = {
        "clause_id": str(uuid.uuid4()),
        "clause_number": 1,
        "page_number": 1,
        "heading": "Notice Period",
        "distance": 0.2,
    }
    with patch("app.services.rag_service.semantic_search", return_value=[fake_hit]):
        with patch("app.services.rag_service.get_clauses_by_document") as mock_clauses:
            c = MagicMock()
            c.id = fake_hit["clause_id"]
            c.clause_number = 1
            c.page_number = 1
            c.heading = "Notice Period"
            c.content = "Either party shall provide sixty days notice."
            mock_clauses.return_value = [c]
            rag_service.answer_question("What is the notice period?", "doc-id", db=None)

    args = mock_llm.call_args
    messages = args[0][0]
    assert messages[0]["role"] == "system"
    assert "ClauseGuard" in messages[0]["content"]
    assert "NOT a lawyer" in messages[0]["content"]


def test_rag_context_contains_clause_text(mock_embed, mock_llm):
    """LLM prompt must include the actual clause content."""
    from app.services import rag_service

    fake_hit = {
        "clause_id": "clause-abc",
        "clause_number": 2,
        "page_number": 1,
        "heading": "Notice Period",
        "distance": 0.15,
    }
    with patch("app.services.rag_service.semantic_search", return_value=[fake_hit]):
        with patch("app.services.rag_service.get_clauses_by_document") as mock_clauses:
            c = MagicMock()
            c.id = "clause-abc"
            c.clause_number = 2
            c.page_number = 1
            c.heading = "Notice Period"
            c.content = "UNIQUE_CONTENT_STRING_XYZ"
            mock_clauses.return_value = [c]
            rag_service.answer_question("notice period?", "doc-id", db=None)

    args = mock_llm.call_args
    messages = args[0][0]
    full_text = " ".join(m["content"] for m in messages)
    assert "UNIQUE_CONTENT_STRING_XYZ" in full_text


def test_rag_no_relevant_clauses_returns_fallback(mock_embed, monkeypatch):
    """When no relevant clauses found, return fallback without calling LLM."""
    from app.services import rag_service
    import app.services.llm_service as llm_svc

    llm_mock = MagicMock()
    monkeypatch.setattr(llm_svc, "chat_complete", llm_mock)

    with patch("app.services.rag_service.semantic_search", return_value=[]):
        result = rag_service.answer_question("irrelevant question", "doc-id", db=None)

    assert result.answer == rag_service.FALLBACK_ANSWER
    assert result.citations == []
    llm_mock.assert_not_called()


def test_rag_threshold_filters_irrelevant_hits(mock_embed, monkeypatch):
    """Hits above RELEVANCE_THRESHOLD must be filtered out."""
    from app.services import rag_service
    import app.services.llm_service as llm_svc

    llm_mock = MagicMock()
    monkeypatch.setattr(llm_svc, "chat_complete", llm_mock)

    # Hit with distance > threshold
    bad_hit = {
        "clause_id": "c1",
        "clause_number": 1,
        "page_number": 1,
        "heading": None,
        "distance": 1.5,  # above RELEVANCE_THRESHOLD (0.85)
    }
    with patch("app.services.rag_service.semantic_search", return_value=[bad_hit]):
        result = rag_service.answer_question("something", "doc-id", db=None)

    assert result.answer == rag_service.FALLBACK_ANSWER
    llm_mock.assert_not_called()


def test_rag_citations_come_from_database_not_llm(mock_embed, mock_llm):
    """Citations must be generated from database records, not from LLM output."""
    from app.services import rag_service

    clause_id = str(uuid.uuid4())
    fake_hit = {
        "clause_id": clause_id,
        "clause_number": 3,
        "page_number": 2,
        "heading": "Lock-in Period",
        "distance": 0.1,
    }
    with patch("app.services.rag_service.semantic_search", return_value=[fake_hit]):
        with patch("app.services.rag_service.get_clauses_by_document") as mc:
            c = MagicMock()
            c.id = clause_id
            c.clause_number = 3
            c.page_number = 2
            c.heading = "Lock-in Period"
            c.content = "Minimum twelve month lock-in."
            mc.return_value = [c]
            result = rag_service.answer_question("lock-in?", "doc-id", db=None)

    assert len(result.citations) == 1
    cit = result.citations[0]
    assert cit.clause_id == clause_id
    assert cit.clause_number == 3
    assert cit.page_number == 2
    assert cit.heading == "Lock-in Period"


def test_rag_llm_failure_returns_safe_message(mock_embed, mock_llm_fail):
    """Groq failure must return a safe user-facing message, not expose exceptions."""
    from app.services import rag_service

    fake_hit = {"clause_id": "c1", "clause_number": 1, "page_number": 1, "heading": None, "distance": 0.2}
    with patch("app.services.rag_service.semantic_search", return_value=[fake_hit]):
        with patch("app.services.rag_service.get_clauses_by_document") as mc:
            c = MagicMock()
            c.id = "c1"
            c.clause_number = 1
            c.page_number = 1
            c.heading = None
            c.content = "Some content."
            mc.return_value = [c]
            result = rag_service.answer_question("?", "doc-id", db=None)

    assert result.answer == rag_service.SAFE_ERROR_ANSWER
    assert result.citations == []


def test_rag_empty_llm_response_returns_safe_message(mock_embed, mock_llm_empty):
    """Empty LLM response must return a safe fallback."""
    from app.services import rag_service

    fake_hit = {"clause_id": "c1", "clause_number": 1, "page_number": 1, "heading": None, "distance": 0.2}
    with patch("app.services.rag_service.semantic_search", return_value=[fake_hit]):
        with patch("app.services.rag_service.get_clauses_by_document") as mc:
            c = MagicMock()
            c.id = "c1"
            c.clause_number = 1
            c.page_number = 1
            c.heading = None
            c.content = "Some content."
            mc.return_value = [c]
            result = rag_service.answer_question("?", "doc-id", db=None)

    assert result.answer == rag_service.SAFE_ERROR_ANSWER


def test_rag_prompt_injection_defense():
    """System prompt must explicitly address untrusted document content."""
    from app.services.rag_service import SYSTEM_PROMPT
    assert "untrusted" in SYSTEM_PROMPT.lower()
    assert "cannot modify" in SYSTEM_PROMPT.lower() or "cannot override" in SYSTEM_PROMPT.lower() or "must never override" in SYSTEM_PROMPT.lower() or "cannot" in SYSTEM_PROMPT.lower()


# ── Chat API tests ────────────────────────────────────────────────────────────

def test_authenticated_user_can_chat(client, tmp_uploads, mock_embed, mock_llm):
    token = register_and_login(client, "chat1@example.com")
    pdf = make_text_pdf(AGREEMENT_PAGES)
    doc_id = upload_and_process(client, token, pdf)

    res = client.post(
        f"/api/v1/documents/{doc_id}/chat",
        json={"message": "What is the notice period?"},
        headers=auth_headers(token),
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert "answer" in data
    assert isinstance(data["answer"], str)
    assert len(data["answer"]) > 0
    assert "citations" in data
    assert isinstance(data["citations"], list)


def test_unauthenticated_user_cannot_chat(client, tmp_uploads, mock_embed, mock_llm):
    token = register_and_login(client, "chat2@example.com")
    pdf = make_text_pdf(AGREEMENT_PAGES)
    doc_id = upload_and_process(client, token, pdf)

    res = client.post(
        f"/api/v1/documents/{doc_id}/chat",
        json={"message": "What is the notice period?"},
    )
    assert res.status_code == 403


def test_cross_user_chat_returns_404(client, tmp_uploads, mock_embed, mock_llm):
    token_a = register_and_login(client, "chata@example.com")
    token_b = register_and_login(client, "chatb@example.com")
    pdf = make_text_pdf(AGREEMENT_PAGES)
    doc_id = upload_and_process(client, token_a, pdf)

    res = client.post(
        f"/api/v1/documents/{doc_id}/chat",
        json={"message": "What is the notice period?"},
        headers=auth_headers(token_b),
    )
    assert res.status_code == 404


def test_chat_on_unprocessed_document_returns_409(client, tmp_uploads, mock_embed, mock_llm):
    token = register_and_login(client, "chat3@example.com")
    pdf = make_text_pdf(AGREEMENT_PAGES)
    up = upload_pdf(client, token, pdf)
    doc_id = up.json()["id"]

    res = client.post(
        f"/api/v1/documents/{doc_id}/chat",
        json={"message": "What is the notice period?"},
        headers=auth_headers(token),
    )
    assert res.status_code == 409


def test_empty_message_rejected(client, tmp_uploads, mock_embed, mock_llm):
    token = register_and_login(client, "chat4@example.com")
    pdf = make_text_pdf(AGREEMENT_PAGES)
    doc_id = upload_and_process(client, token, pdf)

    res = client.post(
        f"/api/v1/documents/{doc_id}/chat",
        json={"message": ""},
        headers=auth_headers(token),
    )
    assert res.status_code == 422


def test_oversized_message_rejected(client, tmp_uploads, mock_embed, mock_llm):
    token = register_and_login(client, "chat5@example.com")
    pdf = make_text_pdf(AGREEMENT_PAGES)
    doc_id = upload_and_process(client, token, pdf)

    res = client.post(
        f"/api/v1/documents/{doc_id}/chat",
        json={"message": "x" * 2001},
        headers=auth_headers(token),
    )
    assert res.status_code == 422


def test_user_message_persisted(client, tmp_uploads, mock_embed, mock_llm):
    token = register_and_login(client, "chat6@example.com")
    pdf = make_text_pdf(AGREEMENT_PAGES)
    doc_id = upload_and_process(client, token, pdf)

    client.post(
        f"/api/v1/documents/{doc_id}/chat",
        json={"message": "What is the security deposit?"},
        headers=auth_headers(token),
    )
    history = client.get(
        f"/api/v1/documents/{doc_id}/chat",
        headers=auth_headers(token),
    )
    assert history.status_code == 200
    messages = history.json()["messages"]
    user_msgs = [m for m in messages if m["role"] == "user"]
    assert any("security deposit" in m["content"].lower() for m in user_msgs)


def test_assistant_response_persisted(client, tmp_uploads, mock_embed, mock_llm):
    token = register_and_login(client, "chat7@example.com")
    pdf = make_text_pdf(AGREEMENT_PAGES)
    doc_id = upload_and_process(client, token, pdf)

    client.post(
        f"/api/v1/documents/{doc_id}/chat",
        json={"message": "What is the notice period?"},
        headers=auth_headers(token),
    )
    history = client.get(
        f"/api/v1/documents/{doc_id}/chat",
        headers=auth_headers(token),
    )
    messages = history.json()["messages"]
    assistant_msgs = [m for m in messages if m["role"] == "assistant"]
    assert len(assistant_msgs) >= 1
    assert assistant_msgs[0]["content"] != ""


def test_chat_history_isolated_between_users(client, tmp_uploads, mock_embed, mock_llm):
    token_a = register_and_login(client, "hista@example.com")
    token_b = register_and_login(client, "histb@example.com")
    pdf = make_text_pdf(AGREEMENT_PAGES)
    doc_id_a = upload_and_process(client, token_a, pdf)
    doc_id_b = upload_and_process(client, token_b, pdf)

    client.post(
        f"/api/v1/documents/{doc_id_a}/chat",
        json={"message": "UNIQUE_MESSAGE_FOR_USER_A"},
        headers=auth_headers(token_a),
    )

    # User B cannot read user A's chat
    hist_b_on_a = client.get(
        f"/api/v1/documents/{doc_id_a}/chat",
        headers=auth_headers(token_b),
    )
    assert hist_b_on_a.status_code == 404

    # User B's own history is empty
    hist_b = client.get(
        f"/api/v1/documents/{doc_id_b}/chat",
        headers=auth_headers(token_b),
    )
    assert hist_b.status_code == 200
    for m in hist_b.json()["messages"]:
        assert "UNIQUE_MESSAGE_FOR_USER_A" not in m["content"]


def test_chat_history_get_requires_auth(client, tmp_uploads, mock_embed):
    token = register_and_login(client, "hist2@example.com")
    pdf = make_text_pdf(AGREEMENT_PAGES)
    doc_id = upload_and_process(client, token, pdf)

    res = client.get(f"/api/v1/documents/{doc_id}/chat")
    assert res.status_code == 403


def test_citations_have_correct_fields(client, tmp_uploads, mock_embed, mock_llm):
    token = register_and_login(client, "cit1@example.com")
    pdf = make_text_pdf(AGREEMENT_PAGES)
    doc_id = upload_and_process(client, token, pdf)

    res = client.post(
        f"/api/v1/documents/{doc_id}/chat",
        json={"message": "What is the notice period?"},
        headers=auth_headers(token),
    )
    assert res.status_code == 200
    for cit in res.json()["citations"]:
        assert "clause_id" in cit
        assert "clause_number" in cit
        assert "page_number" in cit
        assert isinstance(cit["clause_number"], int)
        assert isinstance(cit["page_number"], int)


def test_api_key_never_in_response(client, tmp_uploads, mock_embed, mock_llm):
    token = register_and_login(client, "apikey@example.com")
    pdf = make_text_pdf(AGREEMENT_PAGES)
    doc_id = upload_and_process(client, token, pdf)

    res = client.post(
        f"/api/v1/documents/{doc_id}/chat",
        json={"message": "What is the notice period?"},
        headers=auth_headers(token),
    )
    # GROQ_API_KEY in .env is empty string during tests; verify it never appears
    assert "gsk_" not in res.text  # Groq keys start with gsk_
    assert "GROQ_API_KEY" not in res.text


def test_groq_failure_returns_safe_message(client, tmp_uploads, mock_embed, mock_llm_fail):
    token = register_and_login(client, "fail1@example.com")
    pdf = make_text_pdf(AGREEMENT_PAGES)
    doc_id = upload_and_process(client, token, pdf)

    res = client.post(
        f"/api/v1/documents/{doc_id}/chat",
        json={"message": "What is the notice period?"},
        headers=auth_headers(token),
    )
    # Should return 200 with a safe fallback, not a 500 with a stack trace
    assert res.status_code == 200
    data = res.json()
    assert "answer" in data
    assert "Traceback" not in data["answer"]
    assert "groq" not in data["answer"].lower()
    assert "api" not in data["answer"].lower() or "unable" in data["answer"].lower()


def test_chat_nonexistent_document_returns_404(client, tmp_uploads, mock_embed, mock_llm):
    token = register_and_login(client, "notfound@example.com")
    fake_id = str(uuid.uuid4())
    res = client.post(
        f"/api/v1/documents/{fake_id}/chat",
        json={"message": "What is the notice period?"},
        headers=auth_headers(token),
    )
    assert res.status_code == 404


def test_multiple_messages_in_history(client, tmp_uploads, mock_embed, mock_llm):
    token = register_and_login(client, "multi@example.com")
    pdf = make_text_pdf(AGREEMENT_PAGES)
    doc_id = upload_and_process(client, token, pdf)

    client.post(
        f"/api/v1/documents/{doc_id}/chat",
        json={"message": "What is the notice period?"},
        headers=auth_headers(token),
    )
    client.post(
        f"/api/v1/documents/{doc_id}/chat",
        json={"message": "What about the deposit?"},
        headers=auth_headers(token),
    )

    history = client.get(
        f"/api/v1/documents/{doc_id}/chat",
        headers=auth_headers(token),
    )
    messages = history.json()["messages"]
    # 2 user + 2 assistant = 4
    assert len(messages) == 4
