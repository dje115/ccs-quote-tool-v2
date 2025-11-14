"""
Planning Application endpoints for UK county-based planning data monitoring
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_tenant
from app.models import User, Tenant
from app.models.planning import (
    PlanningApplication, PlanningApplicationCampaign, PlanningApplicationKeyword,
    PlanningCampaignStatus, ApplicationType, PlanningApplicationStatus
)
from app.schemas.planning import (
    PlanningApplicationCreate, PlanningApplicationUpdate, PlanningApplicationResponse,
    PlanningApplicationCampaignCreate, PlanningApplicationCampaignUpdate, PlanningApplicationCampaignResponse,
    PlanningKeywordCreate, PlanningKeywordResponse, PlanningApplicationListResponse,
    PlanningApplicationArchiveRequest
)
from app.services.planning_service import PlanningApplicationService
from app.tasks.planning_tasks import run_planning_campaign_task

router = APIRouter()


@router.get("/counties", response_model=List[dict])
async def get_available_counties(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of available UK counties for planning monitoring"""
    service = PlanningApplicationService(db, current_user.tenant_id)
    return service.get_available_counties()


@router.post("/campaigns", response_model=PlanningApplicationCampaignResponse)
async def create_planning_campaign(
    campaign_data: PlanningApplicationCampaignCreate,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Create a new planning application campaign"""
    try:
        # Check if campaign for this county already exists
        existing = db.query(PlanningApplicationCampaign).filter(
            PlanningApplicationCampaign.county == campaign_data.county,
            PlanningApplicationCampaign.tenant_id == current_tenant.id
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Campaign for {campaign_data.county} already exists"
            )
        
        # Create new campaign
        campaign = PlanningApplicationCampaign(
            name=campaign_data.name,
            description=campaign_data.description,
            county=campaign_data.county,
            source_portal=campaign_data.source_portal,
            application_types=campaign_data.application_types,
            include_residential=campaign_data.include_residential,
            include_commercial=campaign_data.include_commercial,
            include_industrial=campaign_data.include_industrial,
            include_change_of_use=campaign_data.include_change_of_use,
            keyword_filters=campaign_data.keyword_filters,
            exclude_keywords=campaign_data.exclude_keywords,
            center_postcode=campaign_data.center_postcode,
            radius_miles=campaign_data.radius_miles,
            days_to_monitor=campaign_data.days_to_monitor,
            max_results_per_run=campaign_data.max_results_per_run,
            is_scheduled=campaign_data.is_scheduled,
            schedule_frequency_days=campaign_data.schedule_frequency_days,
            enable_ai_analysis=campaign_data.enable_ai_analysis,
            max_ai_analysis_per_run=campaign_data.max_ai_analysis_per_run,
            tenant_id=current_tenant.id,
            created_by=current_user.id,
            status=PlanningCampaignStatus.DRAFT
        )
        
        db.add(campaign)
        db.commit()
        db.refresh(campaign)
        
        return PlanningApplicationCampaignResponse.model_validate(campaign)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create campaign: {str(e)}"
        )


@router.get("/campaigns", response_model=List[PlanningApplicationCampaignResponse])
async def list_planning_campaigns(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """List planning campaigns for current tenant"""
    campaigns = db.query(PlanningApplicationCampaign).filter(
        PlanningApplicationCampaign.tenant_id == current_tenant.id
    ).order_by(PlanningApplicationCampaign.created_at.desc()).offset(skip).limit(limit).all()
    
    return [PlanningApplicationCampaignResponse.model_validate(campaign) for campaign in campaigns]


@router.get("/campaigns/{campaign_id}", response_model=PlanningApplicationCampaignResponse)
async def get_planning_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Get planning campaign by ID"""
    campaign = db.query(PlanningApplicationCampaign).filter(
        PlanningApplicationCampaign.id == campaign_id,
        PlanningApplicationCampaign.tenant_id == current_tenant.id
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    return PlanningApplicationCampaignResponse.model_validate(campaign)


@router.put("/campaigns/{campaign_id}", response_model=PlanningApplicationCampaignResponse)
async def update_planning_campaign(
    campaign_id: str,
    campaign_update: PlanningApplicationCampaignUpdate,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Update planning campaign"""
    campaign = db.query(PlanningApplicationCampaign).filter(
        PlanningApplicationCampaign.id == campaign_id,
        PlanningApplicationCampaign.tenant_id == current_tenant.id
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    try:
        # Update fields
        update_data = campaign_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(campaign, field, value)
        
        campaign.updated_by = current_user.id
        campaign.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(campaign)
        
        return PlanningApplicationCampaignResponse.model_validate(campaign)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update campaign: {str(e)}"
        )


@router.post("/campaigns/{campaign_id}/run")
async def run_planning_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Run planning campaign on-demand"""
    service = PlanningApplicationService(db, current_tenant.id)
    
    try:
        result = await service.run_campaign(campaign_id)
        return {
            "message": "Campaign completed successfully",
            "result": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Campaign run failed: {str(e)}"
        )


@router.delete("/campaigns/{campaign_id}")
async def delete_planning_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Delete planning campaign"""
    campaign = db.query(PlanningApplicationCampaign).filter(
        PlanningApplicationCampaign.id == campaign_id,
        PlanningApplicationCampaign.tenant_id == current_tenant.id
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    db.delete(campaign)
    db.commit()
    
    return {"message": "Campaign deleted successfully"}


@router.get("/applications", response_model=PlanningApplicationListResponse)
async def list_planning_applications(
    skip: int = 0,
    limit: int = 500,
    county: Optional[str] = None,
    application_type: Optional[ApplicationType] = None,
    min_score: Optional[int] = Query(None, ge=0, le=100),
    campaign_id: Optional[str] = None,
    include_archived: bool = False,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """List planning applications with filters"""
    query = db.query(PlanningApplication).filter(
        PlanningApplication.tenant_id == current_tenant.id
    )
    
    # Apply filters
    if county:
        query = query.filter(PlanningApplication.county == county)
    
    if application_type:
        query = query.filter(PlanningApplication.application_type == application_type)
    
    if min_score is not None:
        query = query.filter(PlanningApplication.relevance_score >= min_score)
    
    # Filter by archived status
    if include_archived:
        query = query.filter(PlanningApplication.is_archived == True)
    else:
        query = query.filter((PlanningApplication.is_archived == False) | (PlanningApplication.is_archived.is_(None)))
    
    # Count total results
    total = query.count()
    
    # Get paginated results
    applications = query.order_by(PlanningApplication.created_at.desc()).offset(skip).limit(limit).all()
    
    total_pages = (total + limit - 1) // limit
    
    return PlanningApplicationListResponse(
        applications=[PlanningApplicationResponse.model_validate(app) for app in applications],
        total=total,
        page=(skip // limit) + 1,
        per_page=limit,
        total_pages=total_pages
    )


@router.get("/applications/{application_id}", response_model=PlanningApplicationResponse)
async def get_planning_application(
    application_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Get planning application by ID"""
    application = db.query(PlanningApplication).filter(
        PlanningApplication.id == application_id,
        PlanningApplication.tenant_id == current_tenant.id
    ).first()
    
    if not application:
        raise HTTPException(status_code=404, detail="Planning application not found")
    
    return PlanningApplicationResponse.model_validate(application)


@router.put("/applications/{application_id}", response_model=PlanningApplicationResponse)
async def update_planning_application(
    application_id: str,
    application_update: PlanningApplicationUpdate,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Update planning application"""
    application = db.query(PlanningApplication).filter(
        PlanningApplication.id == application_id,
        PlanningApplication.tenant_id == current_tenant.id
    ).first()
    
    if not application:
        raise HTTPException(status_code=404, detail="Planning application not found")
    
    try:
        # Update fields
        update_data = application_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(application, field, value)
        
        db.commit()
        db.refresh(application)
        
        return PlanningApplicationResponse.model_validate(application)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update planning application: {str(e)}"
        )


# Keyword management endpoints

@router.post("/keywords", response_model=PlanningKeywordResponse)
async def create_planning_keyword(
    keyword_data: PlanningKeywordCreate,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Create a new planning keyword"""
    keyword = PlanningApplicationKeyword(
        keyword=keyword_data.keyword,
        keyword_type=keyword_data.keyword_type,
        weight=keyword_data.weight,
        category=keyword_data.category,
        tenant_id=current_tenant.id
    )
    
    db.add(keyword)
    db.commit()
    db.refresh(keyword)
    
    return PlanningKeywordResponse.model_validate(keyword)


@router.get("/keywords", response_model=List[PlanningKeywordResponse])
async def list_planning_keywords(
    keyword_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """List planning keywords for current tenant"""
    query = db.query(PlanningApplicationKeyword).filter(
        PlanningApplicationKeyword.tenant_id == current_tenant.id
    )
    
    if keyword_type:
        query = query.filter(PlanningApplicationKeyword.keyword_type == keyword_type)
    
    keywords = query.order_by(PlanningApplicationKeyword.keyword).all()
    
    return [PlanningKeywordResponse.model_validate(keyword) for keyword in keywords]


@router.delete("/keywords/{keyword_id}")
async def delete_planning_keyword(
    keyword_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Delete planning keyword"""
    keyword = db.query(PlanningApplicationKeyword).filter(
        PlanningApplicationKeyword.id == keyword_id,
        PlanningApplicationKeyword.tenant_id == current_tenant.id
    ).first()
    
    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")
    
    db.delete(keyword)
    db.commit()
    
    return {"message": "Keyword deleted successfully"}


# County-based endpoints for simplified management

@router.get("/counties/status", response_model=List[dict])
async def get_county_status(
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Get county status and configuration"""
    service = PlanningApplicationService(db, current_tenant.id)
    counties_data = service.get_available_counties()
    
    # Get or create county configurations for this tenant
    result = []
    for county in counties_data:
        # Check if we have a campaign for this county
        campaign = db.query(PlanningApplicationCampaign).filter(
            PlanningApplicationCampaign.county == county["name"],
            PlanningApplicationCampaign.tenant_id == current_tenant.id
        ).first()
        
        # Get recent application counts for this county
        recent_app_count = db.query(PlanningApplication).filter(
            PlanningApplication.county == county["name"],
            PlanningApplication.tenant_id == current_tenant.id,
            func.date(PlanningApplication.created_at) >= func.date(func.now() - timedelta(days=30))
        ).count()
        
        result.append({
            "code": county["code"],
            "name": county["name"],
            "enabled": county["enabled"],
            "is_scheduled": campaign.is_scheduled if campaign else False,
            "last_run_at": campaign.last_run_at.isoformat() if campaign and campaign.last_run_at else None,
            "next_run_at": campaign.next_run_at.isoformat() if campaign and campaign.next_run_at else None,
            "total_applications_found": campaign.total_applications_found if campaign else 0,
            "new_applications_this_run": campaign.new_applications_this_run if campaign else 0,
            "recent_applications": recent_app_count
        })
    
    return result


@router.post("/counties/{county_code}/run")
async def run_county_scan(
    county_code: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Run planning application scan for a specific county"""
    service = PlanningApplicationService(db, current_tenant.id)
    counties_data = service.get_available_counties()
    
    # Find the county by code
    county_config = next((c for c in counties_data if c["code"] == county_code), None)
    if not county_config:
        raise HTTPException(status_code=404, detail="County not found")
    
    try:
        # Get or create a campaign for this county
        campaign = db.query(PlanningApplicationCampaign).filter(
            PlanningApplicationCampaign.county == county_config["name"],
            PlanningApplicationCampaign.tenant_id == current_tenant.id
        ).first()
        
        if not campaign:
            # Create a default campaign for this county
            campaign = PlanningApplicationCampaign(
                name=f"{county_config['name']} Planning Monitoring",
                description=f"Automatic planning monitoring for {county_config['name']}",
                county=county_config["name"],
                source_portal=f"{county_code}_opendatasoft",
                tenant_id=current_tenant.id,
                created_by=current_user.id,
                enable_ai_analysis=True,
                max_ai_analysis_per_run=20
            )
            db.add(campaign)
            db.commit()
            db.refresh(campaign)
        
        # Start the planning campaign as a background Celery task
        task = run_planning_campaign_task.delay(campaign.id, current_tenant.id)
        
        return {
            "message": f"Planning scan started for {county_config['name']}",
            "task_id": task.id,
            "status": "running",
            "campaign_id": campaign.id
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"County scan failed: {str(e)}"
        )


@router.put("/counties/{county_code}/schedule")
async def update_county_schedule(
    county_code: str,
    schedule_data: dict,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Update scheduling settings for a county"""
    service = PlanningApplicationService(db, current_tenant.id)
    counties_data = service.get_available_counties()
    
    # Find the county by code
    county_config = next((c for c in counties_data if c["code"] == county_code), None)
    if not county_config:
        raise HTTPException(status_code=404, detail="County not found")
    
    try:
        # Get or create a campaign for this county
        campaign = db.query(PlanningApplicationCampaign).filter(
            PlanningApplicationCampaign.county == county_config["name"],
            PlanningApplicationCampaign.tenant_id == current_tenant.id
        ).first()
        
        if not campaign:
            # Create a default campaign for this county
            campaign = PlanningApplicationCampaign(
                name=f"{county_config['name']} Planning Monitoring",
                description=f"Automatic planning monitoring for {county_config['name']}",
                county=county_config["name"],
                source_portal=f"{county_code}_opendatasoft",
                tenant_id=current_tenant.id,
                created_by=current_user.id
            )
            db.add(campaign)
        
        # Update schedule settings
        campaign.is_scheduled = schedule_data.get("is_scheduled", False)
        campaign.schedule_frequency_days = schedule_data.get("frequency_days", 14)
        
        if campaign.is_scheduled:
            # Set next run time (offset by county code to spread load)
            import hashlib
            offset_hours = int(hashlib.md5(county_code.encode()).hexdigest()[:2], 16) % 12
            from datetime import datetime, timezone, timedelta
            next_run = datetime.now(timezone.utc) + timedelta(days=campaign.schedule_frequency_days, hours=offset_hours)
            campaign.next_run_at = next_run
        else:
            campaign.next_run_at = None
        
        campaign.updated_by = current_user.id
        
        db.commit()
        
        return {
            "message": f"Scheduling updated for {county_config['name']}",
            "is_scheduled": campaign.is_scheduled,
            "next_run_at": campaign.next_run_at.isoformat() if campaign.next_run_at else None
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update schedule: {str(e)}"
        )


@router.post("/counties/{county_code}/stop")
async def stop_county_scan(
    county_code: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Stop planning application scan for a specific county"""
    service = PlanningApplicationService(db, current_tenant.id)
    counties_data = service.get_available_counties()
    
    # Find the county by code
    county_config = next((c for c in counties_data if c["code"] == county_code), None)
    if not county_config:
        raise HTTPException(status_code=404, detail="County not found")
    
    try:
        # Get the campaign for this county
        campaign = db.query(PlanningApplicationCampaign).filter(
            PlanningApplicationCampaign.county == county_config["name"],
            PlanningApplicationCampaign.tenant_id == current_tenant.id
        ).first()
        
        if campaign:
            # Update campaign status to paused/stopped
            campaign.status = PlanningCampaignStatus.PAUSED
            campaign.updated_by = current_user.id
            db.commit()
        
        # TODO: Implement actual Celery task cancellation
        # This would require storing task IDs and using Celery's revoke functionality
        
        return {
            "message": f"Planning scan stopped for {county_config['name']}",
            "status": "stopped"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop county scan: {str(e)}"
        )


@router.post("/applications/archive")
async def archive_planning_applications(
    request: PlanningApplicationArchiveRequest,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Archive or unarchive planning applications"""
    try:
        # Update applications to set archived status
        updated_count = db.query(PlanningApplication).filter(
            PlanningApplication.id.in_(request.application_ids),
            PlanningApplication.tenant_id == current_tenant.id
        ).update(
            {"is_archived": request.archived},
            synchronize_session=False
        )
        db.commit()
        
        action = "archived" if request.archived else "unarchived"
        return {
            "message": f"Successfully {action} {updated_count} planning applications",
            "updated_count": updated_count
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update applications: {str(e)}"
        )
