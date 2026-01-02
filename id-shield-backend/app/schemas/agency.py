from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class AgencyBase(BaseModel):
    name: str
    code: str
    agency_type: str
    jurisdiction: Optional[str] = None
    country: str
    address: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None


class AgencyCreate(AgencyBase):
    data_retention_days: int = 365


class AgencyUpdate(BaseModel):
    name: Optional[str] = None
    jurisdiction: Optional[str] = None
    address: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    is_active: Optional[bool] = None
    data_retention_days: Optional[int] = None


class AgencyResponse(BaseModel):
    id: int
    uuid: str
    name: str
    code: str
    agency_type: str
    jurisdiction: Optional[str]
    country: str
    address: Optional[str]
    contact_email: Optional[str]
    contact_phone: Optional[str]
    is_active: bool
    data_retention_days: int
    created_at: datetime
    
    class Config:
        from_attributes = True
