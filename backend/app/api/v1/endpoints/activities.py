#!/usr/bin/env python3
"""
Sales Activity API Endpoints

Handles all sales activity operations including:
- Creating and logging activities (calls, notes, emails, meetings)
- AI-powered note enhancement
- Action suggestions
- Activity history
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.core.dependencies import get_db, get_current_user, get_current_tenant
from app.models.tenant import User, Tenant
from app.models.sales import SalesActivity, ActivityType, ActivityOutcome
from app.services.activity_service import ActivityService
from app.core.celery_app import celery_app

router = APIRouter()


# Pydantic schemas
class ActivityCreate(BaseModel):
    customer_id: str
    activity_type: str  # 'call', 'note', 'email', 'meeting', 'task'
    notes: str
    subject: Optional[str] = None
    contact_id: Optional[str] = None
    duration_minutes: Optional[int] = None
    outcome: Optional[str] = None
    process_with_ai: bool = True


class ActivityResponse(BaseModel):
    id: str
    customer_id: str
    user_id: str
    contact_id: Optional[str]
    activity_type: str
    activity_date: datetime
    duration_minutes: Optional[int]
    subject: Optional[str]
    notes: str
    notes_cleaned: Optional[str]
    ai_suggested_action: Optional[str]
    outcome: Optional[str]
    follow_up_required: bool
    follow_up_date: Optional[datetime]
    ai_context: Optional[dict]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ActionSuggestionsResponse(BaseModel):
    success: bool
    suggestions: Optional[dict]
    generated_at: Optional[str]
    error: Optional[str] = None


@router.post("/", response_model=ActivityResponse)
async def create_activity(
    activity: ActivityCreate,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Create a new sales activity
    
    Activity will be automatically enhanced with AI to:
    - Clean up and structure notes
    - Suggest next actions
    - Extract key information
    """
    print(f"[CREATE ACTIVITY] Type: {activity.activity_type}, Customer: {activity.customer_id}")
    print(f"[CREATE ACTIVITY] Notes: {activity.notes[:100]}...")
    
    try:
        # Map string to enum
        activity_type_enum = ActivityType[activity.activity_type.upper()]
        outcome_enum = ActivityOutcome[activity.outcome.upper()] if activity.outcome else None
        
        service = ActivityService(db, current_tenant.id)
        
        new_activity = await service.create_activity(
            customer_id=activity.customer_id,
            user_id=current_user.id,
            activity_type=activity_type_enum,
            notes=activity.notes,
            subject=activity.subject,
            contact_id=activity.contact_id,
            duration_minutes=activity.duration_minutes,
            outcome=outcome_enum,
            process_with_ai=activity.process_with_ai
        )
        
        print(f"✓ Activity created with AI enhancement: {new_activity.id}")
        
        # Publish activity.created event
        from app.core.events import get_event_publisher
        event_publisher = get_event_publisher()
        activity_dict = {
            "id": new_activity.id,
            "customer_id": new_activity.customer_id,
            "activity_type": new_activity.activity_type.value if hasattr(new_activity.activity_type, 'value') else str(new_activity.activity_type),
            "subject": new_activity.subject,
            "notes": new_activity.notes,
            "activity_date": new_activity.activity_date.isoformat() if new_activity.activity_date else None,
        }
        event_publisher.publish_activity_created(
            tenant_id=current_tenant.id,
            activity_id=new_activity.id,
            activity_data=activity_dict
        )
        
        return new_activity
        
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid activity type or outcome: {str(e)}"
        )
    except Exception as e:
        print(f"[ERROR] Failed to create activity: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create activity: {str(e)}"
        )


@router.get("/customer/{customer_id}", response_model=List[ActivityResponse])
async def get_customer_activities(
    customer_id: str,
    activity_type: Optional[str] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Get all activities for a customer"""
    try:
        service = ActivityService(db, current_tenant.id)
        
        activity_type_enum = None
        if activity_type:
            activity_type_enum = ActivityType[activity_type.upper()]
        
        activities = service.get_activities(
            customer_id=customer_id,
            activity_type=activity_type_enum,
            limit=limit
        )
        
        return activities
        
    except Exception as e:
        print(f"[ERROR] Failed to get activities: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get activities: {str(e)}"
        )


@router.get("/customer/{customer_id}/suggestions", response_model=ActionSuggestionsResponse)
async def get_action_suggestions(
    customer_id: str,
    force_refresh: bool = False,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Get AI-powered action suggestions for a customer
    
    Returns suggestions for:
    - Phone calls (with talking points)
    - Emails (with topics)
    - Customer visits (with objectives)
    
    Based on customer history, status, and AI analysis
    
    Query Parameters:
    - force_refresh: Set to true to regenerate suggestions even if cached. Default: false (use cache if available)
    """
    cache_status = "refresh" if force_refresh else "cache-first"
    print(f"[ACTION SUGGESTIONS] Getting for customer: {customer_id} (mode: {cache_status})")
    
    try:
        service = ActivityService(db, current_tenant.id)
        result = await service.generate_action_suggestions(customer_id, force_refresh=force_refresh)
        
        cached_msg = " (cached)" if result.get('cached') else " (generated)"
        print(f"✓ Got action suggestions for customer {customer_id}{cached_msg}")
        
        return result
        
    except Exception as e:
        print(f"[ERROR] Failed to get suggestions: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'suggestions': None,
            'generated_at': None,
            'error': str(e)
        }


@router.post("/customer/{customer_id}/suggestions/refresh")
async def refresh_suggestions_background(
    customer_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Queue a background task to refresh AI action suggestions for a customer
    
    This endpoint immediately returns and the suggestions are generated in the background.
    The user can continue working while the AI processes the request.
    Once complete, the cached suggestions will be available on the next page load.
    """
    print(f"\n{'='*80}")
    print(f"🔄 QUEUEING SUGGESTION REFRESH TO CELERY")
    print(f"Customer ID: {customer_id}")
    print(f"Tenant: {current_tenant.name} ({current_tenant.id})")
    print(f"{'='*80}\n")
    
    # Queue the refresh task to Celery
    task = celery_app.send_task(
        'refresh_customer_suggestions',
        args=[customer_id, str(current_tenant.id)]
    )
    
    print(f"✓ Task queued: {task.id}")
    
    return {
        'success': True,
        'message': 'Suggestion refresh queued in background',
        'task_id': task.id,
        'status': 'processing'
    }


@router.get("/pending-followups", response_model=List[ActivityResponse])
async def get_pending_follow_ups(
    days_ahead: int = 7,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Get all activities requiring follow-up in the next N days"""
    try:
        service = ActivityService(db, current_tenant.id)
        follow_ups = service.get_pending_follow_ups(days_ahead)
        
        return follow_ups
        
    except Exception as e:
        print(f"[ERROR] Failed to get follow-ups: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get follow-ups: {str(e)}"
        )

