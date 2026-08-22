from fastapi import APIRouter, Depends, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from typing import List

from app.dependencies import get_db, get_current_user
from app.schemas.document import DocumentResponse, ClauseResponse, ProcessingResult
from app.services.document_service import (
    upload_document,
    get_document,
    list_documents,
    remove_document,
)
from app.services.processing_service import process_document
from app.repositories.clause_repo import (
    get_clauses_by_document,
    count_clauses_by_document,
)
from app.repositories.document_repo import get_document_by_id

router = APIRouter(prefix="/documents", tags=["documents"])


def _doc_to_response(doc, clause_count: int = None) -> DocumentResponse:
    return DocumentResponse(
        id=str(doc.id),
        title=doc.title,
        original_filename=doc.original_filename,
        processing_status=doc.processing_status,
        processing_error=doc.processing_error,
        clause_count=clause_count,
        created_at=doc.created_at.isoformat(),
        updated_at=doc.updated_at.isoformat(),
    )


# ── Upload ────────────────────────────────────────────────────────────────────

@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload(
    file: UploadFile = File(...),
    title: str = Form(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Upload a PDF rental agreement."""
    file_bytes = await file.read()
    doc = upload_document(
        db=db,
        user_id=str(current_user.id),
        title=title,
        original_filename=file.filename or "document.pdf",
        file_bytes=file_bytes,
    )
    return _doc_to_response(doc)


# ── List ──────────────────────────────────────────────────────────────────────

@router.get("", response_model=List[DocumentResponse])
def list_user_documents(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List all documents belonging to the authenticated user."""
    docs = list_documents(db, str(current_user.id))
    return [_doc_to_response(d) for d in docs]


# ── Retrieve ──────────────────────────────────────────────────────────────────

@router.get("/{document_id}", response_model=DocumentResponse)
def get_user_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Retrieve a single document — 404 if not owned by the authenticated user."""
    doc = get_document(db, document_id, str(current_user.id))
    clause_count = count_clauses_by_document(db, document_id)
    return _doc_to_response(doc, clause_count=clause_count)


# ── Delete ────────────────────────────────────────────────────────────────────

@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a document and its stored file — 404 if not owned by the authenticated user."""
    remove_document(db, document_id, str(current_user.id))


# ── Process ───────────────────────────────────────────────────────────────────

@router.post("/{document_id}/process", response_model=ProcessingResult)
def trigger_processing(
    document_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Process an uploaded PDF — extract text and clauses.
    Ownership enforced: returns 404 for cross-user access.
    Reprocessing replaces existing clauses (no duplicates).
    """
    result = process_document(db, document_id, str(current_user.id))
    return ProcessingResult(**result)


# ── Clauses ───────────────────────────────────────────────────────────────────

@router.get("/{document_id}/clauses", response_model=List[ClauseResponse])
def get_document_clauses(
    document_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Return all extracted clauses for a document.
    Ownership enforced: returns 404 for cross-user access.
    """
    # Ownership check
    doc = get_document_by_id(db, document_id, str(current_user.id))
    if not doc:
        from fastapi import HTTPException
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    clauses = get_clauses_by_document(db, document_id)
    return [
        ClauseResponse(
            id=str(c.id),
            clause_number=c.clause_number,
            heading=c.heading,
            content=c.content,
            page_number=c.page_number,
        )
        for c in clauses
    ]
