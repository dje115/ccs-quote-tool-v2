#!/usr/bin/env python3
"""
Celery tasks for email ticket processing
"""

import logging
from celery import shared_task
from app.core.database import SessionLocal
from app.services.email_ticket_service import EmailTicketService

logger = logging.getLogger(__name__)


@shared_task(name="process_email_tickets")
def process_email_tickets_task(tenant_id: str, email_config: dict, user_id: str = None):
    """
    Process emails and convert to tickets (Celery task)
    
    Args:
        tenant_id: Tenant ID
        email_config: Email configuration dictionary
        user_id: User ID processing tickets (optional)
    
    Returns:
        Dict with processing results
    """
    db = SessionLocal()
    try:
        service = EmailTicketService(db, tenant_id)
        results = service.process_email_tickets(
            email_config=email_config,
            user_id=user_id,
            limit=50  # Process up to 50 emails per run
        )
        
        logger.info(f"Processed {results['processed']} emails, created {results['created']} tickets for tenant {tenant_id}")
        
        return results
    except Exception as e:
        logger.error(f"Failed to process email tickets for tenant {tenant_id}: {e}", exc_info=True)
        return {
            "processed": 0,
            "created": 0,
            "errors": [{"error": str(e)}]
        }
    finally:
        db.close()

