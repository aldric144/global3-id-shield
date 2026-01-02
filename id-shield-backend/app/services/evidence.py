import os
import uuid
import aiofiles
from datetime import datetime, timezone
from typing import Optional, List, BinaryIO, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, status, UploadFile

from app.models.evidence import Evidence, EvidenceType, EvidenceStatus
from app.models.case import Case
from app.models.user import User
from app.schemas.evidence import EvidenceCreate, EvidenceResponse
from app.utils.hashing import compute_file_hashes
from app.utils.audit import create_audit_log
from app.models.audit import AuditAction
from app.config import settings


class EvidenceService:
    
    @staticmethod
    def determine_evidence_type(mime_type: str) -> EvidenceType:
        if mime_type in settings.allowed_image_types:
            return EvidenceType.PHOTO
        elif mime_type in settings.allowed_video_types:
            return EvidenceType.VIDEO
        elif mime_type in settings.allowed_audio_types:
            return EvidenceType.AUDIO
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {mime_type}"
            )
    
    @staticmethod
    def generate_evidence_number(case_number: str, sequence: int) -> str:
        return f"{case_number}-EV{sequence:04d}"
    
    @staticmethod
    async def get_next_evidence_sequence(db: AsyncSession, case_id: int) -> int:
        result = await db.execute(
            select(func.count(Evidence.id)).where(Evidence.case_id == case_id)
        )
        count = result.scalar()
        return count + 1
    
    @staticmethod
    async def upload_evidence(
        db: AsyncSession,
        case_id: int,
        file: UploadFile,
        user: User,
        evidence_data: EvidenceCreate,
        ip_address: Optional[str] = None
    ) -> Evidence:
        result = await db.execute(select(Case).where(Case.id == case_id))
        case = result.scalar_one_or_none()
        
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Case not found"
            )
        
        if case.agency_id != user.agency_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this case"
            )
        
        if case.is_sealed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot add evidence to a sealed case"
            )
        
        content = await file.read()
        file_size = len(content)
        
        if file_size > settings.max_file_size_mb * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds maximum allowed ({settings.max_file_size_mb}MB)"
            )
        
        import io
        file_obj = io.BytesIO(content)
        sha256_hash, md5_hash = compute_file_hashes(file_obj)
        
        mime_type = file.content_type or "application/octet-stream"
        evidence_type = EvidenceService.determine_evidence_type(mime_type)
        
        sequence = await EvidenceService.get_next_evidence_sequence(db, case_id)
        evidence_number = EvidenceService.generate_evidence_number(case.case_number, sequence)
        
        file_ext = os.path.splitext(file.filename)[1] if file.filename else ""
        stored_filename = f"{uuid.uuid4()}{file_ext}"
        
        case_dir = os.path.join(settings.upload_dir, str(case.uuid))
        os.makedirs(case_dir, exist_ok=True)
        file_path = os.path.join(case_dir, stored_filename)
        
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        evidence = Evidence(
            evidence_number=evidence_number,
            case_id=case_id,
            uploaded_by=user.id,
            original_filename=file.filename or "unknown",
            stored_filename=stored_filename,
            file_path=file_path,
            evidence_type=evidence_type,
            mime_type=mime_type,
            file_size=file_size,
            sha256_hash=sha256_hash,
            md5_hash=md5_hash,
            status=EvidenceStatus.UPLOADED,
            description=evidence_data.description,
            source=evidence_data.source,
            collection_date=evidence_data.collection_date,
            collection_location=evidence_data.collection_location,
            collector_name=evidence_data.collector_name,
            is_locked=True,
            is_original=True
        )
        
        db.add(evidence)
        await db.commit()
        await db.refresh(evidence)
        
        await create_audit_log(
            db=db,
            action=AuditAction.EVIDENCE_UPLOAD,
            user_id=user.id,
            agency_id=user.agency_id,
            resource_type="evidence",
            resource_id=evidence.id,
            resource_uuid=evidence.uuid,
            ip_address=ip_address,
            details={
                "case_id": case_id,
                "evidence_number": evidence_number,
                "original_filename": file.filename,
                "file_size": file_size,
                "sha256_hash": sha256_hash,
                "md5_hash": md5_hash,
                "evidence_type": evidence_type.value
            }
        )
        
        return evidence
    
    @staticmethod
    async def get_evidence(
        db: AsyncSession,
        evidence_id: int,
        user: User
    ) -> Evidence:
        result = await db.execute(
            select(Evidence).where(Evidence.id == evidence_id)
        )
        evidence = result.scalar_one_or_none()
        
        if not evidence:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evidence not found"
            )
        
        case_result = await db.execute(select(Case).where(Case.id == evidence.case_id))
        case = case_result.scalar_one_or_none()
        
        if case.agency_id != user.agency_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this evidence"
            )
        
        await create_audit_log(
            db=db,
            action=AuditAction.EVIDENCE_VIEW,
            user_id=user.id,
            agency_id=user.agency_id,
            resource_type="evidence",
            resource_id=evidence.id,
            resource_uuid=evidence.uuid
        )
        
        return evidence
    
    @staticmethod
    async def list_evidence_for_case(
        db: AsyncSession,
        case_id: int,
        user: User
    ) -> List[Evidence]:
        case_result = await db.execute(select(Case).where(Case.id == case_id))
        case = case_result.scalar_one_or_none()
        
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Case not found"
            )
        
        if case.agency_id != user.agency_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this case"
            )
        
        result = await db.execute(
            select(Evidence)
            .where(Evidence.case_id == case_id)
            .order_by(Evidence.created_at.desc())
        )
        
        return list(result.scalars().all())
