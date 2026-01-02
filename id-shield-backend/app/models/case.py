from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import uuid
import enum


class CaseStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    PENDING_REVIEW = "pending_review"
    CLOSED = "closed"
    ARCHIVED = "archived"


class CasePriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Case(Base):
    __tablename__ = "cases"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    case_number = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    
    case_type = Column(String(100), nullable=False)
    status = Column(Enum(CaseStatus), default=CaseStatus.OPEN, nullable=False)
    priority = Column(Enum(CasePriority), default=CasePriority.MEDIUM, nullable=False)
    
    agency_id = Column(Integer, ForeignKey("agencies.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_to = Column(Integer, ForeignKey("users.id"))
    
    incident_date = Column(DateTime(timezone=True))
    incident_location = Column(Text)
    
    is_sealed = Column(Boolean, default=False)
    seal_reason = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    closed_at = Column(DateTime(timezone=True))
    
    agency = relationship("Agency", back_populates="cases")
    created_by_user = relationship("User", back_populates="created_cases", foreign_keys=[created_by])
    assigned_user = relationship("User", foreign_keys=[assigned_to])
    evidence_items = relationship("Evidence", back_populates="case")
    reports = relationship("Report", back_populates="case")
    
    def __repr__(self):
        return f"<Case {self.case_number}: {self.title[:50]}>"
