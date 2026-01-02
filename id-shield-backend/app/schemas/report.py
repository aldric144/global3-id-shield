from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.report import ReportType, ReportStatus


class ReportCreate(BaseModel):
    case_id: int
    report_type: ReportType
    title: str
    evidence_ids: Optional[List[int]] = None


class ReportResponse(BaseModel):
    id: int
    uuid: str
    report_number: str
    case_id: int
    generated_by: int
    report_type: ReportType
    title: str
    status: ReportStatus
    file_path: Optional[str]
    file_hash: Optional[str]
    included_evidence_ids: Optional[List[int]]
    summary: Optional[str]
    limitations_section: Optional[str]
    is_certified: bool
    certification_hash: Optional[str]
    certified_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True
