from typing import Optional, Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit import AuditLog, AuditAction


async def create_audit_log(
    db: AsyncSession,
    action: AuditAction,
    user_id: Optional[int] = None,
    agency_id: Optional[int] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[int] = None,
    resource_uuid: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    previous_state: Optional[Dict[str, Any]] = None,
    new_state: Optional[Dict[str, Any]] = None,
    success: bool = True,
    error_message: Optional[str] = None
) -> AuditLog:
    """
    Create an audit log entry for chain-of-custody tracking.
    
    Every significant action in the system must be logged:
    - User authentication events
    - Case creation/modification
    - Evidence upload/access
    - Analysis execution
    - Report generation
    
    This is critical for legal defensibility.
    """
    audit_log = AuditLog(
        user_id=user_id,
        agency_id=agency_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        resource_uuid=resource_uuid,
        ip_address=ip_address,
        user_agent=user_agent,
        details=details,
        previous_state=previous_state,
        new_state=new_state,
        success=1 if success else 0,
        error_message=error_message
    )
    
    db.add(audit_log)
    await db.commit()
    await db.refresh(audit_log)
    
    return audit_log
