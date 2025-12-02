#!/usr/bin/env python3
"""
Celery tasks for ticket description AI cleanup
Handles AI cleanup of customer-facing ticket descriptions
"""

import logging
from typing import Dict, Any
from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.helpdesk import Ticket
from app.services.ai_orchestration_service import AIOrchestrationService
from app.models.ai_prompt import PromptCategory

logger = logging.getLogger(__name__)


@celery_app.task(
    name="ticket.cleanup_description",
    bind=True,
    max_retries=3,
    default_retry_delay=60  # 1 minute
)
def cleanup_ticket_description_task(self, ticket_id: str, tenant_id: str, original_description: str):
    """
    Celery task to clean up ticket description using AI for customer-facing content
    
    Args:
        self: Celery task instance (bind=True)
        ticket_id: Ticket UUID
        tenant_id: Tenant UUID
        original_description: Original description as typed by agent
    
    Returns:
        dict: Task result with cleaned description
    """
    logger.info(f"Starting ticket description cleanup for ticket {ticket_id}")
    
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
        
        # Update status to processing
        ticket.description_ai_cleanup_status = "processing"
        ticket.description_ai_cleanup_task_id = self.request.id
        db.commit()
        
        # Use AI to clean up the description
        ai_service = AIOrchestrationService(db, tenant_id)
        
        prompt = f"""
        Clean up and professionalize the following helpdesk ticket description.
        Make it customer-friendly, clear, and professional while maintaining the original meaning and technical accuracy.
        
        Original description:
        {original_description}
        
        Requirements:
        - Use professional language
        - Be clear and concise
        - Maintain technical accuracy
        - Remove any internal jargon or abbreviations
        - Fix spelling and grammar errors
        - Make it suitable for customer-facing communication
        - Keep the same meaning and intent
        - Preserve technical details but explain them clearly
        
        Return only the cleaned description, no explanations.
        """
        
        # Generate cleaned description (AI service is async, need to run in event loop)
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        response = loop.run_until_complete(
            ai_service.generate_response(
                prompt_text=prompt,
                category=PromptCategory.CUSTOMER_SERVICE.value,
                max_tokens=1000
            )
        )
        
        cleaned_description = response.strip()
        
        # Update ticket with cleaned description
        ticket.cleaned_description = cleaned_description
        ticket.original_description = original_description  # Store original if not already set
        ticket.description_ai_cleanup_status = "completed"
        # Update main description field to cleaned version for customer portal
        ticket.description = cleaned_description
        db.commit()
        
        logger.info(f"Successfully cleaned ticket description for ticket {ticket_id}")
        
        return {
            "success": True,
            "cleaned_description": cleaned_description,
            "original_description": original_description
        }
        
    except Exception as e:
        logger.error(f"Error cleaning ticket description for ticket {ticket_id}: {e}", exc_info=True)
        
        # Update status to failed
        try:
            ticket = db.query(Ticket).filter(
                Ticket.id == ticket_id,
                Ticket.tenant_id == tenant_id
            ).first()
            if ticket:
                ticket.description_ai_cleanup_status = "failed"
                db.commit()
        except:
            pass
        
        # Retry if not exceeded max retries
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)
        
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        db.close()

