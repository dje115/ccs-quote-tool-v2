#!/usr/bin/env python3
"""
Quote management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_, select, func, and_
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from decimal import Decimal
import uuid
import asyncio
from datetime import datetime

from app.core.database import get_async_db, SessionLocal
from app.core.dependencies import get_current_user, check_permission, get_current_tenant
from app.models.quotes import Quote, QuoteStatus
from app.models.quote_documents import QuoteDocument, QuoteDocumentVersion, DocumentType
from app.models.quote_prompt_history import QuotePromptHistory
from app.models.tenant import User, Tenant
from app.services.quote_analysis_service import QuoteAnalysisService
from app.services.quote_pricing_service import QuotePricingService
from app.services.quote_consistency_service import QuoteConsistencyService
from app.services.quote_builder_service import QuoteBuilderService
from app.services.quote_versioning_service import QuoteVersioningService
from app.core.api_keys import get_api_keys

router = APIRouter()


class QuoteCreate(BaseModel):
    customer_id: str
    title: str
    description: str | None = None
    valid_until: datetime | None = None
    quote_type: str | None = None  # e.g., 'cabling', 'network_build', 'server_build', 'software_dev', 'testing', 'design'
    auto_analyze: bool = False  # Automatically trigger AI analysis after creation
    # Project details (from v1)
    project_title: str | None = None
    project_description: str | None = None
    site_address: str | None = None
    building_type: str | None = None
    building_size: float | None = None
    number_of_floors: int | None = None
    number_of_rooms: int | None = None
    cabling_type: str | None = None
    wifi_requirements: bool = False
    cctv_requirements: bool = False
    door_entry_requirements: bool = False
    special_requirements: str | None = None


class QuoteResponse(BaseModel):
    id: str
    customer_id: str
    quote_number: str
    title: str
    status: str
    total_amount: float
    created_at: datetime
    
    class Config:
        from_attributes = True


class QuoteUpdate(BaseModel):
    status: QuoteStatus | None = None
    title: str | None = None
    description: str | None = None
    # Project details
    project_title: str | None = None
    project_description: str | None = None
    site_address: str | None = None
    building_type: str | None = None
    building_size: float | None = None
    number_of_floors: int | None = None
    number_of_rooms: int | None = None
    cabling_type: str | None = None
    wifi_requirements: bool | None = None
    cctv_requirements: bool | None = None
    door_entry_requirements: bool | None = None
    special_requirements: str | None = None


class QuoteAnalyzeRequest(BaseModel):
    quote_id: str | None = None
    clarification_answers: List[Dict[str, str]] | None = None
    questions_only: bool = False
    # Quote data for analysis before creation
    project_title: str | None = None
    project_description: str | None = None
    site_address: str | None = None
    building_type: str | None = None
    building_size: float | None = None
    number_of_floors: int | None = None
    number_of_rooms: int | None = None
    cabling_type: str | None = None
    wifi_requirements: bool = False
    cctv_requirements: bool = False
    door_entry_requirements: bool = False
    special_requirements: str | None = None


class QuoteCalculatePricingRequest(BaseModel):
    quote_id: str


class PaginatedQuoteResponse(BaseModel):
    """Paginated quotes response"""
    items: List[QuoteResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


@router.get("/", response_model=PaginatedQuoteResponse)
async def list_quotes(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: QuoteStatus | None = None,
    customer_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    List quotes for current tenant with pagination
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        # Build base query
        stmt = select(Quote).where(
            Quote.tenant_id == current_user.tenant_id,
            Quote.is_deleted == False
        )
        
        # Build count query for total
        count_stmt = select(func.count(Quote.id)).where(
            Quote.tenant_id == current_user.tenant_id,
            Quote.is_deleted == False
        )
        
        if status:
            stmt = stmt.where(Quote.status == status)
            count_stmt = count_stmt.where(Quote.status == status)
        
        if customer_id:
            stmt = stmt.where(Quote.customer_id == customer_id)
            count_stmt = count_stmt.where(Quote.customer_id == customer_id)
        
        # Apply search filter if provided
        if search:
            search_filter = f"%{search}%"
            search_condition = or_(
                Quote.title.ilike(search_filter),
                Quote.quote_number.ilike(search_filter),
                Quote.project_title.ilike(search_filter)
            )
            stmt = stmt.where(search_condition)
            count_stmt = count_stmt.where(search_condition)
        
        # Get total count before pagination
        total_result = await db.execute(count_stmt)
        total = total_result.scalar() or 0
        
        # Apply pagination
        stmt = stmt.order_by(Quote.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(stmt)
        quotes = result.scalars().all()
        
        # Calculate total pages
        total_pages = (total + limit - 1) // limit if limit > 0 else 1
        current_page = (skip // limit) + 1 if limit > 0 else 1
        
        # Convert to response format
        items = [
            QuoteResponse(
                id=quote.id,
                customer_id=quote.customer_id,
                quote_number=quote.quote_number,
                title=quote.title,
                status=quote.status.value if hasattr(quote.status, 'value') else str(quote.status),
                total_amount=float(quote.total_amount) if quote.total_amount else 0.0,
                created_at=quote.created_at
            )
            for quote in quotes
        ]
        
        return PaginatedQuoteResponse(
            items=items,
            total=total,
            page=current_page,
            page_size=limit,
            total_pages=total_pages
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error fetching quotes: {str(e)}")


@router.post("/", response_model=QuoteResponse, status_code=status.HTTP_201_CREATED)
async def create_quote(
    quote_data: QuoteCreate,
    current_user: User = Depends(check_permission("quote:create")),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Create new quote
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    from sqlalchemy import select, func
    
    try:
        # Generate quote number
        count_stmt = select(func.count(Quote.id)).where(Quote.tenant_id == current_user.tenant_id)
        count_result = await db.execute(count_stmt)
        quote_count = count_result.scalar() or 0
        quote_number = f"Q-{datetime.now().strftime('%Y%m')}-{quote_count + 1:04d}"
        
        quote = Quote(
            id=str(uuid.uuid4()),
            tenant_id=current_user.tenant_id,
            customer_id=quote_data.customer_id,
            quote_number=quote_number,
            title=quote_data.title,
            description=quote_data.description,
            quote_type=quote_data.quote_type,
            status=QuoteStatus.DRAFT,
            valid_until=quote_data.valid_until,
            subtotal=Decimal('0.00'),
            tax_rate=0.20,
            tax_amount=Decimal('0.00'),
            total_amount=Decimal('0.00'),
            # Project details
            project_title=quote_data.project_title,
            project_description=quote_data.project_description,
            site_address=quote_data.site_address,
            building_type=quote_data.building_type,
            building_size=quote_data.building_size,
            number_of_floors=quote_data.number_of_floors,
            number_of_rooms=quote_data.number_of_rooms,
            cabling_type=quote_data.cabling_type,
            wifi_requirements=quote_data.wifi_requirements,
            cctv_requirements=quote_data.cctv_requirements,
            door_entry_requirements=quote_data.door_entry_requirements,
            special_requirements=quote_data.special_requirements,
            created_by=current_user.id
        )
        
        db.add(quote)
        await db.commit()
        await db.refresh(quote)
        
        # Optionally trigger AI analysis if requested (queued as background task)
        if quote_data.auto_analyze:
            try:
                from app.core.api_keys import get_api_keys
                from app.core.celery_app import celery_app
                from app.models.tenant import Tenant
                
                tenant_stmt = select(Tenant).where(Tenant.id == current_user.tenant_id)
                tenant_result = await db.execute(tenant_stmt)
                tenant = tenant_result.scalar_one_or_none()
                if tenant:
                    # For async session, we need to use a sync session for get_api_keys
                    # This is a temporary workaround - get_api_keys should be refactored to support async
                    from app.core.database import SessionLocal
                    sync_db = SessionLocal()
                    try:
                        api_keys = get_api_keys(sync_db, tenant)
                        if api_keys.openai:
                            quote_data_dict = {
                                'project_title': quote.project_title or quote.title,
                                'project_description': quote.project_description or quote.description,
                                'site_address': quote.site_address,
                                'building_type': quote.building_type,
                                'building_size': quote.building_size,
                                'number_of_floors': quote.number_of_floors or 1,
                                'number_of_rooms': quote.number_of_rooms or 1,
                                'cabling_type': quote.cabling_type,
                                'wifi_requirements': quote.wifi_requirements or False,
                                'cctv_requirements': quote.cctv_requirements or False,
                                'door_entry_requirements': quote.door_entry_requirements or False,
                                'special_requirements': quote.special_requirements,
                                'quote_type': quote.quote_type
                            }
                            
                            # Queue analysis task to Celery (non-blocking)
                            celery_app.send_task(
                                'analyze_quote_requirements',
                                args=[
                                    quote.id,
                                    str(current_user.tenant_id),
                                    quote_data_dict,
                                    None,  # clarification_answers
                                    False  # questions_only
                                ]
                            )
                            import logging
                            logger = logging.getLogger(__name__)
                            logger.info(f"[QUOTE CREATION] Queued auto-analysis task for quote {quote.id}")
                    finally:
                        sync_db.close()
            except Exception as e:
                # Don't fail quote creation if analysis fails
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"[QUOTE CREATION] Error queueing auto-analysis: {e}", exc_info=True)
        
        # Publish quote.created event (async, non-blocking)
        from app.core.events import get_event_publisher
        event_publisher = get_event_publisher()
        quote_dict = {
            "id": quote.id,
            "quote_number": quote.quote_number,
            "customer_id": quote.customer_id,
            "title": quote.title,
            "status": quote.status.value if hasattr(quote.status, 'value') else str(quote.status),
            "total_amount": float(quote.total_amount) if quote.total_amount else 0.0,
        }
        # Fire and forget - don't await to avoid blocking response
        asyncio.create_task(event_publisher.publish_quote_created(
            tenant_id=current_user.tenant_id,
            quote_id=quote.id,
            quote_data=quote_dict
        ))
        
        return quote
        
    except Exception as e:
        await db.rollback()
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error creating quote: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating quote: {str(e)}"
        )


@router.get("/{quote_id}", response_model=QuoteResponse)
async def get_quote(
    quote_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get quote by ID
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    from sqlalchemy import select
    
    stmt = select(Quote).where(
        Quote.id == quote_id,
        Quote.tenant_id == current_user.tenant_id,
        Quote.is_deleted == False
    )
    result = await db.execute(stmt)
    quote = result.scalar_one_or_none()
    
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    return quote


@router.put("/{quote_id}", response_model=QuoteResponse)
async def update_quote(
    quote_id: str,
    quote_update: QuoteUpdate,
    current_user: User = Depends(check_permission("quote:update")),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Update quote
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    from sqlalchemy import select
    
    stmt = select(Quote).where(
        Quote.id == quote_id,
        Quote.tenant_id == current_user.tenant_id,
        Quote.is_deleted == False
    )
    result = await db.execute(stmt)
    quote = result.scalar_one_or_none()
    
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    old_status = quote.status
    if quote_update.status is not None:
        quote.status = quote_update.status
    if quote_update.title is not None:
        quote.title = quote_update.title
    if quote_update.description is not None:
        quote.description = quote_update.description
    # Update project details
    if quote_update.project_title is not None:
        quote.project_title = quote_update.project_title
    if quote_update.project_description is not None:
        quote.project_description = quote_update.project_description
    if quote_update.site_address is not None:
        quote.site_address = quote_update.site_address
    if quote_update.building_type is not None:
        quote.building_type = quote_update.building_type
    if quote_update.building_size is not None:
        quote.building_size = quote_update.building_size
    if quote_update.number_of_floors is not None:
        quote.number_of_floors = quote_update.number_of_floors
    if quote_update.number_of_rooms is not None:
        quote.number_of_rooms = quote_update.number_of_rooms
    if quote_update.cabling_type is not None:
        quote.cabling_type = quote_update.cabling_type
    if quote_update.wifi_requirements is not None:
        quote.wifi_requirements = quote_update.wifi_requirements
    if quote_update.cctv_requirements is not None:
        quote.cctv_requirements = quote_update.cctv_requirements
    if quote_update.door_entry_requirements is not None:
        quote.door_entry_requirements = quote_update.door_entry_requirements
    if quote_update.special_requirements is not None:
        quote.special_requirements = quote_update.special_requirements
    
    await db.commit()
    await db.refresh(quote)
    
    # Publish quote.updated event (async, non-blocking)
    from app.core.events import get_event_publisher
    event_publisher = get_event_publisher()
    quote_dict = {
        "id": quote.id,
        "quote_number": quote.quote_number,
        "customer_id": quote.customer_id,
        "title": quote.title,
        "status": quote.status.value if hasattr(quote.status, 'value') else str(quote.status),
        "total_amount": float(quote.total_amount) if quote.total_amount else 0.0,
    }
    # Fire and forget - don't await to avoid blocking response
    asyncio.create_task(event_publisher.publish_quote_updated(
        tenant_id=current_user.tenant_id,
        quote_id=quote.id,
        quote_data=quote_dict
    ))
    
    # Publish status change event if status changed
    if quote_update.status is not None and old_status != quote.status:
        asyncio.create_task(event_publisher.publish_quote_status_changed(
            tenant_id=current_user.tenant_id,
            quote_id=quote.id,
            old_status=old_status.value if hasattr(old_status, 'value') else str(old_status),
            new_status=quote.status.value if hasattr(quote.status, 'value') else str(quote.status)
        ))
    
    return quote


@router.delete("/{quote_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_quote(
    quote_id: str,
    current_user: User = Depends(check_permission("quote:delete")),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Soft delete quote
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    from sqlalchemy import select
    
    stmt = select(Quote).where(
        Quote.id == quote_id,
        Quote.tenant_id == current_user.tenant_id,
        Quote.is_deleted == False
    )
    result = await db.execute(stmt)
    quote = result.scalar_one_or_none()
    
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    quote.is_deleted = True
    quote.deleted_at = datetime.utcnow()
    await db.commit()
    
    return None


@router.post("/analyze", status_code=status.HTTP_202_ACCEPTED)
async def analyze_quote_requirements(
    request: QuoteAnalyzeRequest,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Analyze quote requirements using AI (queued as background task)
    
    Returns 202 Accepted with task ID. Analysis runs in background via Celery.
    Results will be available via WebSocket events or by polling the quote.
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        from app.core.celery_app import celery_app
        
        # Get API keys to validate configuration (use sync session for get_api_keys)
        from app.core.database import SessionLocal
        sync_db = SessionLocal()
        try:
            api_keys = get_api_keys(sync_db, current_tenant)
        finally:
            sync_db.close()
        if not api_keys.openai:
            raise HTTPException(
                status_code=400,
                detail="OpenAI API key not configured"
            )
        
        # Build quote data dict - use request data if provided, otherwise fetch from quote
        if request.quote_id:
            stmt = select(Quote).where(
                Quote.id == request.quote_id,
                Quote.tenant_id == current_user.tenant_id
            )
            result = await db.execute(stmt)
            quote = result.scalar_one_or_none()
            
            if not quote:
                raise HTTPException(status_code=404, detail="Quote not found")
            
            quote_data = {
                'project_title': quote.project_title or quote.title,
                'project_description': quote.project_description or quote.description,
                'site_address': quote.site_address,
                'building_type': quote.building_type,
                'building_size': quote.building_size,
                'number_of_floors': quote.number_of_floors or 1,
                'number_of_rooms': quote.number_of_rooms or 1,
                'cabling_type': quote.cabling_type,
                'wifi_requirements': quote.wifi_requirements or False,
                'cctv_requirements': quote.cctv_requirements or False,
                'door_entry_requirements': quote.door_entry_requirements or False,
                'special_requirements': quote.special_requirements,
                'quote_type': quote.quote_type or request.quote_type
            }
        else:
            # Use data from request (for analysis before quote creation)
            quote_data = {
                'project_title': request.project_title or '',
                'project_description': request.project_description or '',
                'site_address': request.site_address or '',
                'building_type': request.building_type,
                'building_size': request.building_size,
                'number_of_floors': request.number_of_floors or 1,
                'number_of_rooms': request.number_of_rooms or 1,
                'cabling_type': request.cabling_type,
                'wifi_requirements': request.wifi_requirements,
                'cctv_requirements': request.cctv_requirements,
                'door_entry_requirements': request.door_entry_requirements,
                'special_requirements': request.special_requirements,
                'quote_type': request.quote_type
            }
        
        # Queue analysis task to Celery
        task = celery_app.send_task(
            'analyze_quote_requirements',
            args=[
                request.quote_id,
                str(current_user.tenant_id),
                quote_data,
                request.clarification_answers,
                request.questions_only
            ]
        )
        
        return {
            'success': True,
            'message': 'Quote analysis queued',
            'task_id': task.id,
            'status': 'queued',
            'quote_id': request.quote_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error queueing quote analysis: {str(e)}"
        )


@router.post("/{quote_id}/calculate-pricing")
async def calculate_quote_pricing(
    quote_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Calculate pricing for a quote
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        stmt = select(Quote).where(
            Quote.id == quote_id,
            Quote.tenant_id == current_user.tenant_id
        )
        result = await db.execute(stmt)
        quote = result.scalar_one_or_none()
        
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")
        
        # QuotePricingService currently expects sync session - use sync wrapper
        from app.core.database import SessionLocal
        sync_db = SessionLocal()
        try:
            pricing_service = QuotePricingService(sync_db, tenant_id=current_user.tenant_id)
            pricing_breakdown = pricing_service.calculate_quote_pricing(quote)
        finally:
            sync_db.close()
        
        await db.commit()
        await db.refresh(quote)
        
        return {
            'success': True,
            'pricing_breakdown': pricing_breakdown,
            'quote': quote
        }
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error calculating pricing: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating pricing: {str(e)}"
        )


@router.post("/{quote_id}/duplicate")
async def duplicate_quote(
    quote_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Duplicate a quote
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        stmt = select(Quote).where(
            Quote.id == quote_id,
            Quote.tenant_id == current_user.tenant_id
        )
        result = await db.execute(stmt)
        original_quote = result.scalar_one_or_none()
        
        if not original_quote:
            raise HTTPException(status_code=404, detail="Quote not found")
        
        # Generate new quote number
        count_stmt = select(func.count(Quote.id)).where(Quote.tenant_id == current_user.tenant_id)
        count_result = await db.execute(count_stmt)
        quote_count = count_result.scalar() or 0
        new_quote_number = f"Q-{datetime.now().strftime('%Y%m')}-{quote_count + 1:04d}"
        
        # Create duplicate
        new_quote = Quote(
            id=str(uuid.uuid4()),
            tenant_id=current_user.tenant_id,
            customer_id=original_quote.customer_id,
            quote_number=new_quote_number,
            title=f"{original_quote.title} (Copy)",
            description=original_quote.description,
            status=QuoteStatus.DRAFT,
            # Copy project details
            project_title=original_quote.project_title,
            project_description=original_quote.project_description,
            site_address=original_quote.site_address,
            building_type=original_quote.building_type,
            building_size=original_quote.building_size,
            number_of_floors=original_quote.number_of_floors,
            number_of_rooms=original_quote.number_of_rooms,
            cabling_type=original_quote.cabling_type,
            wifi_requirements=original_quote.wifi_requirements,
            cctv_requirements=original_quote.cctv_requirements,
            door_entry_requirements=original_quote.door_entry_requirements,
            special_requirements=original_quote.special_requirements,
            created_by=current_user.id
        )
        
        db.add(new_quote)
        await db.flush()
        
        # Copy quote items if any
        # Load items relationship using async query
        from app.models.quotes import QuoteItem
        items_stmt = select(QuoteItem).where(
            and_(
                QuoteItem.quote_id == quote_id,
                QuoteItem.tenant_id == current_user.tenant_id
            )
        ).order_by(QuoteItem.sort_order)
        items_result = await db.execute(items_stmt)
        items = items_result.scalars().all()
        
        if items:
            for item in items:
                new_item = QuoteItem(
                    id=str(uuid.uuid4()),
                    tenant_id=current_user.tenant_id,
                    quote_id=new_quote.id,
                    description=item.description,
                    category=item.category,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    discount_rate=item.discount_rate,
                    discount_amount=item.discount_amount,
                    total_price=item.total_price,
                    notes=item.notes,
                    sort_order=item.sort_order
                )
                db.add(new_item)
        
        await db.commit()
        await db.refresh(new_quote)
        
        return new_quote
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error duplicating quote: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error duplicating quote: {str(e)}"
        )


@router.post("/{quote_id}/clarifications", status_code=status.HTTP_202_ACCEPTED)
async def submit_clarifications(
    quote_id: str,
    clarification_answers: List[Dict[str, str]],
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Submit clarification answers and re-analyze quote (queued as background task)
    
    Returns 202 Accepted with task ID. Analysis runs in background via Celery.
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        import json
        from app.core.celery_app import celery_app
        
        stmt = select(Quote).where(
            Quote.id == quote_id,
            Quote.tenant_id == current_user.tenant_id
        )
        result = await db.execute(stmt)
        quote = result.scalar_one_or_none()
        
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")
        
        # Store clarification answers immediately
        clarifications_log = []
        if quote.clarifications_log:
            if isinstance(quote.clarifications_log, str):
                clarifications_log = json.loads(quote.clarifications_log)
            else:
                clarifications_log = quote.clarifications_log
        
        clarifications_log.extend(clarification_answers)
        quote.clarifications_log = json.dumps(clarifications_log)
        await db.commit()
        
        # Get API keys to validate configuration (use sync session for get_api_keys)
        from app.core.database import SessionLocal
        sync_db = SessionLocal()
        try:
            api_keys = get_api_keys(sync_db, current_tenant)
        finally:
            sync_db.close()
        if not api_keys.openai:
            raise HTTPException(
                status_code=400,
                detail="OpenAI API key not configured"
            )
        
        # Build quote data for analysis
        quote_data = {
            'project_title': quote.project_title or quote.title,
            'project_description': quote.project_description or quote.description,
            'site_address': quote.site_address,
            'building_type': quote.building_type,
            'building_size': quote.building_size,
            'number_of_floors': quote.number_of_floors,
            'number_of_rooms': quote.number_of_rooms,
            'cabling_type': quote.cabling_type,
            'wifi_requirements': quote.wifi_requirements or False,
            'cctv_requirements': quote.cctv_requirements or False,
            'door_entry_requirements': quote.door_entry_requirements or False,
            'special_requirements': quote.special_requirements,
            'quote_type': quote.quote_type
        }
        
        # Queue re-analysis task to Celery
        task = celery_app.send_task(
            'analyze_quote_requirements',
            args=[
                quote_id,
                str(current_user.tenant_id),
                quote_data,
                clarification_answers,
                False  # questions_only
            ]
        )
        
        return {
            'success': True,
            'message': 'Clarifications submitted and analysis queued',
            'task_id': task.id,
            'status': 'queued',
            'quote_id': quote_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error submitting clarifications: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error submitting clarifications: {str(e)}"
        )


@router.post("/{quote_id}/approve")
async def approve_quote(
    quote_id: str,
    current_user: User = Depends(check_permission("quote:approve")),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Approve a quote
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        stmt = select(Quote).where(
            Quote.id == quote_id,
            Quote.tenant_id == current_user.tenant_id
        )
        result = await db.execute(stmt)
        quote = result.scalar_one_or_none()
        
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")
        
        quote.status = QuoteStatus.ACCEPTED
        await db.commit()
        await db.refresh(quote)
        
        # Publish quote.approved event (async, non-blocking)
        from app.core.events import get_event_publisher
        event_publisher = get_event_publisher()
        # Fire and forget - don't await to avoid blocking response
        asyncio.create_task(event_publisher.publish_quote_status_changed(
            tenant_id=current_user.tenant_id,
            quote_id=quote.id,
            old_status="pending",
            new_status="accepted"
        ))
        
        return {
            'success': True,
            'quote': quote
        }
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error approving quote: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error approving quote: {str(e)}"
        )


@router.post("/{quote_id}/reject")
async def reject_quote(
    quote_id: str,
    reason: Optional[str] = None,
    current_user: User = Depends(check_permission("quote:approve")),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Reject a quote
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        stmt = select(Quote).where(
            Quote.id == quote_id,
            Quote.tenant_id == current_user.tenant_id
        )
        result = await db.execute(stmt)
        quote = result.scalar_one_or_none()
        
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")
        
        quote.status = QuoteStatus.REJECTED
        if reason:
            quote.notes = (quote.notes or "") + f"\nRejection reason: {reason}"
        
        await db.commit()
        await db.refresh(quote)
        
        # Publish quote.rejected event (async, non-blocking)
        from app.core.events import get_event_publisher
        event_publisher = get_event_publisher()
        # Fire and forget - don't await to avoid blocking response
        asyncio.create_task(event_publisher.publish_quote_status_changed(
            tenant_id=current_user.tenant_id,
            quote_id=quote.id,
            old_status="pending",
            new_status="rejected"
        ))
        
        return {
            'success': True,
            'quote': quote
        }
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error rejecting quote: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error rejecting quote: {str(e)}"
        )


@router.get("/{quote_id}/consistency")
async def get_quote_consistency(
    quote_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get consistency analysis for a quote
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        stmt = select(Quote).where(
            Quote.id == quote_id,
            Quote.tenant_id == current_user.tenant_id
        )
        result = await db.execute(stmt)
        quote = result.scalar_one_or_none()
        
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")
        
        # QuoteConsistencyService currently expects sync session - use sync wrapper
        from app.core.database import SessionLocal
        sync_db = SessionLocal()
        try:
            consistency_service = QuoteConsistencyService(sync_db, current_user.tenant_id)
            analysis = consistency_service.analyze_quote_consistency(quote_id)
        finally:
            sync_db.close()
        
        return {
            'success': True,
            'analysis': analysis
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing consistency: {str(e)}"
        )


@router.get("/{quote_id}/versions")
async def list_quote_versions(
    quote_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    List all versions of a quote
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        from app.models.product import QuoteVersion
        
        stmt = select(Quote).where(
            Quote.id == quote_id,
            Quote.tenant_id == current_user.tenant_id
        )
        result = await db.execute(stmt)
        quote = result.scalar_one_or_none()
        
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")
        
        versions_stmt = select(QuoteVersion).where(
            QuoteVersion.quote_id == quote_id
        ).order_by(QuoteVersion.created_at.desc())
        versions_result = await db.execute(versions_stmt)
        versions = versions_result.scalars().all()
        
        return {
            'success': True,
            'versions': versions
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing versions: {str(e)}"
        )


@router.post("/{quote_id}/create-version")
async def create_quote_version(
    quote_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Create a new version snapshot of a quote
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        from app.models.product import QuoteVersion
        import json
        
        stmt = select(Quote).where(
            Quote.id == quote_id,
            Quote.tenant_id == current_user.tenant_id
        )
        result = await db.execute(stmt)
        quote = result.scalar_one_or_none()
        
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")
        
        # Get current version number
        count_stmt = select(func.count(QuoteVersion.id)).where(
            QuoteVersion.quote_id == quote_id
        )
        count_result = await db.execute(count_stmt)
        existing_versions = count_result.scalar() or 0
        
        version_number = f"{existing_versions + 1}.0"
        
        # Create snapshot of quote data
        quote_snapshot = {
            'id': quote.id,
            'quote_number': quote.quote_number,
            'title': quote.title,
            'description': quote.description,
            'status': quote.status.value if hasattr(quote.status, 'value') else str(quote.status),
            'subtotal': float(quote.subtotal) if quote.subtotal else 0,
            'tax_amount': float(quote.tax_amount) if quote.tax_amount else 0,
            'total_amount': float(quote.total_amount) if quote.total_amount else 0,
            'project_title': quote.project_title,
            'project_description': quote.project_description,
            'site_address': quote.site_address,
            'building_type': quote.building_type,
            'building_size': quote.building_size,
            'number_of_floors': quote.number_of_floors,
            'number_of_rooms': quote.number_of_rooms,
            'cabling_type': quote.cabling_type,
            'wifi_requirements': quote.wifi_requirements,
            'cctv_requirements': quote.cctv_requirements,
            'door_entry_requirements': quote.door_entry_requirements,
            'special_requirements': quote.special_requirements,
            'ai_analysis': quote.ai_analysis,
            'recommended_products': quote.recommended_products,
            'labour_breakdown': quote.labour_breakdown,
            'quotation_details': quote.quotation_details,
            'items': []  # Will be populated below using sync session
        }
        
        # Load items relationship using async query
        from app.models.quotes import QuoteItem
        items_stmt = select(QuoteItem).where(
            and_(
                QuoteItem.quote_id == quote_id,
                QuoteItem.tenant_id == current_user.tenant_id
            )
        ).order_by(QuoteItem.sort_order)
        items_result = await db.execute(items_stmt)
        items = items_result.scalars().all()
        
        if items:
            quote_snapshot['items'] = [{
                'description': item.description,
                'quantity': float(item.quantity),
                'unit_price': float(item.unit_price),
                'total_price': float(item.total_price)
            } for item in items]
        
        version = QuoteVersion(
            quote_id=quote_id,
            version=version_number,
            quote_data=json.dumps(quote_snapshot),
            created_by=current_user.id
        )
        
        db.add(version)
        await db.commit()
        await db.refresh(version)
        
        return {
            'success': True,
            'version': version
        }
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error creating version: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error creating version: {str(e)}"
        )


@router.get("/{quote_id}/document")
async def generate_quote_document(
    quote_id: str,
    format: str = Query("docx", regex="^(docx|pdf)$"),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Generate Word or PDF document for a quote
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        from fastapi.responses import StreamingResponse
        from app.services.document_generator_service import DocumentGeneratorService
        
        stmt = select(Quote).where(
            Quote.id == quote_id,
            Quote.tenant_id == current_user.tenant_id
        )
        result = await db.execute(stmt)
        quote = result.scalar_one_or_none()
        
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")
        
        # DocumentGeneratorService currently expects sync session - use sync wrapper
        from app.core.database import SessionLocal
        sync_db = SessionLocal()
        try:
            generator = DocumentGeneratorService(sync_db, current_user.tenant_id)
            
            if format == "pdf":
                document = generator.generate_pdf_document(quote)
                if not document:
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to generate PDF document"
                    )
                return StreamingResponse(
                    document,
                    media_type="application/pdf",
                    headers={
                        "Content-Disposition": f'attachment; filename="quote_{quote.quote_number}.pdf"'
                    }
                )
            else:  # docx
                document = generator.generate_word_document(quote)
                if not document:
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to generate Word document"
                    )
                return StreamingResponse(
                    document,
                    media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    headers={
                        "Content-Disposition": f'attachment; filename="quote_{quote.quote_number}.docx"'
                    }
                )
        finally:
            sync_db.close()
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating document: {str(e)}"
        )


# ============================================================================
# Quote AI Copilot Endpoints
# ============================================================================

@router.get("/{quote_id}/ai/scope-analysis")
async def analyze_quote_scope(
    quote_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Analyze quote scope and provide summary with risks and recommendations
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        from app.services.quote_ai_copilot_service import QuoteAICopilotService
        from app.core.database import SessionLocal
        
        # Get quote
        stmt = select(Quote).where(
            and_(
                Quote.id == quote_id,
                Quote.tenant_id == current_user.tenant_id
            )
        )
        result = await db.execute(stmt)
        quote = result.scalar_one_or_none()
        
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")
        
        # Use sync session for AI service
        sync_db = SessionLocal()
        try:
            copilot_service = QuoteAICopilotService(sync_db, current_user.tenant_id)
            analysis = await copilot_service.analyze_quote_scope(quote)
        finally:
            sync_db.close()
        
        return analysis
    
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error analyzing quote scope: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing quote scope: {str(e)}"
        )


@router.get("/{quote_id}/ai/clarifying-questions")
async def get_clarifying_questions(
    quote_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Generate clarifying questions for quote
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        from app.services.quote_ai_copilot_service import QuoteAICopilotService
        from app.core.database import SessionLocal
        
        # Get quote
        stmt = select(Quote).where(
            and_(
                Quote.id == quote_id,
                Quote.tenant_id == current_user.tenant_id
            )
        )
        result = await db.execute(stmt)
        quote = result.scalar_one_or_none()
        
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")
        
        # Use sync session for AI service
        sync_db = SessionLocal()
        try:
            copilot_service = QuoteAICopilotService(sync_db, current_user.tenant_id)
            questions = await copilot_service.generate_clarifying_questions(quote)
        finally:
            sync_db.close()
        
        return {"questions": questions}
    
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error generating clarifying questions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating clarifying questions: {str(e)}"
        )


@router.get("/{quote_id}/ai/upsells")
async def get_upsell_suggestions(
    quote_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get upsell suggestions for quote
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        from app.services.quote_ai_copilot_service import QuoteAICopilotService
        from app.core.database import SessionLocal
        
        # Get quote
        stmt = select(Quote).where(
            and_(
                Quote.id == quote_id,
                Quote.tenant_id == current_user.tenant_id
            )
        )
        result = await db.execute(stmt)
        quote = result.scalar_one_or_none()
        
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")
        
        # Use sync session for AI service
        sync_db = SessionLocal()
        try:
            copilot_service = QuoteAICopilotService(sync_db, current_user.tenant_id)
            upsells = await copilot_service.suggest_upsells(quote)
        finally:
            sync_db.close()
        
        return {"upsells": upsells}
    
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting upsell suggestions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting upsell suggestions: {str(e)}"
        )


@router.get("/{quote_id}/ai/cross-sells")
async def get_cross_sell_suggestions(
    quote_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get cross-sell suggestions for quote
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        from app.services.quote_ai_copilot_service import QuoteAICopilotService
        from app.core.database import SessionLocal
        
        # Get quote
        stmt = select(Quote).where(
            and_(
                Quote.id == quote_id,
                Quote.tenant_id == current_user.tenant_id
            )
        )
        result = await db.execute(stmt)
        quote = result.scalar_one_or_none()
        
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")
        
        # Use sync session for AI service
        sync_db = SessionLocal()
        try:
            copilot_service = QuoteAICopilotService(sync_db, current_user.tenant_id)
            cross_sells = await copilot_service.suggest_cross_sells(quote)
        finally:
            sync_db.close()
        
        return {"cross_sells": cross_sells}
    
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting cross-sell suggestions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting cross-sell suggestions: {str(e)}"
        )


@router.get("/{quote_id}/ai/executive-summary")
async def get_executive_summary(
    quote_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Generate executive summary for quote
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        from app.services.quote_ai_copilot_service import QuoteAICopilotService
        from app.core.database import SessionLocal
        
        # Get quote
        stmt = select(Quote).where(
            and_(
                Quote.id == quote_id,
                Quote.tenant_id == current_user.tenant_id
            )
        )
        result = await db.execute(stmt)
        quote = result.scalar_one_or_none()
        
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")
        
        # Use sync session for AI service
        sync_db = SessionLocal()
        try:
            copilot_service = QuoteAICopilotService(sync_db, current_user.tenant_id)
            summary = await copilot_service.generate_executive_summary(quote)
        finally:
            sync_db.close()
        
        return {"summary": summary}
    
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error generating executive summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating executive summary: {str(e)}"
        )


class EmailCopyRequest(BaseModel):
    email_type: str = "send_quote"  # "send_quote", "follow_up", "reminder"


class EmailCopyResponse(BaseModel):
    subject: str
    body: str


@router.post("/{quote_id}/ai/email-copy", response_model=EmailCopyResponse)
async def generate_email_copy(
    quote_id: str,
    request: EmailCopyRequest,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Generate email copy for quote
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        from app.services.quote_ai_copilot_service import QuoteAICopilotService
        from app.core.database import SessionLocal
        
        # Get quote
        stmt = select(Quote).where(
            and_(
                Quote.id == quote_id,
                Quote.tenant_id == current_user.tenant_id
            )
        )
        result = await db.execute(stmt)
        quote = result.scalar_one_or_none()
        
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")
        
        # Use sync session for AI service
        sync_db = SessionLocal()
        try:
            copilot_service = QuoteAICopilotService(sync_db, current_user.tenant_id)
            email_copy = await copilot_service.generate_email_copy(
                quote,
                email_type=request.email_type
            )
        finally:
            sync_db.close()
        
        return EmailCopyResponse(**email_copy)
    
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error generating email copy: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating email copy: {str(e)}"
        )


# ============================================================================
# Enhanced Multi-Part Quote System Endpoints
# ============================================================================

class QuoteGenerateRequest(BaseModel):
    """Request model for AI quote generation"""
    customer_id: str = Field(..., description="Customer ID (required - quotes are only for customers, not leads)")
    customer_request: str = Field(..., description="Plain English description of what the client wants")
    quote_title: str = Field(..., description="Title for the quote")
    required_deadline: Optional[str] = None
    location: Optional[str] = None
    quantity: Optional[int] = None


class DocumentUpdateRequest(BaseModel):
    """Request model for updating a document"""
    content: Dict[str, Any] = Field(..., description="Document content structure")
    changes_summary: Optional[str] = None


@router.post("/generate", status_code=status.HTTP_201_CREATED)
async def generate_quote(
    request: QuoteGenerateRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    Generate a complete quote with AI and all document types
    
    Creates:
    - Quote record
    - Quote items (pricing)
    - 4 document types (parts list, technical, overview, build)
    """
    try:
        # Use sync session for services (they use sync sessions)
        sync_db = SessionLocal()
        builder_service = QuoteBuilderService(sync_db, str(current_tenant.id))
        
        try:
            # Await async method directly (we're in an async endpoint)
            result = await builder_service.build_quote(
                customer_request=request.customer_request,
                quote_title=request.quote_title,
                customer_id=request.customer_id,
                quote_type=None,  # AI will auto-detect from customer_request
                required_deadline=request.required_deadline,
                location=request.location,
                quantity=request.quantity,
                user_id=str(current_user.id)
            )
            
            if not result.get("success"):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.get("error", "Failed to generate quote")
                )
            
            quote = result["quote"]
            documents = result["documents"]
            
            return {
                "success": True,
                "quote_id": quote.id,
                "quote_number": quote.quote_number,
                "tier_type": quote.tier_type,
                "documents": [
                    {
                        "id": doc.id,
                        "document_type": doc.document_type,
                        "version": doc.version
                    }
                    for doc in documents
                ]
            }
        
        finally:
            sync_db.close()
    
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error generating quote: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating quote: {str(e)}"
        )


@router.get("/{quote_id}/documents")
async def get_quote_documents(
    quote_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Get all documents for a quote"""
    try:
        # Verify quote exists and belongs to tenant
        quote_stmt = select(Quote).where(
            and_(
                Quote.id == quote_id,
                Quote.tenant_id == str(current_tenant.id),
                Quote.is_deleted == False
            )
        )
        result = await db.execute(quote_stmt)
        quote = result.scalar_one_or_none()
        
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")
        
        # Get documents
        docs_stmt = select(QuoteDocument).where(
            and_(
                QuoteDocument.quote_id == quote_id,
                QuoteDocument.tenant_id == str(current_tenant.id)
            )
        )
        docs_result = await db.execute(docs_stmt)
        documents = docs_result.scalars().all()
        
        return {
            "quote_id": quote_id,
            "documents": [
                {
                    "id": doc.id,
                    "document_type": doc.document_type,
                    "version": doc.version,
                    "created_at": doc.created_at.isoformat(),
                    "updated_at": doc.updated_at.isoformat()
                }
                for doc in documents
            ]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting quote documents: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting quote documents: {str(e)}"
        )


@router.get("/{quote_id}/documents/{document_type}")
async def get_quote_document(
    quote_id: str,
    document_type: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Get a specific document for a quote"""
    try:
        # Verify quote exists
        quote_stmt = select(Quote).where(
            and_(
                Quote.id == quote_id,
                Quote.tenant_id == str(current_tenant.id),
                Quote.is_deleted == False
            )
        )
        result = await db.execute(quote_stmt)
        quote = result.scalar_one_or_none()
        
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")
        
        # Get document (latest version)
        doc_stmt = select(QuoteDocument).where(
            and_(
                QuoteDocument.quote_id == quote_id,
                QuoteDocument.document_type == document_type,
                QuoteDocument.tenant_id == str(current_tenant.id)
            )
        ).order_by(QuoteDocument.version.desc())
        
        doc_result = await db.execute(doc_stmt)
        document = doc_result.scalar_one_or_none()
        
        if not document:
            raise HTTPException(status_code=404, detail=f"Document type '{document_type}' not found")
        
        return {
            "id": document.id,
            "quote_id": quote_id,
            "document_type": document.document_type,
            "version": document.version,
            "content": document.content,
            "created_at": document.created_at.isoformat(),
            "updated_at": document.updated_at.isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting quote document: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting quote document: {str(e)}"
        )


@router.put("/{quote_id}/documents/{document_type}")
async def update_quote_document(
    quote_id: str,
    document_type: str,
    request: DocumentUpdateRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Update a quote document (creates new version automatically)"""
    try:
        # Verify quote exists
        quote_stmt = select(Quote).where(
            and_(
                Quote.id == quote_id,
                Quote.tenant_id == str(current_tenant.id),
                Quote.is_deleted == False
            )
        )
        result = await db.execute(quote_stmt)
        quote = result.scalar_one_or_none()
        
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")
        
        # Get document
        doc_stmt = select(QuoteDocument).where(
            and_(
                QuoteDocument.quote_id == quote_id,
                QuoteDocument.document_type == document_type,
                QuoteDocument.tenant_id == str(current_tenant.id)
            )
        )
        doc_result = await db.execute(doc_stmt)
        document = doc_result.scalar_one_or_none()
        
        if not document:
            raise HTTPException(status_code=404, detail=f"Document type '{document_type}' not found")
        
        # Use sync session for versioning service
        sync_db = SessionLocal()
        versioning_service = QuoteVersioningService(sync_db, str(current_tenant.id))
        
        try:
            # Get document in sync session
            sync_doc = sync_db.query(QuoteDocument).filter(
                QuoteDocument.id == document.id
            ).first()
            
            if not sync_doc:
                raise HTTPException(status_code=404, detail="Document not found")
            
            # Create new version before updating
            versioning_service.create_version(
                document=sync_doc,
                changes_summary=request.changes_summary,
                user_id=str(current_user.id)
            )
            
            # Update document content
            sync_doc.content = request.content
            sync_db.commit()
            sync_db.refresh(sync_doc)
            
            # Refresh async document
            await db.refresh(document)
            document.content = request.content
            
            return {
                "success": True,
                "document_id": document.id,
                "version": sync_doc.version,
                "message": "Document updated and new version created"
            }
        
        finally:
            sync_db.close()
    
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error updating quote document: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating quote document: {str(e)}"
        )


@router.post("/{quote_id}/documents/{document_type}/version")
async def create_document_version(
    quote_id: str,
    document_type: str,
    changes_summary: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Manually create a new version of a document"""
    try:
        sync_db = SessionLocal()
        versioning_service = QuoteVersioningService(sync_db, str(current_tenant.id))
        
        try:
            # Get document
            doc_stmt = select(QuoteDocument).where(
                and_(
                    QuoteDocument.quote_id == quote_id,
                    QuoteDocument.document_type == document_type,
                    QuoteDocument.tenant_id == str(current_tenant.id)
                )
            )
            doc_result = await db.execute(doc_stmt)
            document = doc_result.scalar_one_or_none()
            
            if not document:
                raise HTTPException(status_code=404, detail=f"Document type '{document_type}' not found")
            
            # Create version
            version = versioning_service.create_version(
                document=document,
                changes_summary=changes_summary,
                user_id=str(current_user.id)
            )
            
            return {
                "success": True,
                "version_id": version.id,
                "version": version.version,
                "created_at": version.created_at.isoformat()
            }
        
        finally:
            sync_db.close()
    
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error creating document version: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating document version: {str(e)}"
        )


@router.get("/{quote_id}/documents/{document_type}/versions")
async def get_document_versions(
    quote_id: str,
    document_type: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Get version history for a document"""
    try:
        sync_db = SessionLocal()
        versioning_service = QuoteVersioningService(sync_db, str(current_tenant.id))
        
        try:
            # Get document
            doc_stmt = select(QuoteDocument).where(
                and_(
                    QuoteDocument.quote_id == quote_id,
                    QuoteDocument.document_type == document_type,
                    QuoteDocument.tenant_id == str(current_tenant.id)
                )
            )
            doc_result = await db.execute(doc_stmt)
            document = doc_result.scalar_one_or_none()
            
            if not document:
                raise HTTPException(status_code=404, detail=f"Document type '{document_type}' not found")
            
            # Get version history
            versions = versioning_service.get_version_history(document.id)
            
            return {
                "document_id": document.id,
                "document_type": document_type,
                "current_version": document.version,
                "versions": [
                    {
                        "id": v.id,
                        "version": v.version,
                        "changes_summary": v.changes_summary,
                        "created_at": v.created_at.isoformat(),
                        "created_by": v.created_by
                    }
                    for v in versions
                ]
            }
        
        finally:
            sync_db.close()
    
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting document versions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting document versions: {str(e)}"
        )


@router.post("/{quote_id}/documents/{document_type}/rollback/{target_version}")
async def rollback_document_version(
    quote_id: str,
    document_type: str,
    target_version: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Rollback a document to a specific version"""
    try:
        sync_db = SessionLocal()
        versioning_service = QuoteVersioningService(sync_db, str(current_tenant.id))
        
        try:
            # Get document
            doc_stmt = select(QuoteDocument).where(
                and_(
                    QuoteDocument.quote_id == quote_id,
                    QuoteDocument.document_type == document_type,
                    QuoteDocument.tenant_id == str(current_tenant.id)
                )
            )
            doc_result = await db.execute(doc_stmt)
            document = doc_result.scalar_one_or_none()
            
            if not document:
                raise HTTPException(status_code=404, detail=f"Document type '{document_type}' not found")
            
            # Rollback
            success = versioning_service.rollback_to_version(
                document=document,
                target_version=target_version,
                user_id=str(current_user.id)
            )
            
            if not success:
                raise HTTPException(status_code=404, detail=f"Version {target_version} not found")
            
            await db.commit()
            await db.refresh(document)
            
            return {
                "success": True,
                "document_id": document.id,
                "current_version": document.version,
                "message": f"Document rolled back to version {target_version}"
            }
        
        finally:
            sync_db.close()
    
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error rolling back document version: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error rolling back document version: {str(e)}"
        )
