"""
Planning Application endpoints for UK county-based planning data monitoring
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, and_, or_, update
from typing import List, Optional
from datetime import datetime, timedelta
import asyncio

from app.core.database import get_async_db, SessionLocal
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
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get list of available UK counties for planning monitoring
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    Note: Wraps sync service calls in executor.
    """
    def _get_counties():
        sync_db = SessionLocal()
        try:
            service = PlanningApplicationService(sync_db, current_user.tenant_id)
            return service.get_available_counties()
        finally:
            sync_db.close()
    
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _get_counties)


@router.post("/campaigns", response_model=PlanningApplicationCampaignResponse)
async def create_planning_campaign(
    campaign_data: PlanningApplicationCampaignCreate,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """Create a new planning application campaign"""
    try:
        # Check if campaign for this county already exists
        existing_stmt = select(PlanningApplicationCampaign).where(
            and_(
                PlanningApplicationCampaign.county == campaign_data.county,
                PlanningApplicationCampaign.tenant_id == current_tenant.id
            )
        )
        existing_result = await db.execute(existing_stmt)
        existing = existing_result.scalars().first()
        
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
        await db.commit()
        await db.refresh(campaign)
        
        return PlanningApplicationCampaignResponse.model_validate(campaign)
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
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
    db: AsyncSession = Depends(get_async_db)
):
    """
    List planning campaigns for current tenant
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    stmt = select(PlanningApplicationCampaign).where(
        PlanningApplicationCampaign.tenant_id == current_tenant.id
    ).order_by(PlanningApplicationCampaign.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    campaigns = result.scalars().all()
    
    return [PlanningApplicationCampaignResponse.model_validate(campaign) for campaign in campaigns]


@router.get("/campaigns/{campaign_id}", response_model=PlanningApplicationCampaignResponse)
async def get_planning_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get planning campaign by ID
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    stmt = select(PlanningApplicationCampaign).where(
        and_(
            PlanningApplicationCampaign.id == campaign_id,
            PlanningApplicationCampaign.tenant_id == current_tenant.id
        )
    )
    result = await db.execute(stmt)
    campaign = result.scalars().first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    return PlanningApplicationCampaignResponse.model_validate(campaign)


@router.put("/campaigns/{campaign_id}", response_model=PlanningApplicationCampaignResponse)
async def update_planning_campaign(
    campaign_id: str,
    campaign_update: PlanningApplicationCampaignUpdate,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Update planning campaign
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    stmt = select(PlanningApplicationCampaign).where(
        and_(
            PlanningApplicationCampaign.id == campaign_id,
            PlanningApplicationCampaign.tenant_id == current_tenant.id
        )
    )
    result = await db.execute(stmt)
    campaign = result.scalars().first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    try:
        # Update fields
        update_data = campaign_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(campaign, field, value)
        
        campaign.updated_by = current_user.id
        campaign.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(campaign)
        
        return PlanningApplicationCampaignResponse.model_validate(campaign)
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update campaign: {str(e)}"
        )


@router.post("/campaigns/{campaign_id}/run")
async def run_planning_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Run planning campaign on-demand
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    Note: Service method is async, but service uses sync db.
    """
    sync_db = SessionLocal()
    try:
        service = PlanningApplicationService(sync_db, current_tenant.id)
        result = await service.run_campaign(campaign_id)
    finally:
        sync_db.close()
    
    try:
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
    db: AsyncSession = Depends(get_async_db)
):
    """
    Delete planning campaign
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    stmt = select(PlanningApplicationCampaign).where(
        and_(
            PlanningApplicationCampaign.id == campaign_id,
            PlanningApplicationCampaign.tenant_id == current_tenant.id
        )
    )
    result = await db.execute(stmt)
    campaign = result.scalars().first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    await db.delete(campaign)
    await db.commit()
    
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
    db: AsyncSession = Depends(get_async_db)
):
    """
    List planning applications with filters
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    stmt = select(PlanningApplication).where(
        PlanningApplication.tenant_id == current_tenant.id
    )
    
    # Apply filters
    if county:
        stmt = stmt.where(PlanningApplication.county == county)
    
    if application_type:
        stmt = stmt.where(PlanningApplication.application_type == application_type)
    
    if min_score is not None:
        stmt = stmt.where(PlanningApplication.relevance_score >= min_score)
    
    # Filter by archived status
    if include_archived:
        stmt = stmt.where(PlanningApplication.is_archived == True)
    else:
        stmt = stmt.where(
            or_(
                PlanningApplication.is_archived == False,
                PlanningApplication.is_archived.is_(None)
            )
        )
    
    # Count total results (need to create a separate count query)
    count_stmt = select(func.count()).select_from(PlanningApplication).where(
        PlanningApplication.tenant_id == current_tenant.id
    )
    if county:
        count_stmt = count_stmt.where(PlanningApplication.county == county)
    if application_type:
        count_stmt = count_stmt.where(PlanningApplication.application_type == application_type)
    if min_score is not None:
        count_stmt = count_stmt.where(PlanningApplication.relevance_score >= min_score)
    if include_archived:
        count_stmt = count_stmt.where(PlanningApplication.is_archived == True)
    else:
        count_stmt = count_stmt.where(
            or_(
                PlanningApplication.is_archived == False,
                PlanningApplication.is_archived.is_(None)
            )
        )
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0
    
    # Get paginated results
    stmt = stmt.order_by(PlanningApplication.created_at.desc()).offset(skip).limit(limit)
    applications_result = await db.execute(stmt)
    applications = applications_result.scalars().all()
    
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
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get planning application by ID
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    stmt = select(PlanningApplication).where(
        and_(
            PlanningApplication.id == application_id,
            PlanningApplication.tenant_id == current_tenant.id
        )
    )
    result = await db.execute(stmt)
    application = result.scalars().first()
    
    if not application:
        raise HTTPException(status_code=404, detail="Planning application not found")
    
    return PlanningApplicationResponse.model_validate(application)


@router.put("/applications/{application_id}", response_model=PlanningApplicationResponse)
async def update_planning_application(
    application_id: str,
    application_update: PlanningApplicationUpdate,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Update planning application
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    stmt = select(PlanningApplication).where(
        and_(
            PlanningApplication.id == application_id,
            PlanningApplication.tenant_id == current_tenant.id
        )
    )
    result = await db.execute(stmt)
    application = result.scalars().first()
    
    if not application:
        raise HTTPException(status_code=404, detail="Planning application not found")
    
    try:
        # Update fields
        update_data = application_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(application, field, value)
        
        await db.commit()
        await db.refresh(application)
        
        return PlanningApplicationResponse.model_validate(application)
        
    except Exception as e:
        await db.rollback()
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
    db: AsyncSession = Depends(get_async_db)
):
    """
    Create a new planning keyword
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    keyword = PlanningApplicationKeyword(
        keyword=keyword_data.keyword,
        keyword_type=keyword_data.keyword_type,
        weight=keyword_data.weight,
        category=keyword_data.category,
        tenant_id=current_tenant.id
    )
    
    db.add(keyword)
    await db.commit()
    await db.refresh(keyword)
    
    return PlanningKeywordResponse.model_validate(keyword)


@router.get("/keywords", response_model=List[PlanningKeywordResponse])
async def list_planning_keywords(
    keyword_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    List planning keywords for current tenant
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    stmt = select(PlanningApplicationKeyword).where(
        PlanningApplicationKeyword.tenant_id == current_tenant.id
    )
    
    if keyword_type:
        stmt = stmt.where(PlanningApplicationKeyword.keyword_type == keyword_type)
    
    stmt = stmt.order_by(PlanningApplicationKeyword.keyword)
    result = await db.execute(stmt)
    keywords = result.scalars().all()
    
    return [PlanningKeywordResponse.model_validate(keyword) for keyword in keywords]


@router.delete("/keywords/{keyword_id}")
async def delete_planning_keyword(
    keyword_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Delete planning keyword
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    stmt = select(PlanningApplicationKeyword).where(
        and_(
            PlanningApplicationKeyword.id == keyword_id,
            PlanningApplicationKeyword.tenant_id == current_tenant.id
        )
    )
    result = await db.execute(stmt)
    keyword = result.scalars().first()
    
    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")
    
    await db.delete(keyword)
    await db.commit()
    
    return {"message": "Keyword deleted successfully"}


# County-based endpoints for simplified management

@router.get("/counties/status", response_model=List[dict])
async def get_county_status(
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get county status and configuration
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    Note: Wraps sync service calls in executor.
    """
    def _get_counties():
        sync_db = SessionLocal()
        try:
            service = PlanningApplicationService(sync_db, current_tenant.id)
            return service.get_available_counties()
        finally:
            sync_db.close()
    
    loop = asyncio.get_event_loop()
    counties_data = await loop.run_in_executor(None, _get_counties)
    
    # Get or create county configurations for this tenant
    result = []
    for county in counties_data:
        # Check if we have a campaign for this county
        campaign_stmt = select(PlanningApplicationCampaign).where(
            and_(
                PlanningApplicationCampaign.county == county["name"],
                PlanningApplicationCampaign.tenant_id == current_tenant.id
            )
        )
        campaign_result = await db.execute(campaign_stmt)
        campaign = campaign_result.scalars().first()
        
        # Get recent application counts for this county
        recent_app_stmt = select(func.count()).select_from(PlanningApplication).where(
            and_(
                PlanningApplication.county == county["name"],
                PlanningApplication.tenant_id == current_tenant.id,
                func.date(PlanningApplication.created_at) >= func.date(func.now() - timedelta(days=30))
            )
        )
        recent_app_result = await db.execute(recent_app_stmt)
        recent_app_count = recent_app_result.scalar() or 0
        
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
    db: AsyncSession = Depends(get_async_db)
):
    """
    Run planning application scan for a specific county
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    Note: Wraps sync service calls in executor.
    """
    def _get_counties():
        sync_db = SessionLocal()
        try:
            service = PlanningApplicationService(sync_db, current_tenant.id)
            return service.get_available_counties()
        finally:
            sync_db.close()
    
    loop = asyncio.get_event_loop()
    counties_data = await loop.run_in_executor(None, _get_counties)
    
    # Find the county by code
    county_config = next((c for c in counties_data if c["code"] == county_code), None)
    if not county_config:
        raise HTTPException(status_code=404, detail="County not found")
    
    try:
        # Get or create a campaign for this county
        campaign_stmt = select(PlanningApplicationCampaign).where(
            and_(
                PlanningApplicationCampaign.county == county_config["name"],
                PlanningApplicationCampaign.tenant_id == current_tenant.id
            )
        )
        campaign_result = await db.execute(campaign_stmt)
        campaign = campaign_result.scalars().first()
        
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
            await db.commit()
            await db.refresh(campaign)
        
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
    db: AsyncSession = Depends(get_async_db)
):
    """
    Update scheduling settings for a county
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    Note: Wraps sync service calls in executor.
    """
    def _get_counties():
        sync_db = SessionLocal()
        try:
            service = PlanningApplicationService(sync_db, current_tenant.id)
            return service.get_available_counties()
        finally:
            sync_db.close()
    
    loop = asyncio.get_event_loop()
    counties_data = await loop.run_in_executor(None, _get_counties)
    
    # Find the county by code
    county_config = next((c for c in counties_data if c["code"] == county_code), None)
    if not county_config:
        raise HTTPException(status_code=404, detail="County not found")
    
    try:
        # Get or create a campaign for this county
        campaign_stmt = select(PlanningApplicationCampaign).where(
            and_(
                PlanningApplicationCampaign.county == county_config["name"],
                PlanningApplicationCampaign.tenant_id == current_tenant.id
            )
        )
        campaign_result = await db.execute(campaign_stmt)
        campaign = campaign_result.scalars().first()
        
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
        
        await db.commit()
        
        return {
            "message": f"Scheduling updated for {county_config['name']}",
            "is_scheduled": campaign.is_scheduled,
            "next_run_at": campaign.next_run_at.isoformat() if campaign.next_run_at else None
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update schedule: {str(e)}"
        )


@router.post("/counties/{county_code}/stop")
async def stop_county_scan(
    county_code: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Stop planning application scan for a specific county
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    Note: Wraps sync service calls in executor.
    """
    def _get_counties():
        sync_db = SessionLocal()
        try:
            service = PlanningApplicationService(sync_db, current_tenant.id)
            return service.get_available_counties()
        finally:
            sync_db.close()
    
    loop = asyncio.get_event_loop()
    counties_data = await loop.run_in_executor(None, _get_counties)
    
    # Find the county by code
    county_config = next((c for c in counties_data if c["code"] == county_code), None)
    if not county_config:
        raise HTTPException(status_code=404, detail="County not found")
    
    try:
        # Get the campaign for this county
        campaign_stmt = select(PlanningApplicationCampaign).where(
            and_(
                PlanningApplicationCampaign.county == county_config["name"],
                PlanningApplicationCampaign.tenant_id == current_tenant.id
            )
        )
        campaign_result = await db.execute(campaign_stmt)
        campaign = campaign_result.scalars().first()
        
        if campaign:
            # Update campaign status to paused/stopped
            campaign.status = PlanningCampaignStatus.PAUSED
            campaign.updated_by = current_user.id
            await db.commit()
        
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
    db: AsyncSession = Depends(get_async_db)
):
    """
    Archive or unarchive planning applications
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        # Update applications to set archived status
        stmt = update(PlanningApplication).where(
            and_(
                PlanningApplication.id.in_(request.application_ids),
                PlanningApplication.tenant_id == current_tenant.id
            )
        ).values(is_archived=request.archived)
        result = await db.execute(stmt)
        updated_count = result.rowcount
        await db.commit()
        
        action = "archived" if request.archived else "unarchived"
        return {
            "message": f"Successfully {action} {updated_count} planning applications",
            "updated_count": updated_count
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update applications: {str(e)}"
        )
