from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import uuid
import enum


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    SUPERVISOR = "supervisor"
    INVESTIGATOR = "investigator"
    JUDGE = "judge"


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    badge_number = Column(String(50))
    title = Column(String(100))
    
    role = Column(Enum(UserRole), default=UserRole.INVESTIGATOR, nullable=False)
    agency_id = Column(Integer, ForeignKey("agencies.id"), nullable=False)
    
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    last_login = Column(DateTime(timezone=True))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    agency = relationship("Agency", back_populates="users")
    created_cases = relationship("Case", back_populates="created_by_user", foreign_keys="Case.created_by")
    audit_logs = relationship("AuditLog", back_populates="user")
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def __repr__(self):
        return f"<User {self.email} ({self.role.value})>"
