from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import uuid

from app.database import get_db
from app.models.case import Case, CaseStatus
from app.models.evidence import Evidence
from app.models.user import User, UserRole
from app.schemas.case import CaseCreate, CaseUpdate, CaseResponse, CaseListResponse
from app.services.auth import AuthService
from app.utils.audit import create_audit_log
from app.models.audit import AuditAction

router = APIRouter(prefix="/cases", tags=["Cases"])


def generate_case_number(agency_code: str) -> str:
    """Generate unique case number."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    unique_id = str(uuid.uuid4())[:8].upper()
    return f"{agency_code}-{timestamp}-{unique_id}"


@router.post("/", response_model=CaseResponse)
async def create_case(
    case_data: CaseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Create a new case."""
    if current_user.role == UserRole.JUDGE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Judges have read-only access"
        )
    
    from app.models.agency import Agency
    agency_result = await db.execute(select(Agency).where(Agency.id == current_user.agency_id))
    agency = agency_result.scalar_one_or_none()
    
    case_number = case_data.case_number or generate_case_number(agency.code if agency else "CASE")
    
    case = Case(
        case_number=case_number,
        title=case_data.title,
        description=case_data.description,
        case_type=case_data.case_type,
        priority=case_data.priority,
        agency_id=current_user.agency_id,
        created_by=current_user.id,
        incident_date=case_data.incident_date,
        incident_location=case_data.incident_location,
        status=CaseStatus.OPEN
    )
    
    db.add(case)
    await db.commit()
    await db.refresh(case)
    
    await create_audit_log(
        db=db,
        action=AuditAction.CASE_CREATE,
        user_id=current_user.id,
        agency_id=current_user.agency_id,
        resource_type="case",
        resource_id=case.id,
        resource_uuid=case.uuid,
        details={
            "case_number": case_number,
            "title": case.title,
            "case_type": case.case_type
        }
    )
    
    return CaseResponse(
        id=case.id,
        uuid=case.uuid,
        case_number=case.case_number,
        title=case.title,
        description=case.description,
        case_type=case.case_type,
        status=case.status,
        priority=case.priority,
        agency_id=case.agency_id,
        created_by=case.created_by,
        assigned_to=case.assigned_to,
        incident_date=case.incident_date,
        incident_location=case.incident_location,
        is_sealed=case.is_sealed,
        evidence_count=0,
        created_at=case.created_at,
        updated_at=case.updated_at
    )


@router.get("/", response_model=CaseListResponse)
async def list_cases(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[CaseStatus] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """List cases for the user's agency."""
    query = select(Case).where(Case.agency_id == current_user.agency_id)
    
    if status:
        query = query.where(Case.status == status)
    
    if search:
        query = query.where(
            (Case.case_number.ilike(f"%{search}%")) |
            (Case.title.ilike(f"%{search}%"))
        )
    
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    query = query.order_by(Case.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    cases = list(result.scalars().all())
    
    case_responses = []
    for case in cases:
        ev_count_result = await db.execute(
            select(func.count()).where(Evidence.case_id == case.id)
        )
        ev_count = ev_count_result.scalar()
        
        case_responses.append(CaseResponse(
            id=case.id,
            uuid=case.uuid,
            case_number=case.case_number,
            title=case.title,
            description=case.description,
            case_type=case.case_type,
            status=case.status,
            priority=case.priority,
            agency_id=case.agency_id,
            created_by=case.created_by,
            assigned_to=case.assigned_to,
            incident_date=case.incident_date,
            incident_location=case.incident_location,
            is_sealed=case.is_sealed,
            evidence_count=ev_count,
            created_at=case.created_at,
            updated_at=case.updated_at
        ))
    
    return CaseListResponse(
        cases=case_responses,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(
    case_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Get case by ID."""
    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    
    if case.agency_id != current_user.agency_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    ev_count_result = await db.execute(
        select(func.count()).where(Evidence.case_id == case.id)
    )
    ev_count = ev_count_result.scalar()
    
    await create_audit_log(
        db=db,
        action=AuditAction.CASE_VIEW,
        user_id=current_user.id,
        agency_id=current_user.agency_id,
        resource_type="case",
        resource_id=case.id,
        resource_uuid=case.uuid
    )
    
    return CaseResponse(
        id=case.id,
        uuid=case.uuid,
        case_number=case.case_number,
        title=case.title,
        description=case.description,
        case_type=case.case_type,
        status=case.status,
        priority=case.priority,
        agency_id=case.agency_id,
        created_by=case.created_by,
        assigned_to=case.assigned_to,
        incident_date=case.incident_date,
        incident_location=case.incident_location,
        is_sealed=case.is_sealed,
        evidence_count=ev_count,
        created_at=case.created_at,
        updated_at=case.updated_at
    )


@router.patch("/{case_id}", response_model=CaseResponse)
async def update_case(
    case_id: int,
    case_data: CaseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Update case."""
    if current_user.role == UserRole.JUDGE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Judges have read-only access"
        )
    
    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    
    if case.agency_id != current_user.agency_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    if case.is_sealed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify a sealed case"
        )
    
    previous_state = {
        "status": case.status.value if case.status else None,
        "priority": case.priority.value if case.priority else None,
        "title": case.title
    }
    
    update_data = case_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(case, field, value)
    
    await db.commit()
    await db.refresh(case)
    
    await create_audit_log(
        db=db,
        action=AuditAction.CASE_UPDATE,
        user_id=current_user.id,
        agency_id=current_user.agency_id,
        resource_type="case",
        resource_id=case.id,
        resource_uuid=case.uuid,
        previous_state=previous_state,
        new_state=update_data
    )
    
    ev_count_result = await db.execute(
        select(func.count()).where(Evidence.case_id == case.id)
    )
    ev_count = ev_count_result.scalar()
    
    return CaseResponse(
        id=case.id,
        uuid=case.uuid,
        case_number=case.case_number,
        title=case.title,
        description=case.description,
        case_type=case.case_type,
        status=case.status,
        priority=case.priority,
        agency_id=case.agency_id,
        created_by=case.created_by,
        assigned_to=case.assigned_to,
        incident_date=case.incident_date,
        incident_location=case.incident_location,
        is_sealed=case.is_sealed,
        evidence_count=ev_count,
        created_at=case.created_at,
        updated_at=case.updated_at
    )
