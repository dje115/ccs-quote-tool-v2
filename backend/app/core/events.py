#!/usr/bin/env python3
"""
Event Publisher Service for Real-Time Updates
Publishes events to Redis Pub/Sub channels for WebSocket broadcasting
"""

import json
import redis
from typing import Dict, Any, Optional
from datetime import datetime
from app.core.config import settings


class EventPublisher:
    """
    Publishes events to Redis Pub/Sub channels
    All events are tenant-scoped for multi-tenant isolation
    """
    
    def __init__(self):
        """Initialize Redis connection for Pub/Sub"""
        self.redis_client: Optional[redis.Redis] = None
        self._connect()
    
    def _connect(self):
        """Connect to Redis"""
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            # Test connection
            self.redis_client.ping()
        except Exception as e:
            print(f"⚠️ EventPublisher: Redis connection failed: {e}")
            self.redis_client = None
    
    def _publish(self, tenant_id: str, event_type: str, data: Dict[str, Any]):
        """
        Publish event to tenant-specific Redis channel
        
        Args:
            tenant_id: Tenant ID for channel isolation
            event_type: Event type (e.g., 'customer.updated')
            data: Event payload
        """
        if not self.redis_client:
            self._connect()
            if not self.redis_client:
                print(f"⚠️ EventPublisher: Cannot publish event, Redis not available")
                return
        
        try:
            channel = f"tenant:{tenant_id}:events"
            event = {
                "type": event_type,
                "tenant_id": tenant_id,
                "data": data,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
            self.redis_client.publish(channel, json.dumps(event))
            print(f"📡 Published event: {event_type} to {channel}")
        except Exception as e:
            print(f"❌ EventPublisher: Failed to publish event: {e}")
    
    # Customer Events
    def publish_customer_created(self, tenant_id: str, customer_id: str, customer_data: Dict[str, Any]):
        """Publish customer.created event"""
        self._publish(tenant_id, "customer.created", {
            "customer_id": customer_id,
            "customer": customer_data
        })
    
    def publish_customer_updated(self, tenant_id: str, customer_id: str, customer_data: Dict[str, Any]):
        """Publish customer.updated event"""
        self._publish(tenant_id, "customer.updated", {
            "customer_id": customer_id,
            "customer": customer_data
        })
    
    def publish_customer_deleted(self, tenant_id: str, customer_id: str):
        """Publish customer.deleted event"""
        self._publish(tenant_id, "customer.deleted", {
            "customer_id": customer_id
        })
    
    # AI Analysis Events
    def publish_ai_analysis_started(self, tenant_id: str, customer_id: str, task_id: str, customer_name: str):
        """Publish ai_analysis.started event"""
        self._publish(tenant_id, "ai_analysis.started", {
            "customer_id": customer_id,
            "task_id": task_id,
            "customer_name": customer_name
        })
    
    def publish_ai_analysis_progress(self, tenant_id: str, customer_id: str, task_id: str, progress: Dict[str, Any]):
        """Publish ai_analysis.progress event"""
        self._publish(tenant_id, "ai_analysis.progress", {
            "customer_id": customer_id,
            "task_id": task_id,
            "progress": progress
        })
    
    def publish_ai_analysis_completed(self, tenant_id: str, customer_id: str, task_id: str, customer_name: str, result: Dict[str, Any]):
        """Publish ai_analysis.completed event"""
        self._publish(tenant_id, "ai_analysis.completed", {
            "customer_id": customer_id,
            "task_id": task_id,
            "customer_name": customer_name,
            "result": result
        })
    
    def publish_ai_analysis_failed(self, tenant_id: str, customer_id: str, task_id: str, customer_name: str, error: str):
        """Publish ai_analysis.failed event"""
        self._publish(tenant_id, "ai_analysis.failed", {
            "customer_id": customer_id,
            "task_id": task_id,
            "customer_name": customer_name,
            "error": error
        })
    
    # Campaign Events
    def publish_campaign_started(self, tenant_id: str, campaign_id: str, campaign_name: str, task_id: str):
        """Publish campaign.started event"""
        self._publish(tenant_id, "campaign.started", {
            "campaign_id": campaign_id,
            "campaign_name": campaign_name,
            "task_id": task_id
        })
    
    def publish_campaign_progress(self, tenant_id: str, campaign_id: str, progress: Dict[str, Any]):
        """Publish campaign.progress event"""
        self._publish(tenant_id, "campaign.progress", {
            "campaign_id": campaign_id,
            "progress": progress
        })
    
    def publish_campaign_completed(self, tenant_id: str, campaign_id: str, campaign_name: str, result: Dict[str, Any]):
        """Publish campaign.completed event"""
        self._publish(tenant_id, "campaign.completed", {
            "campaign_id": campaign_id,
            "campaign_name": campaign_name,
            "result": result
        })
    
    def publish_campaign_failed(self, tenant_id: str, campaign_id: str, campaign_name: str, error: str):
        """Publish campaign.failed event"""
        self._publish(tenant_id, "campaign.failed", {
            "campaign_id": campaign_id,
            "campaign_name": campaign_name,
            "error": error
        })
    
    # Activity Events
    def publish_activity_suggestions_updated(self, tenant_id: str, customer_id: str):
        """Publish activity.suggestions_updated event"""
        self._publish(tenant_id, "activity.suggestions_updated", {
            "customer_id": customer_id
        })
    
    def publish_activity_created(self, tenant_id: str, activity_id: str, activity_data: Dict[str, Any]):
        """Publish activity.created event"""
        self._publish(tenant_id, "activity.created", {
            "activity_id": activity_id,
            "activity": activity_data
        })
    
    def publish_activity_updated(self, tenant_id: str, activity_id: str, activity_data: Dict[str, Any]):
        """Publish activity.updated event"""
        self._publish(tenant_id, "activity.updated", {
            "activity_id": activity_id,
            "activity": activity_data
        })
    
    # Quote Events
    def publish_quote_created(self, tenant_id: str, quote_id: str, quote_data: Dict[str, Any]):
        """Publish quote.created event"""
        self._publish(tenant_id, "quote.created", {
            "quote_id": quote_id,
            "quote": quote_data
        })
    
    def publish_quote_updated(self, tenant_id: str, quote_id: str, quote_data: Dict[str, Any]):
        """Publish quote.updated event"""
        self._publish(tenant_id, "quote.updated", {
            "quote_id": quote_id,
            "quote": quote_data
        })
    
    def publish_quote_status_changed(self, tenant_id: str, quote_id: str, old_status: str, new_status: str):
        """Publish quote.status_changed event"""
        self._publish(tenant_id, "quote.status_changed", {
            "quote_id": quote_id,
            "old_status": old_status,
            "new_status": new_status
        })


# Global event publisher instance
_event_publisher: Optional[EventPublisher] = None


def get_event_publisher() -> EventPublisher:
    """Get global event publisher instance"""
    global _event_publisher
    if _event_publisher is None:
        _event_publisher = EventPublisher()
    return _event_publisher

