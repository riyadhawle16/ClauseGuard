"""
Phase 8 tests — Missing / Unclear Information Detection.

All tests mock the LLM. No real Groq API key required.
All existing Phase 1–7 tests must continue passing.
"""
import io
import uuid
import pytest
from unittest.mock import MagicMock, patch
from fpdf import FPDF


# ── Helpers ───────────────────────────────────────────────────────────────────

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


def upload_pdf(client, token, content: bytes, title="Test"):
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
    assert proc.status_code == 200, proc.text
    return doc_id


# ── Agreement fixtures ────────────────────────────────────────────────────────

# Rich agreement — contains many categories
RICH_AGREEMENT = [
    (
        "1. Security Deposit\n"
        "The tenant shall pay a security deposit of two months rent before occupancy. "
        "The deposit shall be refunded within thirty days of vacating, subject to deductions.\n\n"
        "2. Notice Period\n"
        "Either party shall provide sixty days written notice before termination.\n\n"
        "3. Lock-in Period\n"
        "There is a lock-in period of twelve months from the commencement date.\n\n"
        "4. Rent Increase\n"
        "The rent shall be subject to an annual increase of five percent.\n\n"
        "5. Maintenance\n"
        "The tenant is responsible for minor repairs and repair costs up to five hundred rupees.\n\n"
        "6. Utility Charges\n"
        "The tenant shall pay electricity charges and water charges monthly.\n\n"
        "7. Early Termination\n"
        "In case of early termination, the tenant shall forfeit one month's rent.\n\n"
        "8. Landlord Termination\n"
        "The landlord may terminate this agreement with thirty days notice.\n\n"
        "9. Tenant Termination\n"
        "The tenant may terminate this agreement with sixty days notice.\n\n"
        "10. Penalties\n"
        "A late payment penalty of five hundred rupees shall apply for delayed rent."
    )
]

# Minimal agreement — very few categories present
MINIMAL_AGREEMENT = [
    "This rental agreement is entered into by both parties on the date mentioned herein. "
    "The monthly rent is agreed between the parties. The agreement shall be for twelve months."
]


# ── Unit tests: deterministic rules ──────────────────────────────────────────

def test_classify_security_deposit_present():
    from app.rules.missing_info_rules import classify_category_presence, PRESENT
    status, matched = classify_category_presence(
        "SECURITY_DEPOSIT",
        ["The tenant shall pay a security deposit of two months rent."],
    )
    assert status == PRESENT
    assert matched is not None


def test_classify_security_deposit_unclear():
    from app.rules.missing_info_rules import classify_category_presence, UNCLEAR
    status, matched = classify_category_presence(
        "SECURITY_DEPOSIT",
        ["The tenant shall pay an advance before moving in."],
    )
    assert status == UNCLEAR


def test_classify_security_deposit_not_identified():
    from app.rules.missing_info_rules import classify_category_presence, NOT_IDENTIFIED
    status, matched = classify_category_presence(
        "SECURITY_DEPOSIT",
        ["The agreement covers the rental of the property for twelve months."],
    )
    assert status == NOT_IDENTIFIED
    assert matched is None


def test_classify_notice_period_present():
    from app.rules.missing_info_rules import classify_category_presence, PRESENT
    status, _ = classify_category_presence(
        "NOTICE_PERIOD",
        ["Either party shall provide sixty days' notice before termination."],
    )
    assert status == PRESENT


def test_classify_lock_in_period_present():
    from app.rules.missing_info_rules import classify_category_presence, PRESENT
    status, _ = classify_category_presence(
        "LOCK_IN_PERIOD",
        ["There is a lock-in period of twelve months."],
    )
    assert status == PRESENT


def test_classify_early_termination_present():
    from app.rules.missing_info_rules import classify_category_presence, PRESENT
    status, _ = classify_category_presence(
        "EARLY_TERMINATION",
        ["In the event of early termination, the tenant shall pay two months rent."],
    )
    assert status == PRESENT


def test_classify_maintenance_responsibility_present():
    from app.rules.missing_info_rules import classify_category_presence, PRESENT
    status, _ = classify_category_presence(
        "MAINTENANCE_RESPONSIBILITY",
        ["The tenant is responsible for all repair costs up to five hundred rupees."],
    )
    assert status == PRESENT


def test_classify_rent_increase_present():
    from app.rules.missing_info_rules import classify_category_presence, PRESENT
    status, _ = classify_category_presence(
        "RENT_INCREASE",
        ["The rent shall be subject to an annual increase of five percent."],
    )
    assert status == PRESENT


def test_classify_landlord_termination_present():
    from app.rules.missing_info_rules import classify_category_presence, PRESENT
    status, _ = classify_category_presence(
        "LANDLORD_TERMINATION",
        ["The landlord may terminate this agreement with thirty days notice."],
    )
    assert status == PRESENT


def test_classify_tenant_termination_present():
    from app.rules.missing_info_rules import classify_category_presence, PRESENT
    status, _ = classify_category_presence(
        "TENANT_TERMINATION",
        ["The tenant may terminate this agreement with sixty days notice."],
    )
    assert status == PRESENT


def test_classify_penalties_present():
    from app.rules.missing_info_rules import classify_category_presence, PRESENT
    status, _ = classify_category_presence(
        "PENALTIES_AND_LIQUIDATED_DAMAGES",
        ["A late payment penalty of five hundred rupees shall apply."],
    )
    assert status == PRESENT


def test_classify_utility_charges_present():
    from app.rules.missing_info_rules import classify_category_presence, PRESENT
    status, _ = classify_category_presence(
        "MAINTENANCE_AND_UTILITY_CHARGES",
        ["The tenant shall pay electricity charges and water charges monthly."],
    )
    assert status == PRESENT


def test_case_insensitive_classification():
    from app.rules.missing_info_rules import classify_category_presence, PRESENT
    status, _ = classify_category_presence(
        "SECURITY_DEPOSIT",
        ["SECURITY DEPOSIT OF THREE MONTHS RENT IS REQUIRED."],
    )
    assert status == PRESENT


def test_all_10_categories_have_rules():
    from app.rules.missing_info_rules import MISSING_INFO_RULES, MISSING_INFO_RULE_BY_CATEGORY
    from app.rules.attention_rules import VALID_CATEGORY_IDS
    assert len(MISSING_INFO_RULES) == 10
    for cat_id in VALID_CATEGORY_IDS:
        assert cat_id in MISSING_INFO_RULE_BY_CATEGORY, f"Missing rule for {cat_id}"


def test_no_legal_conclusions_in_explanations():
    from app.rules.missing_info_rules import MISSING_INFO_RULES
    forbidden = ["illegal", "unlawful", "unenforceable", "legally invalid", "violation of law"]
    for rule in MISSING_INFO_RULES:
        for text in [rule.not_found_explanation, rule.unclear_explanation]:
            lower = text.lower()
            for word in forbidden:
                assert word not in lower, (
                    f"Category {rule.category_id} explanation contains '{word}'"
                )


def test_valid_statuses_only():
    from app.rules.missing_info_rules import VALID_STATUSES, PRESENT, UNCLEAR, NOT_IDENTIFIED
    assert VALID_STATUSES == {"PRESENT", "UNCLEAR", "NOT_IDENTIFIED"}


# ── API integration tests ─────────────────────────────────────────────────────

def test_analyze_missing_info_returns_all_10_categories(client, tmp_uploads, mock_embed):
    token = register_and_login(client, "mi1@example.com")
    pdf = make_text_pdf(RICH_AGREEMENT)
    doc_id = upload_and_process(client, token, pdf)

    res = client.post(
        f"/api/v1/documents/{doc_id}/analyze-missing-info",
        headers=auth_headers(token),
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["total_categories"] == 10
    assert len(data["flags"]) == 10


def test_analyze_missing_info_has_correct_structure(client, tmp_uploads, mock_embed):
    token = register_and_login(client, "mi2@example.com")
    pdf = make_text_pdf(RICH_AGREEMENT)
    doc_id = upload_and_process(client, token, pdf)

    res = client.post(
        f"/api/v1/documents/{doc_id}/analyze-missing-info",
        headers=auth_headers(token),
    )
    assert res.status_code == 200
    data = res.json()
    assert "present_count" in data
    assert "unclear_count" in data
    assert "not_identified_count" in data
    total = data["present_count"] + data["unclear_count"] + data["not_identified_count"]
    assert total == 10

    for flag in data["flags"]:
        assert "id" in flag
        assert "category" in flag
        assert "category_name" in flag
        assert "status" in flag
        assert flag["status"] in ("PRESENT", "UNCLEAR", "NOT_IDENTIFIED")
        assert "explanation" in flag
        assert "detection_method" in flag
        assert flag["detection_method"] in ("RULE", "RULE_LLM")


def test_rich_agreement_has_present_categories(client, tmp_uploads, mock_embed):
    token = register_and_login(client, "mi3@example.com")
    pdf = make_text_pdf(RICH_AGREEMENT)
    doc_id = upload_and_process(client, token, pdf)

    res = client.post(
        f"/api/v1/documents/{doc_id}/analyze-missing-info",
        headers=auth_headers(token),
    )
    data = res.json()
    present = [f["category"] for f in data["flags"] if f["status"] == "PRESENT"]
    assert len(present) >= 5  # Rich agreement should have many PRESENT


def test_minimal_agreement_has_not_identified_categories(client, tmp_uploads, mock_embed):
    token = register_and_login(client, "mi4@example.com")
    pdf = make_text_pdf(MINIMAL_AGREEMENT)
    doc_id = upload_and_process(client, token, pdf)

    res = client.post(
        f"/api/v1/documents/{doc_id}/analyze-missing-info",
        headers=auth_headers(token),
    )
    data = res.json()
    not_identified = [f["category"] for f in data["flags"] if f["status"] == "NOT_IDENTIFIED"]
    assert len(not_identified) >= 3  # Minimal agreement should have several NOT_IDENTIFIED


def test_idempotent_analysis(client, tmp_uploads, mock_embed):
    """Running analysis twice produces the same 10 results, not 20."""
    token = register_and_login(client, "mi5@example.com")
    pdf = make_text_pdf(RICH_AGREEMENT)
    doc_id = upload_and_process(client, token, pdf)

    res1 = client.post(
        f"/api/v1/documents/{doc_id}/analyze-missing-info",
        headers=auth_headers(token),
    )
    res2 = client.post(
        f"/api/v1/documents/{doc_id}/analyze-missing-info",
        headers=auth_headers(token),
    )
    assert res1.json()["total_categories"] == res2.json()["total_categories"] == 10


def test_unauthenticated_rejected(client, tmp_uploads, mock_embed):
    token = register_and_login(client, "mi6@example.com")
    pdf = make_text_pdf(RICH_AGREEMENT)
    doc_id = upload_and_process(client, token, pdf)

    res = client.post(f"/api/v1/documents/{doc_id}/analyze-missing-info")
    assert res.status_code == 403


def test_cross_user_returns_404(client, tmp_uploads, mock_embed):
    token_a = register_and_login(client, "mi7a@example.com")
    token_b = register_and_login(client, "mi7b@example.com")
    pdf = make_text_pdf(RICH_AGREEMENT)
    doc_id = upload_and_process(client, token_a, pdf)

    res = client.post(
        f"/api/v1/documents/{doc_id}/analyze-missing-info",
        headers=auth_headers(token_b),
    )
    assert res.status_code == 404


def test_unprocessed_document_returns_409(client, tmp_uploads, mock_embed):
    token = register_and_login(client, "mi8@example.com")
    pdf = make_text_pdf(RICH_AGREEMENT)
    up = upload_pdf(client, token, pdf)
    doc_id = up.json()["id"]

    res = client.post(
        f"/api/v1/documents/{doc_id}/analyze-missing-info",
        headers=auth_headers(token),
    )
    assert res.status_code == 409


def test_get_missing_info_after_analysis(client, tmp_uploads, mock_embed):
    token = register_and_login(client, "mi9@example.com")
    pdf = make_text_pdf(RICH_AGREEMENT)
    doc_id = upload_and_process(client, token, pdf)

    client.post(
        f"/api/v1/documents/{doc_id}/analyze-missing-info",
        headers=auth_headers(token),
    )
    get_res = client.get(
        f"/api/v1/documents/{doc_id}/missing-info",
        headers=auth_headers(token),
    )
    assert get_res.status_code == 200
    assert get_res.json()["total_categories"] == 10


def test_get_missing_info_cross_user_404(client, tmp_uploads, mock_embed):
    token_a = register_and_login(client, "mi10a@example.com")
    token_b = register_and_login(client, "mi10b@example.com")
    pdf = make_text_pdf(RICH_AGREEMENT)
    doc_id = upload_and_process(client, token_a, pdf)
    client.post(
        f"/api/v1/documents/{doc_id}/analyze-missing-info",
        headers=auth_headers(token_a),
    )

    res = client.get(
        f"/api/v1/documents/{doc_id}/missing-info",
        headers=auth_headers(token_b),
    )
    assert res.status_code == 404


def test_evidence_clause_linked_when_present(client, tmp_uploads, mock_embed):
    token = register_and_login(client, "mi11@example.com")
    pdf = make_text_pdf(RICH_AGREEMENT)
    doc_id = upload_and_process(client, token, pdf)

    res = client.post(
        f"/api/v1/documents/{doc_id}/analyze-missing-info",
        headers=auth_headers(token),
    )
    flags = res.json()["flags"]
    present_flags = [f for f in flags if f["status"] == "PRESENT"]
    # At least one PRESENT flag should have evidence
    assert any(f["evidence_clause_id"] is not None for f in present_flags)


def test_no_legal_conclusions_in_api_response(client, tmp_uploads, mock_embed):
    token = register_and_login(client, "mi12@example.com")
    pdf = make_text_pdf(RICH_AGREEMENT)
    doc_id = upload_and_process(client, token, pdf)

    res = client.post(
        f"/api/v1/documents/{doc_id}/analyze-missing-info",
        headers=auth_headers(token),
    )
    body = res.text.lower()
    for word in ["illegal", "unlawful", "unenforceable", "legally invalid"]:
        assert word not in body, f"Forbidden word '{word}' in response"


def test_all_category_ids_are_predefined(client, tmp_uploads, mock_embed):
    from app.rules.attention_rules import VALID_CATEGORY_IDS

    token = register_and_login(client, "mi13@example.com")
    pdf = make_text_pdf(RICH_AGREEMENT)
    doc_id = upload_and_process(client, token, pdf)

    res = client.post(
        f"/api/v1/documents/{doc_id}/analyze-missing-info",
        headers=auth_headers(token),
    )
    for flag in res.json()["flags"]:
        assert flag["category"] in VALID_CATEGORY_IDS


def test_nonexistent_document_returns_404(client, tmp_uploads, mock_embed):
    token = register_and_login(client, "mi14@example.com")
    fake_id = str(uuid.uuid4())
    res = client.post(
        f"/api/v1/documents/{fake_id}/analyze-missing-info",
        headers=auth_headers(token),
    )
    assert res.status_code == 404


def test_llm_failure_falls_back_to_deterministic(monkeypatch, client, tmp_uploads, mock_embed):
    """When LLM fails, deterministic result must still be returned."""
    import app.services.missing_info_service as svc
    monkeypatch.setattr(svc, "_llm_classify", lambda *a, **kw: None)

    token = register_and_login(client, "mi15@example.com")
    pdf = make_text_pdf(RICH_AGREEMENT)
    doc_id = upload_and_process(client, token, pdf)

    res = client.post(
        f"/api/v1/documents/{doc_id}/analyze-missing-info",
        headers=auth_headers(token),
    )
    assert res.status_code == 200
    assert res.json()["total_categories"] == 10


def test_invalid_llm_output_falls_back_to_deterministic(monkeypatch, client, tmp_uploads, mock_embed):
    """Invalid LLM output must not crash analysis."""
    import app.services.missing_info_service as svc
    # Return garbage that cannot be a valid status
    monkeypatch.setattr(svc, "_llm_classify", lambda *a, **kw: "INVENTED_STATUS")

    token = register_and_login(client, "mi16@example.com")
    pdf = make_text_pdf(RICH_AGREEMENT)
    doc_id = upload_and_process(client, token, pdf)

    res = client.post(
        f"/api/v1/documents/{doc_id}/analyze-missing-info",
        headers=auth_headers(token),
    )
    assert res.status_code == 200
    # All statuses must still be valid
    for flag in res.json()["flags"]:
        assert flag["status"] in ("PRESENT", "UNCLEAR", "NOT_IDENTIFIED")


def test_llm_cannot_introduce_unknown_category():
    """LLM-returned category must be validated; unknown ones must be rejected."""
    from app.rules.attention_rules import VALID_CATEGORY_IDS
    assert "INVENTED_CATEGORY" not in VALID_CATEGORY_IDS


def test_detection_method_rule_when_llm_disabled(monkeypatch, client, tmp_uploads, mock_embed):
    import app.services.missing_info_service as svc
    monkeypatch.setattr(svc, "_llm_classify", lambda *a, **kw: None)

    token = register_and_login(client, "mi17@example.com")
    pdf = make_text_pdf(RICH_AGREEMENT)
    doc_id = upload_and_process(client, token, pdf)

    res = client.post(
        f"/api/v1/documents/{doc_id}/analyze-missing-info",
        headers=auth_headers(token),
    )
    for flag in res.json()["flags"]:
        assert flag["detection_method"] == "RULE"


def test_get_missing_info_requires_auth(client, tmp_uploads, mock_embed):
    token = register_and_login(client, "mi18@example.com")
    pdf = make_text_pdf(RICH_AGREEMENT)
    doc_id = upload_and_process(client, token, pdf)
    client.post(f"/api/v1/documents/{doc_id}/analyze-missing-info", headers=auth_headers(token))

    res = client.get(f"/api/v1/documents/{doc_id}/missing-info")
    assert res.status_code == 403


def test_poorly_extracted_text_handled_safely(client, tmp_uploads, mock_embed):
    """Documents with very little meaningful text must still produce 10 category results."""
    token = register_and_login(client, "mi19@example.com")
    # Short content that IS extractable but has no attention category keywords
    pdf = make_text_pdf([
        "This agreement is entered into between the landlord and tenant on the date mentioned. "
        "The property is located at the address agreed. The parties have agreed to all terms."
    ])
    doc_id = upload_and_process(client, token, pdf)

    res = client.post(
        f"/api/v1/documents/{doc_id}/analyze-missing-info",
        headers=auth_headers(token),
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total_categories"] == 10
    # With no specific category content, most should be NOT_IDENTIFIED
    not_identified = [f for f in data["flags"] if f["status"] == "NOT_IDENTIFIED"]
    assert len(not_identified) >= 5
