"""
Attention Analysis API — Phase 7.

POST /api/v1/documents/{document_id}/analyze-attention
  Run attention analysis (deterministic + optional LLM).
  Idempotent — safe to run multiple times.

GET /api/v1/documents/{document_id}/attention
  Retrieve stored attention flags for the document.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user
from app.repositories.document_repo import get_document_by_id
from app.repositories.clause_repo import (
    get_clauses_by_document,
    count_clauses_by_document,
)
from app.repositories.attention_flag_repo import get_flags_by_document
from app.services.attention_service import run_attention_analysis
from app.schemas.attention import AttentionFlagResponse, AttentionAnalysisResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["attention"])


def _flag_to_response(flag, clauses_map: dict) -> AttentionFlagResponse:
    clause = clauses_map.get(str(flag.clause_id))
    return AttentionFlagResponse(
        id=str(flag.id),
        clause_id=str(flag.clause_id),
        clause_number=clause.clause_number if clause else None,
        clause_page=clause.page_number if clause else None,
        category=flag.category,
        category_name=flag.category_name,
        title=flag.title,
        explanation=flag.explanation,
        matched_text=flag.matched_text,
        severity=flag.severity,
        confidence=flag.confidence,
        detection_method=flag.detection_method,
    )


@router.post(
    "/documents/{document_id}/analyze-attention",
    response_model=AttentionAnalysisResponse,
)
def analyze_attention(
    document_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Run attention analysis on a processed document.
    - Requires authentication and document ownership.
    - Document must be in 'ready' status.
    - Idempotent: running twice replaces previous flags (no duplicates).
    - Does NOT generate legal advice or legal verdicts.
    """
    doc = get_document_by_id(db, document_id, str(current_user.id))
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    if doc.processing_status != "ready":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Document is not ready. Please process it first.",
        )

    total_clauses = count_clauses_by_document(db, document_id)

    try:
        flags = run_attention_analysis(db, document_id)
    except Exception:
        logger.exception("Attention analysis failed for document %s", document_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Attention analysis failed. Please try again.",
        )

    clauses_map = {
        str(c.id): c for c in get_clauses_by_document(db, document_id)
    }
    categories_found = list({f.category for f in flags})
    flag_responses = [_flag_to_response(f, clauses_map) for f in flags]

    return AttentionAnalysisResponse(
        document_id=document_id,
        total_clauses=total_clauses,
        flags_found=len(flags),
        categories_found=categories_found,
        flags=flag_responses,
    )


@router.get(
    "/documents/{document_id}/attention",
    response_model=AttentionAnalysisResponse,
)
def get_attention(
    document_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Retrieve stored attention flags for a document.
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

    total_clauses = count_clauses_by_document(db, document_id)
    flags = get_flags_by_document(db, document_id)
    clauses_map = {
        str(c.id): c for c in get_clauses_by_document(db, document_id)
    }
    categories_found = list({f.category for f in flags})
    flag_responses = [_flag_to_response(f, clauses_map) for f in flags]

    return AttentionAnalysisResponse(
        document_id=document_id,
        total_clauses=total_clauses,
        flags_found=len(flags),
        categories_found=categories_found,
        flags=flag_responses,
    )
