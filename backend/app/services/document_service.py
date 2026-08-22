"""
Document service — orchestrates upload validation, DB record creation,
and file storage. Keeps the API layer thin.
"""
from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.document import Document
from app.repositories.document_repo import (
    create_document,
    get_document_by_id,
    list_documents_by_user,
    delete_document,
)
from app.services import storage_service
from app.utils.pdf_validator import validate_pdf
from app.config import get_settings

settings = get_settings()


def upload_document(
    db: Session,
    user_id: str,
    title: str,
    original_filename: str,
    file_bytes: bytes,
) -> Document:
    """
    Validate the PDF, persist it to storage, and create the DB record.
    processing_status is set to 'uploaded' — no processing happens in Phase 3.
    """
    # Validate before touching the DB or filesystem
    validate_pdf(file_bytes, original_filename, settings.MAX_FILE_SIZE_MB)

    # Create DB record first to obtain the document UUID
    doc = create_document(
        db=db,
        user_id=user_id,
        title=title,
        original_filename=original_filename,
    )

    # Store file using safe UUID-based name — never the original filename
    try:
        storage_service.save_upload(str(doc.id), file_bytes)
    except Exception as exc:
        # Roll back the DB record if storage fails
        db.delete(doc)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store the uploaded file",
        ) from exc

    return doc


def get_document(db: Session, doc_id: str, user_id: str) -> Document:
    """Return document owned by user or raise 404."""
    doc = get_document_by_id(db, doc_id, user_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return doc


def list_documents(db: Session, user_id: str) -> List[Document]:
    return list_documents_by_user(db, user_id)


def remove_document(db: Session, doc_id: str, user_id: str) -> None:
    """Delete document record, its stored file, and its Chroma vectors. Raises 404 if not owned."""
    doc = get_document_by_id(db, doc_id, user_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    # Remove stored PDF (best-effort)
    storage_service.delete_upload(str(doc.id))

    # Remove Chroma vectors (best-effort — don't fail delete if Chroma is unavailable)
    try:
        from app.services.indexing_service import delete_document_index
        delete_document_index(str(doc.id))
    except Exception:
        import logging
        logging.getLogger(__name__).warning(
            "Could not remove Chroma vectors for document %s during deletion", doc.id
        )

    # Remove chat sessions and messages for this document (best-effort)
    try:
        from app.models.chat import ChatSession, ChatMessage
        sessions = db.query(ChatSession).filter(ChatSession.document_id == str(doc.id)).all()
        for s in sessions:
            db.query(ChatMessage).filter(ChatMessage.session_id == str(s.id)).delete(synchronize_session=False)
            db.delete(s)
        db.commit()
    except Exception:
        import logging
        logging.getLogger(__name__).warning(
            "Could not remove chat sessions for document %s during deletion", doc.id
        )

    # Remove DB record
    delete_document(db, doc_id, user_id)
