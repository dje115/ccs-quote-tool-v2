from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import time
import json
import uuid
import asyncio

from app.core.database import get_async_db, SessionLocal
from app.core.dependencies import get_current_user, get_current_tenant
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
    db: AsyncSession = Depends(get_async_db),
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
        await db.commit()
        await db.refresh(campaign)
        
        return CampaignResponse.from_orm(campaign)
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create campaign: {str(e)}"
        )

@router.get("/", response_model=List[CampaignResponse])
async def get_campaigns(
    skip: int = 0,
    limit: int = 100,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all campaigns for the current tenant with sorting
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        # Build query with sorting
        stmt = select(LeadGenerationCampaign).where(
            and_(
                LeadGenerationCampaign.tenant_id == current_user.tenant_id,
                LeadGenerationCampaign.is_deleted == False
            )
        )
        
        # Apply sorting
        if sort_by == "name":
            stmt = stmt.order_by(LeadGenerationCampaign.name.asc() if sort_order == "asc" else LeadGenerationCampaign.name.desc())
        elif sort_by == "status":
            stmt = stmt.order_by(LeadGenerationCampaign.status.asc() if sort_order == "asc" else LeadGenerationCampaign.status.desc())
        elif sort_by == "leads_created" or sort_by == "total_leads":
            stmt = stmt.order_by(LeadGenerationCampaign.leads_created.asc() if sort_order == "asc" else LeadGenerationCampaign.leads_created.desc())
        elif sort_by == "created_at":
            stmt = stmt.order_by(LeadGenerationCampaign.created_at.asc() if sort_order == "asc" else LeadGenerationCampaign.created_at.desc())
        else:
            stmt = stmt.order_by(LeadGenerationCampaign.created_at.desc())
        
        stmt = stmt.offset(skip).limit(limit)
        result = await db.execute(stmt)
        campaigns = result.scalars().all()
        
        return [CampaignResponse.from_orm(campaign) for campaign in campaigns]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve campaigns: {str(e)}"
        )

@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific campaign by ID
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    stmt = select(LeadGenerationCampaign).where(
        and_(
            LeadGenerationCampaign.id == campaign_id,
            LeadGenerationCampaign.tenant_id == current_user.tenant_id
        )
    )
    result = await db.execute(stmt)
    campaign = result.scalars().first()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    return CampaignResponse.from_orm(campaign)

@router.post("/{campaign_id}/start")
async def start_campaign(
    campaign_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Start a lead generation campaign
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        # Get the campaign from database
        stmt = select(LeadGenerationCampaign).where(
            and_(
                LeadGenerationCampaign.id == campaign_id,
                LeadGenerationCampaign.tenant_id == current_user.tenant_id
            )
        )
        result = await db.execute(stmt)
        campaign = result.scalars().first()
        
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        # Update campaign status to running
        campaign.status = LeadGenerationStatus.RUNNING
        await db.commit()
        
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
async def stop_campaign(
    campaign_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Stop a running campaign
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        stmt = select(LeadGenerationCampaign).where(
            and_(
                LeadGenerationCampaign.id == campaign_id,
                LeadGenerationCampaign.tenant_id == current_user.tenant_id
            )
        )
        result = await db.execute(stmt)
        campaign = result.scalars().first()
        
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        campaign.status = LeadGenerationStatus.CANCELLED
        await db.commit()
        
        # Publish campaign status change event (stopped) (async, non-blocking)
        from app.core.events import get_event_publisher
        import asyncio
        event_publisher = get_event_publisher()
        # Fire and forget - don't await to avoid blocking response
        asyncio.create_task(event_publisher.publish_campaign_failed(
            tenant_id=current_user.tenant_id,
            campaign_id=campaign_id,
            campaign_name=campaign.name,
            error="Campaign stopped by user"
        ))
        
        return {"message": "Campaign stopped successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop campaign: {str(e)}"
        )

@router.post("/{campaign_id}/pause")
async def pause_campaign(
    campaign_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Pause a running campaign
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        stmt = select(LeadGenerationCampaign).where(
            and_(
                LeadGenerationCampaign.id == campaign_id,
                LeadGenerationCampaign.tenant_id == current_user.tenant_id
            )
        )
        result = await db.execute(stmt)
        campaign = result.scalars().first()
        
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        # Note: We don't have a PAUSED status, so we'll use DRAFT
        campaign.status = LeadGenerationStatus.DRAFT
        await db.commit()
        
        return {"message": "Campaign paused successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to pause campaign: {str(e)}"
        )

@router.post("/{campaign_id}/restart")
async def restart_campaign(
    campaign_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Restart a paused or failed campaign
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        # Get the campaign from database
        stmt = select(LeadGenerationCampaign).where(
            and_(
                LeadGenerationCampaign.id == campaign_id,
                LeadGenerationCampaign.tenant_id == current_user.tenant_id
            )
        )
        result = await db.execute(stmt)
        campaign = result.scalars().first()
        
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        # Update campaign status to running
        campaign.status = LeadGenerationStatus.RUNNING
        await db.commit()
        
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
async def delete_campaign(
    campaign_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a campaign
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        print(f"🗑️ Delete campaign request: {campaign_id} for tenant: {current_user.tenant_id}")
        
        stmt = select(LeadGenerationCampaign).where(
            and_(
                LeadGenerationCampaign.id == campaign_id,
                LeadGenerationCampaign.tenant_id == current_user.tenant_id
            )
        )
        result = await db.execute(stmt)
        campaign = result.scalars().first()
        
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
        await db.commit()
        
        print(f"✅ Campaign deleted successfully: {campaign_id}")
        return {"message": "Campaign deleted successfully"}
    except Exception as e:
        print(f"❌ Delete campaign error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete campaign: {str(e)}"
        )

def _safe_json_parse(json_data: Optional[Any]) -> Dict[str, Any]:
    """Safely parse JSON data (string or dict), return empty dict if invalid"""
    if json_data is None:
        return {}
    if isinstance(json_data, dict):
        return json_data
    if isinstance(json_data, str):
        if not json_data.strip():
            return {}
        try:
            return json.loads(json_data)
        except (json.JSONDecodeError, TypeError):
            return {}
    # If it's already a dict-like object, try to convert
    try:
        return dict(json_data)
    except (TypeError, ValueError):
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
async def get_all_leads(
    skip: int = 0,
    limit: int = 100,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all leads (discoveries) for the current tenant with campaign information
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        # Normalize sort_by parameter (handle truncated values like "lead_sco")
        if sort_by and sort_by.startswith("lead_sco"):
            sort_by = "lead_score"
        elif sort_by not in ["company_name", "lead_score", "postcode", "created_at", "status"]:
            sort_by = "created_at"
        
        # Normalize sort_order
        if sort_order not in ["asc", "desc"]:
            sort_order = "desc"
        
        # Build query with sorting
        stmt = select(Lead).where(
            and_(
                Lead.tenant_id == current_user.tenant_id,
                Lead.is_deleted == False
            )
        )
        
        # Apply sorting
        if sort_by == "company_name":
            stmt = stmt.order_by(Lead.company_name.asc() if sort_order == "asc" else Lead.company_name.desc())
        elif sort_by == "lead_score":
            stmt = stmt.order_by(Lead.lead_score.asc() if sort_order == "asc" else Lead.lead_score.desc())
        elif sort_by == "postcode":
            stmt = stmt.order_by(Lead.postcode.asc() if sort_order == "asc" else Lead.postcode.desc())
        elif sort_by == "status":
            stmt = stmt.order_by(Lead.status.asc() if sort_order == "asc" else Lead.status.desc())
        elif sort_by == "created_at":
            stmt = stmt.order_by(Lead.created_at.asc() if sort_order == "asc" else Lead.created_at.desc())
        else:
            stmt = stmt.order_by(Lead.created_at.desc())
        
        stmt = stmt.offset(skip).limit(limit)
        result = await db.execute(stmt)
        leads = result.scalars().all()
        
        # Convert to response format with campaign information
        result = []
        for lead in leads:
            try:
                lead_data = {
                    "id": str(lead.id),
                    "company_name": lead.company_name or "",
                    "contact_name": lead.contact_name or None,
                    "contact_email": lead.contact_email or None,
                    "contact_phone": lead.contact_phone or None,
                    "website": lead.website or None,
                    "address": lead.address or None,
                    "postcode": lead.postcode or None,
                    "business_sector": lead.business_sector or None,
                    "company_size": lead.company_size or None,
                    "lead_score": lead.lead_score or 0,
                    "status": lead.status.value if lead.status else "NEW",
                    "source": lead.source.value if lead.source else "AI_GENERATED",
                    "campaign_id": str(lead.campaign_id) if lead.campaign_id else None,
                    "campaign_name": None,
                    "description": lead.qualification_reason or None,
                    "qualification_reason": lead.qualification_reason or None,
                    "project_value": float(lead.potential_project_value) if lead.potential_project_value else None,
                    "timeline": lead.timeline_estimate or None,
                    "created_at": lead.created_at.isoformat() if lead.created_at else None,
                    "external_data": {
                        "google_maps": _safe_json_parse(lead.google_maps_data),
                        "companies_house": _safe_json_parse(lead.companies_house_data),
                        "website": _safe_json_parse(lead.website_data),
                        "linkedin": _safe_json_parse(lead.linkedin_data)
                    },
                    "ai_analysis": _safe_parse_ai_analysis(lead.ai_analysis)
                }
                
                # Get campaign name if campaign_id exists
                if lead.campaign_id:
                    try:
                        campaign_stmt = select(LeadGenerationCampaign).where(
                            LeadGenerationCampaign.id == lead.campaign_id
                        )
                        campaign_result = await db.execute(campaign_stmt)
                        campaign = campaign_result.scalars().first()
                        if campaign:
                            lead_data["campaign_name"] = campaign.name
                    except Exception as campaign_error:
                        print(f"[WARNING] Failed to get campaign name for lead {lead.id}: {campaign_error}")
                        lead_data["campaign_name"] = None
                
                result.append(lead_data)
            except Exception as lead_error:
                print(f"[ERROR] Failed to process lead {lead.id if lead else 'unknown'}: {lead_error}")
                import traceback
                traceback.print_exc()
                # Skip this lead and continue
                continue
        
        return {"data": result}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to retrieve leads: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve leads: {str(e)}"
        )

@router.get("/{campaign_id}/leads")
async def get_campaign_leads(
    campaign_id: str,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get leads for a specific campaign
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        # Verify campaign exists and belongs to tenant
        campaign_stmt = select(LeadGenerationCampaign).where(
            and_(
                LeadGenerationCampaign.id == campaign_id,
                LeadGenerationCampaign.tenant_id == current_user.tenant_id
            )
        )
        campaign_result = await db.execute(campaign_stmt)
        campaign = campaign_result.scalars().first()
        
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        # Get leads for this campaign
        leads_stmt = select(Lead).where(
            and_(
                Lead.campaign_id == campaign_id,
                Lead.tenant_id == current_user.tenant_id,
                Lead.is_deleted == False
            )
        )
        leads_stmt = leads_stmt.offset(skip).limit(limit)
        leads_result = await db.execute(leads_stmt)
        leads = leads_result.scalars().all()
        
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
                "ai_analysis": _safe_parse_ai_analysis(lead.ai_analysis)
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
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Convert a discovery lead to a customer record
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        # Find the lead
        lead_stmt = select(Lead).where(
            and_(
                Lead.id == lead_id,
                Lead.tenant_id == current_user.tenant_id,
                Lead.is_deleted == False
            )
        )
        lead_result = await db.execute(lead_stmt)
        lead = lead_result.scalars().first()
        
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
        
        # Prepare comprehensive AI analysis data including all discovery fields
        ai_analysis_data = _safe_parse_ai_analysis(lead.ai_analysis) or {}
        
        # Ensure ai_analysis_data is a dict
        if not isinstance(ai_analysis_data, dict):
            ai_analysis_data = {}
        
        # Add all additional discovery AI fields to the analysis data
        if lead.ai_confidence_score is not None:
            ai_analysis_data['ai_confidence_score'] = lead.ai_confidence_score
        if lead.ai_recommendation:
            ai_analysis_data['ai_recommendation'] = lead.ai_recommendation
        if lead.ai_notes:
            ai_analysis_data['ai_notes'] = lead.ai_notes
        if lead.potential_project_value is not None:
            ai_analysis_data['potential_project_value'] = lead.potential_project_value
        if lead.timeline_estimate:
            ai_analysis_data['timeline_estimate'] = lead.timeline_estimate
        if lead.annual_revenue:
            ai_analysis_data['annual_revenue'] = lead.annual_revenue
        if lead.social_media_links:
            social_media = _safe_json_parse(lead.social_media_links)
            if social_media:
                ai_analysis_data['social_media_links'] = social_media
        
        # Add qualification reason if not already in analysis
        if lead.qualification_reason and 'qualification_reason' not in ai_analysis_data:
            ai_analysis_data['qualification_reason'] = lead.qualification_reason
        
        # Build description combining qualification reason and notes
        description_parts = []
        if lead.qualification_reason:
            description_parts.append(lead.qualification_reason)
        if lead.notes:
            description_parts.append(f"Discovery Notes: {lead.notes}")
        description = "\n\n".join(description_parts) if description_parts else f"Converted from discovery - {lead.company_name}"
        
        # Create customer record
        customer = Customer(
            id=str(uuid.uuid4()),
            tenant_id=current_user.tenant_id,
            company_name=lead.company_name,
            status=CustomerStatus.LEAD,  # Start as LEAD status
            business_sector=business_sector,
            business_size=business_size,
            description=description,
            website=lead.website,
            main_email=lead.contact_email,
            main_phone=lead.contact_phone,
            billing_address=lead.address,
            billing_postcode=lead.postcode,
            lead_score=lead.lead_score,
            # Copy comprehensive AI analysis data (Discovery AI Analysis + all related fields)
            ai_analysis_raw=ai_analysis_data if ai_analysis_data else None,
            # Copy external data sources (always parse and copy, even if empty dict)
            # This preserves the data structure even if minimal
            companies_house_data=_safe_json_parse(lead.companies_house_data) if lead.companies_house_data is not None else None,
            google_maps_data=_safe_json_parse(lead.google_maps_data) if lead.google_maps_data is not None else None,
            website_data=_safe_json_parse(lead.website_data) if lead.website_data is not None else None,
            linkedin_url=lead.linkedin_url,
            linkedin_data=_safe_json_parse(lead.linkedin_data) if lead.linkedin_data is not None else None,
            # Copy company registration if available
            company_registration=lead.company_registration,
            registration_confirmed=lead.registration_confirmed,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        db.add(customer)
        await db.flush()  # Get the customer ID
        
        # Create contact record if contact name/title exists
        if lead.contact_name:
            from app.models.crm import Contact, ContactRole
            # Parse contact name (assume "First Last" format)
            name_parts = lead.contact_name.strip().split(' ', 1)
            first_name = name_parts[0] if name_parts else lead.contact_name
            last_name = name_parts[1] if len(name_parts) > 1 else ''
            
            contact = Contact(
                id=str(uuid.uuid4()),
                customer_id=customer.id,
                first_name=first_name,
                last_name=last_name or 'Unknown',
                job_title=lead.contact_title,
                email=lead.contact_email,
                phone=lead.contact_phone,
                role=ContactRole.PRIMARY if not lead.contact_title else ContactRole.OTHER,
                is_primary=True,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            db.add(contact)
        
        # Update the lead to reference the new customer
        lead.converted_to_customer_id = customer.id
        lead.status = LeadStatus.CONVERTED  # Update lead status
        lead.conversion_date = datetime.now(timezone.utc)
        
        await db.commit()
        await db.refresh(customer)
        
        return {
            "success": True,
            "message": "Lead converted to customer successfully",
            "customer_id": customer.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to convert lead: {str(e)}"
        )


@router.post("/leads/{lead_id}/analyze")
async def analyze_lead_with_ai(
    lead_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    Queue AI analysis for lead to run in background
    
    Analysis runs asynchronously using Celery and includes:
    - Opportunity summary and risk assessment
    - Conversion probability calculation
    - Recommendations and next steps
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    from sqlalchemy import select, and_
    from app.core.celery_app import celery_app
    
    # Get lead
    lead_stmt = select(Lead).where(
        and_(
            Lead.id == lead_id,
            Lead.tenant_id == current_user.tenant_id,
            Lead.is_deleted == False
        )
    )
    result = await db.execute(lead_stmt)
    lead = result.scalar_one_or_none()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    print(f"\n{'='*80}")
    print(f"🔄 QUEUEING LEAD ANALYSIS TO CELERY")
    print(f"Lead: {lead.company_name} ({lead_id})")
    print(f"Tenant: {current_tenant.name} ({current_tenant.id})")
    print(f"{'='*80}\n")
    
    try:
        # Queue the lead analysis task to Celery
        task = celery_app.send_task(
            'run_lead_analysis',
            args=[lead_id, str(current_tenant.id)]
        )
        
        print(f"✓ Task queued: {task.id}")
        
        return {
            'success': True,
            'message': 'AI analysis queued in background. The page will refresh automatically when complete.',
            'task_id': task.id,
            'status': 'queued',
            'lead_name': lead.company_name
        }
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error queuing lead analysis: {e}", exc_info=True)
        
        # Check if it's a Redis/Celery connection error
        error_msg = str(e)
        if 'Connection refused' in error_msg or 'Redis' in error_msg or 'kombu' in error_msg:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI analysis service is temporarily unavailable. Please check that Redis and Celery workers are running."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error queuing lead analysis: {str(e)}"
            )