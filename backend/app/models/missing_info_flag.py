import uuid as uuid_module
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Integer, ForeignKey
from app.models.user import GUID
from app.database import Base


class MissingInfoFlag(Base):
    __tablename__ = "missing_info_flags"

    id = Column(GUID(), primary_key=True, default=uuid_module.uuid4)
    document_id = Column(GUID(), ForeignKey("documents.id"), nullable=False, index=True)

    # Category — always one of the 10 predefined identifiers from Phase 7
    category = Column(String(60), nullable=False)
    category_name = Column(String(120), nullable=False)

    # status: PRESENT | UNCLEAR | NOT_IDENTIFIED
    status = Column(String(20), nullable=False)

    # Plain-language explanation — no legal advice
    explanation = Column(Text, nullable=False)

    # Optional reference to the clause where evidence was found
    evidence_clause_id = Column(GUID(), ForeignKey("clauses.id"), nullable=True)
    evidence_page_number = Column(Integer, nullable=True)

    # RULE or RULE_LLM
    detection_method = Column(String(20), nullable=False, default="RULE")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
