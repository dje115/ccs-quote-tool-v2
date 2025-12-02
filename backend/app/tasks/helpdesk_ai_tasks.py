#!/usr/bin/env python3
"""
Celery tasks for helpdesk AI operations
All helpdesk AI operations should run as Celery background tasks for multi-tenant, multi-user support
"""

from celery import Task
from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.helpdesk import Ticket
from app.services.knowledge_base_service import KnowledgeBaseService
from app.services.ai_orchestration_service import AIOrchestrationService
import logging
import asyncio

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def suggest_kb_articles_task(
    self: Task,
    ticket_id: str,
    tenant_id: str,
    limit: int = 5
):
    """
    Get AI-powered knowledge base article suggestions for a ticket
    
    Args:
        ticket_id: Ticket ID
        tenant_id: Tenant ID
        limit: Maximum number of suggestions
    
    Returns:
        List of suggested articles with relevance scores
    """
    db = SessionLocal()
    try:
        ticket = db.query(Ticket).filter(
            Ticket.id == ticket_id,
            Ticket.tenant_id == tenant_id
        ).first()
        
        if not ticket:
            logger.error(f"Ticket {ticket_id} not found")
            return {"suggestions": []}
        
        kb_service = KnowledgeBaseService(db, tenant_id)
        
        # Run async method in event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        suggestions = loop.run_until_complete(
            kb_service.suggest_articles_with_ai(ticket, limit=limit)
        )
        
        # Format suggestions for response
        formatted_suggestions = []
        for s in suggestions:
            if isinstance(s, dict) and "article" in s:
                article = s["article"]
                formatted_suggestions.append({
                    "article_id": article.id,
                    "title": article.title,
                    "summary": article.summary or "",
                    "category": article.category or "",
                    "relevance_score": s.get("relevance_score", 0),
                    "reason": s.get("reason", "AI-matched")
                })
        
        return {
            "ticket_id": ticket_id,
            "suggestions": formatted_suggestions
        }
        
    except Exception as e:
        logger.error(f"Error in suggest_kb_articles_task: {e}", exc_info=True)
        db.rollback()
        
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))
        
        return {
            "ticket_id": ticket_id,
            "suggestions": [],
            "error": str(e)
        }
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def generate_kb_answer_task(
    self: Task,
    ticket_id: str,
    tenant_id: str,
    article_id: str = None
):
    """
    Generate AI-powered answer from knowledge base articles
    
    Args:
        ticket_id: Ticket ID
        tenant_id: Tenant ID
        article_id: Optional specific article ID to use
    
    Returns:
        Dict with generated answer and source articles
    """
    db = SessionLocal()
    try:
        ticket = db.query(Ticket).filter(
            Ticket.id == ticket_id,
            Ticket.tenant_id == tenant_id
        ).first()
        
        if not ticket:
            logger.error(f"Ticket {ticket_id} not found")
            return {
                "success": False,
                "error": "Ticket not found",
                "answer": None,
                "sources": []
            }
        
        kb_service = KnowledgeBaseService(db, tenant_id)
        
        # Run async method in event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            kb_service.generate_answer_from_kb(ticket, article_id=article_id)
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error in generate_kb_answer_task: {e}", exc_info=True)
        db.rollback()
        
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))
        
        return {
            "success": False,
            "error": str(e),
            "answer": None,
            "sources": []
        }
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def generate_quick_response_task(
    self: Task,
    ticket_id: str,
    tenant_id: str
):
    """
    Generate quick response template from knowledge base
    
    Args:
        ticket_id: Ticket ID
        tenant_id: Tenant ID
    
    Returns:
        Dict with response template
    """
    db = SessionLocal()
    try:
        ticket = db.query(Ticket).filter(
            Ticket.id == ticket_id,
            Ticket.tenant_id == tenant_id
        ).first()
        
        if not ticket:
            logger.error(f"Ticket {ticket_id} not found")
            return {
                "success": False,
                "error": "Ticket not found",
                "template": None,
                "article": None
            }
        
        kb_service = KnowledgeBaseService(db, tenant_id)
        
        # Run async method in event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            kb_service.generate_quick_response(ticket)
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error in generate_quick_response_task: {e}", exc_info=True)
        db.rollback()
        
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))
        
        return {
            "success": False,
            "error": str(e),
            "template": None,
            "article": None
        }
    finally:
        db.close()

