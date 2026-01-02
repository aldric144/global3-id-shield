from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import uuid
import enum


class ReportType(str, enum.Enum):
    FULL_FORENSIC = "full_forensic"
    EXECUTIVE_SUMMARY = "executive_summary"
    JUDGE_SUMMARY = "judge_summary"
    CHAIN_OF_CUSTODY = "chain_of_custody"


class ReportStatus(str, enum.Enum):
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class Report(Base):
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    report_number = Column(String(100), unique=True, nullable=False, index=True)
    
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    generated_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    report_type = Column(Enum(ReportType), nullable=False)
    title = Column(String(500), nullable=False)
    
    status = Column(Enum(ReportStatus), default=ReportStatus.GENERATING, nullable=False)
    
    file_path = Column(Text)
    file_hash = Column(String(64))
    
    included_evidence_ids = Column(JSON)
    included_analysis_ids = Column(JSON)
    
    summary = Column(Text)
    limitations_section = Column(Text)
    
    is_certified = Column(Boolean, default=False)
    certification_hash = Column(String(64))
    certified_at = Column(DateTime(timezone=True))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    case = relationship("Case", back_populates="reports")
    generator = relationship("User", foreign_keys=[generated_by])
    
    def __repr__(self):
        return f"<Report {self.report_number}: {self.title[:50]}>"
