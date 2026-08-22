from pydantic import BaseModel
from typing import Optional, List


class DocumentResponse(BaseModel):
    id: str
    title: str
    original_filename: str
    processing_status: str
    processing_error: Optional[str] = None
    clause_count: Optional[int] = None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]


class ClauseResponse(BaseModel):
    id: str
    clause_number: int
    heading: Optional[str] = None
    content: str
    page_number: int

    model_config = {"from_attributes": True}


class ProcessingResult(BaseModel):
    document_id: str
    status: str
    pages_extracted: int
    clauses_extracted: int
    vectors_indexed: Optional[int] = None


class SearchResult(BaseModel):
    clause_id: str
    clause_number: int
    heading: Optional[str] = None
    content: str
    page_number: int
    distance: Optional[float] = None
