#!/usr/bin/env python3
"""
Security monitoring endpoints

SECURITY: Provides endpoints for monitoring and auditing security events.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_super_admin
from app.models.tenant import User
from app.models.security_event import SecurityEvent, SecurityEventType, SecurityEventSeverity
from app.services.security_event_service import SecurityEventService

router = APIRouter()


class SecurityEventResponse(BaseModel):
    """Response model for security events"""
    id: str
    tenant_id: Optional[str]
    user_id: Optional[str]
    event_type: str
    severity: str
    description: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    metadata: Optional[dict]
    resolved: Optional[str]
    resolved_at: Optional[datetime]
    occurred_at: datetime
    
    class Config:
        from_attributes = True


class SecurityEventStatistics(BaseModel):
    """Security event statistics"""
    total_events: int
    by_type: dict
    by_severity: dict
    failed_logins: int
    account_lockouts: int
    rate_limit_exceeded: int


@router.get("/events", response_model=List[SecurityEventResponse])
async def get_security_events(
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    hours: int = Query(24, description="Number of hours to look back"),
    limit: int = Query(100, description="Maximum number of events to return"),
    current_user: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
    """
    Get recent security events
    
    SECURITY: Only accessible to super admins.
    """
    # Parse event type and severity if provided
    parsed_event_type = None
    if event_type:
        try:
            parsed_event_type = SecurityEventType(event_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid event type: {event_type}"
            )
    
    parsed_severity = None
    if severity:
        try:
            parsed_severity = SecurityEventSeverity(severity)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid severity: {severity}"
            )
    
    service = SecurityEventService(db)
    events = service.get_recent_events(
        tenant_id=tenant_id,
        user_id=user_id,
        event_type=parsed_event_type,
        severity=parsed_severity,
        limit=limit,
        hours=hours
    )
    
    return events


@router.get("/statistics", response_model=SecurityEventStatistics)
async def get_security_statistics(
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
    hours: int = Query(24, description="Number of hours to analyze"),
    current_user: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
    """
    Get security event statistics
    
    SECURITY: Only accessible to super admins.
    """
    service = SecurityEventService(db)
    stats = service.get_event_statistics(tenant_id=tenant_id, hours=hours)
    
    return stats


@router.post("/events/{event_id}/resolve")
async def resolve_security_event(
    event_id: str,
    current_user: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
    """
    Mark a security event as resolved
    
    SECURITY: Only accessible to super admins.
    """
    service = SecurityEventService(db)
    resolved = service.mark_resolved(event_id, current_user.id)
    
    if not resolved:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Security event not found"
        )
    
    return {"message": "Security event resolved", "event_id": event_id}

