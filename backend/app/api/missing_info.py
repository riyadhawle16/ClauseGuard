"""
Missing Information API — Phase 8.

POST /api/v1/documents/{document_id}/analyze-missing-info
  Run missing-information analysis. Idempotent.

GET /api/v1/documents/{document_id}/missing-info
  Retrieve stored analysis results.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user
from app.repositories.document_repo import get_document_by_id
from app.repositories.clause_repo import get_clauses_by_document
from app.repositories.missing_info_repo import get_flags_by_document
from app.services.missing_info_service import run_missing_info_analysis
from app.schemas.missing_info import MissingInfoFlagResponse, MissingInfoAnalysisResponse
from app.rules.missing_info_rules import PRESENT, UNCLEAR, NOT_IDENTIFIED

logger = logging.getLogger(__name__)
router = APIRouter(tags=["missing-info"])


def _build_response(document_id: str, flags, clauses_map: dict) -> MissingInfoAnalysisResponse:
    flag_responses = []
    for f in flags:
        clause = clauses_map.get(str(f.evidence_clause_id)) if f.evidence_clause_id else None
        flag_responses.append(MissingInfoFlagResponse(
            id=str(f.id),
            category=f.category,
            category_name=f.category_name,
            status=f.status,
            explanation=f.explanation,
            evidence_clause_id=str(f.evidence_clause_id) if f.evidence_clause_id else None,
            evidence_clause_number=clause.clause_number if clause else None,
            evidence_page_number=f.evidence_page_number,
            detection_method=f.detection_method,
        ))

    present_count = sum(1 for f in flags if f.status == PRESENT)
    unclear_count = sum(1 for f in flags if f.status == UNCLEAR)
    not_identified_count = sum(1 for f in flags if f.status == NOT_IDENTIFIED)

    return MissingInfoAnalysisResponse(
        document_id=document_id,
        total_categories=len(flags),
        present_count=present_count,
        unclear_count=unclear_count,
        not_identified_count=not_identified_count,
        flags=flag_responses,
    )


@router.post(
    "/documents/{document_id}/analyze-missing-info",
    response_model=MissingInfoAnalysisResponse,
)
def analyze_missing_info(
    document_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Run missing-information analysis on a processed document.
    - Requires authentication and document ownership.
    - Document must be 'ready'.
    - Idempotent: running twice replaces previous results.
    - Does NOT provide legal advice.
    """
    doc = get_document_by_id(db, document_id, str(current_user.id))
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    if doc.processing_status != "ready":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Document is not ready. Please process it first.",
        )

    try:
        flags = run_missing_info_analysis(db, document_id)
    except Exception:
        logger.exception("Missing-info analysis failed for document %s", document_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Analysis failed. Please try again.",
        )

    clauses_map = {str(c.id): c for c in get_clauses_by_document(db, document_id)}
    return _build_response(document_id, flags, clauses_map)


@router.get(
    "/documents/{document_id}/missing-info",
    response_model=MissingInfoAnalysisResponse,
)
def get_missing_info(
    document_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Retrieve stored missing-information analysis for a document.
    - Requires authentication and document ownership.
    - Returns 404 for cross-user access.
    - Returns 409 if document is not ready.
    """
    doc = get_document_by_id(db, document_id, str(current_user.id))
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    if doc.processing_status != "ready":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Document is not ready.",
        )

    flags = get_flags_by_document(db, document_id)
    clauses_map = {str(c.id): c for c in get_clauses_by_document(db, document_id)}
    return _build_response(document_id, flags, clauses_map)
