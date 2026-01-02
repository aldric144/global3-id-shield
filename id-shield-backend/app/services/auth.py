from typing import Optional
from datetime import timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserResponse, Token
from app.utils.security import verify_password, get_password_hash, create_access_token, decode_token
from app.utils.audit import create_audit_log
from app.models.audit import AuditAction
from app.database import get_db
from app.config import settings


security = HTTPBearer()


class AuthService:
    
    @staticmethod
    async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
        existing = await db.execute(select(User).where(User.email == user_data.email))
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        hashed_password = get_password_hash(user_data.password)
        
        user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            badge_number=user_data.badge_number,
            title=user_data.title,
            role=user_data.role,
            agency_id=user_data.agency_id,
            is_active=True,
            is_verified=True
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        await create_audit_log(
            db=db,
            action=AuditAction.USER_CREATE,
            user_id=user.id,
            agency_id=user.agency_id,
            resource_type="user",
            resource_id=user.id,
            resource_uuid=user.uuid,
            details={"email": user.email, "role": user.role.value}
        )
        
        return user
    
    @staticmethod
    async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        
        return user
    
    @staticmethod
    async def login(db: AsyncSession, email: str, password: str, ip_address: str = None) -> Token:
        user = await AuthService.authenticate_user(db, email, password)
        
        if not user:
            await create_audit_log(
                db=db,
                action=AuditAction.LOGIN,
                details={"email": email},
                ip_address=ip_address,
                success=False,
                error_message="Invalid credentials"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "email": user.email,
                "role": user.role.value,
                "agency_id": user.agency_id
            },
            expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
        )
        
        await create_audit_log(
            db=db,
            action=AuditAction.LOGIN,
            user_id=user.id,
            agency_id=user.agency_id,
            ip_address=ip_address,
            details={"email": user.email}
        )
        
        return Token(
            access_token=access_token,
            user=UserResponse.model_validate(user)
        )
    
    @staticmethod
    async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: AsyncSession = Depends(get_db)
    ) -> User:
        token = credentials.credentials
        token_data = decode_token(token)
        
        if token_data is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        result = await db.execute(select(User).where(User.id == token_data.user_id))
        user = result.scalar_one_or_none()
        
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        return user


def require_roles(*roles: UserRole):
    async def role_checker(current_user: User = Depends(AuthService.get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[r.value for r in roles]}"
            )
        return current_user
    return role_checker
