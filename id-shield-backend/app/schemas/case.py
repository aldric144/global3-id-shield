from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.case import CaseStatus, CasePriority


class CaseBase(BaseModel):
    title: str
    description: Optional[str] = None
    case_type: str
    priority: CasePriority = CasePriority.MEDIUM
    incident_date: Optional[datetime] = None
    incident_location: Optional[str] = None


class CaseCreate(CaseBase):
    case_number: Optional[str] = None


class CaseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[CaseStatus] = None
    priority: Optional[CasePriority] = None
    assigned_to: Optional[int] = None
    incident_date: Optional[datetime] = None
    incident_location: Optional[str] = None


class CaseResponse(BaseModel):
    id: int
    uuid: str
    case_number: str
    title: str
    description: Optional[str]
    case_type: str
    status: CaseStatus
    priority: CasePriority
    agency_id: int
    created_by: int
    assigned_to: Optional[int]
    incident_date: Optional[datetime]
    incident_location: Optional[str]
    is_sealed: bool
    evidence_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class CaseListResponse(BaseModel):
    cases: List[CaseResponse]
    total: int
    page: int
    page_size: int
