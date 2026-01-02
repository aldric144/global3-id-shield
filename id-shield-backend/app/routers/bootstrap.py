from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.agency import Agency
from app.models.user import User, UserRole
from app.utils.security import get_password_hash

router = APIRouter(prefix="/bootstrap", tags=["Bootstrap"])


@router.post("/setup")
async def bootstrap_setup(
    db: AsyncSession = Depends(get_db)
):
    """
    Bootstrap the system with initial agency and admin user.
    Only works if no agencies exist yet.
    """
    existing_agency = await db.execute(select(Agency).limit(1))
    if existing_agency.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="System already bootstrapped. Agencies exist."
        )
    
    agency = Agency(
        name="Global3 Technology & Intelligence",
        code="G3TI",
        agency_type="forensic_intelligence",
        jurisdiction="International",
        country="USA",
        contact_email="admin@global3ti.com",
        data_retention_days=365
    )
    db.add(agency)
    await db.commit()
    await db.refresh(agency)
    
    admin_user = User(
        email="admin@global3ti.com",
        hashed_password=get_password_hash("admin123"),
        first_name="System",
        last_name="Administrator",
        title="Platform Administrator",
        role=UserRole.ADMIN,
        agency_id=agency.id,
        is_active=True,
        is_verified=True
    )
    db.add(admin_user)
    
    investigator = User(
        email="investigator@global3ti.com",
        hashed_password=get_password_hash("investigator123"),
        first_name="John",
        last_name="Investigator",
        badge_number="INV-001",
        title="Senior Forensic Investigator",
        role=UserRole.INVESTIGATOR,
        agency_id=agency.id,
        is_active=True,
        is_verified=True
    )
    db.add(investigator)
    
    judge_user = User(
        email="judge@global3ti.com",
        hashed_password=get_password_hash("judge123"),
        first_name="Jane",
        last_name="Judge",
        title="Presiding Judge",
        role=UserRole.JUDGE,
        agency_id=agency.id,
        is_active=True,
        is_verified=True
    )
    db.add(judge_user)
    
    await db.commit()
    
    return {
        "status": "success",
        "message": "System bootstrapped successfully",
        "agency": {
            "id": agency.id,
            "name": agency.name,
            "code": agency.code
        },
        "users": [
            {"email": "admin@global3ti.com", "password": "admin123", "role": "admin"},
            {"email": "investigator@global3ti.com", "password": "investigator123", "role": "investigator"},
            {"email": "judge@global3ti.com", "password": "judge123", "role": "judge (read-only)"}
        ],
        "note": "Please change these passwords immediately in production!"
    }
