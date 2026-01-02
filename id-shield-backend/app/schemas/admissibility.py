"""Pydantic schemas for Evidence Admissibility API."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel


class LimitationSchema(BaseModel):
    """Schema for a single limitation statement."""
    code: str
    what: str
    why: str
    impact: str
    severity: str  # critical, high, medium, low


class SuitabilityTagsSchema(BaseModel):
    """Schema for suitability tags."""
    identity_attribution: str  # allowed, not_allowed
    manipulation_detection: str  # strong, moderate, limited
    timeline_context: str  # strong, moderate, limited
    audio_content: str  # strong, moderate, limited, not_reliable, n/a


class QualityMetricsResponse(BaseModel):
    """Response schema for quality metrics."""
    evidence_id: int
    evidence_uuid: str
    metrics: Dict[str, Any]
    viability_score: int
    thresholds_version: str
    computed_at: datetime
    computed_by: Optional[int] = None

    class Config:
        from_attributes = True


class AdmissibilityResponse(BaseModel):
    """Response schema for admissibility data."""
    evidence_id: int
    evidence_uuid: str
    grade: str  # A, B, C, D
    grade_label: str  # High reliability, Moderate reliability, etc.
    viability_score: int
    suitability: SuitabilityTagsSchema
    limitations: List[LimitationSchema]
    limitations_count: int
    thresholds_version: str
    computed_at: datetime
    computed_by: Optional[int] = None

    class Config:
        from_attributes = True


class AdmissibilityComputeRequest(BaseModel):
    """Request schema for computing admissibility (optional, for future use)."""
    force_recompute: bool = False


# Grade labels for display
GRADE_LABELS = {
    "A": "High reliability",
    "B": "Moderate reliability",
    "C": "Limited reliability",
    "D": "Insufficient"
}


def get_grade_label(grade: str) -> str:
    """Get human-readable label for grade."""
    return GRADE_LABELS.get(grade, "Unknown")
