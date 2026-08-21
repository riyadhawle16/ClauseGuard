import uuid as uuid_module
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from app.models.user import GUID
from app.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(GUID(), primary_key=True, default=uuid_module.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=False)
    processing_status = Column(String(20), nullable=False, default="uploaded")
    processing_error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
