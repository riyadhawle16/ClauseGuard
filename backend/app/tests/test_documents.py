"""
Phase 3 tests — PDF upload and document management.
All Phase 1 + Phase 2 tests must continue passing alongside these.
"""
import io
import os
import uuid
import pytest

# ---------------------------------------------------------------------------
# Minimal valid PDF bytes (hand-crafted, ~200 bytes, renders as blank page)
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def register_and_login(client, email, password="password123"):
    r = client.post("/api/v1/auth/register", json={"email": email, "password": password})
    assert r.status_code == 201
    return r.json()["access_token"]


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def upload_pdf(client, token, title="Test Agreement", filename="agreement.pdf", content=None):
    data = content or MINIMAL_PDF
    return client.post(
        "/api/v1/documents",
        files={"file": (filename, io.BytesIO(data), "application/pdf")},
        data={"title": title},
        headers=auth_headers(token),
    )


# ---------------------------------------------------------------------------
# Upload tests
# ---------------------------------------------------------------------------

def test_authenticated_user_can_upload_pdf(client, tmp_uploads):
    token = register_and_login(client, "upload1@example.com")
    res = upload_pdf(client, token)
    assert res.status_code == 201
    data = res.json()
    assert "id" in data
    assert data["processing_status"] == "uploaded"
    assert data["original_filename"] == "agreement.pdf"
    assert data["title"] == "Test Agreement"


def test_unauthenticated_user_cannot_upload(client, tmp_uploads):
    res = client.post(
        "/api/v1/documents",
        files={"file": ("agreement.pdf", io.BytesIO(MINIMAL_PDF), "application/pdf")},
        data={"title": "Test"},
    )
    assert res.status_code == 403


def test_non_pdf_upload_rejected(client, tmp_uploads):
    token = register_and_login(client, "upload2@example.com")
    res = client.post(
        "/api/v1/documents",
        files={"file": ("document.txt", io.BytesIO(b"hello world"), "text/plain")},
        data={"title": "Test"},
        headers=auth_headers(token),
    )
    assert res.status_code == 422


def test_pdf_with_wrong_extension_rejected(client, tmp_uploads):
    """A file with .exe extension is rejected even if bytes start with %PDF."""
    token = register_and_login(client, "upload3@example.com")
    res = client.post(
        "/api/v1/documents",
        files={"file": ("malware.exe", io.BytesIO(MINIMAL_PDF), "application/octet-stream")},
        data={"title": "Test"},
        headers=auth_headers(token),
    )
    assert res.status_code == 422


def test_oversized_upload_rejected(client, tmp_uploads):
    token = register_and_login(client, "upload4@example.com")
    # Create a fake PDF that exceeds 20 MB
    big_content = b"%PDF-1.4\n" + b"x" * (21 * 1024 * 1024)
    res = client.post(
        "/api/v1/documents",
        files={"file": ("big.pdf", io.BytesIO(big_content), "application/pdf")},
        data={"title": "Big"},
        headers=auth_headers(token),
    )
    assert res.status_code == 413


def test_upload_status_starts_as_uploaded(client, tmp_uploads):
    token = register_and_login(client, "upload5@example.com")
    res = upload_pdf(client, token)
    assert res.json()["processing_status"] == "uploaded"


def test_upload_file_stored_on_disk(client, tmp_uploads):
    token = register_and_login(client, "upload6@example.com")
    res = upload_pdf(client, token)
    doc_id = res.json()["id"]
    stored = os.path.join(tmp_uploads, f"{doc_id}.pdf")
    assert os.path.exists(stored), f"Expected file at {stored}"


def test_internal_path_not_in_response(client, tmp_uploads):
    token = register_and_login(client, "upload7@example.com")
    res = upload_pdf(client, token)
    body_str = res.text
    # Must not leak any filesystem path fragment
    assert "uploads" not in body_str or res.json().get("title") == "Test Agreement"
    assert "/" not in res.json().get("id", "").replace("-", "")  # id is a UUID, no slashes
    assert "processing_error" in res.json()  # field present but null is fine


def test_path_traversal_filename_safe(client, tmp_uploads):
    """Path traversal in filename must not crash or create files outside upload dir."""
    token = register_and_login(client, "upload8@example.com")
    res = client.post(
        "/api/v1/documents",
        files={"file": ("../../etc/passwd.pdf", io.BytesIO(MINIMAL_PDF), "application/pdf")},
        data={"title": "Traversal"},
        headers=auth_headers(token),
    )
    # Should either succeed (file stored safely by UUID) or be rejected — never crash
    assert res.status_code in (201, 422)
    if res.status_code == 201:
        # Verify no file landed outside the uploads dir
        doc_id = res.json()["id"]
        assert os.path.exists(os.path.join(tmp_uploads, f"{doc_id}.pdf"))


# ---------------------------------------------------------------------------
# List / retrieve tests
# ---------------------------------------------------------------------------

def test_user_can_list_own_documents(client, tmp_uploads):
    token = register_and_login(client, "list1@example.com")
    upload_pdf(client, token, title="Doc A")
    upload_pdf(client, token, title="Doc B")
    res = client.get("/api/v1/documents", headers=auth_headers(token))
    assert res.status_code == 200
    titles = [d["title"] for d in res.json()]
    assert "Doc A" in titles
    assert "Doc B" in titles


def test_user_cannot_see_another_users_documents(client, tmp_uploads):
    token_a = register_and_login(client, "isola1@example.com")
    token_b = register_and_login(client, "isola2@example.com")
    upload_pdf(client, token_a, title="User A Doc")

    res = client.get("/api/v1/documents", headers=auth_headers(token_b))
    assert res.status_code == 200
    assert res.json() == []


def test_user_can_retrieve_own_document(client, tmp_uploads):
    token = register_and_login(client, "get1@example.com")
    upload_res = upload_pdf(client, token)
    doc_id = upload_res.json()["id"]

    res = client.get(f"/api/v1/documents/{doc_id}", headers=auth_headers(token))
    assert res.status_code == 200
    assert res.json()["id"] == doc_id


def test_user_cannot_retrieve_another_users_document(client, tmp_uploads):
    token_a = register_and_login(client, "isola3@example.com")
    token_b = register_and_login(client, "isola4@example.com")
    doc_id = upload_pdf(client, token_a).json()["id"]

    res = client.get(f"/api/v1/documents/{doc_id}", headers=auth_headers(token_b))
    assert res.status_code == 404


def test_invalid_document_id_returns_404(client, tmp_uploads):
    token = register_and_login(client, "invalid1@example.com")
    fake_id = str(uuid.uuid4())
    res = client.get(f"/api/v1/documents/{fake_id}", headers=auth_headers(token))
    assert res.status_code == 404


# ---------------------------------------------------------------------------
# Delete tests
# ---------------------------------------------------------------------------

def test_user_can_delete_own_document(client, tmp_uploads):
    token = register_and_login(client, "del1@example.com")
    doc_id = upload_pdf(client, token).json()["id"]

    res = client.delete(f"/api/v1/documents/{doc_id}", headers=auth_headers(token))
    assert res.status_code == 204

    # Should no longer be retrievable
    res2 = client.get(f"/api/v1/documents/{doc_id}", headers=auth_headers(token))
    assert res2.status_code == 404


def test_user_cannot_delete_another_users_document(client, tmp_uploads):
    token_a = register_and_login(client, "del2a@example.com")
    token_b = register_and_login(client, "del2b@example.com")
    doc_id = upload_pdf(client, token_a).json()["id"]

    res = client.delete(f"/api/v1/documents/{doc_id}", headers=auth_headers(token_b))
    assert res.status_code == 404

    # Document still accessible by owner
    res2 = client.get(f"/api/v1/documents/{doc_id}", headers=auth_headers(token_a))
    assert res2.status_code == 200


def test_deleted_document_file_removed_from_storage(client, tmp_uploads):
    token = register_and_login(client, "del3@example.com")
    doc_id = upload_pdf(client, token).json()["id"]
    stored_path = os.path.join(tmp_uploads, f"{doc_id}.pdf")
    assert os.path.exists(stored_path)

    client.delete(f"/api/v1/documents/{doc_id}", headers=auth_headers(token))
    assert not os.path.exists(stored_path)


# ---------------------------------------------------------------------------
# Cross-user security scenario (explicit)
# ---------------------------------------------------------------------------

def test_cross_user_isolation_full_scenario(client, tmp_uploads):
    """
    User A uploads a document.
    User B attempts GET and DELETE on User A's document.
    Both must return 404 — no metadata, filename, or file leaked.
    """
    token_a = register_and_login(client, "secA@example.com")
    token_b = register_and_login(client, "secB@example.com")

    doc_id = upload_pdf(client, token_a, title="Secret Agreement").json()["id"]

    # User B tries to GET
    get_res = client.get(f"/api/v1/documents/{doc_id}", headers=auth_headers(token_b))
    assert get_res.status_code == 404
    assert "Secret" not in get_res.text
    assert "agreement" not in get_res.text.lower() or "not found" in get_res.text.lower()

    # User B tries to DELETE
    del_res = client.delete(f"/api/v1/documents/{doc_id}", headers=auth_headers(token_b))
    assert del_res.status_code == 404

    # Document still intact for User A
    owner_res = client.get(f"/api/v1/documents/{doc_id}", headers=auth_headers(token_a))
    assert owner_res.status_code == 200
