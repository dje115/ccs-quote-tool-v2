#!/usr/bin/env python3
"""
Celery tasks for Next Point of Action (NPA) processing
Handles AI cleanup of customer-facing NPA text
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
    name="npa.cleanup_text",
    bind=True,
    max_retries=3,
    default_retry_delay=60  # 1 minute
)
def cleanup_npa_text_task(self, ticket_id: str, tenant_id: str, original_text: str):
    """
    Celery task to clean up NPA text using AI for customer-facing content
    
    Args:
        self: Celery task instance (bind=True)
        ticket_id: Ticket UUID
        tenant_id: Tenant UUID
        original_text: Original NPA text as typed by agent
    
    Returns:
        dict: Task result with cleaned text
    """
    logger.info(f"Starting NPA text cleanup for ticket {ticket_id}")
    
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
        ticket.npa_ai_cleanup_status = "processing"
        ticket.npa_ai_cleanup_task_id = self.request.id
        db.commit()
        
        # Use AI to clean up the text
        ai_service = AIOrchestrationService(db, tenant_id)
        
        prompt = f"""
        Clean up and professionalize the following helpdesk ticket next point of action text.
        Make it customer-friendly, clear, and professional while maintaining the original meaning.
        
        Original text:
        {original_text}
        
        Requirements:
        - Use professional language
        - Be clear and concise
        - Maintain technical accuracy
        - Remove any internal jargon or abbreviations
        - Make it suitable for customer-facing communication
        - Keep the same meaning and intent
        
        Return only the cleaned text, no explanations.
        """
        
        # Generate cleaned text (AI service is async, need to run in event loop)
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
                max_tokens=500
            )
        )
        
        cleaned_text = response.strip()
        
        # Update ticket with cleaned text
        ticket.npa_cleaned_text = cleaned_text
        ticket.npa_original_text = original_text  # Store original
        ticket.npa_ai_cleanup_status = "completed"
        db.commit()
        
        logger.info(f"Successfully cleaned NPA text for ticket {ticket_id}")
        
        return {
            "success": True,
            "cleaned_text": cleaned_text,
            "original_text": original_text
        }
        
    except Exception as e:
        logger.error(f"Error cleaning NPA text for ticket {ticket_id}: {e}", exc_info=True)
        
        # Update status to failed
        try:
            ticket = db.query(Ticket).filter(
                Ticket.id == ticket_id,
                Ticket.tenant_id == tenant_id
            ).first()
            if ticket:
                ticket.npa_ai_cleanup_status = "failed"
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

