from pydantic import BaseModel, Field
from typing import Optional, List


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)


class CitationSchema(BaseModel):
    clause_id: str
    clause_number: int
    page_number: int
    heading: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    citations: List[CitationSchema] = []


class ChatMessageResponse(BaseModel):
    id: str
    role: str
    content: str
    citations: List[CitationSchema] = []
    created_at: str

    model_config = {"from_attributes": True}


class ChatHistoryResponse(BaseModel):
    session_id: str
    document_id: str
    messages: List[ChatMessageResponse] = []
