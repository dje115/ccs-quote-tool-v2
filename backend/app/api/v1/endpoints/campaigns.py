#!/usr/bin/env python3
"""
Campaign management endpoints  
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
import uuid
from datetime import datetime

from app.core.database import get_db
from app.core.dependencies import get_current_user, check_permission
from app.models.leads import LeadGenerationCampaign, LeadGenerationStatus
from app.models.tenant import User
from app.services.lead_generation_service import LeadGenerationService

router = APIRouter()


class CampaignCreate(BaseModel):
    name: str
    description: str | None = None
    prompt_type: str = "it_msp_expansion"
    postcode: str
    distance_miles: int = 20
    max_results: int = 100
    custom_prompt: str | None = None


class CampaignResponse(BaseModel):
    id: str
    name: str
    status: str
    postcode: str
    distance_miles: int
    total_found: int
    leads_created: int
    created_at: datetime
    
    class Config:
        from_attributes = True


@router.get("/", response_model=List[CampaignResponse])
async def list_campaigns(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List campaigns for current tenant"""
    campaigns = db.query(LeadGenerationCampaign).filter_by(
        tenant_id=current_user.tenant_id,
        is_deleted=False
    ).order_by(LeadGenerationCampaign.created_at.desc()).offset(skip).limit(limit).all()
    
    return campaigns


@router.post("/", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    campaign_data: CampaignCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(check_permission("lead:create")),
    db: Session = Depends(get_db)
):
    """Create and run new campaign"""
    
    try:
        campaign = LeadGenerationCampaign(
            id=str(uuid.uuid4()),
            tenant_id=current_user.tenant_id,
            name=campaign_data.name,
            description=campaign_data.description,
            prompt_type=campaign_data.prompt_type,
            postcode=campaign_data.postcode,
            distance_miles=campaign_data.distance_miles,
            max_results=campaign_data.max_results,
            custom_prompt=campaign_data.custom_prompt,
            status=LeadGenerationStatus.DRAFT,
            total_found=0,
            leads_created=0,
            duplicates_found=0,
            errors_count=0
        )
        
        db.add(campaign)
        db.commit()
        db.refresh(campaign)
        
        # Run campaign in background
        background_tasks.add_task(run_campaign_task, campaign.id, current_user.tenant_id, db)
        
        print(f"[OK] Campaign created and queued: {campaign.name}")
        
        return campaign
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating campaign: {str(e)}"
        )


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get campaign by ID"""
    campaign = db.query(LeadGenerationCampaign).filter_by(
        id=campaign_id,
        tenant_id=current_user.tenant_id,
        is_deleted=False
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    return campaign


@router.post("/{campaign_id}/stop", status_code=status.HTTP_200_OK)
async def stop_campaign(
    campaign_id: str,
    current_user: User = Depends(check_permission("lead:update")),
    db: Session = Depends(get_db)
):
    """Stop a running campaign"""
    campaign = db.query(LeadGenerationCampaign).filter_by(
        id=campaign_id,
        tenant_id=current_user.tenant_id
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if campaign.status == LeadGenerationStatus.RUNNING:
        campaign.status = LeadGenerationStatus.CANCELLED
        campaign.completed_at = datetime.utcnow()
        db.commit()
        
        return {"message": "Campaign stopped", "status": "cancelled"}
    
    return {"message": "Campaign not running", "status": campaign.status.value}


async def run_campaign_task(campaign_id: str, tenant_id: str, db: Session):
    """Background task to run campaign"""
    try:
        service = LeadGenerationService(db, tenant_id)
        campaign = db.query(LeadGenerationCampaign).filter_by(id=campaign_id).first()
        
        if campaign:
            await service.generate_leads(campaign)
            print(f"[OK] Campaign {campaign_id} completed")
        
    except Exception as e:
        print(f"[ERROR] Campaign {campaign_id} failed: {e}")
