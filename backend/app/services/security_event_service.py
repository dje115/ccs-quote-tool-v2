#!/usr/bin/env python3
"""
Security Event Service

SECURITY: Centralized service for logging and monitoring security events.
"""

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, desc, func

from app.models.security_event import SecurityEvent, SecurityEventType, SecurityEventSeverity
from app.core.config import settings

logger = logging.getLogger(__name__)


class SecurityEventService:
    """Service for managing security events"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def log_event(
        self,
        event_type: SecurityEventType,
        description: str,
        severity: SecurityEventSeverity = SecurityEventSeverity.MEDIUM,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> SecurityEvent:
        """
        Log a security event
        
        Args:
            event_type: Type of security event
            description: Human-readable description
            severity: Severity level (default: MEDIUM)
            tenant_id: Optional tenant ID
            user_id: Optional user ID
            ip_address: Optional IP address
            user_agent: Optional user agent string
            metadata: Optional additional data (will be JSON-encoded)
            
        Returns:
            Created SecurityEvent record
        """
        import uuid
        
        event = SecurityEvent(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            user_id=user_id,
            event_type=event_type,
            severity=severity,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=json.dumps(metadata) if metadata else None,
            occurred_at=datetime.now(timezone.utc)
        )
        
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        
        # Log to application logger as well
        log_level = {
            SecurityEventSeverity.LOW: logging.INFO,
            SecurityEventSeverity.MEDIUM: logging.WARNING,
            SecurityEventSeverity.HIGH: logging.ERROR,
            SecurityEventSeverity.CRITICAL: logging.CRITICAL
        }.get(severity, logging.WARNING)
        
        logger.log(
            log_level,
            f"Security Event: {event_type.value} - {description}",
            extra={
                "event_id": event.id,
                "tenant_id": tenant_id,
                "user_id": user_id,
                "ip_address": ip_address,
                "severity": severity.value
            }
        )
        
        return event
    
    def get_recent_events(
        self,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        event_type: Optional[SecurityEventType] = None,
        severity: Optional[SecurityEventSeverity] = None,
        limit: int = 100,
        hours: int = 24
    ) -> List[SecurityEvent]:
        """
        Get recent security events
        
        Args:
            tenant_id: Filter by tenant ID
            user_id: Filter by user ID
            event_type: Filter by event type
            severity: Filter by severity
            limit: Maximum number of events to return
            hours: Number of hours to look back
            
        Returns:
            List of SecurityEvent records
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        stmt = select(SecurityEvent).where(
            SecurityEvent.occurred_at >= cutoff_time
        )
        
        if tenant_id:
            stmt = stmt.where(SecurityEvent.tenant_id == tenant_id)
        
        if user_id:
            stmt = stmt.where(SecurityEvent.user_id == user_id)
        
        if event_type:
            stmt = stmt.where(SecurityEvent.event_type == event_type)
        
        if severity:
            stmt = stmt.where(SecurityEvent.severity == severity)
        
        stmt = stmt.order_by(desc(SecurityEvent.occurred_at)).limit(limit)
        
        result = self.db.execute(stmt)
        return result.scalars().all()
    
    def get_event_statistics(
        self,
        tenant_id: Optional[str] = None,
        hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get statistics about security events
        
        Args:
            tenant_id: Filter by tenant ID
            hours: Number of hours to analyze
            
        Returns:
            Dictionary with event statistics
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        stmt = select(
            SecurityEvent.event_type,
            SecurityEvent.severity,
            func.count(SecurityEvent.id).label('count')
        ).where(
            SecurityEvent.occurred_at >= cutoff_time
        )
        
        if tenant_id:
            stmt = stmt.where(SecurityEvent.tenant_id == tenant_id)
        
        stmt = stmt.group_by(SecurityEvent.event_type, SecurityEvent.severity)
        
        result = self.db.execute(stmt)
        rows = result.all()
        
        stats = {
            "total_events": sum(row.count for row in rows),
            "by_type": {},
            "by_severity": {
                "low": 0,
                "medium": 0,
                "high": 0,
                "critical": 0
            },
            "failed_logins": 0,
            "account_lockouts": 0,
            "rate_limit_exceeded": 0
        }
        
        for row in rows:
            event_type = row.event_type.value
            severity = row.severity.value
            count = row.count
            
            if event_type not in stats["by_type"]:
                stats["by_type"][event_type] = 0
            stats["by_type"][event_type] += count
            
            stats["by_severity"][severity] += count
            
            if event_type == SecurityEventType.FAILED_LOGIN.value:
                stats["failed_logins"] += count
            elif event_type == SecurityEventType.ACCOUNT_LOCKED.value:
                stats["account_lockouts"] += count
            elif event_type == SecurityEventType.RATE_LIMIT_EXCEEDED.value:
                stats["rate_limit_exceeded"] += count
        
        return stats
    
    def mark_resolved(self, event_id: str, resolved_by: str) -> bool:
        """
        Mark a security event as resolved
        
        Args:
            event_id: ID of the event to resolve
            resolved_by: User ID who resolved the event
            
        Returns:
            True if event was found and resolved, False otherwise
        """
        stmt = select(SecurityEvent).where(SecurityEvent.id == event_id)
        result = self.db.execute(stmt)
        event = result.scalar_one_or_none()
        
        if not event:
            return False
        
        event.resolved = resolved_by
        event.resolved_at = datetime.now(timezone.utc)
        self.db.commit()
        
        return True

