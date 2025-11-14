#!/usr/bin/env python3
"""
Quote management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from decimal import Decimal
import uuid
from datetime import datetime

from app.core.database import get_db
from app.core.dependencies import get_current_user, check_permission, get_current_tenant
from app.models.quotes import Quote, QuoteStatus
from app.models.tenant import User, Tenant
from app.services.quote_analysis_service import QuoteAnalysisService
from app.services.quote_pricing_service import QuotePricingService
from app.services.quote_consistency_service import QuoteConsistencyService
from app.core.api_keys import get_api_keys

router = APIRouter()


class QuoteCreate(BaseModel):
    customer_id: str
    title: str
    description: str | None = None
    valid_until: datetime | None = None
    quote_type: str | None = None  # e.g., 'cabling', 'network_build', 'server_build', 'software_dev', 'testing', 'design'
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


@router.get("/", response_model=List[QuoteResponse])
async def list_quotes(
    skip: int = 0,
    limit: int = 20,
    status: QuoteStatus | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List quotes for current tenant"""
    try:
        query = db.query(Quote).filter_by(
            tenant_id=current_user.tenant_id,
            is_deleted=False
        )
        
        if status:
            query = query.filter_by(status=status)
        
        quotes = query.order_by(Quote.created_at.desc()).offset(skip).limit(limit).all()
        
        # Convert to response format
        return [
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
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error fetching quotes: {str(e)}")


@router.post("/", response_model=QuoteResponse, status_code=status.HTTP_201_CREATED)
async def create_quote(
    quote_data: QuoteCreate,
    current_user: User = Depends(check_permission("quote:create")),
    db: Session = Depends(get_db)
):
    """Create new quote"""
    
    try:
        # Generate quote number
        quote_count = db.query(Quote).filter_by(tenant_id=current_user.tenant_id).count()
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
        db.commit()
        db.refresh(quote)
        
        # Publish quote.created event
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
        event_publisher.publish_quote_created(
            tenant_id=current_user.tenant_id,
            quote_id=quote.id,
            quote_data=quote_dict
        )
        
        return quote
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating quote: {str(e)}"
        )


@router.get("/{quote_id}", response_model=QuoteResponse)
async def get_quote(
    quote_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get quote by ID"""
    quote = db.query(Quote).filter_by(
        id=quote_id,
        tenant_id=current_user.tenant_id,
        is_deleted=False
    ).first()
    
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    return quote


@router.put("/{quote_id}", response_model=QuoteResponse)
async def update_quote(
    quote_id: str,
    quote_update: QuoteUpdate,
    current_user: User = Depends(check_permission("quote:update")),
    db: Session = Depends(get_db)
):
    """Update quote"""
    quote = db.query(Quote).filter_by(
        id=quote_id,
        tenant_id=current_user.tenant_id,
        is_deleted=False
    ).first()
    
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
    
    db.commit()
    db.refresh(quote)
    
    # Publish quote.updated event
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
    event_publisher.publish_quote_updated(
        tenant_id=current_user.tenant_id,
        quote_id=quote.id,
        quote_data=quote_dict
    )
    
    # Publish status change event if status changed
    if quote_update.status is not None and old_status != quote.status:
        event_publisher.publish_quote_status_changed(
            tenant_id=current_user.tenant_id,
            quote_id=quote.id,
            old_status=old_status.value if hasattr(old_status, 'value') else str(old_status),
            new_status=quote.status.value if hasattr(quote.status, 'value') else str(quote.status)
        )
    
    return quote


@router.delete("/{quote_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_quote(
    quote_id: str,
    current_user: User = Depends(check_permission("quote:delete")),
    db: Session = Depends(get_db)
):
    """Soft delete quote"""
    quote = db.query(Quote).filter_by(
        id=quote_id,
        tenant_id=current_user.tenant_id,
        is_deleted=False
    ).first()
    
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    quote.is_deleted = True
    quote.deleted_at = datetime.utcnow()
    db.commit()
    
    return None


@router.post("/analyze")
async def analyze_quote_requirements(
    request: QuoteAnalyzeRequest,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Analyze quote requirements using AI (can analyze before or after quote creation)"""
    try:
        # Get API keys
        api_keys = get_api_keys(db, current_tenant)
        if not api_keys.openai:
            raise HTTPException(
                status_code=400,
                detail="OpenAI API key not configured"
            )
        
        # Build quote data dict - use request data if provided, otherwise fetch from quote
        if request.quote_id:
            quote = db.query(Quote).filter(
                Quote.id == request.quote_id,
                Quote.tenant_id == current_user.tenant_id
            ).first()
            
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
            quote = None
        
        # Analyze requirements
        analysis_service = QuoteAnalysisService(
            db=db,
            tenant_id=current_user.tenant_id,
            openai_api_key=api_keys.openai
        )
        
        result = await analysis_service.analyze_requirements(
            quote_data=quote_data,
            clarification_answers=request.clarification_answers,
            questions_only=request.questions_only
        )
        
        if not result.get('success'):
            raise HTTPException(
                status_code=500,
                detail=result.get('error', 'Analysis failed')
            )
        
        # Update quote with analysis results (if not questions_only and quote exists)
        if quote and not request.questions_only and result.get('analysis'):
            analysis = result['analysis']
            quote.ai_analysis = analysis
            quote.recommended_products = analysis.get('recommended_products')
            quote.labour_breakdown = analysis.get('labour_breakdown')
            quote.estimated_time = analysis.get('estimated_time')
            quote.estimated_cost = analysis.get('estimated_cost')
            quote.quotation_details = analysis.get('quotation')
            
            # Update travel costs if provided
            if 'travel_distance_km' in analysis:
                quote.travel_distance_km = analysis.get('travel_distance_km')
                quote.travel_time_minutes = analysis.get('travel_time_minutes')
                quote.travel_cost = analysis.get('travel_cost')
            
            if result.get('raw_response'):
                quote.ai_raw_response = result['raw_response']
            
            db.commit()
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing quote: {str(e)}"
        )


@router.post("/{quote_id}/calculate-pricing")
async def calculate_quote_pricing(
    quote_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Calculate pricing for a quote"""
    try:
        quote = db.query(Quote).filter(
            Quote.id == quote_id,
            Quote.tenant_id == current_user.tenant_id
        ).first()
        
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")
        
        pricing_service = QuotePricingService(db, tenant_id=current_user.tenant_id)
        pricing_breakdown = pricing_service.calculate_quote_pricing(quote)
        
        db.commit()
        db.refresh(quote)
        
        return {
            'success': True,
            'pricing_breakdown': pricing_breakdown,
            'quote': quote
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating pricing: {str(e)}"
        )


@router.post("/{quote_id}/duplicate")
async def duplicate_quote(
    quote_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Duplicate a quote"""
    try:
        original_quote = db.query(Quote).filter(
            Quote.id == quote_id,
            Quote.tenant_id == current_user.tenant_id
        ).first()
        
        if not original_quote:
            raise HTTPException(status_code=404, detail="Quote not found")
        
        # Generate new quote number
        quote_count = db.query(Quote).filter_by(tenant_id=current_user.tenant_id).count()
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
        db.flush()
        
        # Copy quote items if any
        for item in original_quote.items:
            from app.models.quotes import QuoteItem
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
        
        db.commit()
        db.refresh(new_quote)
        
        return new_quote
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error duplicating quote: {str(e)}"
        )


@router.post("/{quote_id}/clarifications")
async def submit_clarifications(
    quote_id: str,
    clarification_answers: List[Dict[str, str]],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit clarification answers and re-analyze quote"""
    try:
        import json
        
        quote = db.query(Quote).filter(
            Quote.id == quote_id,
            Quote.tenant_id == current_user.tenant_id
        ).first()
        
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")
        
        # Store clarification answers
        clarifications_log = []
        if quote.clarifications_log:
            if isinstance(quote.clarifications_log, str):
                clarifications_log = json.loads(quote.clarifications_log)
            else:
                clarifications_log = quote.clarifications_log
        
        clarifications_log.extend(clarification_answers)
        quote.clarifications_log = json.dumps(clarifications_log)
        
        # Re-analyze with clarification answers
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
            'special_requirements': quote.special_requirements
        }
        
        api_keys = get_api_keys(db, current_user.tenant)
        analysis_service = QuoteAnalysisService(
            db=db,
            tenant_id=current_user.tenant_id,
            openai_api_key=api_keys.openai
        )
        
        result = await analysis_service.analyze_requirements(
            quote_data=quote_data,
            clarification_answers=clarification_answers,
            questions_only=False
        )
        
        if result.get('success') and result.get('analysis'):
            analysis = result['analysis']
            quote.ai_analysis = analysis
            quote.recommended_products = json.dumps(analysis.get('recommended_products', []))
            quote.labour_breakdown = json.dumps(analysis.get('labour_breakdown', []))
            quote.estimated_time = analysis.get('estimated_time')
            quote.estimated_cost = analysis.get('estimated_cost')
            quote.quotation_details = json.dumps(analysis.get('quotation', {}))
            
            if result.get('raw_response'):
                quote.ai_raw_response = result['raw_response']
        
        db.commit()
        db.refresh(quote)
        
        return {
            'success': True,
            'quote': quote,
            'analysis': result.get('analysis')
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error submitting clarifications: {str(e)}"
        )


@router.post("/{quote_id}/approve")
async def approve_quote(
    quote_id: str,
    current_user: User = Depends(check_permission("quote:approve")),
    db: Session = Depends(get_db)
):
    """Approve a quote"""
    try:
        quote = db.query(Quote).filter(
            Quote.id == quote_id,
            Quote.tenant_id == current_user.tenant_id
        ).first()
        
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")
        
        quote.status = QuoteStatus.ACCEPTED
        db.commit()
        db.refresh(quote)
        
        # Publish quote.approved event
        from app.core.events import get_event_publisher
        event_publisher = get_event_publisher()
        await event_publisher.publish_quote_status_changed(
            tenant_id=current_user.tenant_id,
            quote_id=quote.id,
            old_status="pending",
            new_status="accepted"
        )
        
        return {
            'success': True,
            'quote': quote
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error approving quote: {str(e)}"
        )


@router.post("/{quote_id}/reject")
async def reject_quote(
    quote_id: str,
    reason: Optional[str] = None,
    current_user: User = Depends(check_permission("quote:approve")),
    db: Session = Depends(get_db)
):
    """Reject a quote"""
    try:
        quote = db.query(Quote).filter(
            Quote.id == quote_id,
            Quote.tenant_id == current_user.tenant_id
        ).first()
        
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")
        
        quote.status = QuoteStatus.REJECTED
        if reason:
            quote.notes = (quote.notes or "") + f"\nRejection reason: {reason}"
        
        db.commit()
        db.refresh(quote)
        
        # Publish quote.rejected event
        from app.core.events import get_event_publisher
        event_publisher = get_event_publisher()
        await event_publisher.publish_quote_status_changed(
            tenant_id=current_user.tenant_id,
            quote_id=quote.id,
            old_status="pending",
            new_status="rejected"
        )
        
        return {
            'success': True,
            'quote': quote
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error rejecting quote: {str(e)}"
        )


@router.get("/{quote_id}/consistency")
async def get_quote_consistency(
    quote_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get consistency analysis for a quote"""
    try:
        quote = db.query(Quote).filter(
            Quote.id == quote_id,
            Quote.tenant_id == current_user.tenant_id
        ).first()
        
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")
        
        consistency_service = QuoteConsistencyService(db, current_user.tenant_id)
        analysis = consistency_service.analyze_quote_consistency(quote_id)
        
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
    db: Session = Depends(get_db)
):
    """List all versions of a quote"""
    try:
        from app.models.product import QuoteVersion
        
        quote = db.query(Quote).filter(
            Quote.id == quote_id,
            Quote.tenant_id == current_user.tenant_id
        ).first()
        
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")
        
        versions = db.query(QuoteVersion).filter(
            QuoteVersion.quote_id == quote_id
        ).order_by(QuoteVersion.created_at.desc()).all()
        
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
    db: Session = Depends(get_db)
):
    """Create a new version of a quote"""
    try:
        from app.models.product import QuoteVersion
        import json
        
        quote = db.query(Quote).filter(
            Quote.id == quote_id,
            Quote.tenant_id == current_user.tenant_id
        ).first()
        
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")
        
        # Get current version number
        existing_versions = db.query(QuoteVersion).filter(
            QuoteVersion.quote_id == quote_id
        ).count()
        
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
            'items': [{
                'description': item.description,
                'quantity': float(item.quantity),
                'unit_price': float(item.unit_price),
                'total_price': float(item.total_price)
            } for item in quote.items]
        }
        
        version = QuoteVersion(
            quote_id=quote_id,
            version=version_number,
            quote_data=json.dumps(quote_snapshot),
            created_by=current_user.id
        )
        
        db.add(version)
        db.commit()
        db.refresh(version)
        
        return {
            'success': True,
            'version': version
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
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
    db: Session = Depends(get_db)
):
    """Generate Word or PDF document for a quote"""
    try:
        from fastapi.responses import StreamingResponse
        from app.services.document_generator_service import DocumentGeneratorService
        
        quote = db.query(Quote).filter(
            Quote.id == quote_id,
            Quote.tenant_id == current_user.tenant_id
        ).first()
        
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")
        
        generator = DocumentGeneratorService(db, current_user.tenant_id)
        
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
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating document: {str(e)}"
        )
