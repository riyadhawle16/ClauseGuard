from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.document import Document


def create_document(
    db: Session,
    user_id: str,
    title: str,
    original_filename: str,
) -> Document:
    doc = Document(
        user_id=str(user_id),
        title=title,
        original_filename=original_filename,
        processing_status="uploaded",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def get_document_by_id(db: Session, doc_id: str, user_id: str) -> Optional[Document]:
    """Return document only if it belongs to the requesting user."""
    return (
        db.query(Document)
        .filter(Document.id == str(doc_id), Document.user_id == str(user_id))
        .first()
    )


def list_documents_by_user(db: Session, user_id: str) -> List[Document]:
    return (
        db.query(Document)
        .filter(Document.user_id == str(user_id))
        .order_by(Document.created_at.desc())
        .all()
    )


def update_processing_status(
    db: Session,
    doc_id: str,
    status: str,
    error: Optional[str] = None,
) -> Optional[Document]:
    doc = db.query(Document).filter(Document.id == str(doc_id)).first()
    if doc:
        doc.processing_status = status
        if error is not None:
            doc.processing_error = error
        db.commit()
        db.refresh(doc)
    return doc


def delete_document(db: Session, doc_id: str, user_id: str) -> bool:
    """Delete document only if it belongs to the requesting user. Returns True if deleted."""
    doc = get_document_by_id(db, doc_id, user_id)
    if not doc:
        return False
    db.delete(doc)
    db.commit()
    return True
