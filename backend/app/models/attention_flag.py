import uuid as uuid_module
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Float, ForeignKey
from app.models.user import GUID
from app.database import Base


class AttentionFlag(Base):
    __tablename__ = "attention_flags"

    id = Column(GUID(), primary_key=True, default=uuid_module.uuid4)
    document_id = Column(GUID(), ForeignKey("documents.id"), nullable=False, index=True)
    clause_id = Column(GUID(), ForeignKey("clauses.id"), nullable=False)

    # Category — always one of the 10 predefined identifiers
    category = Column(String(60), nullable=False)
    category_name = Column(String(120), nullable=False)

    # Human-readable content
    title = Column(String(200), nullable=False)
    explanation = Column(Text, nullable=False)
    matched_text = Column(String(500), nullable=True)   # pattern that triggered the flag

    # severity: "review" or "important" — NOT a legal assessment
    severity = Column(String(20), nullable=False, default="review")

    # LLM confidence (0–1) when LLM classification was used; None otherwise
    confidence = Column(Float, nullable=True)

    # "rule" = deterministic only; "rule+llm" = deterministic + LLM confirmed
    detection_method = Column(String(20), nullable=False, default="rule")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
