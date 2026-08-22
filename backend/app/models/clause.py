import uuid as uuid_module
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from app.models.user import GUID
from app.database import Base


class Clause(Base):
    __tablename__ = "clauses"

    id = Column(GUID(), primary_key=True, default=uuid_module.uuid4)
    document_id = Column(GUID(), ForeignKey("documents.id"), nullable=False, index=True)
    clause_number = Column(Integer, nullable=False)
    heading = Column(String(500), nullable=True)   # detected heading, if any
    content = Column(Text, nullable=False)
    page_number = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
