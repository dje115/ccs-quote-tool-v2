#!/usr/bin/env python3
"""
Celery tasks for customer lifecycle automation

Runs periodic checks for:
- Dormant customers (no contact > 90 days)
- Closed Lost customers (dormant > 180 days)
"""

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.tenant import Tenant
from app.services.customer_lifecycle_service import CustomerLifecycleService
from sqlalchemy import select
import logging

logger = logging.getLogger(__name__)


@celery_app.task(name="check_dormant_customers")
def check_dormant_customers_task():
    """
    Daily task to check for customers that should transition to Dormant or Closed Lost.
    
    This task runs once per day and processes all tenants.
    """
    db = SessionLocal()
    try:
        # Get all active tenants
        stmt = select(Tenant).where(Tenant.status == "active")
        tenants = db.execute(stmt).scalars().all()
        
        total_updated = 0
        for tenant in tenants:
            try:
                # Use async session for lifecycle service
                from app.core.database import get_async_db
                import asyncio
                
                async def process_tenant():
                    async_db = await get_async_db().__anext__()
                    try:
                        updated = await CustomerLifecycleService.check_dormant_customers_batch(
                            async_db, tenant.id, batch_size=100
                        )
                        return updated
                    finally:
                        await async_db.close()
                
                # Run async function in sync context
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    updated = loop.run_until_complete(process_tenant())
                    total_updated += updated
                    logger.info(f"Updated {updated} customers for tenant {tenant.id}")
                finally:
                    loop.close()
                    
            except Exception as e:
                logger.error(f"Error processing tenant {tenant.id}: {e}", exc_info=True)
                continue
        
        logger.info(f"Lifecycle automation completed: {total_updated} customers updated across all tenants")
        return {"updated_count": total_updated}
        
    except Exception as e:
        logger.error(f"Error in check_dormant_customers_task: {e}", exc_info=True)
        raise
    finally:
        db.close()


@celery_app.task(name="check_lifecycle_transitions")
def check_lifecycle_transitions_task(customer_id: str, tenant_id: str):
    """
    Task to check lifecycle transitions for a specific customer.
    
    This is called after:
    - Opportunity stage changes
    - Activity creation
    - Quote status changes
    
    Args:
        customer_id: ID of the customer to check
        tenant_id: ID of the tenant
    """
    try:
        from app.core.database import get_async_db
        import asyncio
        
        async def process_transition():
            async_db = await get_async_db().__anext__()
            try:
                new_status = await CustomerLifecycleService.check_lifecycle_transitions(
                    customer_id, async_db, tenant_id
                )
                if new_status:
                    await CustomerLifecycleService.update_customer_status(
                        customer_id, new_status, async_db, tenant_id
                    )
                    logger.info(f"Customer {customer_id} status updated to {new_status.value}")
                    return {"updated": True, "new_status": new_status.value}
                return {"updated": False}
            finally:
                await async_db.close()
        
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(process_transition())
            return result
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error in check_lifecycle_transitions_task for customer {customer_id}: {e}", exc_info=True)
        raise



