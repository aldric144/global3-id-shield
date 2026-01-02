from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import uuid


class Agency(Base):
    __tablename__ = "agencies"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False, index=True)
    agency_type = Column(String(100), nullable=False)
    jurisdiction = Column(String(255))
    country = Column(String(100), nullable=False)
    address = Column(Text)
    contact_email = Column(String(255))
    contact_phone = Column(String(50))
    
    is_active = Column(Boolean, default=True)
    data_retention_days = Column(Integer, default=365)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    users = relationship("User", back_populates="agency")
    cases = relationship("Case", back_populates="agency")
    
    def __repr__(self):
        return f"<Agency {self.code}: {self.name}>"
