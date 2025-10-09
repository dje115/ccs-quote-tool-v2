#!/usr/bin/env python3
"""
Lead management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import uuid
from datetime import datetime

from app.core.database import get_db
from app.core.dependencies import get_current_user, check_permission
from app.models.leads import Lead, LeadStatus, LeadSource
from app.models.tenant import User

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


@router.get("/", response_model=List[LeadResponse])
async def list_leads(
    skip: int = 0,
    limit: int = 20,
    status: Optional[LeadStatus] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List leads for current tenant"""
    query = db.query(Lead).filter_by(
        tenant_id=current_user.tenant_id,
        is_deleted=False
    )
    
    if status:
        query = query.filter_by(status=status)
    
    leads = query.order_by(Lead.created_at.desc()).offset(skip).limit(limit).all()
    return leads


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get lead by ID"""
    lead = db.query(Lead).filter_by(
        id=lead_id,
        tenant_id=current_user.tenant_id,
        is_deleted=False
    ).first()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    return lead


@router.put("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: str,
    lead_update: LeadUpdate,
    current_user: User = Depends(check_permission("lead:update")),
    db: Session = Depends(get_db)
):
    """Update lead"""
    lead = db.query(Lead).filter_by(
        id=lead_id,
        tenant_id=current_user.tenant_id,
        is_deleted=False
    ).first()
    
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
    
    db.commit()
    db.refresh(lead)
    
    return lead


@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lead(
    lead_id: str,
    current_user: User = Depends(check_permission("lead:delete")),
    db: Session = Depends(get_db)
):
    """Soft delete lead"""
    lead = db.query(Lead).filter_by(
        id=lead_id,
        tenant_id=current_user.tenant_id,
        is_deleted=False
    ).first()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    lead.is_deleted = True
    lead.deleted_at = datetime.utcnow()
    db.commit()
    
    return None
