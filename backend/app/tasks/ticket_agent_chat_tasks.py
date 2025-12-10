#!/usr/bin/env python3
"""
Celery tasks for Ticket Agent Chat
Handles AI chat responses in the background
"""

import logging
import uuid
from typing import Dict, Any, List, Optional
from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.helpdesk import Ticket, TicketAgentChat
from app.services.ticket_agent_assistant_service import TicketAgentAssistantService
import asyncio

logger = logging.getLogger(__name__)


@celery_app.task(
    name="ticket.agent_chat",
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def agent_chat_task(
    self,
    ticket_id: str,
    tenant_id: str,
    user_id: str,
    user_message_id: str,
    messages: List[Dict[str, str]],
    attachments: Optional[List[Dict[str, Any]]] = None,
    log_files: Optional[List[str]] = None
):
    """
    Celery task to generate AI chat response in the background
    
    Args:
        self: Celery task instance (bind=True)
        ticket_id: Ticket UUID
        tenant_id: Tenant UUID
        user_id: User UUID (agent)
        user_message_id: ID of the user message that triggered this
        messages: Full conversation history
        attachments: Optional attachments
        log_files: Optional log files
    
    Returns:
        dict: Task result with AI response
    """
    logger.info(f"Starting AI chat response for ticket {ticket_id}, message {user_message_id}")
    
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
        
        # Update user message status
        user_message = db.query(TicketAgentChat).filter(
            TicketAgentChat.id == user_message_id
        ).first()
        
        if user_message:
            user_message.ai_status = "processing"
            user_message.ai_task_id = self.request.id
            db.commit()
        
        # Run AI chat
        service = TicketAgentAssistantService(db, tenant_id)
        
        # Run async method in sync context using async bridge
        from app.core.async_bridge import run_async_safe
        result = run_async_safe(service.chat(
            ticket_id,
            messages,
            attachments=attachments,
            log_files=log_files
        ))
        
        # Save AI response to database
        ai_message = TicketAgentChat(
            id=str(uuid.uuid4()),
            ticket_id=ticket_id,
            tenant_id=tenant_id,
            user_id=user_id,
            role="assistant",
            content=result.get("message", ""),
            ai_task_id=self.request.id,
            ai_status="completed",
            ai_model=result.get("model"),
            ai_usage=result.get("usage"),
            attachments=attachments,
            log_files=log_files
        )
        db.add(ai_message)
        
        # Update user message status
        if user_message:
            user_message.ai_status = "completed"
        
        db.commit()
        
        logger.info(f"Successfully completed AI chat response for ticket {ticket_id}")
        
        return {
            "success": True,
            "message_id": ai_message.id,
            "message": result.get("message", ""),
            "model": result.get("model"),
            "usage": result.get("usage")
        }
        
    except Exception as e:
        logger.error(f"Error in agent chat task for ticket {ticket_id}: {e}", exc_info=True)
        
        # Update user message status to failed
        if user_message:
            user_message.ai_status = "failed"
            db.commit()
        
        # Retry if not exceeded max retries
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)
        
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        db.close()

