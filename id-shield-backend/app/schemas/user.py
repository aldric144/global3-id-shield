from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from app.models.user import UserRole


class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    badge_number: Optional[str] = None
    title: Optional[str] = None
    role: UserRole = UserRole.INVESTIGATOR


class UserCreate(UserBase):
    password: str
    agency_id: int


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    badge_number: Optional[str] = None
    title: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    id: int
    uuid: str
    email: str
    first_name: str
    last_name: str
    badge_number: Optional[str]
    title: Optional[str]
    role: UserRole
    agency_id: int
    is_active: bool
    is_verified: bool
    last_login: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    user_id: Optional[int] = None
    email: Optional[str] = None
    role: Optional[str] = None
    agency_id: Optional[int] = None
