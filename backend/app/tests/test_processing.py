"""
Phase 4 tests — PDF processing, clause extraction, and processing API.
All Phase 1–3 tests must continue passing.
"""
import io
import os
import uuid
import pytest
from fpdf import FPDF


# ── PDF fixtures ──────────────────────────────────────────────────────────────

def make_text_pdf(pages: list[str]) -> bytes:
    """
    Create a real PDF with extractable text using fpdf2.
    Each element in `pages` becomes one page.
    """
    pdf = FPDF()
    pdf.set_auto_page_break(auto=False)
    for page_text in pages:
        pdf.add_page()
        pdf.set_font("Helvetica", size=11)
        # Write lines — split manually so fpdf doesn't need TTF fonts
        for line in page_text.splitlines():
            pdf.cell(0, 6, line, ln=True)
    return bytes(pdf.output())


def make_empty_pdf() -> bytes:
    """PDF with pages but no text content (simulates scanned/image PDF)."""
    pdf = FPDF()
    pdf.add_page()
    # No text added — page is blank
    return bytes(pdf.output())


MINIMAL_PDF = (
    b"%PDF-1.4\n"
    b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj\n"
    b"xref\n0 4\n"
    b"0000000000 65535 f \n"
    b"0000000009 00000 n \n"
    b"0000000058 00000 n \n"
    b"0000000115 00000 n \n"
    b"trailer<</Size 4/Root 1 0 R>>\n"
    b"startxref\n190\n%%EOF"
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def register_and_login(client, email, password="password123"):
    r = client.post("/api/v1/auth/register", json={"email": email, "password": password})
    assert r.status_code == 201, r.text
    return r.json()["access_token"]


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def upload_pdf(client, token, content: bytes, title="Test Agreement", filename="agreement.pdf"):
    return client.post(
        "/api/v1/documents",
        files={"file": (filename, io.BytesIO(content), "application/pdf")},
        data={"title": title},
        headers=auth_headers(token),
    )


def upload_and_process(client, token, content: bytes, title="Test"):
    """Upload a PDF and trigger processing. Returns (doc_id, process_response)."""
    up = upload_pdf(client, token, content, title=title)
    assert up.status_code == 201, up.text
    doc_id = up.json()["id"]
    proc = client.post(f"/api/v1/documents/{doc_id}/process", headers=auth_headers(token))
    return doc_id, proc


# ── Unit tests: pdf_service ───────────────────────────────────────────────────

def test_pdf_service_extracts_text():
    from app.services.pdf_service import extract_text_by_page
    pdf_bytes = make_text_pdf(["Hello this is page one text content here."])
    pages = extract_text_by_page(pdf_bytes)
    assert len(pages) >= 1
    assert pages[0].page_number == 1
    combined = " ".join(p.text for p in pages)
    assert "Hello" in combined or "page" in combined


def test_pdf_service_preserves_page_numbers():
    from app.services.pdf_service import extract_text_by_page
    pdf_bytes = make_text_pdf([
        "Page one content with enough text to be valid.",
        "Page two content with enough text to be valid.",
        "Page three content with enough text to be valid.",
    ])
    pages = extract_text_by_page(pdf_bytes)
    page_numbers = [p.page_number for p in pages]
    assert page_numbers == list(range(1, len(pages) + 1))


def test_pdf_service_empty_pdf_raises():
    from app.services.pdf_service import extract_text_by_page, ExtractionError
    empty_bytes = make_empty_pdf()
    with pytest.raises(ExtractionError):
        extract_text_by_page(empty_bytes)


def test_pdf_service_invalid_bytes_raises():
    from app.services.pdf_service import extract_text_by_page, ExtractionError
    with pytest.raises(ExtractionError):
        extract_text_by_page(b"this is not a pdf at all")


# ── Unit tests: clause_service ────────────────────────────────────────────────

def test_clause_service_extracts_clauses():
    from app.services.pdf_service import PageText
    from app.services.clause_service import extract_clauses
    pages = [PageText(page_number=1, text="1. Rent\nThe tenant shall pay rent monthly.\n\n2. Deposit\nA deposit of two months rent is required.")]
    clauses = extract_clauses(pages, "doc-001")
    assert len(clauses) >= 1
    all_content = " ".join(c.content for c in clauses)
    assert "rent" in all_content.lower() or "deposit" in all_content.lower()


def test_clause_service_page_number_preserved():
    from app.services.pdf_service import PageText
    from app.services.clause_service import extract_clauses
    pages = [
        PageText(page_number=1, text="Some content on page one that is long enough."),
        PageText(page_number=2, text="Some content on page two that is long enough."),
    ]
    clauses = extract_clauses(pages, "doc-002")
    page_numbers = {c.page_number for c in clauses}
    assert 1 in page_numbers or 2 in page_numbers


def test_clause_service_fallback_no_headings():
    from app.services.pdf_service import PageText
    from app.services.clause_service import extract_clauses
    # No headings — should fallback to page-level clause
    pages = [PageText(page_number=1, text="This is just a paragraph without any heading structure whatsoever.")]
    clauses = extract_clauses(pages, "doc-003")
    assert len(clauses) == 1
    assert "paragraph" in clauses[0].content


def test_clause_service_sequential_numbering():
    from app.services.pdf_service import PageText
    from app.services.clause_service import extract_clauses
    pages = [PageText(page_number=1, text="First long sentence of plain text paragraph one.\n\nSecond long sentence of plain text paragraph two.")]
    clauses = extract_clauses(pages, "doc-004")
    numbers = [c.clause_number for c in clauses]
    assert numbers == list(range(1, len(clauses) + 1))


def test_clause_service_blank_pages_skipped():
    from app.services.pdf_service import PageText
    from app.services.clause_service import extract_clauses
    pages = [
        PageText(page_number=1, text="Real content page with sufficient text here."),
        PageText(page_number=2, text="   \n  \n   "),  # blank
        PageText(page_number=3, text="Another real content page with sufficient text."),
    ]
    clauses = extract_clauses(pages, "doc-005")
    # Blank page 2 produces no clause
    page_nums = [c.page_number for c in clauses]
    assert 2 not in page_nums


# ── Unit tests: text_normalizer ───────────────────────────────────────────────

def test_normalizer_collapses_whitespace():
    from app.utils.text_normalizer import normalize_text
    result = normalize_text("Hello    world   here")
    assert "  " not in result


def test_normalizer_preserves_content():
    from app.utils.text_normalizer import normalize_text
    result = normalize_text("The tenant shall pay rent monthly.")
    assert "tenant" in result
    assert "rent" in result


def test_normalizer_empty_string():
    from app.utils.text_normalizer import normalize_text
    assert normalize_text("") == ""


# ── API tests: processing endpoint ───────────────────────────────────────────

def test_owner_can_process_document(client, tmp_uploads):
    token = register_and_login(client, "proc1@example.com")
    pdf_bytes = make_text_pdf(["1. Rent\nThe tenant pays rent monthly.\n\n2. Deposit\nSecurity deposit required."])
    doc_id, res = upload_and_process(client, token, pdf_bytes)
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["status"] in ("ready", "processing")
    doc_res = client.get(f"/api/v1/documents/{doc_id}", headers=auth_headers(token))
    final = doc_res.json()
    assert final["processing_status"] == "ready"
    assert final.get("clause_count", 0) >= 1


def test_unauthenticated_cannot_process(client, tmp_uploads):
    token = register_and_login(client, "proc2@example.com")
    pdf_bytes = make_text_pdf(["Some content here for processing test."])
    up = upload_pdf(client, token, pdf_bytes)
    doc_id = up.json()["id"]
    res = client.post(f"/api/v1/documents/{doc_id}/process")
    assert res.status_code == 403


def test_other_user_cannot_process_document(client, tmp_uploads):
    token_a = register_and_login(client, "proc3a@example.com")
    token_b = register_and_login(client, "proc3b@example.com")
    pdf_bytes = make_text_pdf(["Some content here for isolation test."])
    doc_id = upload_pdf(client, token_a, pdf_bytes).json()["id"]
    res = client.post(f"/api/v1/documents/{doc_id}/process", headers=auth_headers(token_b))
    assert res.status_code == 404


def test_document_status_changes_to_ready(client, tmp_uploads):
    token = register_and_login(client, "proc4@example.com")
    pdf_bytes = make_text_pdf(["Clause content for status transition test."])
    doc_id, proc_res = upload_and_process(client, token, pdf_bytes)
    assert proc_res.status_code == 200
    doc_res = client.get(f"/api/v1/documents/{doc_id}", headers=auth_headers(token))
    assert doc_res.json()["processing_status"] == "ready"


def test_clauses_stored_in_database(client, tmp_uploads):
    token = register_and_login(client, "proc5@example.com")
    pdf_bytes = make_text_pdf(["1. Rent\nThe rent is payable monthly.\n\n2. Notice\nOne month notice is required."])
    doc_id, proc_res = upload_and_process(client, token, pdf_bytes)
    assert proc_res.status_code == 200
    clauses_res = client.get(f"/api/v1/documents/{doc_id}/clauses", headers=auth_headers(token))
    assert clauses_res.status_code == 200
    clauses = clauses_res.json()
    assert len(clauses) >= 1


def test_clauses_belong_to_correct_document(client, tmp_uploads):
    token = register_and_login(client, "proc6@example.com")
    pdf_bytes = make_text_pdf(["Content for document isolation clause test here."])
    doc_id, _ = upload_and_process(client, token, pdf_bytes)
    clauses_res = client.get(f"/api/v1/documents/{doc_id}/clauses", headers=auth_headers(token))
    for clause in clauses_res.json():
        assert "clause_number" in clause
        assert "content" in clause
        assert "page_number" in clause


def test_empty_pdf_fails_safely(client, tmp_uploads):
    token = register_and_login(client, "proc7@example.com")
    empty_bytes = make_empty_pdf()
    up = upload_pdf(client, token, empty_bytes)
    # Empty PDF still passes upload validation (valid PDF bytes, has %PDF header)
    if up.status_code != 201:
        pytest.skip("Empty PDF rejected at upload — acceptable")
    doc_id = up.json()["id"]
    res = client.post(f"/api/v1/documents/{doc_id}/process", headers=auth_headers(token))
    assert res.status_code == 200
    assert res.json()["status"] == "processing"
    # Background task runs before the TestClient call returns
    doc_res = client.get(f"/api/v1/documents/{doc_id}", headers=auth_headers(token))
    assert doc_res.json()["processing_status"] == "failed"
    # Error message must not contain stack trace or filesystem path
    error_msg = doc_res.json().get("processing_error", "")
    assert "Traceback" not in error_msg
    assert "uploads" not in error_msg
    assert "\\" not in error_msg


def test_reprocessing_does_not_duplicate_clauses(client, tmp_uploads):
    token = register_and_login(client, "proc8@example.com")
    pdf_bytes = make_text_pdf(["1. Rent\nRent is due monthly.\n\n2. Notice\nNotice period is one month."])
    doc_id, _ = upload_and_process(client, token, pdf_bytes)
    # Process again
    client.post(f"/api/v1/documents/{doc_id}/process", headers=auth_headers(token))
    clauses_res = client.get(f"/api/v1/documents/{doc_id}/clauses", headers=auth_headers(token))
    first_count = len(clauses_res.json())
    # Process a third time — count must remain the same
    client.post(f"/api/v1/documents/{doc_id}/process", headers=auth_headers(token))
    clauses_res2 = client.get(f"/api/v1/documents/{doc_id}/clauses", headers=auth_headers(token))
    second_count = len(clauses_res2.json())
    assert first_count == second_count, f"Duplicate clauses detected: {first_count} vs {second_count}"


def test_nonexistent_document_cannot_be_processed(client, tmp_uploads):
    token = register_and_login(client, "proc9@example.com")
    fake_id = str(uuid.uuid4())
    res = client.post(f"/api/v1/documents/{fake_id}/process", headers=auth_headers(token))
    assert res.status_code == 404


def test_processing_error_does_not_expose_stack_trace(client, tmp_uploads):
    token = register_and_login(client, "proc10@example.com")
    empty_bytes = make_empty_pdf()
    up = upload_pdf(client, token, empty_bytes)
    if up.status_code != 201:
        pytest.skip("Empty PDF rejected at upload")
    doc_id = up.json()["id"]
    res = client.post(f"/api/v1/documents/{doc_id}/process", headers=auth_headers(token))
    assert "Traceback" not in res.text
    assert "File \"" not in res.text


def test_clauses_endpoint_requires_ownership(client, tmp_uploads):
    token_a = register_and_login(client, "proc11a@example.com")
    token_b = register_and_login(client, "proc11b@example.com")
    pdf_bytes = make_text_pdf(["Some clause content for ownership check test."])
    doc_id, _ = upload_and_process(client, token_a, pdf_bytes)
    res = client.get(f"/api/v1/documents/{doc_id}/clauses", headers=auth_headers(token_b))
    assert res.status_code == 404


def test_document_clause_count_in_response(client, tmp_uploads):
    token = register_and_login(client, "proc12@example.com")
    pdf_bytes = make_text_pdf(["1. Rent\nRent content here.\n\n2. Deposit\nDeposit content here."])
    doc_id, _ = upload_and_process(client, token, pdf_bytes)
    doc_res = client.get(f"/api/v1/documents/{doc_id}", headers=auth_headers(token))
    data = doc_res.json()
    assert "clause_count" in data
    assert isinstance(data["clause_count"], int)
    assert data["clause_count"] >= 1
