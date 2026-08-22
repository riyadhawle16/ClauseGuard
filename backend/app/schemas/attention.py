from pydantic import BaseModel
from typing import Optional, List


class AttentionFlagResponse(BaseModel):
    id: str
    clause_id: str
    clause_number: Optional[int] = None
    clause_page: Optional[int] = None
    category: str
    category_name: str
    title: str
    explanation: str
    matched_text: Optional[str] = None
    severity: str
    confidence: Optional[float] = None
    detection_method: str

    model_config = {"from_attributes": True}


class AttentionAnalysisResponse(BaseModel):
    document_id: str
    total_clauses: int
    flags_found: int
    categories_found: List[str]
    flags: List[AttentionFlagResponse]
