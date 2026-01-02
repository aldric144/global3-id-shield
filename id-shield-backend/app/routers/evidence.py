from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
import os

from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.evidence import EvidenceCreate, EvidenceResponse, EvidenceListResponse
from app.services.auth import AuthService
from app.services.evidence import EvidenceService
from app.services.analysis import AnalysisService
from app.utils.audit import create_audit_log
from app.models.audit import AuditAction

router = APIRouter(prefix="/evidence", tags=["Evidence"])


@router.post("/upload/{case_id}", response_model=EvidenceResponse)
async def upload_evidence(
    case_id: int,
    request: Request,
    file: UploadFile = File(...),
    description: str = Form(None),
    source: str = Form(None),
    collector_name: str = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Upload evidence to a case."""
    if current_user.role == UserRole.JUDGE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Judges have read-only access"
        )
    
    evidence_data = EvidenceCreate(
        description=description,
        source=source,
        collector_name=collector_name
    )
    
    ip_address = request.client.host if request.client else None
    
    evidence = await EvidenceService.upload_evidence(
        db=db,
        case_id=case_id,
        file=file,
        user=current_user,
        evidence_data=evidence_data,
        ip_address=ip_address
    )
    
    return evidence


@router.get("/case/{case_id}", response_model=EvidenceListResponse)
async def list_evidence(
    case_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """List all evidence for a case."""
    evidence_items = await EvidenceService.list_evidence_for_case(db, case_id, current_user)
    
    return EvidenceListResponse(
        evidence=evidence_items,
        total=len(evidence_items)
    )


@router.get("/{evidence_id}", response_model=EvidenceResponse)
async def get_evidence(
    evidence_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Get evidence by ID."""
    evidence = await EvidenceService.get_evidence(db, evidence_id, current_user)
    return evidence


@router.get("/{evidence_id}/download")
async def download_evidence(
    evidence_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Download evidence file."""
    evidence = await EvidenceService.get_evidence(db, evidence_id, current_user)
    
    if not os.path.exists(evidence.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence file not found on disk"
        )
    
    ip_address = request.client.host if request.client else None
    
    await create_audit_log(
        db=db,
        action=AuditAction.EVIDENCE_DOWNLOAD,
        user_id=current_user.id,
        agency_id=current_user.agency_id,
        resource_type="evidence",
        resource_id=evidence.id,
        resource_uuid=evidence.uuid,
        ip_address=ip_address
    )
    
    return FileResponse(
        evidence.file_path,
        filename=evidence.original_filename,
        media_type=evidence.mime_type
    )


@router.post("/{evidence_id}/analyze", response_model=List)
async def analyze_evidence(
    evidence_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Run full analysis pipeline on evidence."""
    if current_user.role == UserRole.JUDGE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Judges have read-only access"
        )
    
    evidence = await EvidenceService.get_evidence(db, evidence_id, current_user)
    
    ip_address = request.client.host if request.client else None
    
    results = await AnalysisService.run_full_analysis(
        db=db,
        evidence=evidence,
        user=current_user,
        ip_address=ip_address
    )
    
    from app.schemas.analysis import AnalysisResultResponse
    return [AnalysisResultResponse.model_validate(r) for r in results]


@router.get("/{evidence_id}/analysis")
async def get_analysis_results(
    evidence_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Get all analysis results for evidence."""
    evidence = await EvidenceService.get_evidence(db, evidence_id, current_user)
    
    results = await AnalysisService.get_analysis_results(db, evidence_id)
    
    await create_audit_log(
        db=db,
        action=AuditAction.ANALYSIS_VIEW,
        user_id=current_user.id,
        agency_id=current_user.agency_id,
        resource_type="evidence",
        resource_id=evidence.id,
        resource_uuid=evidence.uuid
    )
    
    from app.schemas.analysis import AnalysisResultResponse
    return [AnalysisResultResponse.model_validate(r) for r in results]
