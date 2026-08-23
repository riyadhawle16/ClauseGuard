"""
Processing service — orchestrates the full Phase 4+5 pipeline:
  load PDF → extract text → extract clauses → store in PostgreSQL
           → generate embeddings → store in Chroma → mark ready
"""
import logging
import sys
import traceback
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status as http_status

from app.database import SessionLocal
from app.repositories.document_repo import get_document_by_id, update_processing_status
from app.repositories.clause_repo import (
    delete_clauses_by_document,
    create_clauses_bulk,
    get_clauses_by_document,
)
from app.services import storage_service
from app.services.pdf_service import extract_text_by_page, ExtractionError
from app.services.clause_service import extract_clauses, build_clause_records
from app.services.indexing_service import index_clauses, delete_document_index

logger = logging.getLogger(__name__)


def process_document(
    db: Session,
    document_id: str,
    user_id: str,
    chroma_persist_directory: Optional[str] = None,
) -> dict:
    """
    Run the full processing pipeline for a document owned by user_id.

    chroma_persist_directory:
      - None  → use the configured production Chroma directory
      - ""    → in-memory EphemeralClient (for tests)
      - <path> → custom path (for tests with tmp_path)

    Returns a dict with processing results on success.
    Raises HTTPException on ownership/state errors.
    Updates document status: processing → ready (or failed).
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
        # 4. Load PDF bytes
        try:
            file_bytes = storage_service.load_upload(document_id)
        except FileNotFoundError:
            raise ExtractionError("Stored PDF file not found — the upload may be incomplete.")

        # 5. Extract text (raises ExtractionError on empty/invalid PDF)
        pages = extract_text_by_page(file_bytes)

        # 6. Extract structured clauses
        clause_data = extract_clauses(pages, document_id)
        if not clause_data:
            raise ExtractionError("No clauses could be extracted from this document.")

        # 7. Delete old PostgreSQL clauses (reprocessing safety)
        deleted_pg = delete_clauses_by_document(db, document_id)
        if deleted_pg:
            logger.info("Reprocessing: deleted %d clause(s) from PG for doc %s", deleted_pg, document_id)

        # 8. Delete old Chroma vectors (reprocessing safety)
        try:
            delete_document_index(document_id, chroma_persist_directory)
        except Exception:
            logger.warning("Could not clean old vectors for doc %s before reprocessing", document_id)

        # 9. Insert new clauses into PostgreSQL
        records = build_clause_records(clause_data)
        create_clauses_bulk(db, records)

        # 10. Index clauses into Chroma — if this fails, document is marked failed
        #     but PostgreSQL clauses are kept for debugging/reprocessing.
        try:
            clauses_from_db = get_clauses_by_document(db, document_id)
            indexed = index_clauses(
                clauses_from_db,
                document_id,
                persist_directory=chroma_persist_directory,
            )
        except Exception as idx_exc:
            logger.exception("Chroma indexing failed for document %s", document_id)
            # Clean up any partial vectors
            try:
                delete_document_index(document_id, chroma_persist_directory)
            except Exception:
                pass
            raise ExtractionError(
                "Document text was extracted but could not be indexed for search. "
                "Please try processing again."
            ) from idx_exc

        # 11. Mark as ready
        update_processing_status(db, document_id, "ready")

        return {
            "document_id": document_id,
            "status": "ready",
            "pages_extracted": len(pages),
            "clauses_extracted": len(records),
            "vectors_indexed": indexed,
        }

    except ExtractionError as exc:
        safe_message = str(exc)
        logger.warning("Processing failed for document %s: %s", document_id, safe_message)
        update_processing_status(db, document_id, "failed", error=safe_message)
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=safe_message,
        )
    except Exception:
        traceback.print_exc(file=sys.stderr)
        logger.exception("Unexpected error processing document %s", document_id)
        update_processing_status(
            db, document_id, "failed",
            error="An unexpected error occurred during processing.",
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Document processing failed. Please try again.",
        )


def run_processing_job(
    document_id: str,
    user_id: str,
    chroma_persist_directory: Optional[str] = None,
) -> None:
    """
    Background worker entry point. Opens its own DB session so the HTTP
    request can return immediately while processing continues.
    """
    db = SessionLocal()
    try:
        process_document(db, document_id, user_id, chroma_persist_directory)
    except HTTPException as exc:
        logger.warning(
            "Processing job for document %s finished with HTTP %s: %s",
            document_id,
            exc.status_code,
            exc.detail,
        )
    except Exception:
        traceback.print_exc(file=sys.stderr)
        logger.exception("Background processing job crashed for document %s", document_id)
        try:
            update_processing_status(
                db,
                document_id,
                "failed",
                error="An unexpected error occurred during processing.",
            )
        except Exception:
            logger.exception("Could not mark document %s as failed", document_id)
    finally:
        db.close()
