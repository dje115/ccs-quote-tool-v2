#!/usr/bin/env python3
"""
Lead management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel
import uuid
from datetime import datetime

from app.core.database import get_async_db
from app.core.dependencies import get_current_user, get_current_tenant, check_permission
from app.models.leads import Lead, LeadStatus, LeadSource
from app.models.tenant import User, Tenant

router = APIRouter()


class LeadResponse(BaseModel):
    id: str
    company_name: str
    website: str | None
    status: str
    lead_score: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class LeadUpdate(BaseModel):
    status: LeadStatus | None = None
    lead_score: int | None = None
    contact_email: str | None = None
    contact_phone: str | None = None


class CompetitorLeadsCreate(BaseModel):
    """Schema for creating leads from competitor names"""
    company_names: List[str]
    source_customer_id: Optional[str] = None  # The customer whose competitors these are
    source_customer_name: Optional[str] = None


@router.get("/", response_model=List[LeadResponse])
async def list_leads(
    skip: int = 0,
    limit: int = 20,
    status: Optional[LeadStatus] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    List leads for current tenant
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    stmt = select(Lead).where(
        Lead.tenant_id == current_user.tenant_id,
        Lead.is_deleted == False
    )
    
    if status:
        stmt = stmt.where(Lead.status == status)
    
    stmt = stmt.order_by(Lead.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    leads = result.scalars().all()
    return leads


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get lead by ID
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    stmt = select(Lead).where(
        Lead.id == lead_id,
        Lead.tenant_id == current_user.tenant_id,
        Lead.is_deleted == False
    )
    result = await db.execute(stmt)
    lead = result.scalar_one_or_none()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    return lead


@router.put("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: str,
    lead_update: LeadUpdate,
    current_user: User = Depends(check_permission("lead:update")),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Update lead
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    stmt = select(Lead).where(
        Lead.id == lead_id,
        Lead.tenant_id == current_user.tenant_id,
        Lead.is_deleted == False
    )
    result = await db.execute(stmt)
    lead = result.scalar_one_or_none()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    if lead_update.status is not None:
        lead.status = lead_update.status
    if lead_update.lead_score is not None:
        lead.lead_score = lead_update.lead_score
    if lead_update.contact_email is not None:
        lead.contact_email = lead_update.contact_email
    if lead_update.contact_phone is not None:
        lead.contact_phone = lead_update.contact_phone
    
    await db.commit()
    await db.refresh(lead)
    
    return lead


@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lead(
    lead_id: str,
    current_user: User = Depends(check_permission("lead:delete")),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Soft delete lead
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    stmt = select(Lead).where(
        Lead.id == lead_id,
        Lead.tenant_id == current_user.tenant_id,
        Lead.is_deleted == False
    )
    result = await db.execute(stmt)
    lead = result.scalar_one_or_none()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    lead.is_deleted = True
    lead.deleted_at = datetime.utcnow()
    await db.commit()
    
    return None


@router.post("/from-competitors")
async def create_leads_from_competitors(
    data: CompetitorLeadsCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Create discovery leads from competitor company names
    These will be queued for AI analysis
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    created_leads = []
    skipped_duplicates = []
    
    for company_name in data.company_names:
        # Check if lead already exists
        stmt = select(Lead).where(
            Lead.tenant_id == current_user.tenant_id,
            Lead.company_name == company_name,
            Lead.is_deleted == False
        )
        result = await db.execute(stmt)
        existing_lead = result.scalar_one_or_none()
        
        if existing_lead:
            skipped_duplicates.append(company_name)
            continue
        
        # Create new lead
        lead = Lead(
            id=str(uuid.uuid4()),
            tenant_id=current_user.tenant_id,
            company_name=company_name,
            status=LeadStatus.DISCOVERY,
            source=LeadSource.COMPETITOR_ANALYSIS,
            lead_score=50,  # Default score
            qualification_reason=f"Competitor of {data.source_customer_name}" if data.source_customer_name else "Competitor analysis",
            created_at=datetime.utcnow()
        )
        
        db.add(lead)
        created_leads.append(company_name)
    
    await db.commit()
    
    return {
        "success": True,
        "created_count": len(created_leads),
        "skipped_count": len(skipped_duplicates),
        "created_leads": created_leads,
        "skipped_duplicates": skipped_duplicates,
        "message": f"Created {len(created_leads)} discovery leads from competitors"
    }


# ============================================================================
# Lead Intelligence Endpoints
# ============================================================================

@router.get("/{lead_id}/ai/analyze")
async def analyze_lead_with_ai(
    lead_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Analyze lead with AI and generate intelligence summary
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        from app.services.lead_intelligence_service import LeadIntelligenceService
        from app.core.database import SessionLocal
        from sqlalchemy import select, and_
        
        # Get lead
        stmt = select(Lead).where(
            and_(
                Lead.id == lead_id,
                Lead.tenant_id == current_user.tenant_id
            )
        )
        result = await db.execute(stmt)
        lead = result.scalar_one_or_none()
        
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        # Use sync session for AI service
        sync_db = SessionLocal()
        try:
            intelligence_service = LeadIntelligenceService(sync_db, current_user.tenant_id)
            analysis = await intelligence_service.analyze_lead(lead)
        finally:
            sync_db.close()
        
        return analysis
    
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error analyzing lead with AI: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing lead: {str(e)}"
        )


@router.get("/{lead_id}/ai/outreach-plan")
async def get_outreach_plan(
    lead_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Generate outreach plan for lead
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        from app.services.lead_intelligence_service import LeadIntelligenceService
        from app.core.database import SessionLocal
        from sqlalchemy import select, and_
        
        # Get lead
        stmt = select(Lead).where(
            and_(
                Lead.id == lead_id,
                Lead.tenant_id == current_user.tenant_id
            )
        )
        result = await db.execute(stmt)
        lead = result.scalar_one_or_none()
        
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        # Use sync session for AI service
        sync_db = SessionLocal()
        try:
            intelligence_service = LeadIntelligenceService(sync_db, current_user.tenant_id)
            plan = await intelligence_service.generate_outreach_plan(lead)
        finally:
            sync_db.close()
        
        return plan
    
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error generating outreach plan: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating outreach plan: {str(e)}"
        )


@router.get("/{lead_id}/ai/similar-leads")
async def get_similar_converted_leads(
    lead_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Find similar leads that recently converted
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        from app.services.lead_intelligence_service import LeadIntelligenceService
        from app.core.database import SessionLocal
        from sqlalchemy import select, and_
        
        # Get lead
        stmt = select(Lead).where(
            and_(
                Lead.id == lead_id,
                Lead.tenant_id == current_user.tenant_id
            )
        )
        result = await db.execute(stmt)
        lead = result.scalar_one_or_none()
        
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        # Use sync session for AI service
        sync_db = SessionLocal()
        try:
            intelligence_service = LeadIntelligenceService(sync_db, current_user.tenant_id)
            similar_leads = await intelligence_service.find_similar_converted_leads(lead)
        finally:
            sync_db.close()
        
        return {"similar_leads": similar_leads}
    
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error finding similar leads: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error finding similar leads: {str(e)}"
        )
