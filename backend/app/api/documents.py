from fastapi import APIRouter, Depends, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from typing import List

from app.dependencies import get_db, get_current_user
from app.schemas.document import DocumentResponse
from app.services.document_service import (
    upload_document,
    get_document,
    list_documents,
    remove_document,
)

router = APIRouter(prefix="/documents", tags=["documents"])


def _doc_to_response(doc) -> DocumentResponse:
    return DocumentResponse(
        id=str(doc.id),
        title=doc.title,
        original_filename=doc.original_filename,
        processing_status=doc.processing_status,
        processing_error=doc.processing_error,
        created_at=doc.created_at.isoformat(),
        updated_at=doc.updated_at.isoformat(),
    )


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


@router.get("", response_model=List[DocumentResponse])
def list_user_documents(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List all documents belonging to the authenticated user."""
    docs = list_documents(db, str(current_user.id))
    return [_doc_to_response(d) for d in docs]


@router.get("/{document_id}", response_model=DocumentResponse)
def get_user_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Retrieve a single document — 404 if not owned by the authenticated user."""
    doc = get_document(db, document_id, str(current_user.id))
    return _doc_to_response(doc)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a document and its stored file — 404 if not owned by the authenticated user."""
    remove_document(db, document_id, str(current_user.id))
