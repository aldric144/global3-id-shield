from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.analysis import AnalysisResult
from app.models.evidence import Evidence
from app.models.case import Case
from app.models.user import User
from app.schemas.analysis import AnalysisResultResponse
from app.services.auth import AuthService

router = APIRouter(prefix="/analysis", tags=["Analysis"])


@router.get("/{analysis_id}", response_model=AnalysisResultResponse)
async def get_analysis_result(
    analysis_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Get analysis result by ID."""
    result = await db.execute(
        select(AnalysisResult).where(AnalysisResult.id == analysis_id)
    )
    analysis = result.scalar_one_or_none()
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis result not found"
        )
    
    evidence_result = await db.execute(
        select(Evidence).where(Evidence.id == analysis.evidence_id)
    )
    evidence = evidence_result.scalar_one_or_none()
    
    case_result = await db.execute(
        select(Case).where(Case.id == evidence.case_id)
    )
    case = case_result.scalar_one_or_none()
    
    if case.agency_id != current_user.agency_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return analysis


@router.get("/case/{case_id}", response_model=List[AnalysisResultResponse])
async def get_case_analysis_results(
    case_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Get all analysis results for a case."""
    case_result = await db.execute(select(Case).where(Case.id == case_id))
    case = case_result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )
    
    if case.agency_id != current_user.agency_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    evidence_result = await db.execute(
        select(Evidence.id).where(Evidence.case_id == case_id)
    )
    evidence_ids = [e for e in evidence_result.scalars().all()]
    
    if not evidence_ids:
        return []
    
    analysis_result = await db.execute(
        select(AnalysisResult)
        .where(AnalysisResult.evidence_id.in_(evidence_ids))
        .order_by(AnalysisResult.created_at)
    )
    
    return list(analysis_result.scalars().all())
