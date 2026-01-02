from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user."""
    user = await AuthService.create_user(db, user_data)
    return user


@router.post("/login", response_model=Token)
async def login(
    credentials: UserLogin,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Authenticate user and return access token."""
    ip_address = request.client.host if request.client else None
    return await AuthService.login(db, credentials.email, credentials.password, ip_address)


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user = Depends(AuthService.get_current_user)
):
    """Get current authenticated user."""
    return current_user
