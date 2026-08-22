from pydantic import BaseModel
from typing import Optional, List


class MissingInfoFlagResponse(BaseModel):
    id: str
    category: str
    category_name: str
    status: str                          # PRESENT | UNCLEAR | NOT_IDENTIFIED
    explanation: str
    evidence_clause_id: Optional[str] = None
    evidence_clause_number: Optional[int] = None
    evidence_page_number: Optional[int] = None
    detection_method: str

    model_config = {"from_attributes": True}


class MissingInfoAnalysisResponse(BaseModel):
    document_id: str
    total_categories: int
    present_count: int
    unclear_count: int
    not_identified_count: int
    flags: List[MissingInfoFlagResponse]
