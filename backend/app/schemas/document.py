from pydantic import BaseModel
from typing import Optional


class DocumentResponse(BaseModel):
    id: str
    title: str
    original_filename: str
    processing_status: str
    processing_error: Optional[str] = None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]
