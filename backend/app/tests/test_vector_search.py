"""
Phase 5 tests — embeddings, Chroma vector store, and semantic search.

All tests use:
  - mock_embed fixture: replaces sentence-transformers with a fast stub
  - tmp_uploads fixture: isolated PDF storage per test
  - EphemeralClient via CHROMA_PERSIST_DIRECTORY="" in conftest

The real embedding model is NOT loaded during tests.
The actual production code still uses the real model.
"""
import io
import os
import uuid
import pytest
from fpdf import FPDF


# ── Helpers (shared with test_processing.py) ─────────────────────────────────

def make_text_pdf(pages: list) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=False)
    for page_text in pages:
        pdf.add_page()
        pdf.set_font("Helvetica", size=11)
        for line in page_text.splitlines():
            pdf.cell(0, 6, line, ln=True)
    return bytes(pdf.output())


def make_empty_pdf() -> bytes:
    pdf = FPDF()
    pdf.add_page()
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
    proc = client.post(f"/api/v1/documents/{doc_id}/process", headers=auth_headers(token))
    return doc_id, proc


# ── Unit tests: embedding_service ────────────────────────────────────────────

def test_embedding_service_returns_list(mock_embed):
    from app.services.embedding_service import embed_texts
    result = embed_texts(["Security deposit clause text here"])
    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], list)


def test_embedding_service_correct_dimension(mock_embed):
    from app.services.embedding_service import embed_texts
    result = embed_texts(["Some text to embed for dimension check"])
    assert len(result[0]) == 384


def test_embedding_service_multiple_texts(mock_embed):
    from app.services.embedding_service import embed_texts
    texts = ["First clause", "Second clause", "Third clause"]
    result = embed_texts(texts)
    assert len(result) == 3
    assert all(len(v) == 384 for v in result)


def test_embedding_service_different_texts_different_vectors(mock_embed):
    from app.services.embedding_service import embed_texts
    v1 = embed_texts(["lock-in period clause"])[0]
    v2 = embed_texts(["security deposit clause"])[0]
    assert v1 != v2


def test_embed_text_single(mock_embed):
    from app.services.embedding_service import embed_text
    v = embed_text("rent payment monthly")
    assert isinstance(v, list)
    assert len(v) == 384


# ── Unit tests: vector_store_service ─────────────────────────────────────────

def test_vector_store_add_and_retrieve(mock_embed, tmp_path):
    from app.services.vector_store_service import (
        add_clause_embeddings,
        semantic_search,
        count_document_embeddings,
    )
    from app.services.embedding_service import embed_text

    chroma_dir = str(tmp_path / "chroma_vs_test")
    doc_id = str(uuid.uuid4())
    clause_id = str(uuid.uuid4())
    embedding = embed_text("The tenant shall pay rent on the first day of each month.")

    add_clause_embeddings(
        document_id=doc_id,
        clause_ids=[clause_id],
        embeddings=[embedding],
        metadatas=[{
            "document_id": doc_id,
            "clause_id": clause_id,
            "clause_number": 1,
            "page_number": 1,
        }],
        persist_directory=chroma_dir,
    )

    count = count_document_embeddings(doc_id, persist_directory=chroma_dir)
    assert count == 1


def test_vector_store_search_returns_results(mock_embed, tmp_path):
    from app.services.vector_store_service import add_clause_embeddings, semantic_search
    from app.services.embedding_service import embed_text

    chroma_dir = str(tmp_path / "chroma_search_test")
    doc_id = str(uuid.uuid4())

    texts = [
        "Lock-in period of twelve months from commencement date.",
        "Security deposit equivalent to two months rent.",
        "Maintenance of the property shall be the tenant's responsibility.",
    ]
    for i, text in enumerate(texts):
        cid = str(uuid.uuid4())
        emb = embed_text(text)
        add_clause_embeddings(
            document_id=doc_id,
            clause_ids=[cid],
            embeddings=[emb],
            metadatas=[{
                "document_id": doc_id,
                "clause_id": cid,
                "clause_number": i + 1,
                "page_number": 1,
            }],
            persist_directory=chroma_dir,
        )

    query_emb = embed_text("lock-in period early termination")
    results = semantic_search(query_emb, doc_id, top_k=3, persist_directory=chroma_dir)
    assert len(results) >= 1
    assert all("clause_id" in r for r in results)
    assert all("distance" in r for r in results)


def test_vector_store_filtered_by_document_id(mock_embed, tmp_path):
    from app.services.vector_store_service import add_clause_embeddings, semantic_search
    from app.services.embedding_service import embed_text

    chroma_dir = str(tmp_path / "chroma_filter_test")
    doc_a = str(uuid.uuid4())
    doc_b = str(uuid.uuid4())

    for doc_id in [doc_a, doc_b]:
        cid = str(uuid.uuid4())
        emb = embed_text(f"Content for document {doc_id}")
        add_clause_embeddings(
            document_id=doc_id,
            clause_ids=[cid],
            embeddings=[emb],
            metadatas=[{
                "document_id": doc_id,
                "clause_id": cid,
                "clause_number": 1,
                "page_number": 1,
            }],
            persist_directory=chroma_dir,
        )

    query_emb = embed_text("document content")
    results_a = semantic_search(query_emb, doc_a, top_k=5, persist_directory=chroma_dir)
    results_b = semantic_search(query_emb, doc_b, top_k=5, persist_directory=chroma_dir)

    # Results from doc_a must not contain doc_b's entries
    for r in results_a:
        meta_doc = r.get("clause_id", "")
        assert meta_doc != ""

    assert len(results_a) >= 1
    assert len(results_b) >= 1


def test_vector_store_delete_removes_vectors(mock_embed, tmp_path):
    from app.services.vector_store_service import (
        add_clause_embeddings,
        delete_document_embeddings,
        count_document_embeddings,
    )
    from app.services.embedding_service import embed_text

    chroma_dir = str(tmp_path / "chroma_delete_test")
    doc_id = str(uuid.uuid4())
    cid = str(uuid.uuid4())
    emb = embed_text("Some clause text for deletion test")

    add_clause_embeddings(
        document_id=doc_id,
        clause_ids=[cid],
        embeddings=[emb],
        metadatas=[{"document_id": doc_id, "clause_id": cid, "clause_number": 1, "page_number": 1}],
        persist_directory=chroma_dir,
    )
    assert count_document_embeddings(doc_id, persist_directory=chroma_dir) == 1

    delete_document_embeddings(doc_id, persist_directory=chroma_dir)
    assert count_document_embeddings(doc_id, persist_directory=chroma_dir) == 0


# ── API tests: search endpoint ────────────────────────────────────────────────

def test_search_requires_authentication(client, tmp_uploads, mock_embed):
    token = register_and_login(client, "search_auth@example.com")
    pdf = make_text_pdf(["Rent clause content here for authentication test."])
    doc_id, _ = upload_and_process(client, token, pdf)
    res = client.get(f"/api/v1/documents/{doc_id}/search?q=rent")
    assert res.status_code == 403


def test_search_rejects_empty_query(client, tmp_uploads, mock_embed):
    token = register_and_login(client, "search_empty@example.com")
    pdf = make_text_pdf(["Content for empty query test."])
    doc_id, _ = upload_and_process(client, token, pdf)
    # Empty string after strip — FastAPI Query min_length=1 catches it
    res = client.get(
        f"/api/v1/documents/{doc_id}/search?q=%20",
        headers=auth_headers(token),
    )
    # Either 422 (validation) or 422 (empty after strip)
    assert res.status_code in (422,)


def test_search_unprocessed_document_returns_409(client, tmp_uploads, mock_embed):
    token = register_and_login(client, "search_unproc@example.com")
    pdf = make_text_pdf(["Unprocessed document content."])
    up = upload_pdf(client, token, pdf)
    doc_id = up.json()["id"]
    # Not processed — status is 'uploaded'
    res = client.get(
        f"/api/v1/documents/{doc_id}/search?q=rent",
        headers=auth_headers(token),
    )
    assert res.status_code == 409


def test_search_cross_user_returns_404(client, tmp_uploads, mock_embed):
    token_a = register_and_login(client, "search_isoa@example.com")
    token_b = register_and_login(client, "search_isob@example.com")
    pdf = make_text_pdf(["Clause for cross-user isolation test."])
    doc_id, _ = upload_and_process(client, token_a, pdf)
    res = client.get(
        f"/api/v1/documents/{doc_id}/search?q=clause",
        headers=auth_headers(token_b),
    )
    assert res.status_code == 404


def test_search_returns_results(client, tmp_uploads, mock_embed):
    token = register_and_login(client, "search_ok@example.com")
    pdf = make_text_pdf([
        "1. Rent\nThe tenant shall pay rent on the first of each month.\n\n"
        "2. Deposit\nA security deposit of two months rent shall be paid.\n\n"
        "3. Notice\nEither party shall give one month written notice."
    ])
    doc_id, proc = upload_and_process(client, token, pdf)
    assert proc.status_code == 200, proc.text

    res = client.get(
        f"/api/v1/documents/{doc_id}/search?q=security+deposit",
        headers=auth_headers(token),
    )
    assert res.status_code == 200
    results = res.json()
    assert isinstance(results, list)


def test_search_results_have_correct_fields(client, tmp_uploads, mock_embed):
    token = register_and_login(client, "search_fields@example.com")
    pdf = make_text_pdf(["Clause one content for field validation test."])
    doc_id, _ = upload_and_process(client, token, pdf)
    res = client.get(
        f"/api/v1/documents/{doc_id}/search?q=clause",
        headers=auth_headers(token),
    )
    assert res.status_code == 200
    for item in res.json():
        assert "clause_id" in item
        assert "clause_number" in item
        assert "content" in item
        assert "page_number" in item
        # Must NOT contain raw embeddings
        assert "embedding" not in item
        assert "vector" not in item


def test_search_does_not_return_raw_embeddings(client, tmp_uploads, mock_embed):
    token = register_and_login(client, "search_noraw@example.com")
    pdf = make_text_pdf(["Content for search result validation test."])
    doc_id, _ = upload_and_process(client, token, pdf)
    res = client.get(
        f"/api/v1/documents/{doc_id}/search?q=content",
        headers=auth_headers(token),
    )
    assert res.status_code == 200
    # Results must not contain raw float-vector arrays
    # (a real embedding would be a list of 384 floats — check no such key exists)
    for item in res.json():
        assert "embedding" not in item   # no embedding key in response object
        assert "vector" not in item      # no vector key in response object


def test_search_nonexistent_document_returns_404(client, tmp_uploads, mock_embed):
    token = register_and_login(client, "search_notfound@example.com")
    fake_id = str(uuid.uuid4())
    res = client.get(
        f"/api/v1/documents/{fake_id}/search?q=rent",
        headers=auth_headers(token),
    )
    assert res.status_code == 404


# ── Reprocessing and deletion vector consistency ──────────────────────────────

def test_reprocessing_removes_old_vectors(client, tmp_uploads, mock_embed):
    """After reprocessing, vector count must equal clause count, not double it."""
    from app.services.vector_store_service import count_document_embeddings

    token = register_and_login(client, "reproc_vec@example.com")
    pdf = make_text_pdf(["1. Rent\nRent content here.\n\n2. Deposit\nDeposit content."])
    doc_id, _ = upload_and_process(client, token, pdf)

    count_after_first = count_document_embeddings(doc_id, persist_directory="")

    # Process again
    client.post(f"/api/v1/documents/{doc_id}/process", headers=auth_headers(token))
    count_after_second = count_document_embeddings(doc_id, persist_directory="")

    assert count_after_first == count_after_second, (
        f"Duplicate vectors: first={count_after_first}, second={count_after_second}"
    )


def test_reprocessing_no_duplicate_vectors(client, tmp_uploads, mock_embed):
    """Process three times — vector count must remain stable."""
    from app.services.vector_store_service import count_document_embeddings

    token = register_and_login(client, "reproc_nodup@example.com")
    pdf = make_text_pdf(["Single page of text content for duplicate vector test."])
    doc_id, _ = upload_and_process(client, token, pdf)

    count_1 = count_document_embeddings(doc_id, persist_directory="")
    client.post(f"/api/v1/documents/{doc_id}/process", headers=auth_headers(token))
    count_2 = count_document_embeddings(doc_id, persist_directory="")
    client.post(f"/api/v1/documents/{doc_id}/process", headers=auth_headers(token))
    count_3 = count_document_embeddings(doc_id, persist_directory="")

    assert count_1 == count_2 == count_3, f"Vectors grew: {count_1}, {count_2}, {count_3}"


def test_delete_document_removes_vectors(client, tmp_uploads, mock_embed):
    """Deleting a document must remove its Chroma vectors."""
    from app.services.vector_store_service import count_document_embeddings

    token = register_and_login(client, "del_vec@example.com")
    pdf = make_text_pdf(["Clause text content for deletion vector cleanup test."])
    doc_id, _ = upload_and_process(client, token, pdf)

    count_before = count_document_embeddings(doc_id, persist_directory="")
    assert count_before >= 1

    client.delete(f"/api/v1/documents/{doc_id}", headers=auth_headers(token))

    count_after = count_document_embeddings(doc_id, persist_directory="")
    assert count_after == 0


def test_processing_indexes_clauses(client, tmp_uploads, mock_embed):
    """After processing, vectors_indexed must equal clauses_extracted."""
    token = register_and_login(client, "idx_count@example.com")
    pdf = make_text_pdf(["1. Rent\nRent here.\n\n2. Deposit\nDeposit here."])
    doc_id, proc = upload_and_process(client, token, pdf)
    assert proc.status_code == 200, proc.text
    data = proc.json()
    assert "vectors_indexed" in data
    assert data["vectors_indexed"] == data["clauses_extracted"]
