#!/usr/bin/env python3
"""
Compliance endpoints

COMPLIANCE: Provides endpoints for GDPR, security monitoring, and compliance management.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
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


@router.get("/gdpr/sar-subjects")
def get_sar_subjects(
    search: Optional[str] = Query(None, description="Search term for name or email"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get list of contacts and users that can be subjects of SAR requests
    
    COMPLIANCE: Returns all contacts and users in the tenant's database for SAR selection.
    """
    from app.models.crm import Contact, Customer
    from app.models.tenant import User
    
    subjects = []
    
    # Get all contacts with their customer info
    query = db.query(Contact, Customer).join(
        Customer, Contact.customer_id == Customer.id
    ).filter(
        Customer.tenant_id == current_user.tenant_id,
        Customer.is_deleted == False,
        Contact.is_deleted == False
    )
    
    if search:
        search_lower = search.lower().strip()
        search_term = f"%{search_lower}%"
        
        # Split search into words for better matching
        search_words = search_lower.split()
        
        # Build search conditions
        conditions = [
            func.lower(Contact.email).like(search_term),
            func.lower(Customer.company_name).like(search_term)
        ]
        
        # Search in concatenated full name (PostgreSQL uses || for concatenation)
        from sqlalchemy import cast, String
        conditions.append(
            func.lower(
                cast(Contact.first_name, String) + ' ' + cast(Contact.last_name, String)
            ).like(search_term)
        )
        
        # Also search individual words in first_name or last_name
        for word in search_words:
            if len(word) > 1:  # Only search words longer than 1 character
                word_term = f"%{word}%"
                conditions.append(
                    or_(
                        func.lower(Contact.first_name).like(word_term),
                        func.lower(Contact.last_name).like(word_term)
                    )
                )
        
        query = query.filter(or_(*conditions))
    
    contacts = query.limit(100).all()
    
    for contact, customer in contacts:
        subjects.append({
            "id": contact.id,
            "type": "contact",
            "name": f"{contact.first_name} {contact.last_name}",
            "email": contact.email,
            "phone": contact.phone,
            "company": customer.company_name,
            "role": contact.job_title or (contact.role.value if contact.role else None)
        })
    
    # Get all users (User model doesn't have is_deleted, only is_active)
    user_query = db.query(User).filter(
        User.tenant_id == current_user.tenant_id,
        User.is_active == True
    )
    
    if search:
        search_lower = search.lower().strip()
        search_term = f"%{search_lower}%"
        
        # Split search into words for better matching
        search_words = search_lower.split()
        
        # Build search conditions
        conditions = [
            func.lower(User.email).like(search_term),
            func.lower(User.username).like(search_term)
        ]
        
        # Search in concatenated full name (PostgreSQL uses || for concatenation)
        from sqlalchemy import cast, String
        conditions.append(
            func.lower(
                cast(User.first_name, String) + ' ' + cast(User.last_name, String)
            ).like(search_term)
        )
        
        # Also search individual words in first_name or last_name
        for word in search_words:
            if len(word) > 1:  # Only search words longer than 1 character
                word_term = f"%{word}%"
                conditions.append(
                    or_(
                        func.lower(User.first_name).like(word_term),
                        func.lower(User.last_name).like(word_term)
                    )
                )
        
        user_query = user_query.filter(or_(*conditions))
    
    users = user_query.limit(100).all()
    
    for user in users:
        subjects.append({
            "id": user.id,
            "type": "user",
            "name": f"{user.first_name} {user.last_name}" if user.first_name and user.last_name else user.email,
            "email": user.email,
            "phone": user.phone,
            "company": None,
            "role": user.role.value if user.role else None
        })
    
    return {"subjects": subjects}


@router.get("/gdpr/sar-export", response_model=SARExport)
async def get_sar_export(
    contact_id: Optional[str] = Query(None, description="Contact ID to export data for"),
    user_id: Optional[str] = Query(None, description="User ID to export (defaults to current user if no contact_id)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate GDPR-compliant Subject Access Request (SAR) data export
    
    COMPLIANCE: Allows users to export personal data as required by GDPR Article 15.
    Can export data for a specific contact or user.
    
    SECURITY: Users can only export their own data unless they are super admins.
    Super admins can export data for any contact or user.
    """
    gdpr_service = GDPRService(db)
    
    # If contact_id is provided, use it (super admin only)
    if contact_id:
        if current_user.role.value != "super_admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only super admins can export data for contacts"
            )
        export = gdpr_service.generate_sar_export_for_person(
            tenant_id=current_user.tenant_id,
            contact_id=contact_id
        )
    else:
        # Users can only export their own data unless they are super admins
        target_user_id = user_id if user_id and current_user.role.value == "super_admin" else current_user.id
        export = gdpr_service.generate_sar_export_for_person(
            tenant_id=current_user.tenant_id,
            user_id=target_user_id
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

