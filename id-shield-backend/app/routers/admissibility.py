"""API endpoints for Evidence Admissibility computation and retrieval."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.database import get_db
from app.models.evidence import Evidence
from app.models.case import Case
from app.models.user import User
from app.models.admissibility import EvidenceQualityMetrics, EvidenceAdmissibility
from app.schemas.admissibility import (
    AdmissibilityResponse,
    QualityMetricsResponse,
    LimitationSchema,
    SuitabilityTagsSchema,
    get_grade_label
)
from app.services.auth import AuthService
from app.services.admissibility import compute_admissibility, get_admissibility

router = APIRouter(prefix="/analysis", tags=["Admissibility"])


def _sync_session_from_async(async_session: AsyncSession) -> Session:
    """Get sync session from async session for admissibility service.
    
    The admissibility service uses synchronous SQLAlchemy operations
    because it needs to read files and perform CPU-bound computations.
    """
    return async_session.sync_session


@router.post("/evidence/{evidence_id}/admissibility", response_model=AdmissibilityResponse)
async def compute_evidence_admissibility(
    evidence_id: int,
    force_recompute: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Compute admissibility data for evidence.
    
    Runs quality metrics computation, viability scoring, grade derivation,
    and limitations engine. Results are stored and returned.
    
    If admissibility has already been computed, returns existing data
    unless force_recompute=True.
    """
    # Get evidence
    result = await db.execute(
        select(Evidence).where(Evidence.id == evidence_id)
    )
    evidence = result.scalar_one_or_none()
    
    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence not found"
        )
    
    # Check access
    case_result = await db.execute(
        select(Case).where(Case.id == evidence.case_id)
    )
    case = case_result.scalar_one_or_none()
    
    if case.agency_id != current_user.agency_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Check if already computed
    if not force_recompute:
        existing = await db.execute(
            select(EvidenceAdmissibility).where(
                EvidenceAdmissibility.evidence_id == evidence_id
            )
        )
        existing_admissibility = existing.scalar_one_or_none()
        
        if existing_admissibility:
            metrics_result = await db.execute(
                select(EvidenceQualityMetrics).where(
                    EvidenceQualityMetrics.evidence_id == evidence_id
                )
            )
            metrics = metrics_result.scalar_one_or_none()
            
            return _build_response(evidence, metrics, existing_admissibility)
    
    # Delete existing if force recompute
    if force_recompute:
        await db.execute(
            EvidenceQualityMetrics.__table__.delete().where(
                EvidenceQualityMetrics.evidence_id == evidence_id
            )
        )
        await db.execute(
            EvidenceAdmissibility.__table__.delete().where(
                EvidenceAdmissibility.evidence_id == evidence_id
            )
        )
        await db.commit()
    
    # Compute admissibility using sync session
    sync_db = _sync_session_from_async(db)
    
    # Re-fetch evidence in sync session
    sync_evidence = sync_db.query(Evidence).filter(Evidence.id == evidence_id).first()
    
    quality_metrics, admissibility = compute_admissibility(
        db=sync_db,
        evidence=sync_evidence,
        user_id=current_user.id
    )
    
    return _build_response(evidence, quality_metrics, admissibility)


@router.get("/evidence/{evidence_id}/admissibility", response_model=AdmissibilityResponse)
async def get_evidence_admissibility(
    evidence_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Get stored admissibility data for evidence.
    
    Returns 404 if admissibility has not been computed yet.
    Use POST to compute admissibility first.
    """
    # Get evidence
    result = await db.execute(
        select(Evidence).where(Evidence.id == evidence_id)
    )
    evidence = result.scalar_one_or_none()
    
    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence not found"
        )
    
    # Check access
    case_result = await db.execute(
        select(Case).where(Case.id == evidence.case_id)
    )
    case = case_result.scalar_one_or_none()
    
    if case.agency_id != current_user.agency_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Get admissibility data
    metrics_result = await db.execute(
        select(EvidenceQualityMetrics).where(
            EvidenceQualityMetrics.evidence_id == evidence_id
        )
    )
    metrics = metrics_result.scalar_one_or_none()
    
    admissibility_result = await db.execute(
        select(EvidenceAdmissibility).where(
            EvidenceAdmissibility.evidence_id == evidence_id
        )
    )
    admissibility = admissibility_result.scalar_one_or_none()
    
    if not metrics or not admissibility:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admissibility not computed yet. Use POST to compute."
        )
    
    return _build_response(evidence, metrics, admissibility)


@router.get("/evidence/{evidence_id}/quality-metrics", response_model=QualityMetricsResponse)
async def get_evidence_quality_metrics(
    evidence_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Get raw quality metrics for evidence.
    
    Returns 404 if metrics have not been computed yet.
    """
    # Get evidence
    result = await db.execute(
        select(Evidence).where(Evidence.id == evidence_id)
    )
    evidence = result.scalar_one_or_none()
    
    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence not found"
        )
    
    # Check access
    case_result = await db.execute(
        select(Case).where(Case.id == evidence.case_id)
    )
    case = case_result.scalar_one_or_none()
    
    if case.agency_id != current_user.agency_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Get metrics
    metrics_result = await db.execute(
        select(EvidenceQualityMetrics).where(
            EvidenceQualityMetrics.evidence_id == evidence_id
        )
    )
    metrics = metrics_result.scalar_one_or_none()
    
    if not metrics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quality metrics not computed yet. Use POST /admissibility to compute."
        )
    
    return QualityMetricsResponse(
        evidence_id=evidence.id,
        evidence_uuid=evidence.uuid,
        metrics=metrics.metrics_json,
        viability_score=metrics.viability_score,
        thresholds_version=metrics.thresholds_version,
        computed_at=metrics.computed_at,
        computed_by=metrics.computed_by
    )


def _build_response(
    evidence: Evidence,
    metrics: EvidenceQualityMetrics,
    admissibility: EvidenceAdmissibility
) -> AdmissibilityResponse:
    """Build AdmissibilityResponse from models."""
    limitations = [
        LimitationSchema(**lim) for lim in admissibility.limitations_json
    ]
    
    suitability = SuitabilityTagsSchema(**admissibility.suitability_json)
    
    return AdmissibilityResponse(
        evidence_id=evidence.id,
        evidence_uuid=evidence.uuid,
        grade=admissibility.grade,
        grade_label=get_grade_label(admissibility.grade),
        viability_score=metrics.viability_score,
        suitability=suitability,
        limitations=limitations,
        limitations_count=len(limitations),
        thresholds_version=admissibility.thresholds_version,
        computed_at=admissibility.computed_at,
        computed_by=admissibility.computed_by
    )
