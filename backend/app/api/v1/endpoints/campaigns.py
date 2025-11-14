from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import time
import json
import uuid

from app.core.dependencies import get_db, get_current_user
from app.models.tenant import User, Tenant
from app.models.leads import LeadGenerationCampaign, LeadGenerationStatus, Lead, LeadStatus
from app.models.crm import Customer, CustomerStatus, BusinessSector, BusinessSize
from app.schemas.campaign import CampaignCreate, CampaignResponse
from app.services.lead_generation_service import LeadGenerationService
from app.tasks.lead_generation_tasks import run_lead_generation_campaign, test_lead_generation_campaign

router = APIRouter()

@router.post("/", response_model=CampaignResponse)
async def create_campaign(
    campaign_data: CampaignCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new lead generation campaign"""
    try:
        # Create campaign record in database
        campaign = LeadGenerationCampaign(
            name=campaign_data.name,
            description=campaign_data.description,
            business_sectors=[campaign_data.sector_name] if campaign_data.sector_name else ["General Business"],  # Store sector_name as business_sectors array
            postcode=campaign_data.postcode,
            distance_miles=campaign_data.distance_miles,
            max_results=campaign_data.max_results,
            prompt_type=campaign_data.prompt_type,
            custom_prompt=campaign_data.custom_prompt,
            company_size_category=campaign_data.company_size_category,
            # Company list campaign fields
            company_names=campaign_data.company_names,
            exclude_duplicates=campaign_data.exclude_duplicates if campaign_data.exclude_duplicates is not None else True,
            include_existing_customers=campaign_data.include_existing_customers if campaign_data.include_existing_customers is not None else False,
            status=LeadGenerationStatus.DRAFT,
            tenant_id=current_user.tenant_id,
            created_by=current_user.id
        )
        
        db.add(campaign)
        db.commit()
        db.refresh(campaign)
        
        return CampaignResponse.from_orm(campaign)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create campaign: {str(e)}"
        )

@router.get("/", response_model=List[CampaignResponse])
def get_campaigns(
    skip: int = 0,
    limit: int = 100,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all campaigns for the current tenant with sorting"""
    try:
        # Build query with sorting
        query = db.query(LeadGenerationCampaign).filter(
            LeadGenerationCampaign.tenant_id == current_user.tenant_id,
            LeadGenerationCampaign.is_deleted == False
        )
        
        # Apply sorting
        if sort_by == "name":
            query = query.order_by(LeadGenerationCampaign.name.asc() if sort_order == "asc" else LeadGenerationCampaign.name.desc())
        elif sort_by == "status":
            query = query.order_by(LeadGenerationCampaign.status.asc() if sort_order == "asc" else LeadGenerationCampaign.status.desc())
        elif sort_by == "leads_created" or sort_by == "total_leads":
            query = query.order_by(LeadGenerationCampaign.leads_created.asc() if sort_order == "asc" else LeadGenerationCampaign.leads_created.desc())
        elif sort_by == "created_at":
            query = query.order_by(LeadGenerationCampaign.created_at.asc() if sort_order == "asc" else LeadGenerationCampaign.created_at.desc())
        else:
            query = query.order_by(LeadGenerationCampaign.created_at.desc())
        
        campaigns = query.offset(skip).limit(limit).all()
        
        return [CampaignResponse.from_orm(campaign) for campaign in campaigns]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve campaigns: {str(e)}"
        )

@router.get("/{campaign_id}", response_model=CampaignResponse)
def get_campaign(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific campaign by ID"""
    campaign = db.query(LeadGenerationCampaign).filter(
        LeadGenerationCampaign.id == campaign_id,
        LeadGenerationCampaign.tenant_id == current_user.tenant_id
    ).first()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    return CampaignResponse.from_orm(campaign)

@router.post("/{campaign_id}/start")
def start_campaign(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start a lead generation campaign"""
    try:
        # Get the campaign from database
        campaign = db.query(LeadGenerationCampaign).filter(
            LeadGenerationCampaign.id == campaign_id,
            LeadGenerationCampaign.tenant_id == current_user.tenant_id
        ).first()
        
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        # Update campaign status to running
        campaign.status = LeadGenerationStatus.RUNNING
        db.commit()
        
        # Start the real lead generation campaign
        task = run_lead_generation_campaign.delay(
            {
                "id": campaign.id,  # Add the campaign ID!
                "name": campaign.name,
                "description": campaign.description,
                "sector_name": campaign.business_sectors[0] if campaign.business_sectors else "General Business",
                "postcode": campaign.postcode,
                "distance_miles": campaign.distance_miles,
                "max_results": campaign.max_results,
                "prompt_type": campaign.prompt_type,
                "custom_prompt": campaign.custom_prompt,
                "company_size_category": campaign.company_size_category,
                # Company list campaign fields
                "company_names": campaign.company_names,
                "exclude_duplicates": campaign.exclude_duplicates,
                "include_existing_customers": campaign.include_existing_customers
            },
            current_user.tenant_id
        )
        
        return {
            "message": "Campaign started successfully",
            "task_id": task.id,
            "status": "running"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start campaign: {str(e)}"
        )

@router.post("/{campaign_id}/stop")
def stop_campaign(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Stop a running campaign"""
    try:
        campaign = db.query(LeadGenerationCampaign).filter(
            LeadGenerationCampaign.id == campaign_id,
            LeadGenerationCampaign.tenant_id == current_user.tenant_id
        ).first()
        
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        campaign.status = LeadGenerationStatus.CANCELLED
        db.commit()
        
        # Publish campaign status change event (stopped)
        from app.core.events import get_event_publisher
        event_publisher = get_event_publisher()
        event_publisher.publish_campaign_failed(
            tenant_id=current_user.tenant_id,
            campaign_id=campaign_id,
            campaign_name=campaign.name,
            error="Campaign stopped by user"
        )
        
        return {"message": "Campaign stopped successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop campaign: {str(e)}"
        )

@router.post("/{campaign_id}/pause")
def pause_campaign(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Pause a running campaign"""
    try:
        campaign = db.query(LeadGenerationCampaign).filter(
            LeadGenerationCampaign.id == campaign_id,
            LeadGenerationCampaign.tenant_id == current_user.tenant_id
        ).first()
        
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        # Note: We don't have a PAUSED status, so we'll use DRAFT
        campaign.status = LeadGenerationStatus.DRAFT
        db.commit()
        
        return {"message": "Campaign paused successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to pause campaign: {str(e)}"
        )

@router.post("/{campaign_id}/restart")
def restart_campaign(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Restart a paused or failed campaign"""
    try:
        # Get the campaign from database
        campaign = db.query(LeadGenerationCampaign).filter(
            LeadGenerationCampaign.id == campaign_id,
            LeadGenerationCampaign.tenant_id == current_user.tenant_id
        ).first()
        
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        # Update campaign status to running
        campaign.status = LeadGenerationStatus.RUNNING
        db.commit()
        
        # Start the real lead generation campaign
        task = run_lead_generation_campaign.delay(
            {
                "id": campaign.id,  # Add the campaign ID!
                "name": campaign.name,
                "description": campaign.description,
                "sector_name": campaign.business_sectors[0] if campaign.business_sectors else "General Business",
                "postcode": campaign.postcode,
                "distance_miles": campaign.distance_miles,
                "max_results": campaign.max_results,
                "prompt_type": campaign.prompt_type,
                "custom_prompt": campaign.custom_prompt,
                "company_size_category": campaign.company_size_category,
                # Company list campaign fields
                "company_names": campaign.company_names,
                "exclude_duplicates": campaign.exclude_duplicates,
                "include_existing_customers": campaign.include_existing_customers
            },
            current_user.tenant_id
        )
        
        return {
            "message": "Campaign restarted successfully",
            "task_id": task.id,
            "status": "running"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restart campaign: {str(e)}"
        )

@router.delete("/{campaign_id}")
def delete_campaign(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a campaign"""
    try:
        print(f"🗑️ Delete campaign request: {campaign_id} for tenant: {current_user.tenant_id}")
        
        campaign = db.query(LeadGenerationCampaign).filter(
            LeadGenerationCampaign.id == campaign_id,
            LeadGenerationCampaign.tenant_id == current_user.tenant_id
        ).first()
        
        if not campaign:
            print(f"❌ Campaign not found: {campaign_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        print(f"✅ Found campaign: {campaign.name} (status: {campaign.status})")
        
        # Soft delete by marking as deleted
        campaign.is_deleted = True
        campaign.deleted_at = datetime.now(timezone.utc)
        db.commit()
        
        print(f"✅ Campaign deleted successfully: {campaign_id}")
        return {"message": "Campaign deleted successfully"}
    except Exception as e:
        print(f"❌ Delete campaign error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete campaign: {str(e)}"
        )

def _safe_json_parse(json_string: Optional[str]) -> Dict[str, Any]:
    """Safely parse JSON string, return empty dict if invalid"""
    if not json_string or json_string.strip() == "":
        return {}
    try:
        return json.loads(json_string)
    except (json.JSONDecodeError, TypeError):
        return {}

def _safe_parse_ai_analysis(ai_analysis):
    """Safely parse ai_analysis field that might be string or dict"""
    if ai_analysis is None:
        return None
    if isinstance(ai_analysis, dict):
        return ai_analysis
    if isinstance(ai_analysis, str):
        try:
            import json
            return json.loads(ai_analysis)
        except (json.JSONDecodeError, TypeError):
            # If it's not valid JSON, wrap it in a dict
            return {"raw": ai_analysis}
    return None

@router.get("/leads/all")
def get_all_leads(
    skip: int = 0,
    limit: int = 100,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all leads (discoveries) for the current tenant with campaign information"""
    try:
        # Build query with sorting
        query = db.query(Lead).filter(
            Lead.tenant_id == current_user.tenant_id,
            Lead.is_deleted == False
        )
        
        # Apply sorting
        if sort_by == "company_name":
            query = query.order_by(Lead.company_name.asc() if sort_order == "asc" else Lead.company_name.desc())
        elif sort_by == "lead_score":
            query = query.order_by(Lead.lead_score.asc() if sort_order == "asc" else Lead.lead_score.desc())
        elif sort_by == "postcode":
            query = query.order_by(Lead.postcode.asc() if sort_order == "asc" else Lead.postcode.desc())
        elif sort_by == "created_at":
            query = query.order_by(Lead.created_at.asc() if sort_order == "asc" else Lead.created_at.desc())
        else:
            query = query.order_by(Lead.created_at.desc())
        
        leads = query.offset(skip).limit(limit).all()
        
        # Convert to response format with campaign information
        result = []
        for lead in leads:
            lead_data = {
                "id": lead.id,
                "company_name": lead.company_name,
                "contact_name": lead.contact_name,
                "contact_email": lead.contact_email,
                "contact_phone": lead.contact_phone,
                "website": lead.website,
                "address": lead.address,
                "postcode": lead.postcode,
                "business_sector": lead.business_sector,
                "company_size": lead.company_size,
                "lead_score": lead.lead_score,
                "status": lead.status.value if lead.status else "NEW",
                "source": lead.source.value if lead.source else "AI_GENERATED",
                "campaign_id": lead.campaign_id,
                "campaign_name": None,
                "description": lead.qualification_reason,
                "qualification_reason": lead.qualification_reason,
                "project_value": lead.potential_project_value,
                "timeline": lead.timeline_estimate,
                "created_at": lead.created_at.isoformat() if lead.created_at else None,
                "external_data": {
                    "google_maps": _safe_json_parse(lead.google_maps_data),
                    "companies_house": _safe_json_parse(lead.companies_house_data),
                    "website": _safe_json_parse(lead.website_data),
                    "linkedin": _safe_json_parse(lead.linkedin_data)
                },
                "ai_analysis": lead.ai_analysis
            }
            
            # Get campaign name if campaign_id exists
            if lead.campaign_id:
                campaign = db.query(LeadGenerationCampaign).filter(
                    LeadGenerationCampaign.id == lead.campaign_id
                ).first()
                if campaign:
                    lead_data["campaign_name"] = campaign.name
            
            result.append(lead_data)
        
        return {"data": result}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve leads: {str(e)}"
        )

@router.get("/{campaign_id}/leads")
def get_campaign_leads(
    campaign_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get leads for a specific campaign"""
    try:
        # Verify campaign exists and belongs to tenant
        campaign = db.query(LeadGenerationCampaign).filter(
            LeadGenerationCampaign.id == campaign_id,
            LeadGenerationCampaign.tenant_id == current_user.tenant_id
        ).first()
        
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        # Get leads for this campaign
        leads_query = db.query(Lead).filter(
            Lead.campaign_id == campaign_id,
            Lead.tenant_id == current_user.tenant_id,
            Lead.is_deleted == False
        )
        
        leads = leads_query.offset(skip).limit(limit).all()
        
        # Convert to response format
        result = []
        for lead in leads:
            lead_data = {
                "id": lead.id,
                "company_name": lead.company_name,
                "contact_name": lead.contact_name,
                "contact_email": lead.contact_email,
                "contact_phone": lead.contact_phone,
                "website": lead.website,
                "address": lead.address,
                "postcode": lead.postcode,
                "business_sector": lead.business_sector,
                "company_size": lead.company_size,
                "lead_score": lead.lead_score,
                "status": lead.status.value if lead.status else "NEW",
                "source": lead.source.value if lead.source else "AI_GENERATED",
                "campaign_id": lead.campaign_id,
                "campaign_name": campaign.name,
                "description": lead.qualification_reason,
                "qualification_reason": lead.qualification_reason,
                "project_value": lead.potential_project_value,
                "timeline": lead.timeline_estimate,
                "created_at": lead.created_at.isoformat() if lead.created_at else None,
                "external_data": {
                    "google_maps": _safe_json_parse(lead.google_maps_data),
                    "companies_house": _safe_json_parse(lead.companies_house_data),
                    "website": _safe_json_parse(lead.website_data),
                    "linkedin": _safe_json_parse(lead.linkedin_data)
                },
                "ai_analysis": lead.ai_analysis
            }
            result.append(lead_data)
        
        return {"data": result}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve campaign leads: {str(e)}"
        )

@router.post("/leads/{lead_id}/convert")
async def convert_lead_to_customer(
    lead_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Convert a discovery lead to a customer record"""
    try:
        # Find the lead
        lead = db.query(Lead).filter(
            Lead.id == lead_id,
            Lead.tenant_id == current_user.tenant_id,
            Lead.is_deleted == False
        ).first()
        
        if not lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lead not found"
            )
        
        # Check if lead is already converted (has converted_to_customer_id)
        if lead.converted_to_customer_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Lead has already been converted to customer"
            )
        
        # Map lead data to customer fields
        # Handle business sector mapping - ignore empty/N/A values
        business_sector = None
        if lead.business_sector and lead.business_sector.strip() not in ['', 'N/A', 'n/a', 'None', 'null']:
            try:
                # Try to map the sector string to BusinessSector enum
                business_sector = BusinessSector(lead.business_sector)
            except ValueError:
                # If the sector doesn't match any enum value, try to find a close match
                # or default to None - the user can manually update later
                print(f"Warning: Could not map business_sector '{lead.business_sector}' to BusinessSector enum")
        
        # Handle business size mapping - ignore empty/N/A values
        business_size = None
        if lead.company_size and lead.company_size.strip() not in ['', 'N/A', 'n/a', 'None', 'null']:
            try:
                business_size = BusinessSize(lead.company_size)
            except ValueError:
                print(f"Warning: Could not map company_size '{lead.company_size}' to BusinessSize enum")
        
        # Create customer record
        customer = Customer(
            id=str(uuid.uuid4()),
            tenant_id=current_user.tenant_id,
            company_name=lead.company_name,
            status=CustomerStatus.LEAD,  # Start as LEAD status
            business_sector=business_sector,
            business_size=business_size,
            description=lead.qualification_reason or f"Converted from discovery - {lead.company_name}",
            website=lead.website,
            main_email=lead.contact_email,
            main_phone=lead.contact_phone,
            billing_address=lead.address,
            billing_postcode=lead.postcode,
            lead_score=lead.lead_score,
            ai_analysis_raw=_safe_parse_ai_analysis(lead.ai_analysis),
            companies_house_data=_safe_json_parse(lead.companies_house_data),
            google_maps_data=_safe_json_parse(lead.google_maps_data),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        db.add(customer)
        db.flush()  # Get the customer ID
        
        # Update the lead to reference the new customer
        lead.converted_to_customer_id = customer.id
        lead.status = LeadStatus.CONVERTED  # Update lead status
        lead.conversion_date = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(customer)
        
        return {
            "success": True,
            "message": "Lead converted to customer successfully",
            "customer_id": customer.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to convert lead: {str(e)}"
        )