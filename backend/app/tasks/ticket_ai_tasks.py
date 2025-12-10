#!/usr/bin/env python3
"""
Celery tasks for Ticket AI Analysis
Handles AI analysis of tickets in the background
"""

import logging
from typing import Dict, Any
from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.helpdesk import Ticket
from app.services.helpdesk_service import HelpdeskService
import asyncio

logger = logging.getLogger(__name__)


@celery_app.task(
    name="ticket.analyze",
    bind=True,
    max_retries=3,
    default_retry_delay=60  # 1 minute
)
def analyze_ticket_task(self, ticket_id: str, tenant_id: str):
    """
    Celery task to analyze ticket with AI in the background
    
    Args:
        self: Celery task instance (bind=True)
        ticket_id: Ticket UUID
        tenant_id: Tenant UUID
    
    Returns:
        dict: Task result with success status
    """
    logger.info(f"Starting AI analysis for ticket {ticket_id}")
    
    db = SessionLocal()
    try:
        # Get ticket
        ticket = db.query(Ticket).filter(
            Ticket.id == ticket_id,
            Ticket.tenant_id == tenant_id
        ).first()
        
        if not ticket:
            logger.error(f"Ticket {ticket_id} not found")
            return {"success": False, "error": "Ticket not found"}
        
        # Run AI analysis
        service = HelpdeskService(db, tenant_id)
        
        # Run async method in sync context using async bridge
        from app.core.async_bridge import run_async_safe
        run_async_safe(service._analyze_ticket_with_full_history(ticket))
        
        db.commit()
        db.refresh(ticket)
        
        logger.info(f"Successfully completed AI analysis for ticket {ticket_id}")
        
        return {
            "success": True,
            "ticket_id": ticket_id,
            "ai_suggestions": ticket.ai_suggestions,
            "improved_description": ticket.improved_description,
            "ai_analysis_date": ticket.ai_analysis_date.isoformat() if ticket.ai_analysis_date else None
        }
        
    except Exception as e:
        logger.error(f"Error analyzing ticket {ticket_id}: {e}", exc_info=True)
        
        # Retry if not exceeded max retries
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)
        
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        db.close()

