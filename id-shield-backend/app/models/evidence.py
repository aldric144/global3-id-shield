from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Enum, BigInteger, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import uuid
import enum


class EvidenceType(str, enum.Enum):
    PHOTO = "photo"
    VIDEO = "video"
    AUDIO = "audio"
    SCREENSHOT = "screenshot"
    DOCUMENT = "document"


class EvidenceStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    ANALYZED = "analyzed"
    FAILED = "failed"
    QUARANTINED = "quarantined"


class Evidence(Base):
    __tablename__ = "evidence"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    evidence_number = Column(String(100), nullable=False, index=True)
    
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    original_filename = Column(String(500), nullable=False)
    stored_filename = Column(String(500), nullable=False)
    file_path = Column(Text, nullable=False)
    
    evidence_type = Column(Enum(EvidenceType), nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    
    sha256_hash = Column(String(64), nullable=False, index=True)
    md5_hash = Column(String(32), nullable=False)
    
    status = Column(Enum(EvidenceStatus), default=EvidenceStatus.UPLOADED, nullable=False)
    
    description = Column(Text)
    source = Column(String(255))
    collection_date = Column(DateTime(timezone=True))
    collection_location = Column(Text)
    collector_name = Column(String(255))
    
    metadata_raw = Column(JSON)
    
    is_locked = Column(Boolean, default=True)
    is_original = Column(Boolean, default=True)
    parent_evidence_id = Column(Integer, ForeignKey("evidence.id"))
    
    quality_score = Column(Integer)
    quality_issues = Column(JSON)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    case = relationship("Case", back_populates="evidence_items")
    uploader = relationship("User", foreign_keys=[uploaded_by])
    parent_evidence = relationship("Evidence", remote_side=[id])
    analysis_results = relationship("AnalysisResult", back_populates="evidence")
    
    def __repr__(self):
        return f"<Evidence {self.evidence_number}: {self.original_filename}>"
