from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import uuid
import enum


class AdmissibilityGrade(str, enum.Enum):
    """Evidence admissibility grade for court-facing use.
    
    This is NOT a legal decision - it's a technical reliability grade.
    """
    A = "A"  # High reliability: quality sufficient, integrity strong, limitations minimal
    B = "B"  # Moderate reliability: usable with disclosures / corroboration recommended
    C = "C"  # Limited reliability: only contextual use; identity attribution NOT allowed
    D = "D"  # Insufficient: not suitable for conclusions; only storage/documentation


class IdentitySuitability(str, enum.Enum):
    """Whether identity attribution analysis is allowed based on evidence quality."""
    ALLOWED = "allowed"
    NOT_ALLOWED = "not_allowed"


class SuitabilityLevel(str, enum.Enum):
    """Suitability level for various analysis types."""
    STRONG = "strong"
    MODERATE = "moderate"
    LIMITED = "limited"
    NOT_RELIABLE = "not_reliable"


class EvidenceQualityMetrics(Base):
    """Stores raw quality metrics and viability score for evidence.
    
    This table captures objective, measurable signals used to compute
    the viability score and admissibility grade.
    """
    __tablename__ = "evidence_quality_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    
    evidence_id = Column(Integer, ForeignKey("evidence.id"), nullable=False, unique=True)
    
    # Raw metrics stored as JSON for flexibility and reproducibility
    # For images: resolution, blur_score, brightness_histogram, compression_ratio, etc.
    # For video: bitrate, frame_count, keyframe_interval, sample_frame_metrics, etc.
    # For audio: snr_estimate, speech_presence_confidence, sample_rate, etc.
    metrics_json = Column(JSON, nullable=False)
    
    # Computed viability score (0-100) based on metrics
    viability_score = Column(Integer, nullable=False)
    
    # Thresholds version used for computation (for reproducibility)
    thresholds_version = Column(String(20), nullable=False, default="1.0.0")
    
    computed_at = Column(DateTime(timezone=True), server_default=func.now())
    computed_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    evidence = relationship("Evidence", backref="quality_metrics")
    computed_by_user = relationship("User", foreign_keys=[computed_by])


class EvidenceAdmissibility(Base):
    """Stores admissibility grade, suitability tags, and limitations for evidence.
    
    This is derived from quality metrics and integrity analysis results.
    """
    __tablename__ = "evidence_admissibility"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    
    evidence_id = Column(Integer, ForeignKey("evidence.id"), nullable=False, unique=True)
    
    # Admissibility grade (A/B/C/D)
    grade = Column(String(1), nullable=False)
    
    # Suitability tags stored as JSON
    # {
    #   "identity_attribution": "allowed" | "not_allowed",
    #   "manipulation_detection": "strong" | "moderate" | "limited",
    #   "timeline_context": "strong" | "moderate" | "limited",
    #   "audio_content": "strong" | "moderate" | "limited" | "not_reliable"
    # }
    suitability_json = Column(JSON, nullable=False)
    
    # Limitations stored as JSON array
    # Each limitation has: code, what, why, impact, severity
    # Example: {
    #   "code": "LOW_FACE_RESOLUTION",
    #   "what": "Identity attribution was not performed",
    #   "why": "Insufficient facial resolution (detected face width: 45px, minimum required: 80px)",
    #   "impact": "Cannot assess identity consistency for this evidence",
    #   "severity": "high"
    # }
    limitations_json = Column(JSON, nullable=False)
    
    # Thresholds version used for computation (for reproducibility)
    thresholds_version = Column(String(20), nullable=False, default="1.0.0")
    
    computed_at = Column(DateTime(timezone=True), server_default=func.now())
    computed_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    evidence = relationship("Evidence", backref="admissibility")
    computed_by_user = relationship("User", foreign_keys=[computed_by])


class ExpertWitnessSummary(Base):
    """Stores expert witness explanations for courtroom presentation.
    
    This provides court-ready, neutral explanations of forensic findings
    that can survive cross-examination. Built on top of admissibility data.
    """
    __tablename__ = "expert_witness_summaries"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    
    evidence_id = Column(Integer, ForeignKey("evidence.id"), nullable=False, unique=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    
    # Methods Summary: neutral explanation of what was analyzed and how
    methods_summary = Column(Text, nullable=False)
    
    # Findings Summary: plain language translation of technical results
    findings_summary = Column(Text, nullable=False)
    
    # Limitations Disclosure: pulled from Limitations Engine (never empty)
    limitations_disclosure = Column(Text, nullable=False)
    
    # Confidence Alignment: ties viability score, grade, and confidence tier
    confidence_alignment = Column(Text, nullable=False)
    
    # Cross-Examination Q&A: standardized Q&A block for courtroom challenges
    # Stored as JSON array of {question, answer} objects
    cross_examination_qa = Column(JSON, nullable=False)
    
    # Version tracking for reproducibility
    version = Column(String(20), nullable=False, default="1.0.0")
    
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    generated_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    evidence = relationship("Evidence", backref="expert_witness_summary")
    case = relationship("Case", backref="expert_witness_summaries")
    generated_by_user = relationship("User", foreign_keys=[generated_by])
