import uuid as uuid_module
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from app.models.user import GUID
from app.database import Base


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(GUID(), primary_key=True, default=uuid_module.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    document_id = Column(GUID(), ForeignKey("documents.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(GUID(), primary_key=True, default=uuid_module.uuid4)
    session_id = Column(GUID(), ForeignKey("chat_sessions.id"), nullable=False, index=True)
    role = Column(String(10), nullable=False)          # "user" or "assistant"
    content = Column(Text, nullable=False)
    # Citations stored as JSON string — parsed by service layer
    citations_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
