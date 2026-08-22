import json
import uuid as uuid_module
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.chat import ChatSession, ChatMessage


# ── Session ───────────────────────────────────────────────────────────────────

def get_or_create_session(db: Session, user_id: str, document_id: str) -> ChatSession:
    """
    Return the existing chat session for (user, document) or create one.
    One session per user+document for simplicity.
    """
    session = (
        db.query(ChatSession)
        .filter(
            ChatSession.user_id == str(user_id),
            ChatSession.document_id == str(document_id),
        )
        .first()
    )
    if not session:
        session = ChatSession(
            id=uuid_module.uuid4(),
            user_id=str(user_id),
            document_id=str(document_id),
        )
        db.add(session)
        db.commit()
        db.refresh(session)
    return session


def get_session_by_id(
    db: Session, session_id: str, user_id: str
) -> Optional[ChatSession]:
    return (
        db.query(ChatSession)
        .filter(
            ChatSession.id == str(session_id),
            ChatSession.user_id == str(user_id),
        )
        .first()
    )


def get_session_for_document(
    db: Session, user_id: str, document_id: str
) -> Optional[ChatSession]:
    return (
        db.query(ChatSession)
        .filter(
            ChatSession.user_id == str(user_id),
            ChatSession.document_id == str(document_id),
        )
        .first()
    )


# ── Messages ──────────────────────────────────────────────────────────────────

def add_message(
    db: Session,
    session_id: str,
    role: str,
    content: str,
    citations: Optional[list] = None,
) -> ChatMessage:
    msg = ChatMessage(
        id=uuid_module.uuid4(),
        session_id=str(session_id),
        role=role,
        content=content,
        citations_json=json.dumps(citations) if citations else None,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def get_recent_messages(
    db: Session, session_id: str, limit: int = 10
) -> List[ChatMessage]:
    """Return the most recent `limit` messages, oldest first."""
    subq = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == str(session_id))
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
        .subquery()
    )
    # Re-order ascending for conversation context
    return (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == subq.c.id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )


def get_all_messages(db: Session, session_id: str) -> List[ChatMessage]:
    """Return all messages in chronological order."""
    return (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == str(session_id))
        .order_by(ChatMessage.created_at.asc())
        .all()
    )


def get_recent_messages_for_session(
    db: Session, session_id: str, limit: int = 10
) -> List[ChatMessage]:
    """
    Return the `limit` most recent messages for a session, in chronological order.
    Used to build conversation context for the LLM.
    """
    rows = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == str(session_id))
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
        .all()
    )
    return list(reversed(rows))  # oldest first
