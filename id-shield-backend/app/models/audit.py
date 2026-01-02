from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import uuid
import enum


class AuditAction(str, enum.Enum):
    LOGIN = "login"
    LOGOUT = "logout"
    
    CASE_CREATE = "case_create"
    CASE_VIEW = "case_view"
    CASE_UPDATE = "case_update"
    CASE_DELETE = "case_delete"
    CASE_SEAL = "case_seal"
    
    EVIDENCE_UPLOAD = "evidence_upload"
    EVIDENCE_VIEW = "evidence_view"
    EVIDENCE_DOWNLOAD = "evidence_download"
    EVIDENCE_DELETE = "evidence_delete"
    
    ANALYSIS_START = "analysis_start"
    ANALYSIS_COMPLETE = "analysis_complete"
    ANALYSIS_VIEW = "analysis_view"
    
    REPORT_GENERATE = "report_generate"
    REPORT_VIEW = "report_view"
    REPORT_DOWNLOAD = "report_download"
    REPORT_CERTIFY = "report_certify"
    
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DEACTIVATE = "user_deactivate"
    
    PERMISSION_CHANGE = "permission_change"
    SYSTEM_CONFIG = "system_config"
    
    EVIDENCE_ADMISSIBILITY_COMPUTED = "evidence_admissibility_computed"
    EXPERT_WITNESS_SUMMARY_GENERATED = "expert_witness_summary_generated"


class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    
    user_id = Column(Integer, ForeignKey("users.id"))
    agency_id = Column(Integer, ForeignKey("agencies.id"))
    
    action = Column(Enum(AuditAction), nullable=False)
    
    resource_type = Column(String(50))
    resource_id = Column(Integer)
    resource_uuid = Column(String(36))
    
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    details = Column(JSON)
    
    previous_state = Column(JSON)
    new_state = Column(JSON)
    
    success = Column(Integer, default=1)
    error_message = Column(Text)
    
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    user = relationship("User", back_populates="audit_logs")
    
    def __repr__(self):
        return f"<AuditLog {self.action.value} by User {self.user_id} at {self.timestamp}>"
