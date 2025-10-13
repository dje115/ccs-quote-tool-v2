#!/usr/bin/env python3
"""
Campaign management endpoints for lead generation
Supports background processing via Celery for long-running campaigns
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import uuid
from datetime import datetime

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_tenant
from app.core.celery_app import celery_app
from app.models.leads import (
    LeadGenerationCampaign, Lead, LeadGenerationStatus, LeadStatus, LeadSource
)
from app.models.tenant import User, Tenant
from app.services.lead_generation_service import LeadGenerationService

router = APIRouter()


# ============================================================================
# Pydantic Schemas
# ============================================================================

class CampaignCreate(BaseModel):
    """Schema for creating a new campaign"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    prompt_type: str = Field(..., description="Campaign type (it_msp_expansion, education, etc.)")
    postcode: str = Field(..., description="UK postcode for search center")
    distance_miles: int = Field(default=20, ge=1, le=200)
    max_results: int = Field(default=100, ge=1, le=500)
    custom_prompt: Optional[str] = None
    
    # Advanced options
    include_existing_customers: bool = False
    exclude_duplicates: bool = True
    minimum_company_size: Optional[int] = None
    business_sectors: Optional[List[str]] = None


class CampaignUpdate(BaseModel):
    """Schema for updating campaign"""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class CampaignResponse(BaseModel):
    """Schema for campaign response"""
    id: str
    name: str
    description: Optional[str]
    prompt_type: str
    postcode: str
    distance_miles: int
    max_results: int
    status: str
    total_found: int
    leads_created: int
    duplicates_found: int
    errors_count: int
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class LeadResponse(BaseModel):
    """Schema for lead response"""
    id: str
    campaign_id: Optional[str]
    company_name: str
    website: Optional[str]
    address: Optional[str]
    postcode: Optional[str]
    business_sector: Optional[str]
    company_size: Optional[str]
    contact_name: Optional[str]
    contact_email: Optional[str]
    contact_phone: Optional[str]
    status: str
    lead_score: int
    source: str
    potential_project_value: Optional[float]
    timeline_estimate: Optional[str]
    company_registration: Optional[str]
    registration_confirmed: bool
    converted_to_customer_id: Optional[str]
    ai_analysis: Optional[Dict[str, Any]] = None  # AI analysis results
    linkedin_data: Optional[Dict[str, Any]] = None  # LinkedIn data
    companies_house_data: Optional[Dict[str, Any]] = None  # Companies House data
    google_maps_data: Optional[Dict[str, Any]] = None  # Google Maps data
    website_data: Optional[Dict[str, Any]] = None  # Website data
    created_at: datetime
    
    class Config:
        from_attributes = True


class LeadConvertRequest(BaseModel):
    """Schema for converting lead to customer"""
    lead_id: str


class CampaignPromptType(BaseModel):
    """Available campaign prompt types"""
    value: str
    label: str
    description: str
    requires_company_name: bool


# ============================================================================
# Campaign Endpoints
# ============================================================================

@router.get("/prompt-types", response_model=List[CampaignPromptType])
async def get_prompt_types():
    """Get available campaign prompt types"""
    return [
        {
            "value": "it_msp_expansion",
            "label": "IT/MSP Expansion",
            "description": "Find IT/MSP businesses that could add cabling to their portfolio",
            "requires_company_name": False
        },
        {
            "value": "it_msp_gaps",
            "label": "IT/MSP Service Gaps",
            "description": "Find IT/MSP businesses with gaps in service offerings",
            "requires_company_name": False
        },
        {
            "value": "similar_business",
            "label": "Similar Business Lookup",
            "description": "Find businesses similar to a specific company",
            "requires_company_name": True
        },
        {
            "value": "education",
            "label": "Education Sector",
            "description": "Find schools and educational institutions",
            "requires_company_name": False
        },
        {
            "value": "healthcare",
            "label": "Healthcare Facilities",
            "description": "Find healthcare facilities needing network upgrades",
            "requires_company_name": False
        },
        {
            "value": "manufacturing",
            "label": "Manufacturing",
            "description": "Find manufacturing companies modernizing operations",
            "requires_company_name": False
        },
        {
            "value": "retail_office",
            "label": "Retail & Office",
            "description": "Find retail and office businesses renovating/expanding",
            "requires_company_name": False
        },
        {
            "value": "new_businesses",
            "label": "New Businesses",
            "description": "Find recently opened businesses needing IT infrastructure",
            "requires_company_name": False
        },
        {
            "value": "planning_applications",
            "label": "Planning Applications",
            "description": "Find businesses with construction/renovation plans",
            "requires_company_name": False
        }
    ]


@router.get("/", response_model=List[CampaignResponse])
async def list_campaigns(
    skip: int = 0,
    limit: int = 50,
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """List campaigns for current tenant"""
    query = db.query(LeadGenerationCampaign).filter(
        and_(
            LeadGenerationCampaign.tenant_id == current_tenant.id,
            LeadGenerationCampaign.is_deleted == False
        )
    )
    
    # Apply status filter if provided
    if status_filter:
        try:
            status_enum = LeadGenerationStatus[status_filter.upper()]
            query = query.filter(LeadGenerationCampaign.status == status_enum)
        except KeyError:
            pass  # Invalid status, ignore filter
    
    campaigns = query.order_by(
        desc(LeadGenerationCampaign.created_at)
    ).offset(skip).limit(limit).all()
    
    return campaigns


@router.post("/", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    campaign_data: CampaignCreate,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Create new lead generation campaign in DRAFT status
    
    Campaign must be explicitly started using POST /{campaign_id}/start
    This allows for review and configuration before execution
    """
    
    try:
        # Create campaign record
        campaign = LeadGenerationCampaign(
            id=str(uuid.uuid4()),
            tenant_id=current_tenant.id,
            created_by=current_user.id,
            name=campaign_data.name,
            description=campaign_data.description,
            prompt_type=campaign_data.prompt_type,
            postcode=campaign_data.postcode,
            distance_miles=campaign_data.distance_miles,
            max_results=campaign_data.max_results,
            custom_prompt=campaign_data.custom_prompt,
            include_existing_customers=campaign_data.include_existing_customers,
            exclude_duplicates=campaign_data.exclude_duplicates,
            minimum_company_size=campaign_data.minimum_company_size,
            business_sectors=campaign_data.business_sectors,
            status=LeadGenerationStatus.DRAFT,
            total_found=0,
            leads_created=0,
            duplicates_found=0,
            errors_count=0
        )
        
        db.add(campaign)
        db.commit()
        db.refresh(campaign)
        
        print(f"[OK] Campaign created: {campaign.name} ({campaign.id}) - Status: DRAFT")
        print(f"[OK] Use POST /{campaign.id}/start to begin lead generation")
        
        return campaign
        
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Failed to create campaign: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating campaign: {str(e)}"
        )


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Get campaign by ID"""
    campaign = db.query(LeadGenerationCampaign).filter(
        and_(
            LeadGenerationCampaign.id == campaign_id,
            LeadGenerationCampaign.tenant_id == current_tenant.id,
            LeadGenerationCampaign.is_deleted == False
        )
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    return campaign


@router.patch("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: str,
    update_data: CampaignUpdate,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Update campaign (limited fields)"""
    campaign = db.query(LeadGenerationCampaign).filter(
        and_(
            LeadGenerationCampaign.id == campaign_id,
            LeadGenerationCampaign.tenant_id == current_tenant.id
        )
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Update allowed fields
    if update_data.name:
        campaign.name = update_data.name
    if update_data.description is not None:
        campaign.description = update_data.description
    
    campaign.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(campaign)
    
    return campaign


@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Soft delete campaign"""
    campaign = db.query(LeadGenerationCampaign).filter(
        and_(
            LeadGenerationCampaign.id == campaign_id,
            LeadGenerationCampaign.tenant_id == current_tenant.id
        )
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    campaign.is_deleted = True
    campaign.updated_at = datetime.utcnow()
    db.commit()
    
    return None


@router.post("/{campaign_id}/start", status_code=status.HTTP_200_OK)
async def start_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Start a draft campaign using Celery background task
    Campaign will execute asynchronously in a separate worker process
    """
    campaign = db.query(LeadGenerationCampaign).filter(
        and_(
            LeadGenerationCampaign.id == campaign_id,
            LeadGenerationCampaign.tenant_id == current_tenant.id
        )
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if campaign.status != LeadGenerationStatus.DRAFT:
        raise HTTPException(
            status_code=400,
            detail=f"Can only start campaigns with DRAFT status. Current status: {campaign.status}"
        )
    
    # Update campaign status to QUEUED before sending to Celery
    campaign.status = LeadGenerationStatus.QUEUED
    campaign.updated_at = datetime.utcnow()
    db.commit()
    
    # Queue campaign task to Celery
    print(f"\n{'='*80}")
    print(f"🚀 QUEUEING CAMPAIGN TO CELERY")
    print(f"Campaign: {campaign.name} ({campaign.id})")
    print(f"Tenant: {current_tenant.name} ({current_tenant.id})")
    print(f"{'='*80}\n")
    
    # Use send_task() to queue the task by name
    task = celery_app.send_task(
        'run_campaign',
        args=[str(campaign.id), str(current_tenant.id)]
    )
    
    print(f"✓ Celery task created: {task.id}")
    
    return {
        "success": True,
        "message": f"Campaign '{campaign.name}' queued for execution",
        "campaign_id": str(campaign.id),
        "task_id": task.id,
        "status": "queued"
    }


@router.post("/{campaign_id}/restart", status_code=status.HTTP_200_OK)
async def restart_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Restart a completed, failed, or cancelled campaign using Celery
    Campaign will execute asynchronously in a separate worker process
    """
    campaign = db.query(LeadGenerationCampaign).filter(
        and_(
            LeadGenerationCampaign.id == campaign_id,
            LeadGenerationCampaign.tenant_id == current_tenant.id
        )
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if campaign.status in [LeadGenerationStatus.DRAFT, LeadGenerationStatus.RUNNING, LeadGenerationStatus.QUEUED]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot restart campaign with status: {campaign.status}. Use /start for DRAFT or /stop for RUNNING campaigns."
        )
    
    # Reset campaign stats
    campaign.status = LeadGenerationStatus.QUEUED
    campaign.total_found = 0
    campaign.leads_created = 0
    campaign.duplicates_found = 0
    campaign.errors_count = 0
    campaign.started_at = None
    campaign.completed_at = None
    campaign.updated_at = datetime.utcnow()
    campaign.updated_by = current_user.id
    db.commit()
    
    # Queue campaign task to Celery
    print(f"\n{'='*80}")
    print(f"🔄 RESTARTING CAMPAIGN VIA CELERY")
    print(f"Campaign: {campaign.name} ({campaign.id})")
    print(f"Tenant: {current_tenant.name} ({current_tenant.id})")
    print(f"{'='*80}\n")
    
    # Use send_task() to queue the task by name
    task = celery_app.send_task(
        'run_campaign',
        args=[str(campaign.id), str(current_tenant.id)]
    )
    
    print(f"✓ Celery task created: {task.id}")
    
    return {
        "success": True,
        "message": f"Campaign '{campaign.name}' queued for restart",
        "campaign_id": str(campaign.id),
        "task_id": task.id,
        "status": "queued"
    }


@router.post("/{campaign_id}/reset-to-draft", status_code=status.HTTP_200_OK)
async def reset_campaign_to_draft(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Reset a queued campaign back to draft status
    
    Allows users to un-queue a campaign before it starts executing.
    Only works for QUEUED campaigns.
    """
    campaign = db.query(LeadGenerationCampaign).filter(
        and_(
            LeadGenerationCampaign.id == campaign_id,
            LeadGenerationCampaign.tenant_id == current_tenant.id
        )
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if campaign.status != LeadGenerationStatus.QUEUED:
        raise HTTPException(
            status_code=400,
            detail=f"Can only reset QUEUED campaigns to draft. Current status: {campaign.status.value}"
        )
    
    # Reset to draft
    campaign.status = LeadGenerationStatus.DRAFT
    campaign.updated_at = datetime.utcnow()
    campaign.updated_by = current_user.id
    db.commit()
    
    print(f"[OK] Campaign {campaign.id} reset to DRAFT by user {current_user.email}")
    
    return {
        "success": True,
        "message": f"Campaign '{campaign.name}' reset to draft",
        "campaign_id": str(campaign.id),
        "status": "draft"
    }


@router.post("/{campaign_id}/stop", status_code=status.HTTP_200_OK)
async def stop_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Stop/cancel a running or queued campaign
    
    - RUNNING campaigns: Sets status to CANCELLED (task may continue until it checks status)
    - QUEUED campaigns: Sets status to CANCELLED (task will be skipped when worker picks it up)
    """
    campaign = db.query(LeadGenerationCampaign).filter(
        and_(
            LeadGenerationCampaign.id == campaign_id,
            LeadGenerationCampaign.tenant_id == current_tenant.id
        )
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if campaign.status in [LeadGenerationStatus.RUNNING, LeadGenerationStatus.QUEUED]:
        campaign.status = LeadGenerationStatus.CANCELLED
        campaign.completed_at = datetime.utcnow()
        campaign.updated_at = datetime.utcnow()
        campaign.updated_by = current_user.id
        db.commit()
        
        message = "Campaign cancelled" if campaign.status == LeadGenerationStatus.QUEUED else "Campaign stopped"
        
        print(f"[OK] Campaign {campaign.id} cancelled by user {current_user.email}")
        
        return {
            "success": True,
            "message": message,
            "status": "cancelled"
        }
    
    return {
        "success": False,
        "message": f"Cannot stop campaign with status: {campaign.status.value}",
        "status": campaign.status.value
    }


# ============================================================================
# Lead Endpoints
# ============================================================================

@router.get("/{campaign_id}/leads", response_model=List[LeadResponse])
async def get_campaign_leads(
    campaign_id: str,
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    min_score: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Get leads for a specific campaign"""
    # Verify campaign belongs to tenant
    campaign = db.query(LeadGenerationCampaign).filter(
        and_(
            LeadGenerationCampaign.id == campaign_id,
            LeadGenerationCampaign.tenant_id == current_tenant.id
        )
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Build query
    query = db.query(Lead).filter(
        and_(
            Lead.campaign_id == campaign_id,
            Lead.tenant_id == current_tenant.id,
            Lead.is_deleted == False
        )
    )
    
    # Apply filters
    if status_filter:
        try:
            status_enum = LeadStatus[status_filter.upper()]
            query = query.filter(Lead.status == status_enum)
        except KeyError:
            pass
    
    if min_score is not None:
        query = query.filter(Lead.lead_score >= min_score)
    
    # Order by score and creation date
    leads = query.order_by(
        desc(Lead.lead_score),
        desc(Lead.created_at)
    ).offset(skip).limit(limit).all()
    
    return leads


@router.get("/leads/all", response_model=List[LeadResponse])
async def list_all_leads(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    min_score: Optional[int] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """List all leads across all campaigns for the tenant"""
    query = db.query(Lead).filter(
        and_(
            Lead.tenant_id == current_tenant.id,
            Lead.is_deleted == False
        )
    )
    
    # Apply filters
    if status_filter:
        try:
            status_enum = LeadStatus[status_filter.upper()]
            query = query.filter(Lead.status == status_enum)
        except KeyError:
            pass
    
    if min_score is not None:
        query = query.filter(Lead.lead_score >= min_score)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Lead.company_name.ilike(search_pattern),
                Lead.contact_email.ilike(search_pattern),
                Lead.business_sector.ilike(search_pattern)
            )
        )
    
    leads = query.order_by(
        desc(Lead.lead_score),
        desc(Lead.created_at)
    ).offset(skip).limit(limit).all()
    
    return leads


@router.get("/leads/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Get lead by ID"""
    lead = db.query(Lead).filter(
        and_(
            Lead.id == lead_id,
            Lead.tenant_id == current_tenant.id,
            Lead.is_deleted == False
        )
    ).first()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    return lead


@router.post("/leads/{lead_id}/convert", status_code=status.HTTP_200_OK)
async def convert_lead_to_customer(
    lead_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Convert Discovery (Campaign Lead) to CRM Lead
    
    Creates a Customer record with LEAD status (first stage in CRM pipeline)
    
    Workflow:
    - DISCOVERY (Campaign Lead) → LEAD (CRM)
    - LEAD → PROSPECT → OPPORTUNITY → CUSTOMER
    - or LEAD → PROSPECT → CUSTOMER
    """
    service = LeadGenerationService(db, current_tenant.id)
    result = await service.convert_lead_to_customer(lead_id, current_user.id)
    
    if not result['success']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result['error']
        )
    
    return result


@router.post("/leads/{lead_id}/analyze", status_code=status.HTTP_200_OK)
async def analyze_lead(
    lead_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Run AI analysis on a discovery/lead
    
    Analyzes the company using GPT-5-mini with all available data:
    - External data (Google Maps, Companies House, LinkedIn)
    - Website information
    - Financial data
    - Director information
    
    Returns comprehensive business intelligence including:
    - Business sector and size
    - Technology needs and maturity
    - Financial health analysis
    - Growth potential
    - Competitive landscape
    - Business opportunities and risks
    """
    service = LeadGenerationService(db, current_tenant.id)
    result = await service.analyze_lead_with_ai(lead_id)
    
    if not result['success']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result['error']
        )
    
    return result


# ============================================================================
# Background Task Functions
# ============================================================================

def run_campaign_task(campaign_id: str, tenant_id: str):
    """
    Background task to run campaign (SYNC function for BackgroundTasks)
    This runs outside the request/response cycle
    
    Note: For production, this should be moved to Celery for better
    scalability and reliability
    """
    import asyncio
    
    try:
        print(f"\n🚀 [BACKGROUND] Starting campaign {campaign_id}")
        
        # Create new database session for background task
        from app.core.database import SessionLocal
        bg_db = SessionLocal()
        
        try:
            # Initialize service
            service = LeadGenerationService(bg_db, tenant_id)
            
            # Get campaign
            campaign = bg_db.query(LeadGenerationCampaign).filter_by(
                id=campaign_id
            ).first()
            
            if not campaign:
                print(f"❌ [BACKGROUND] Campaign {campaign_id} not found")
                return
            
            # Run lead generation (must use asyncio.run for async function)
            result = asyncio.run(service.generate_leads(campaign))
            
            if result['success']:
                print(f"✅ [BACKGROUND] Campaign {campaign_id} completed successfully")
                print(f"   Leads created: {result.get('leads_created', 0)}")
            else:
                print(f"❌ [BACKGROUND] Campaign {campaign_id} failed: {result.get('error')}")
        
        finally:
            bg_db.close()
        
    except Exception as e:
        print(f"💥 [BACKGROUND] Campaign {campaign_id} crashed: {e}")
        import traceback
        traceback.print_exc()
