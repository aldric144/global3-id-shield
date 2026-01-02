from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
import os

from app.database import get_db
from app.models.user import User, UserRole
from app.models.report import ReportType
from app.schemas.report import ReportCreate, ReportResponse
from app.services.auth import AuthService
from app.services.report import ReportService
from app.utils.audit import create_audit_log
from app.models.audit import AuditAction

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post("/", response_model=ReportResponse)
async def create_report(
    report_data: ReportCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Generate a forensic report for a case."""
    if current_user.role == UserRole.JUDGE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Judges have read-only access"
        )
    
    ip_address = request.client.host if request.client else None
    
    report = await ReportService.create_forensic_report(
        db=db,
        case_id=report_data.case_id,
        report_type=report_data.report_type,
        title=report_data.title,
        user=current_user,
        evidence_ids=report_data.evidence_ids,
        ip_address=ip_address
    )
    
    return report


@router.get("/case/{case_id}", response_model=List[ReportResponse])
async def list_case_reports(
    case_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """List all reports for a case."""
    reports = await ReportService.list_reports_for_case(db, case_id, current_user)
    return reports


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Get report by ID."""
    report = await ReportService.get_report(db, report_id, current_user)
    return report


@router.get("/{report_id}/download")
async def download_report(
    report_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Download report PDF."""
    report = await ReportService.get_report(db, report_id, current_user)
    
    if not report.file_path or not os.path.exists(report.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report file not found"
        )
    
    ip_address = request.client.host if request.client else None
    
    await create_audit_log(
        db=db,
        action=AuditAction.REPORT_DOWNLOAD,
        user_id=current_user.id,
        agency_id=current_user.agency_id,
        resource_type="report",
        resource_id=report.id,
        resource_uuid=report.uuid,
        ip_address=ip_address
    )
    
    return FileResponse(
        report.file_path,
        filename=f"{report.report_number}.pdf",
        media_type="application/pdf"
    )
