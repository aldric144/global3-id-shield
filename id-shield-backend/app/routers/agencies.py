from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.agency import Agency
from app.models.user import User, UserRole
from app.schemas.agency import AgencyCreate, AgencyUpdate, AgencyResponse
from app.services.auth import AuthService, require_roles

router = APIRouter(prefix="/agencies", tags=["Agencies"])


@router.post("/", response_model=AgencyResponse)
async def create_agency(
    agency_data: AgencyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN))
):
    """Create a new agency (admin only)."""
    existing = await db.execute(select(Agency).where(Agency.code == agency_data.code))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Agency code already exists"
        )
    
    agency = Agency(
        name=agency_data.name,
        code=agency_data.code,
        agency_type=agency_data.agency_type,
        jurisdiction=agency_data.jurisdiction,
        country=agency_data.country,
        address=agency_data.address,
        contact_email=agency_data.contact_email,
        contact_phone=agency_data.contact_phone,
        data_retention_days=agency_data.data_retention_days
    )
    
    db.add(agency)
    await db.commit()
    await db.refresh(agency)
    
    return agency


@router.get("/", response_model=List[AgencyResponse])
async def list_agencies(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """List all agencies (filtered by user's agency for non-admins)."""
    if current_user.role == UserRole.ADMIN:
        result = await db.execute(select(Agency).order_by(Agency.name))
        return list(result.scalars().all())
    else:
        result = await db.execute(select(Agency).where(Agency.id == current_user.agency_id))
        return list(result.scalars().all())


@router.get("/{agency_id}", response_model=AgencyResponse)
async def get_agency(
    agency_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Get agency by ID."""
    result = await db.execute(select(Agency).where(Agency.id == agency_id))
    agency = result.scalar_one_or_none()
    
    if not agency:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agency not found")
    
    if current_user.role != UserRole.ADMIN and current_user.agency_id != agency_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    return agency


@router.patch("/{agency_id}", response_model=AgencyResponse)
async def update_agency(
    agency_id: int,
    agency_data: AgencyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN))
):
    """Update agency (admin only)."""
    result = await db.execute(select(Agency).where(Agency.id == agency_id))
    agency = result.scalar_one_or_none()
    
    if not agency:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agency not found")
    
    update_data = agency_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(agency, field, value)
    
    await db.commit()
    await db.refresh(agency)
    
    return agency
