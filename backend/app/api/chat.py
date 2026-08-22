"""
Chat API — RAG-based Q&A for a processed document.

POST /api/v1/documents/{document_id}/chat
    Ask a question; receive a grounded answer + citations.

GET /api/v1/documents/{document_id}/chat
    Retrieve chat history for this user + document.
"""
import json
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user
from app.repositories.document_repo import get_document_by_id
from app.repositories.chat_repo import (
    get_or_create_session,
    get_session_for_document,
    add_message,
    get_all_messages,
    get_recent_messages_for_session,
)
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    CitationSchema,
    ChatMessageResponse,
    ChatHistoryResponse,
)
from app.services.rag_service import answer_question

logger = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])


def _parse_citations(citations_json: str | None) -> list:
    if not citations_json:
        return []
    try:
        return json.loads(citations_json)
    except Exception:
        return []


def _message_to_response(msg) -> ChatMessageResponse:
    citations = [CitationSchema(**c) for c in _parse_citations(msg.citations_json)]
    return ChatMessageResponse(
        id=str(msg.id),
        role=msg.role,
        content=msg.content,
        citations=citations,
        created_at=msg.created_at.isoformat(),
    )


@router.post("/documents/{document_id}/chat", response_model=ChatResponse)
def ask_question(
    document_id: str,
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Ask a question about the document.
    - Authentication required.
    - User must own the document.
    - Document must be in 'ready' status.
    - Returns grounded answer + citations derived from database records.
    """
    # Ownership check (404 hides other users' documents)
    doc = get_document_by_id(db, document_id, str(current_user.id))
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    if doc.processing_status != "ready":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Document is not ready. Please process it first.",
        )

    # Get or create chat session for this user+document
    session = get_or_create_session(db, str(current_user.id), document_id)

    # Build conversation history for context window (last N messages)
    recent = get_recent_messages_for_session(db, str(session.id), limit=8)
    history = [{"role": m.role, "content": m.content} for m in recent]

    # Persist user message
    add_message(db, str(session.id), role="user", content=request.message)

    # Run RAG pipeline
    result = answer_question(
        question=request.message,
        document_id=document_id,
        db=db,
        conversation_history=history,
    )

    # Serialize citations for storage
    citations_data = [
        {
            "clause_id": c.clause_id,
            "clause_number": c.clause_number,
            "page_number": c.page_number,
            "heading": c.heading,
        }
        for c in result.citations
    ]

    # Persist assistant message
    add_message(
        db,
        str(session.id),
        role="assistant",
        content=result.answer,
        citations=citations_data,
    )

    return ChatResponse(
        answer=result.answer,
        citations=[CitationSchema(**c) for c in citations_data],
    )


@router.get("/documents/{document_id}/chat", response_model=ChatHistoryResponse)
def get_chat_history(
    document_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Retrieve full chat history for this user's session on a document.
    Returns 404 for cross-user access.
    """
    doc = get_document_by_id(db, document_id, str(current_user.id))
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    session = get_session_for_document(db, str(current_user.id), document_id)
    if not session:
        return ChatHistoryResponse(
            session_id="",
            document_id=document_id,
            messages=[],
        )

    messages = get_all_messages(db, str(session.id))
    return ChatHistoryResponse(
        session_id=str(session.id),
        document_id=document_id,
        messages=[_message_to_response(m) for m in messages],
    )
