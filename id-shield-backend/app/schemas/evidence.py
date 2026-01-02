from pydantic import BaseModel
from typing import Optional, List, Any, Dict
from datetime import datetime
from app.models.evidence import EvidenceType, EvidenceStatus


class EvidenceCreate(BaseModel):
    description: Optional[str] = None
    source: Optional[str] = None
    collection_date: Optional[datetime] = None
    collection_location: Optional[str] = None
    collector_name: Optional[str] = None


class EvidenceResponse(BaseModel):
    id: int
    uuid: str
    evidence_number: str
    case_id: int
    uploaded_by: int
    original_filename: str
    evidence_type: EvidenceType
    mime_type: str
    file_size: int
    sha256_hash: str
    md5_hash: str
    status: EvidenceStatus
    description: Optional[str]
    source: Optional[str]
    collection_date: Optional[datetime]
    collection_location: Optional[str]
    collector_name: Optional[str]
    metadata_raw: Optional[Dict[str, Any]]
    is_locked: bool
    is_original: bool
    quality_score: Optional[int]
    quality_issues: Optional[List[str]]
    created_at: datetime
    
    class Config:
        from_attributes = True


class EvidenceListResponse(BaseModel):
    evidence: List[EvidenceResponse]
    total: int


class EvidenceDetailResponse(EvidenceResponse):
    analysis_results: List[Any] = []
