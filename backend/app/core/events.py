#!/usr/bin/env python3
"""
Event Publisher Service for Real-Time Updates
Publishes events to Redis Pub/Sub channels for WebSocket broadcasting

SECURITY: Uses async Redis client to prevent blocking the event loop
"""

import json
import redis.asyncio as aioredis
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
from app.core.config import settings


class EventPublisher:
    """
    Publishes events to Redis Pub/Sub channels asynchronously
    All events are tenant-scoped for multi-tenant isolation
    
    PERFORMANCE: Uses async Redis client to prevent blocking the event loop
    """
    
    def __init__(self):
        """Initialize Redis connection for Pub/Sub"""
        self.redis_client: Optional[aioredis.Redis] = None
        self._lock = asyncio.Lock()
    
    async def close(self):
        """Close Redis connection and cleanup resources"""
        if self.redis_client:
            try:
                await self.redis_client.close()
                self.redis_client = None
                print("✅ EventPublisher: Redis connection closed")
            except Exception as e:
                print(f"⚠️ EventPublisher: Error closing Redis connection: {e}")
    
    async def _connect(self):
        """Connect to Redis asynchronously"""
        async with self._lock:
            if self.redis_client:
                return
            
            try:
                self.redis_client = aioredis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True
                )
                # Test connection
                await self.redis_client.ping()
            except Exception as e:
                print(f"⚠️ EventPublisher: Redis connection failed: {e}")
                self.redis_client = None
    
    async def _publish(self, tenant_id: str, event_type: str, data: Dict[str, Any]):
        """
        Publish event to tenant-specific Redis channel asynchronously
        
        Args:
            tenant_id: Tenant ID for channel isolation
            event_type: Event type (e.g., 'customer.updated')
            data: Event payload
        """
        if not self.redis_client:
            await self._connect()
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
            
            await self.redis_client.publish(channel, json.dumps(event))
            print(f"📡 Published event: {event_type} to {channel}")
        except Exception as e:
            print(f"❌ EventPublisher: Failed to publish event: {e}")
    
    def _publish_sync(self, tenant_id: str, event_type: str, data: Dict[str, Any]):
        """
        Synchronous wrapper for publishing events (for use in Celery tasks)
        Uses asyncio.run_in_executor to prevent blocking the Celery worker
        """
        try:
            # For Celery tasks, we need to run async code in a new event loop
            # Use asyncio.run() which creates a new event loop
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is running (shouldn't happen in Celery), use executor
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, self._publish(tenant_id, event_type, data))
                        future.result(timeout=5)  # 5 second timeout
                else:
                    # No loop running, create one
                    asyncio.run(self._publish(tenant_id, event_type, data))
            except RuntimeError:
                # No event loop exists, create one
                asyncio.run(self._publish(tenant_id, event_type, data))
        except Exception as e:
            print(f"❌ EventPublisher: Failed to publish event (sync wrapper): {e}")
    
    # Customer Events
    async def publish_customer_created(self, tenant_id: str, customer_id: str, customer_data: Dict[str, Any]):
        """Publish customer.created event"""
        await self._publish(tenant_id, "customer.created", {
            "customer_id": customer_id,
            "customer": customer_data
        })
    
    async def publish_customer_updated(self, tenant_id: str, customer_id: str, customer_data: Dict[str, Any]):
        """Publish customer.updated event"""
        await self._publish(tenant_id, "customer.updated", {
            "customer_id": customer_id,
            "customer": customer_data
        })
    
    async def publish_customer_deleted(self, tenant_id: str, customer_id: str):
        """Publish customer.deleted event"""
        await self._publish(tenant_id, "customer.deleted", {
            "customer_id": customer_id
        })
    
    # AI Analysis Events
    async def publish_ai_analysis_started(self, tenant_id: str, customer_id: str, task_id: str, customer_name: str):
        """Publish ai_analysis.started event"""
        await self._publish(tenant_id, "ai_analysis.started", {
            "customer_id": customer_id,
            "task_id": task_id,
            "customer_name": customer_name
        })
    
    async def publish_ai_analysis_progress(self, tenant_id: str, customer_id: str, task_id: str, progress: Dict[str, Any]):
        """Publish ai_analysis.progress event"""
        await self._publish(tenant_id, "ai_analysis.progress", {
            "customer_id": customer_id,
            "task_id": task_id,
            "progress": progress
        })
    
    async def publish_ai_analysis_completed(self, tenant_id: str, customer_id: str, task_id: str, customer_name: str, result: Dict[str, Any]):
        """Publish ai_analysis.completed event"""
        await self._publish(tenant_id, "ai_analysis.completed", {
            "customer_id": customer_id,
            "task_id": task_id,
            "customer_name": customer_name,
            "result": result
        })
    
    async def publish_ai_analysis_failed(self, tenant_id: str, customer_id: str, task_id: str, customer_name: str, error: str):
        """Publish ai_analysis.failed event"""
        await self._publish(tenant_id, "ai_analysis.failed", {
            "customer_id": customer_id,
            "task_id": task_id,
            "customer_name": customer_name,
            "error": error
        })
    
    # Campaign Events
    async def publish_campaign_started(self, tenant_id: str, campaign_id: str, campaign_name: str, task_id: str):
        """Publish campaign.started event"""
        await self._publish(tenant_id, "campaign.started", {
            "campaign_id": campaign_id,
            "campaign_name": campaign_name,
            "task_id": task_id
        })
    
    async def publish_campaign_progress(self, tenant_id: str, campaign_id: str, progress: Dict[str, Any]):
        """Publish campaign.progress event"""
        await self._publish(tenant_id, "campaign.progress", {
            "campaign_id": campaign_id,
            "progress": progress
        })
    
    async def publish_campaign_completed(self, tenant_id: str, campaign_id: str, campaign_name: str, result: Dict[str, Any]):
        """Publish campaign.completed event"""
        await self._publish(tenant_id, "campaign.completed", {
            "campaign_id": campaign_id,
            "campaign_name": campaign_name,
            "result": result
        })
    
    async def publish_campaign_failed(self, tenant_id: str, campaign_id: str, campaign_name: str, error: str):
        """Publish campaign.failed event"""
        await self._publish(tenant_id, "campaign.failed", {
            "campaign_id": campaign_id,
            "campaign_name": campaign_name,
            "error": error
        })
    
    # Activity Events
    async def publish_activity_suggestions_updated(self, tenant_id: str, customer_id: str):
        """Publish activity.suggestions_updated event"""
        await self._publish(tenant_id, "activity.suggestions_updated", {
            "customer_id": customer_id
        })
    
    async def publish_activity_created(self, tenant_id: str, activity_id: str, activity_data: Dict[str, Any]):
        """Publish activity.created event"""
        await self._publish(tenant_id, "activity.created", {
            "activity_id": activity_id,
            "activity": activity_data
        })
    
    async def publish_activity_updated(self, tenant_id: str, activity_id: str, activity_data: Dict[str, Any]):
        """Publish activity.updated event"""
        await self._publish(tenant_id, "activity.updated", {
            "activity_id": activity_id,
            "activity": activity_data
        })
    
    # Quote Events
    async def publish_quote_created(self, tenant_id: str, quote_id: str, quote_data: Dict[str, Any]):
        """Publish quote.created event"""
        await self._publish(tenant_id, "quote.created", {
            "quote_id": quote_id,
            "quote": quote_data
        })
    
    async def publish_quote_updated(self, tenant_id: str, quote_id: str, quote_data: Dict[str, Any]):
        """Publish quote.updated event"""
        await self._publish(tenant_id, "quote.updated", {
            "quote_id": quote_id,
            "quote": quote_data
        })
    
    async def publish_quote_status_changed(self, tenant_id: str, quote_id: str, old_status: str, new_status: str):
        """Publish quote.status_changed event"""
        await self._publish(tenant_id, "quote.status_changed", {
            "quote_id": quote_id,
            "old_status": old_status,
            "new_status": new_status
        })
    
    # Synchronous wrappers for Celery tasks (which run in sync context)
    def publish_customer_created_sync(self, tenant_id: str, customer_id: str, customer_data: Dict[str, Any]):
        """Synchronous wrapper for Celery tasks"""
        self._publish_sync(tenant_id, "customer.created", {
            "customer_id": customer_id,
            "customer": customer_data
        })
    
    def publish_ai_analysis_started_sync(self, tenant_id: str, customer_id: str, task_id: str, customer_name: str):
        """Synchronous wrapper for Celery tasks"""
        self._publish_sync(tenant_id, "ai_analysis.started", {
            "customer_id": customer_id,
            "task_id": task_id,
            "customer_name": customer_name
        })
    
    def publish_ai_analysis_completed_sync(self, tenant_id: str, customer_id: str, task_id: str, customer_name: str, result: Dict[str, Any]):
        """Synchronous wrapper for Celery tasks"""
        self._publish_sync(tenant_id, "ai_analysis.completed", {
            "customer_id": customer_id,
            "task_id": task_id,
            "customer_name": customer_name,
            "result": result
        })
    
    def publish_ai_analysis_failed_sync(self, tenant_id: str, customer_id: str, task_id: str, customer_name: str, error: str):
        """Synchronous wrapper for Celery tasks"""
        self._publish_sync(tenant_id, "ai_analysis.failed", {
            "customer_id": customer_id,
            "task_id": task_id,
            "customer_name": customer_name,
            "error": error
        })
    
    def publish_campaign_started_sync(self, tenant_id: str, campaign_id: str, campaign_name: str, task_id: str):
        """Synchronous wrapper for Celery tasks"""
        self._publish_sync(tenant_id, "campaign.started", {
            "campaign_id": campaign_id,
            "campaign_name": campaign_name,
            "task_id": task_id
        })
    
    def publish_campaign_completed_sync(self, tenant_id: str, campaign_id: str, campaign_name: str, result: Dict[str, Any]):
        """Synchronous wrapper for Celery tasks"""
        self._publish_sync(tenant_id, "campaign.completed", {
            "campaign_id": campaign_id,
            "campaign_name": campaign_name,
            "result": result
        })
    
    def publish_campaign_failed_sync(self, tenant_id: str, campaign_id: str, campaign_name: str, error: str):
        """Synchronous wrapper for Celery tasks"""
        self._publish_sync(tenant_id, "campaign.failed", {
            "campaign_id": campaign_id,
            "campaign_name": campaign_name,
            "error": error
        })
    
    def publish_activity_suggestions_updated_sync(self, tenant_id: str, customer_id: str):
        """Synchronous wrapper for Celery tasks"""
        self._publish_sync(tenant_id, "activity.suggestions_updated", {
            "customer_id": customer_id
        })
    
    def publish_quote_updated_sync(self, tenant_id: str, quote_id: str, quote_data: Dict[str, Any]):
        """Synchronous wrapper for Celery tasks"""
        self._publish_sync(tenant_id, "quote.updated", {
            "quote_id": quote_id,
            "quote": quote_data
        })


# Global event publisher instance
_event_publisher: Optional[EventPublisher] = None


def get_event_publisher() -> EventPublisher:
    """Get global event publisher instance"""
    global _event_publisher
    if _event_publisher is None:
        _event_publisher = EventPublisher()
    return _event_publisher

