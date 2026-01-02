from pydantic import BaseModel
from typing import Optional, List, Any, Dict
from datetime import datetime
from app.models.analysis import AnalysisType, AnalysisStatus, ConfidenceTier


class AnalysisRequest(BaseModel):
    evidence_id: int
    analysis_types: Optional[List[AnalysisType]] = None


class AnalysisResultResponse(BaseModel):
    id: int
    uuid: str
    evidence_id: int
    analysis_type: AnalysisType
    status: AnalysisStatus
    confidence_score: Optional[float]
    confidence_tier: Optional[ConfidenceTier]
    summary: Optional[str]
    detailed_findings: Optional[Dict[str, Any]]
    warnings: Optional[List[str]]
    limitations: Optional[List[str]]
    visual_data: Optional[Dict[str, Any]]
    processing_time_ms: Optional[int]
    model_version: Optional[str]
    is_court_admissible: bool
    exclusion_reason: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class AnalysisSummary(BaseModel):
    total_analyses: int
    completed: int
    failed: int
    skipped: int
    overall_confidence: Optional[ConfidenceTier]
    key_findings: List[str]
    warnings: List[str]
    limitations: List[str]
