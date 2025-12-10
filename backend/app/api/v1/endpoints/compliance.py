#!/usr/bin/env python3
"""
Compliance endpoints

COMPLIANCE: Provides endpoints for GDPR, security monitoring, and compliance management.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from pydantic import BaseModel

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_super_admin
from app.models.tenant import User
from app.services.gdpr_service import GDPRService
from app.services.security_event_service import SecurityEventService
from app.models.security_event import SecurityEvent, SecurityEventType, SecurityEventSeverity

router = APIRouter()


# GDPR Models
class DataCollectionAnalysis(BaseModel):
    """Data collection analysis response"""
    data_categories: dict
    data_retention: dict
    data_sharing: dict
    data_subject_rights: dict
    security_measures: list
    last_updated: str


class SARExport(BaseModel):
    """Subject Access Request export"""
    export_date: str
    user_id: str
    tenant_id: str
    data: dict


class GDPRPolicyRequest(BaseModel):
    """Request to generate GDPR policy"""
    include_iso_sections: bool = False


class GDPRPolicyResponse(BaseModel):
    """Generated GDPR policy"""
    policy: str
    generated_at: str
    based_on_analysis: dict


# Security Event Models (reuse from security.py)
class SecurityEventResponse(BaseModel):
    """Response model for security events"""
    id: str
    tenant_id: Optional[str]
    user_id: Optional[str]
    event_type: str
    severity: str
    description: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    metadata: Optional[dict]
    resolved: Optional[str]
    resolved_at: Optional[datetime]
    occurred_at: datetime
    
    class Config:
        from_attributes = True


# GDPR Endpoints
@router.get("/gdpr/data-analysis", response_model=DataCollectionAnalysis)
async def get_data_collection_analysis(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get analysis of what personal data is collected and why
    
    COMPLIANCE: Provides transparency about data collection for GDPR compliance.
    """
    gdpr_service = GDPRService(db)
    analysis = gdpr_service.analyze_data_collection(tenant_id=current_user.tenant_id)
    
    return analysis


@router.get("/gdpr/sar-export", response_model=SARExport)
async def get_sar_export(
    user_id: Optional[str] = Query(None, description="User ID to export (defaults to current user)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate Subject Access Request (SAR) data export
    
    COMPLIANCE: Allows users to export all their personal data as required by GDPR Article 15.
    
    SECURITY: Users can only export their own data unless they are super admins.
    """
    # Users can only export their own data unless they are super admins
    target_user_id = user_id if user_id and current_user.role.value == "super_admin" else current_user.id
    
    gdpr_service = GDPRService(db)
    export = gdpr_service.generate_sar_export(
        user_id=target_user_id,
        tenant_id=current_user.tenant_id
    )
    
    return export


@router.post("/gdpr/generate-policy", response_model=GDPRPolicyResponse)
async def generate_gdpr_policy(
    request: GDPRPolicyRequest,
    current_user: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
    """
    Generate GDPR privacy policy using AI
    
    COMPLIANCE: Uses AI to generate a GDPR-compliant privacy policy based on actual data collection.
    
    SECURITY: Only accessible to super admins.
    """
    from datetime import datetime, timezone
    
    gdpr_service = GDPRService(db)
    analysis = gdpr_service.analyze_data_collection(tenant_id=current_user.tenant_id)
    
    try:
        policy = await gdpr_service.generate_privacy_policy(
            tenant_id=current_user.tenant_id,
            use_ai=True,
            include_iso=request.include_iso_sections
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate policy: {str(e)}"
        )
    
    # Convert datetime to ISO string if needed
    generated_at = policy.generated_at
    if hasattr(generated_at, 'isoformat'):
        generated_at_str = generated_at.isoformat()
    else:
        generated_at_str = str(generated_at)
    
    return {
        "policy": policy.content,
        "generated_at": generated_at_str,
        "based_on_analysis": analysis
    }


# Security Monitoring Endpoints (reuse from security.py)
@router.get("/security/events")
async def get_security_events(
    tenant_id: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    hours: int = Query(24),
    limit: int = Query(100),
    current_user: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
    """Get recent security events (super admin only)"""
    from app.api.v1.endpoints.security import get_security_events as _get_security_events
    return await _get_security_events(
        tenant_id=tenant_id,
        user_id=user_id,
        event_type=event_type,
        severity=severity,
        hours=hours,
        limit=limit,
        current_user=current_user,
        db=db
    )


@router.get("/security/statistics")
async def get_security_statistics(
    tenant_id: Optional[str] = Query(None),
    hours: int = Query(24),
    current_user: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
    """Get security event statistics (super admin only)"""
    from app.api.v1.endpoints.security import get_security_statistics as _get_security_statistics
    return await _get_security_statistics(
        tenant_id=tenant_id,
        hours=hours,
        current_user=current_user,
        db=db
    )

