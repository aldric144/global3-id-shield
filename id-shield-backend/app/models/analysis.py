from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Enum, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import uuid
import enum


class AnalysisType(str, enum.Enum):
    QUALITY_ASSESSMENT = "quality_assessment"
    METADATA_EXTRACTION = "metadata_extraction"
    INTEGRITY_CHECK = "integrity_check"
    MANIPULATION_DETECTION = "manipulation_detection"
    IDENTITY_CONSISTENCY = "identity_consistency"
    BEHAVIORAL_ANALYSIS = "behavioral_analysis"
    PREDICTIVE_INTELLIGENCE = "predictive_intelligence"


class AnalysisStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ConfidenceTier(str, enum.Enum):
    HIGH = "high"
    MODERATE = "moderate"
    LIMITED = "limited"
    INSUFFICIENT = "insufficient"


class AnalysisResult(Base):
    __tablename__ = "analysis_results"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    
    evidence_id = Column(Integer, ForeignKey("evidence.id"), nullable=False)
    analysis_type = Column(Enum(AnalysisType), nullable=False)
    
    status = Column(Enum(AnalysisStatus), default=AnalysisStatus.PENDING, nullable=False)
    
    confidence_score = Column(Float)
    confidence_tier = Column(Enum(ConfidenceTier))
    
    summary = Column(Text)
    detailed_findings = Column(JSON)
    
    warnings = Column(JSON)
    limitations = Column(JSON)
    
    visual_data = Column(JSON)
    
    processing_time_ms = Column(Integer)
    model_version = Column(String(50))
    
    is_court_admissible = Column(Boolean, default=True)
    exclusion_reason = Column(Text)
    
    triggered_by = Column(String(100))
    
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    evidence = relationship("Evidence", back_populates="analysis_results")
    
    def __repr__(self):
        return f"<AnalysisResult {self.analysis_type.value} for Evidence {self.evidence_id}>"
