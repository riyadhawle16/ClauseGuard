"""
Processing service — orchestrates the full Phase 4 pipeline:
  load PDF → extract text → extract clauses → store → update status

Reprocessing decision:
  Option B (replace): if a document already has clauses, delete them all
  before inserting the new batch. This prevents duplicates while allowing
  re-processing if a document was uploaded incorrectly.
  Documents with status 'processing' are rejected to avoid concurrent runs.
"""
import logging
from sqlalchemy.orm import Session
from fastapi import HTTPException, status as http_status

from app.repositories.document_repo import get_document_by_id, update_processing_status
from app.repositories.clause_repo import (
    delete_clauses_by_document,
    create_clauses_bulk,
    count_clauses_by_document,
)
from app.services import storage_service
from app.services.pdf_service import extract_text_by_page, ExtractionError
from app.services.clause_service import extract_clauses, build_clause_records

logger = logging.getLogger(__name__)


def process_document(db: Session, document_id: str, user_id: str) -> dict:
    """
    Run the full processing pipeline for a document owned by user_id.

    Returns a dict with processing results on success.
    Raises HTTPException on ownership/state errors.
    Updates document status to 'processing' → 'ready' (or 'failed').
    """
    # 1. Ownership check — 404 hides other users' documents
    doc = get_document_by_id(db, document_id, user_id)
    if not doc:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # 2. Guard against concurrent processing
    if doc.processing_status == "processing":
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail="Document is already being processed",
        )

    # 3. Mark as processing
    update_processing_status(db, document_id, "processing")

    try:
        # 4. Load PDF bytes from storage
        try:
            file_bytes = storage_service.load_upload(document_id)
        except FileNotFoundError:
            raise ExtractionError("Stored PDF file not found — the upload may be incomplete.")

        # 5. Extract text page by page (raises ExtractionError on failure)
        pages = extract_text_by_page(file_bytes)

        # 6. Extract structured clauses
        clause_data = extract_clauses(pages, document_id)

        if not clause_data:
            raise ExtractionError("No clauses could be extracted from this document.")

        # 7. Delete any existing clauses (reprocessing safety — Option B)
        deleted = delete_clauses_by_document(db, document_id)
        if deleted:
            logger.info("Reprocessing: deleted %d existing clause(s) for document %s", deleted, document_id)

        # 8. Build and bulk-insert Clause ORM records
        records = build_clause_records(clause_data)
        create_clauses_bulk(db, records)

        # 9. Mark as ready
        update_processing_status(db, document_id, "ready")

        return {
            "document_id": document_id,
            "status": "ready",
            "pages_extracted": len(pages),
            "clauses_extracted": len(records),
        }

    except ExtractionError as exc:
        # Safe user-facing error — no stack trace, no internal path
        safe_message = str(exc)
        logger.warning("Extraction failed for document %s: %s", document_id, safe_message)
        update_processing_status(db, document_id, "failed", error=safe_message)
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=safe_message,
        )
    except Exception as exc:
        # Unexpected error — log full details but return a generic message
        logger.exception("Unexpected processing error for document %s", document_id)
        update_processing_status(
            db, document_id, "failed",
            error="An unexpected error occurred during processing."
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Document processing failed. Please try again.",
        )
