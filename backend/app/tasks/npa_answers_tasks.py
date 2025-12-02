#!/usr/bin/env python3
"""
Celery tasks for AI cleanup of NPA answers (answers to questions)
"""

from celery import Task
from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.helpdesk import Ticket, NPAHistory
from app.services.ai_orchestration_service import AIOrchestrationService
from app.models.ai_prompt import PromptCategory
import logging

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def cleanup_npa_answers_task(
    self: Task,
    ticket_id: str,
    tenant_id: str,
    original_text: str,
    npa_history_id: str = None  # If provided, update history entry; otherwise update ticket
):
    """
    Clean up NPA answers text using AI
    
    Args:
        ticket_id: Ticket ID
        tenant_id: Tenant ID
        original_text: Original answers text as typed by agent
        npa_history_id: Optional NPA history entry ID (if updating history)
    """
    db = SessionLocal()
    try:
        # Update status to processing
        if npa_history_id:
            npa_entry = db.query(NPAHistory).filter(
                NPAHistory.id == npa_history_id,
                NPAHistory.tenant_id == tenant_id
            ).first()
            if not npa_entry:
                logger.error(f"NPA history entry {npa_history_id} not found")
                return
            npa_entry.answers_ai_cleanup_status = "processing"
        else:
            ticket = db.query(Ticket).filter(
                Ticket.id == ticket_id,
                Ticket.tenant_id == tenant_id
            ).first()
            if not ticket:
                logger.error(f"Ticket {ticket_id} not found")
                return
            ticket.npa_answers_ai_cleanup_status = "processing"
        
        db.commit()
        
        # Use AI to clean up the text
        ai_service = AIOrchestrationService(db, tenant_id)
        
        prompt_text = f"""
        Clean up and professionalize the following answers to questions from a customer service ticket.
        Make it customer-facing, professional, and clear while preserving all the important information.
        
        Original answers:
        {original_text}
        
        Return ONLY the cleaned, professional version. Do not add explanations or notes.
        """
        
        # Generate cleaned text (AI service is async, need to run in event loop)
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        try:
            response = loop.run_until_complete(
                ai_service.generate(
                    category=PromptCategory.CUSTOMER_SERVICE.value,
                    variables={
                        "original_text": original_text,
                        "context": "NPA answers cleanup - make it professional and customer-facing"
                    },
                    temperature=0.3,
                    max_tokens=1000
                )
            )
            
            # Handle response - it could be AIProviderResponse or dict
            cleaned_text = None
            if response:
                if hasattr(response, 'content'):
                    cleaned_text = response.content.strip()
                elif isinstance(response, dict):
                    cleaned_text = response.get("content", "").strip()
            
            if not cleaned_text:
                logger.warning(f"AI returned empty response for ticket {ticket_id}, using original text")
                cleaned_text = original_text  # Fallback to original if AI fails
        except Exception as ai_error:
            logger.error(f"AI generation error in cleanup_npa_answers_task: {ai_error}", exc_info=True)
            cleaned_text = original_text  # Fallback to original on AI error
        
        # Update with cleaned text
        if npa_history_id:
            npa_entry.answers_cleaned_text = cleaned_text
            npa_entry.answers_ai_cleanup_status = "completed"
        else:
            ticket.npa_answers_cleaned_text = cleaned_text
            ticket.npa_answers_ai_cleanup_status = "completed"
        
        db.commit()
        logger.info(f"Successfully cleaned NPA answers for ticket {ticket_id}")
        
    except Exception as e:
        logger.error(f"Error cleaning NPA answers: {e}", exc_info=True)
        db.rollback()
        
        # Update status to failed
        try:
            if npa_history_id:
                npa_entry = db.query(NPAHistory).filter(NPAHistory.id == npa_history_id).first()
                if npa_entry:
                    npa_entry.answers_ai_cleanup_status = "failed"
            else:
                ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
                if ticket:
                    ticket.npa_answers_ai_cleanup_status = "failed"
            db.commit()
        except:
            pass
        
        # Retry if not exceeded max retries
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))
    finally:
        db.close()

