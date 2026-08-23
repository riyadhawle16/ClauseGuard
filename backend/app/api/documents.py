from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, File, Form, Query, status
from sqlalchemy.orm import Session
from typing import List

from app.dependencies import get_db, get_current_user
from app.schemas.document import DocumentResponse, ClauseResponse, ProcessingResult, SearchResult
from app.services.document_service import (
    upload_document,
    get_document,
    list_documents,
    remove_document,
)
from app.services.processing_service import run_processing_job
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
    docs = list_documents(db, str(current_user.id))
    return [_doc_to_response(d) for d in docs]


# ── Retrieve ──────────────────────────────────────────────────────────────────

@router.get("/{document_id}", response_model=DocumentResponse)
def get_user_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
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
    remove_document(db, document_id, str(current_user.id))


# ── Process ───────────────────────────────────────────────────────────────────

@router.post("/{document_id}/process", response_model=ProcessingResult)
def trigger_processing(
    document_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Start PDF processing in the background.
    Returns immediately with status 'processing' — poll GET /documents/{id}
    until status becomes 'ready' or 'failed'.
    """
    user_id = str(current_user.id)
    doc = get_document_by_id(db, document_id, user_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    if doc.processing_status == "processing":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Document is already being processed",
        )

    background_tasks.add_task(run_processing_job, document_id, user_id)

    return ProcessingResult(
        document_id=document_id,
        status="processing",
        message="Processing started. Poll this document until status is ready or failed.",
    )


# ── Clauses ───────────────────────────────────────────────────────────────────

@router.get("/{document_id}/clauses", response_model=List[ClauseResponse])
def get_document_clauses(
    document_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    doc = get_document_by_id(db, document_id, str(current_user.id))
    if not doc:
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


# ── Semantic Search ───────────────────────────────────────────────────────────

@router.get("/{document_id}/search", response_model=List[SearchResult])
def search_document(
    document_id: str,
    q: str = Query(..., min_length=1, max_length=500, description="Search query"),
    top_k: int = Query(default=5, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Semantic search within a document.
    - Authentication required.
    - Returns 404 for cross-user access.
    - Returns 409 if document is not ready/indexed.
    - Returns top_k most semantically relevant clauses.
    - Does NOT call any LLM or generate explanations.
    """
    # Ownership check
    doc = get_document_by_id(db, document_id, str(current_user.id))
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    # Document must be fully processed
    if doc.processing_status != "ready":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Document is not ready for search. Please process it first.",
        )

    query = q.strip()
    if not query:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Search query must not be empty.",
        )

    # Generate query embedding
    from app.services.embedding_service import embed_text
    from app.services.vector_store_service import semantic_search
    from app.repositories.clause_repo import get_clauses_by_document

    query_embedding = embed_text(query)
    hits = semantic_search(query_embedding, document_id, top_k=top_k)

    if not hits:
        return []

    # Enrich hits with full clause content from PostgreSQL
    clauses_map = {
        str(c.id): c
        for c in get_clauses_by_document(db, document_id)
    }

    results = []
    for hit in hits:
        clause = clauses_map.get(hit["clause_id"])
        if clause:
            results.append(SearchResult(
                clause_id=hit["clause_id"],
                clause_number=hit["clause_number"],
                heading=hit.get("heading"),
                content=clause.content,
                page_number=hit["page_number"],
                distance=hit.get("distance"),
            ))

    return results
