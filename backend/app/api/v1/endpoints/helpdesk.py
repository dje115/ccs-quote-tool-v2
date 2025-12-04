#!/usr/bin/env python3
"""
Helpdesk API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Body
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from app.services.sla_tracking_service import SLATrackingService
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, timezone, date

from app.core.dependencies import get_current_user, get_current_tenant, check_permission
from app.core.database import get_async_db, SessionLocal
from app.models.tenant import User, Tenant
from app.models.helpdesk import Ticket, TicketStatus, TicketPriority, TicketType
from app.services.helpdesk_service import HelpdeskService
from app.services.storage_service import StorageService

router = APIRouter(prefix="/helpdesk", tags=["Helpdesk"])


class TicketCreate(BaseModel):
    subject: str
    description: str
    customer_id: Optional[str] = None
    contact_id: Optional[str] = None
    ticket_type: TicketType = TicketType.SUPPORT
    priority: TicketPriority = TicketPriority.MEDIUM
    related_quote_id: Optional[str] = None
    related_contract_id: Optional[str] = None
    tags: Optional[List[str]] = None


class TicketCommentCreate(BaseModel):
    comment: str
    is_internal: bool = False
    status_change: Optional[str] = None


class CustomerTicketCreate(BaseModel):
    subject: str
    description: str
    contact_name: str
    contact_email: EmailStr
    ticket_type: TicketType = TicketType.SUPPORT
    priority: TicketPriority = TicketPriority.MEDIUM


class KnowledgeBaseArticleCreate(BaseModel):
    title: str
    content: str
    summary: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    is_published: bool = False
    is_featured: bool = False


@router.post("/tickets", status_code=status.HTTP_201_CREATED)
async def create_ticket(
    ticket_data: TicketCreate,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Create a new support ticket
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        # HelpdeskService currently expects sync session - use sync wrapper
        # TODO: Refactor HelpdeskService to support async sessions
        from app.core.database import SessionLocal
        sync_db = SessionLocal()
        try:
            service = HelpdeskService(sync_db, current_user.tenant_id)
            ticket = await service.create_ticket(
                subject=ticket_data.subject,
                description=ticket_data.description,
                customer_id=ticket_data.customer_id,
                contact_id=ticket_data.contact_id,
                ticket_type=ticket_data.ticket_type,
                priority=ticket_data.priority,
                created_by_user_id=current_user.id,
                related_quote_id=ticket_data.related_quote_id,
                related_contract_id=ticket_data.related_contract_id,
                tags=ticket_data.tags
            )
        finally:
            sync_db.close()
        
        # Auto-apply SLA to the ticket
        try:
            from app.services.sla_tracking_service import SLATrackingService
            tracking_service = SLATrackingService(db, current_tenant.id)
            
            # Get the ticket from async db
            from app.models.helpdesk import Ticket
            ticket_id = ticket.get('id') or ticket.id if hasattr(ticket, 'id') else None
            if ticket_id:
                ticket_stmt = select(Ticket).where(Ticket.id == ticket_id)
                ticket_result = await db.execute(ticket_stmt)
                ticket_obj = ticket_result.scalar_one_or_none()
                
                if ticket_obj:
                    # Get contract if linked
                    contract = None
                    if ticket_obj.related_contract_id:
                        from app.models.support_contract import SupportContract
                        contract_stmt = select(SupportContract).where(
                            SupportContract.id == ticket_obj.related_contract_id
                        )
                        contract_result = await db.execute(contract_stmt)
                        contract = contract_result.scalar_one_or_none()
                    
                    # Apply SLA
                    await tracking_service.apply_sla_to_ticket(ticket_obj)
                    
                    # Check initial compliance
                    await tracking_service.check_ticket_sla_compliance(ticket_obj)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to apply SLA to ticket: {e}")
        
        return ticket
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error creating ticket: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating ticket: {str(e)}"
        )


@router.post("/tickets/customer", status_code=status.HTTP_201_CREATED)
async def create_customer_ticket(
    ticket_data: CustomerTicketCreate,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Create a ticket from customer portal (no auth required)
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        # Get tenant from customer email domain or default tenant
        # For now, use default tenant
        from app.models.tenant import Tenant
        from app.models.crm import Customer
        from sqlalchemy import select
        
        tenant_stmt = select(Tenant).where(Tenant.code == "ccs")
        tenant_result = await db.execute(tenant_stmt)
        tenant = tenant_result.scalar_one_or_none()
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        # Find or create customer by email (use async query)
        customer_stmt = select(Customer).where(
            and_(
                Customer.tenant_id == tenant.id,
                Customer.main_email == ticket_data.contact_email
            )
        )
        customer_result = await db.execute(customer_stmt)
        customer = customer_result.scalars().first()
        
        customer_id = customer.id if customer else None
        
        # HelpdeskService currently expects sync session - use sync wrapper
        from app.core.database import SessionLocal
        sync_db = SessionLocal()
        try:
            service = HelpdeskService(sync_db, tenant.id)
            
            ticket = await service.create_ticket(
                subject=ticket_data.subject,
                description=ticket_data.description,
                customer_id=customer_id,
                ticket_type=ticket_data.ticket_type,
                priority=ticket_data.priority,
                tags=None
            )
            
            # Add initial comment from customer
            await service.add_comment(
                ticket_id=ticket.id,
                comment=ticket_data.description,
                author_id=None,
                author_name=ticket_data.contact_name,
                author_email=ticket_data.contact_email,
                is_internal=False
            )
        finally:
            sync_db.close()
        
        return ticket
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error creating customer ticket: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating customer ticket: {str(e)}"
        )


@router.get("/tickets")
async def list_tickets(
    ticket_status: Optional[TicketStatus] = Query(None, alias="status"),
    priority: Optional[TicketPriority] = Query(None),
    assigned_to_id: Optional[str] = Query(None),
    customer_id: Optional[str] = Query(None),
    ticket_type: Optional[TicketType] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    List tickets with filters
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        # HelpdeskService currently expects sync session - use sync wrapper
        from app.core.database import SessionLocal
        sync_db = SessionLocal()
        try:
            service = HelpdeskService(sync_db, current_user.tenant_id)
            tickets = service.get_tickets(
                status=ticket_status,
                priority=priority,
                assigned_to_id=assigned_to_id or (current_user.id if assigned_to_id == "me" else None),
                customer_id=customer_id,
                ticket_type=ticket_type,
                limit=limit,
                offset=offset
            )
        finally:
            sync_db.close()
        return {"tickets": tickets, "count": len(tickets)}
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error listing tickets: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing tickets: {str(e)}"
        )


@router.get("/tickets/stats")
async def get_ticket_stats(
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get ticket statistics
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        # HelpdeskService currently expects sync session - use sync wrapper
        from app.core.database import SessionLocal
        sync_db = SessionLocal()
        try:
            service = HelpdeskService(sync_db, current_user.tenant_id)
            stats = service.get_ticket_stats()
        finally:
            sync_db.close()
        return stats
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting stats: {str(e)}"
        )


@router.get("/tickets/{ticket_id}")
async def get_ticket(
    ticket_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get ticket details with comments and history
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        from app.models.helpdesk import Ticket, TicketComment, TicketHistory
        from sqlalchemy.orm import joinedload
        from sqlalchemy import select
        
        # Use async session with select
        # Note: When using joinedload with collections, we need unique() to avoid duplicate rows
        stmt = select(Ticket).options(
            joinedload(Ticket.comments),
            joinedload(Ticket.history),
            joinedload(Ticket.assigned_to)
        ).where(
            Ticket.id == ticket_id,
            Ticket.tenant_id == current_user.tenant_id
        )
        result = await db.execute(stmt)
        ticket = result.unique().scalar_one_or_none()
        
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        # Get assigned user name if available
        assigned_to_name = None
        if ticket.assigned_to_id and ticket.assigned_to:
            assigned_to_name = ticket.assigned_to.name if hasattr(ticket.assigned_to, 'name') else ticket.assigned_to.email if hasattr(ticket.assigned_to, 'email') else None
        
        # Get customer name if available
        customer_name = None
        if ticket.customer_id:
            from app.models.crm import Customer
            customer_stmt = select(Customer).where(Customer.id == ticket.customer_id)
            customer_result = await db.execute(customer_stmt)
            customer = customer_result.scalar_one_or_none()
            if customer:
                customer_name = customer.company_name
        
        # Parse AI suggestions if it's a string (JSON)
        ai_suggestions = ticket.ai_suggestions
        if isinstance(ai_suggestions, str):
            try:
                import json
                ai_suggestions = json.loads(ai_suggestions)
            except:
                ai_suggestions = None
        
        # Convert to dict and include relationships
        ticket_dict = {
            "id": ticket.id,
            "ticket_number": ticket.ticket_number,
            "subject": ticket.subject,
            "description": ticket.description,
            "original_description": ticket.original_description,
            "improved_description": ticket.improved_description,
            "cleaned_description": getattr(ticket, 'cleaned_description', None),
            "description_ai_cleanup_status": getattr(ticket, 'description_ai_cleanup_status', None),
            "description_ai_cleanup_task_id": getattr(ticket, 'description_ai_cleanup_task_id', None),
            "ai_suggestions": ai_suggestions,
            "ai_analysis_date": ticket.ai_analysis_date.isoformat() if ticket.ai_analysis_date else None,
            "status": ticket.status.value if ticket.status else None,
            "priority": ticket.priority.value if ticket.priority else None,
            "ticket_type": ticket.ticket_type.value if ticket.ticket_type else None,
            "customer_id": ticket.customer_id,
            "customer_name": customer_name,
            "contact_id": ticket.contact_id,
            "assigned_to_id": ticket.assigned_to_id,
            "assigned_to_name": assigned_to_name,
            "created_by_user_id": ticket.created_by_user_id,
            "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
            "updated_at": ticket.updated_at.isoformat() if ticket.updated_at else None,
            "resolved_at": ticket.resolved_at.isoformat() if ticket.resolved_at else None,
            "closed_at": ticket.closed_at.isoformat() if ticket.closed_at else None,
            "first_response_at": ticket.first_response_at.isoformat() if ticket.first_response_at else None,
            "comments": [
                {
                    "id": comment.id,
                    "comment": comment.comment,
                    "author_id": comment.author_id,
                    "author_name": comment.author_name,
                    "author_email": comment.author_email,
                    "is_internal": comment.is_internal,
                    "created_at": comment.created_at.isoformat() if comment.created_at else None
                }
                for comment in ticket.comments
            ] if ticket.comments else [],
            "history": [
                {
                    "id": hist.id,
                    "field_name": hist.field_name,
                    "old_value": hist.old_value,
                    "new_value": hist.new_value,
                    "created_at": hist.created_at.isoformat() if hist.created_at else None
                }
                for hist in ticket.history
            ] if ticket.history else []
        }
        
        return ticket_dict
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting ticket: {str(e)}"
        )


@router.put("/tickets/{ticket_id}")
async def update_ticket(
    ticket_id: str,
    ticket_update: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Update a ticket (description, status, priority, etc.)
    Automatically triggers AI cleanup for description if original_description is updated.
    """
    from app.core.database import SessionLocal
    from app.models.helpdesk import Ticket
    
    sync_db = SessionLocal()
    try:
        ticket = sync_db.query(Ticket).filter(
            Ticket.id == ticket_id,
            Ticket.tenant_id == current_tenant.id
        ).first()
        
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        # Update fields
        if "original_description" in ticket_update:
            ticket.original_description = ticket_update["original_description"]
            # If description is also provided, update it
            if "description" not in ticket_update:
                ticket.description = ticket_update["original_description"]
        
        if "cleaned_description" in ticket_update:
            ticket.cleaned_description = ticket_update["cleaned_description"]
            # Update main description to cleaned version
            ticket.description = ticket_update["cleaned_description"]
        
        if "description" in ticket_update:
            ticket.description = ticket_update["description"]
            # If original_description not set, use description as original
            if not ticket.original_description:
                ticket.original_description = ticket_update["description"]
        
        # Trigger AI cleanup if requested
        if ticket_update.get("trigger_description_cleanup", False) and ticket.original_description:
            try:
                from app.tasks.ticket_description_tasks import cleanup_ticket_description_task
                ticket.description_ai_cleanup_status = "pending"
                task = cleanup_ticket_description_task.delay(
                    ticket_id=ticket.id,
                    tenant_id=current_tenant.id,
                    original_description=ticket.original_description
                )
                ticket.description_ai_cleanup_task_id = task.id
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to queue description cleanup: {e}")
        
        # Update other fields
        if "subject" in ticket_update:
            ticket.subject = ticket_update["subject"]
        if "status" in ticket_update:
            from app.models.helpdesk import TicketStatus
            ticket.status = TicketStatus[ticket_update["status"].upper()]
        if "priority" in ticket_update:
            from app.models.helpdesk import TicketPriority
            ticket.priority = TicketPriority[ticket_update["priority"].upper()]
        if "ticket_type" in ticket_update:
            from app.models.helpdesk import TicketType
            ticket.ticket_type = TicketType[ticket_update["ticket_type"].upper()]
        
        sync_db.commit()
        sync_db.refresh(ticket)
        
        return {
            "id": ticket.id,
            "ticket_number": ticket.ticket_number,
            "subject": ticket.subject,
            "description": ticket.description,
            "original_description": ticket.original_description,
            "cleaned_description": ticket.cleaned_description,
            "description_ai_cleanup_status": ticket.description_ai_cleanup_status,
            "status": ticket.status.value if ticket.status else None,
            "priority": ticket.priority.value if ticket.priority else None
        }
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error updating ticket: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating ticket: {str(e)}"
        )
    finally:
        sync_db.close()


@router.post("/tickets/{ticket_id}/comments")
async def add_comment(
    ticket_id: str,
    comment_data: TicketCommentCreate,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Add a comment to a ticket and trigger AI analysis
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        # HelpdeskService currently expects sync session - use sync wrapper
        from app.core.database import SessionLocal
        sync_db = SessionLocal()
        try:
            service = HelpdeskService(sync_db, current_user.tenant_id)
            comment = await service.add_comment(
                ticket_id=ticket_id,
                comment=comment_data.comment,
                author_id=current_user.id,
                is_internal=comment_data.is_internal,
                status_change=comment_data.status_change
            )
        finally:
            sync_db.close()
        
        # Check SLA compliance after comment/status change
        try:
            from app.services.sla_tracking_service import SLATrackingService
            tracking_service = SLATrackingService(db, current_tenant.id)
            
            from app.models.helpdesk import Ticket
            ticket_stmt = select(Ticket).where(Ticket.id == ticket_id)
            ticket_result = await db.execute(ticket_stmt)
            ticket_obj = ticket_result.scalar_one_or_none()
            
            if ticket_obj:
                await tracking_service.check_ticket_sla_compliance(ticket_obj)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to check SLA compliance for ticket {ticket_id}: {e}")
        
        return comment
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error adding comment: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error adding comment: {str(e)}"
        )


@router.post("/tickets/{ticket_id}/analyze")
async def analyze_ticket(
    ticket_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Manually trigger AI analysis for a ticket (runs as background task)
    
    This endpoint queues the analysis as a Celery background task to avoid timeouts.
    The analysis will complete asynchronously and update the ticket when done.
    """
    try:
        from app.core.database import SessionLocal
        from app.models.helpdesk import Ticket
        from app.tasks.ticket_ai_tasks import analyze_ticket_task
        
        sync_db = SessionLocal()
        try:
            # Verify ticket exists
            ticket = sync_db.query(Ticket).filter(
                Ticket.id == ticket_id,
                Ticket.tenant_id == current_user.tenant_id
            ).first()
            
            if not ticket:
                raise HTTPException(status_code=404, detail="Ticket not found")
            
            # Queue Celery task for background processing
            task = analyze_ticket_task.delay(
                ticket_id=ticket_id,
                tenant_id=current_user.tenant_id
            )
            
            return {
                "success": True,
                "message": "AI analysis queued for background processing",
                "task_id": task.id,
                "status": "processing"
            }
        finally:
            sync_db.close()
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error queueing ticket analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error queueing ticket analysis: {str(e)}"
        )


@router.post("/tickets/{ticket_id}/assign")
async def assign_ticket(
    ticket_id: str,
    assigned_to_id: str,
    current_user: User = Depends(check_permission("ticket:assign")),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Assign a ticket to a user
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        # HelpdeskService currently expects sync session - use sync wrapper
        from app.core.database import SessionLocal
        sync_db = SessionLocal()
        try:
            service = HelpdeskService(sync_db, current_user.tenant_id)
            ticket = service.assign_ticket(
                ticket_id=ticket_id,
                assigned_to_id=assigned_to_id,
                assigned_by_id=current_user.id
            )
        finally:
            sync_db.close()
        return ticket
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error assigning ticket: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error assigning ticket: {str(e)}"
        )


@router.put("/tickets/{ticket_id}/priority")
async def update_priority(
    ticket_id: str,
    priority: TicketPriority,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Update ticket priority
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        # HelpdeskService currently expects sync session - use sync wrapper
        from app.core.database import SessionLocal
        sync_db = SessionLocal()
        try:
            service = HelpdeskService(sync_db, current_user.tenant_id)
            ticket = service.update_priority(
                ticket_id=ticket_id,
                priority=priority,
                changed_by_id=current_user.id
            )
        finally:
            sync_db.close()
        return ticket
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error updating priority: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating priority: {str(e)}"
        )


@router.get("/knowledge-base/search")
async def search_knowledge_base(
    q: str = Query(..., min_length=1),
    category: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Search knowledge base using AI-powered semantic search
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        # HelpdeskService currently expects sync session - use sync wrapper
        from app.core.database import SessionLocal
        sync_db = SessionLocal()
        try:
            service = HelpdeskService(sync_db, current_user.tenant_id)
            results = await service.search_knowledge_base(
                query=q,
                category=category,
                limit=limit
            )
        finally:
            sync_db.close()
        return {"results": results, "query": q}
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error searching knowledge base: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching knowledge base: {str(e)}"
        )


@router.post("/knowledge-base/articles", status_code=status.HTTP_201_CREATED)
async def create_knowledge_base_article(
    article_data: KnowledgeBaseArticleCreate,
    current_user: User = Depends(check_permission("kb:create")),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Create a knowledge base article
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        # HelpdeskService currently expects sync session - use sync wrapper
        from app.core.database import SessionLocal
        sync_db = SessionLocal()
        try:
            service = HelpdeskService(sync_db, current_user.tenant_id)
            article = service.create_knowledge_base_article(
                title=article_data.title,
                content=article_data.content,
                summary=article_data.summary,
                category=article_data.category,
                tags=article_data.tags,
                author_id=current_user.id,
                is_published=article_data.is_published,
                is_featured=article_data.is_featured
            )
        finally:
            sync_db.close()
        return article
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error creating article: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating article: {str(e)}"
        )


@router.get("/knowledge-base/articles")
async def list_knowledge_base_articles(
    category: Optional[str] = Query(None),
    published_only: bool = Query(True),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    List knowledge base articles
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        from app.models.knowledge_base import KnowledgeBaseArticle
        from sqlalchemy import select
        
        stmt = select(KnowledgeBaseArticle).where(
            KnowledgeBaseArticle.tenant_id == current_user.tenant_id
        )
        
        if published_only:
            stmt = stmt.where(KnowledgeBaseArticle.is_published == True)
        
        if category:
            stmt = stmt.where(KnowledgeBaseArticle.category == category)
        
        stmt = stmt.order_by(KnowledgeBaseArticle.created_at.desc())
        result = await db.execute(stmt)
        articles = result.scalars().all()
        return {"articles": articles}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing articles: {str(e)}"
        )


@router.get("/knowledge-base/articles/{article_id}")
async def get_knowledge_base_article(
    article_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get knowledge base article
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        from app.models.knowledge_base import KnowledgeBaseArticle
        from sqlalchemy import select
        
        stmt = select(KnowledgeBaseArticle).where(
            KnowledgeBaseArticle.id == article_id,
            KnowledgeBaseArticle.tenant_id == current_user.tenant_id
        )
        result = await db.execute(stmt)
        article = result.scalar_one_or_none()
        
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        
        # Increment view count
        article.view_count += 1
        await db.commit()
        
        return article
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting article: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting article: {str(e)}"
        )


@router.put("/knowledge-base/articles/{article_id}")
async def update_knowledge_base_article(
    article_id: str,
    article_data: KnowledgeBaseArticleCreate,
    current_user: User = Depends(check_permission("kb:update")),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Update a knowledge base article
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        from app.core.database import SessionLocal
        from app.models.knowledge_base import KnowledgeBaseArticle
        from sqlalchemy import select
        
        # Check if article exists and belongs to tenant
        stmt = select(KnowledgeBaseArticle).where(
            KnowledgeBaseArticle.id == article_id,
            KnowledgeBaseArticle.tenant_id == current_user.tenant_id
        )
        result = await db.execute(stmt)
        article = result.scalar_one_or_none()
        
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        
        # Update article fields
        article.title = article_data.title
        article.content = article_data.content
        article.summary = article_data.summary
        article.category = article_data.category
        article.tags = article_data.tags or []
        article.is_published = article_data.is_published
        article.is_featured = article_data.is_featured
        article.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(article)
        
        return article
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error updating article: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating article: {str(e)}"
        )


@router.delete("/knowledge-base/articles/{article_id}")
async def delete_knowledge_base_article(
    article_id: str,
    current_user: User = Depends(check_permission("kb:delete")),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Delete a knowledge base article
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        from app.models.knowledge_base import KnowledgeBaseArticle
        from sqlalchemy import select
        
        # Check if article exists and belongs to tenant
        stmt = select(KnowledgeBaseArticle).where(
            KnowledgeBaseArticle.id == article_id,
            KnowledgeBaseArticle.tenant_id == current_user.tenant_id
        )
        result = await db.execute(stmt)
        article = result.scalar_one_or_none()
        
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        
        await db.delete(article)
        await db.commit()
        
        return {"message": "Article deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error deleting article: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting article: {str(e)}"
        )


# ============================================================================
# AI-Powered Helpdesk Endpoints
# ============================================================================

class TicketAIAnalysisRequest(BaseModel):
    update_fields: Optional[Dict[str, Any]] = None


class TicketAIAnalysisResponse(BaseModel):
    success: bool
    improved_description: Optional[str] = None
    suggestions: Dict[str, List[str]] = Field(default_factory=lambda: {
        "next_actions": [],
        "questions": [],
        "solutions": []
    })
    ticket_type_suggestion: Optional[str] = None
    priority_suggestion: Optional[str] = None
    sla_risk: Optional[str] = None
    auto_assign_suggestion: Optional[str] = None
    auto_respond_suggestion: Optional[str] = None
    confidence: Optional[float] = None
    error: Optional[str] = None


@router.post("/tickets/{ticket_id}/ai/analyze", response_model=TicketAIAnalysisResponse)
async def analyze_ticket_with_ai(
    ticket_id: str,
    request: Optional[TicketAIAnalysisRequest] = None,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Analyze ticket with AI and generate suggestions
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        from app.models.helpdesk import Ticket
        from app.services.helpdesk_ai_service import HelpdeskAIService
        from sqlalchemy import select
        
        # Get ticket
        stmt = select(Ticket).where(
            Ticket.id == ticket_id,
            Ticket.tenant_id == current_user.tenant_id
        )
        result = await db.execute(stmt)
        ticket = result.scalar_one_or_none()
        
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        # Use sync session for AI service (it expects sync session)
        from app.core.database import SessionLocal
        sync_db = SessionLocal()
        try:
            ai_service = HelpdeskAIService(sync_db, current_user.tenant_id)
            analysis = await ai_service.analyze_ticket(
                ticket,
                update_fields=request.update_fields if request else None
            )
            
            # Update ticket with AI analysis if successful
            if analysis.get("success"):
                ticket.ai_suggestions = analysis.get("suggestions")
                ticket.improved_description = analysis.get("improved_description")
                ticket.ai_analysis_date = datetime.now(timezone.utc)
                
                # Update description if improved version exists
                if analysis.get("improved_description"):
                    if not ticket.original_description:
                        ticket.original_description = ticket.description
                    ticket.description = analysis.get("improved_description")
                
                await db.commit()
        finally:
            sync_db.close()
        
        return TicketAIAnalysisResponse(**analysis)
    
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error analyzing ticket with AI: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing ticket: {str(e)}"
        )


class TicketImproveDescriptionRequest(BaseModel):
    description: str


class TicketImproveDescriptionResponse(BaseModel):
    improved_description: str
    original_description: str


@router.post("/tickets/{ticket_id}/ai/improve-description", response_model=TicketImproveDescriptionResponse)
async def improve_ticket_description(
    ticket_id: str,
    request: TicketImproveDescriptionRequest,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Improve ticket description using AI
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        from app.models.helpdesk import Ticket
        from app.services.helpdesk_ai_service import HelpdeskAIService
        from sqlalchemy import select
        from datetime import timezone
        
        # Get ticket
        stmt = select(Ticket).where(
            Ticket.id == ticket_id,
            Ticket.tenant_id == current_user.tenant_id
        )
        result = await db.execute(stmt)
        ticket = result.scalar_one_or_none()
        
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        # Use sync session for AI service
        from app.core.database import SessionLocal
        sync_db = SessionLocal()
        try:
            ai_service = HelpdeskAIService(sync_db, current_user.tenant_id)
            
            # Temporarily set description for improvement
            original_desc = ticket.description
            ticket.description = request.description
            
            # Improve description
            context = await ai_service._build_ticket_context(ticket)
            improved = await ai_service._improve_description(request.description, context)
            
            # Restore original
            ticket.description = original_desc
        finally:
            sync_db.close()
        
        return TicketImproveDescriptionResponse(
            improved_description=improved,
            original_description=request.description
        )
    
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error improving description: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error improving description: {str(e)}"
        )


class AutoResponseRequest(BaseModel):
    response_type: str = "acknowledgment"  # "acknowledgment", "solution", "question"


class AutoResponseResponse(BaseModel):
    response_text: str


@router.post("/tickets/{ticket_id}/ai/auto-response", response_model=AutoResponseResponse)
async def generate_auto_response(
    ticket_id: str,
    request: AutoResponseRequest,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Generate auto-response for ticket
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        from app.models.helpdesk import Ticket
        from app.services.helpdesk_ai_service import HelpdeskAIService
        from sqlalchemy import select
        
        # Get ticket
        stmt = select(Ticket).where(
            Ticket.id == ticket_id,
            Ticket.tenant_id == current_user.tenant_id
        )
        result = await db.execute(stmt)
        ticket = result.scalar_one_or_none()
        
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        # Use sync session for AI service
        from app.core.database import SessionLocal
        sync_db = SessionLocal()
        try:
            ai_service = HelpdeskAIService(sync_db, current_user.tenant_id)
            response_text = await ai_service.generate_auto_response(
                ticket,
                response_type=request.response_type
            )
        finally:
            sync_db.close()
        
        if not response_text:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate auto-response"
            )
        
        return AutoResponseResponse(response_text=response_text)
    
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error generating auto-response: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating auto-response: {str(e)}"
        )


@router.get("/tickets/{ticket_id}/ai/knowledge-base")
async def get_ai_knowledge_base_suggestions(
    ticket_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """Get AI-powered knowledge base suggestions for a ticket (runs as Celery task)"""
    from app.tasks.helpdesk_ai_tasks import suggest_kb_articles_task
    
    # Trigger Celery task
    task = suggest_kb_articles_task.delay(
        ticket_id=ticket_id,
        tenant_id=current_tenant.id,
        limit=5
    )
    
    # Wait for result (with timeout)
    try:
        result = task.get(timeout=30)  # 30 second timeout
        return result
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting knowledge base suggestions: {e}", exc_info=True)
        # Return empty suggestions on error
        return {
            "ticket_id": ticket_id,
            "suggestions": []
        }


@router.post("/knowledge-base/articles/{article_id}/auto-categorize")
async def auto_categorize_article(
    article_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """Auto-categorize article using AI"""
    from app.core.database import SessionLocal
    from app.services.knowledge_base_service import KnowledgeBaseService
    from app.models.knowledge_base import KnowledgeBaseArticle
    
    sync_db = SessionLocal()
    try:
        article = sync_db.query(KnowledgeBaseArticle).filter(
            KnowledgeBaseArticle.id == article_id,
            KnowledgeBaseArticle.tenant_id == current_tenant.id
        ).first()
        
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        
        kb_service = KnowledgeBaseService(sync_db, current_tenant.id)
        categorization = await kb_service.auto_categorize_article(article.title, article.content)
        
        return categorization
    finally:
        sync_db.close()


@router.get("/knowledge-base/articles/{article_id}/recommendations")
async def get_article_recommendations(
    article_id: str,
    limit: int = Query(5, ge=1, le=20),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """Get article recommendations based on viewing patterns"""
    from app.core.database import SessionLocal
    from app.services.knowledge_base_service import KnowledgeBaseService
    
    sync_db = SessionLocal()
    try:
        kb_service = KnowledgeBaseService(sync_db, current_tenant.id)
        recommendations = await kb_service.generate_article_recommendations(article_id, limit)
        
        return {
            "article_id": article_id,
            "recommendations": [
                {
                    "article_id": r["article"].id,
                    "title": r["article"].title,
                    "summary": r["article"].summary,
                    "category": r["article"].category,
                    "relevance_score": r["relevance_score"],
                    "reason": r["reason"]
                }
                for r in recommendations
            ]
        }
    finally:
        sync_db.close()


@router.post("/knowledge-base/articles/{article_id}/improve")
async def improve_article_with_ai(
    article_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """Get AI suggestions for improving an article"""
    from app.core.database import SessionLocal
    from app.services.knowledge_base_service import KnowledgeBaseService
    from app.models.knowledge_base import KnowledgeBaseArticle
    
    sync_db = SessionLocal()
    try:
        article = sync_db.query(KnowledgeBaseArticle).filter(
            KnowledgeBaseArticle.id == article_id,
            KnowledgeBaseArticle.tenant_id == current_tenant.id
        ).first()
        
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        
        kb_service = KnowledgeBaseService(sync_db, current_tenant.id)
        improvements = await kb_service.improve_article_with_ai(article)
        
        return improvements
    finally:
        sync_db.close()


@router.post("/workflows/execute")
async def execute_workflow(
    ticket_id: str = Body(...),
    workflow_definition: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """Execute a multi-step workflow for a ticket"""
    from app.core.database import SessionLocal
    from app.services.workflow_service import WorkflowService
    from app.models.helpdesk import Ticket
    
    sync_db = SessionLocal()
    try:
        ticket = sync_db.query(Ticket).filter(
            Ticket.id == ticket_id,
            Ticket.tenant_id == current_tenant.id
        ).first()
        
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        workflow_service = WorkflowService(sync_db, current_tenant.id)
        result = await workflow_service.execute_multi_step_workflow(ticket, workflow_definition)
        
        return result
    finally:
        sync_db.close()


@router.post("/workflows/create")
async def create_workflow(
    name: str = Body(...),
    description: str = Body(...),
    workflow_definition: Dict[str, Any] = Body(...),
    is_active: bool = Body(True),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """Create a custom workflow definition"""
    from app.core.database import SessionLocal
    from app.services.workflow_service import WorkflowService
    
    sync_db = SessionLocal()
    try:
        workflow_service = WorkflowService(sync_db, current_tenant.id)
        workflow = await workflow_service.create_custom_workflow(
            name=name,
            description=description,
            workflow_definition=workflow_definition,
            is_active=is_active
        )
        
        return workflow
    finally:
        sync_db.close()


@router.get("/workflows")
async def get_workflows(
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """Get list of available workflows"""
    from app.core.database import SessionLocal
    from app.services.workflow_service import WorkflowService
    
    sync_db = SessionLocal()
    try:
        workflow_service = WorkflowService(sync_db, current_tenant.id)
        workflows = await workflow_service.get_available_workflows()
        
        return {"workflows": workflows}
    finally:
        sync_db.close()


# ==================== Helpdesk Analytics & Reporting ====================

@router.get("/analytics/volume-trends")
async def get_ticket_volume_trends(
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    interval: str = Query("day", regex="^(day|week|month)$", description="Time interval"),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """Get ticket volume trends over time"""
    try:
        from sqlalchemy import func, extract, case
        from datetime import timedelta
        
        start_dt = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        end_dt = datetime.combine(end_date, datetime.max.time()).replace(tzinfo=timezone.utc)
        
        # Build query based on interval
        if interval == "day":
            date_expr = func.date(Ticket.created_at).label('period')
            group_by = func.date(Ticket.created_at)
        elif interval == "week":
            date_expr = func.date_trunc('week', Ticket.created_at).label('period')
            group_by = func.date_trunc('week', Ticket.created_at)
        else:  # month
            date_expr = func.date_trunc('month', Ticket.created_at).label('period')
            group_by = func.date_trunc('month', Ticket.created_at)
        
        # Use text cast for status comparisons to avoid enum type issues
        from sqlalchemy import cast, String
        stmt = select(
            date_expr,
            func.count(Ticket.id).label('total_tickets'),
            func.count(case((cast(Ticket.status, String) == "open", 1))).label('open'),
            func.count(case((cast(Ticket.status, String) == "in_progress", 1))).label('in_progress'),
            func.count(case((cast(Ticket.status, String) == "resolved", 1))).label('resolved'),
            func.count(case((cast(Ticket.status, String) == "closed", 1))).label('closed')
        ).where(
            and_(
                Ticket.tenant_id == current_tenant.id,
                Ticket.created_at >= start_dt,
                Ticket.created_at <= end_dt
            )
        ).group_by(group_by).order_by(group_by)
        
        result = await db.execute(stmt)
        rows = result.all()
        
        trends = []
        for row in rows:
            trends.append({
                'period': row.period.isoformat() if hasattr(row.period, 'isoformat') else str(row.period),
                'total_tickets': row.total_tickets or 0,
                'open': row.open or 0,
                'in_progress': row.in_progress or 0,
                'resolved': row.resolved or 0,
                'closed': row.closed or 0
            })
        
        return {
            'period': {'start': start_date.isoformat(), 'end': end_date.isoformat()},
            'interval': interval,
            'trends': trends
        }
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting volume trends: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/resolution-times")
async def get_resolution_time_analytics(
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    group_by: str = Query("priority", regex="^(priority|type|status)$", description="Group by field"),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """Get resolution time analytics grouped by priority, type, or status"""
    try:
        from sqlalchemy import func, case, extract
        
        start_dt = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        end_dt = datetime.combine(end_date, datetime.max.time()).replace(tzinfo=timezone.utc)
        
        # Build group by expression
        if group_by == "priority":
            group_expr = Ticket.priority
        elif group_by == "type":
            group_expr = Ticket.ticket_type
        else:  # status
            group_expr = Ticket.status
        
        stmt = select(
            group_expr.label('group_value'),
            func.count(Ticket.id).label('total_tickets'),
            func.avg(
                extract('epoch', Ticket.resolved_at - Ticket.created_at) / 3600
            ).label('avg_resolution_hours'),
            func.avg(
                extract('epoch', Ticket.first_response_at - Ticket.created_at) / 3600
            ).label('avg_first_response_hours'),
            func.min(
                extract('epoch', Ticket.resolved_at - Ticket.created_at) / 3600
            ).label('min_resolution_hours'),
            func.max(
                extract('epoch', Ticket.resolved_at - Ticket.created_at) / 3600
            ).label('max_resolution_hours')
        ).where(
            and_(
                Ticket.tenant_id == current_tenant.id,
                Ticket.created_at >= start_dt,
                Ticket.created_at <= end_dt,
                Ticket.resolved_at.isnot(None)
            )
        ).group_by(group_expr)
        
        result = await db.execute(stmt)
        rows = result.all()
        
        analytics = []
        for row in rows:
            analytics.append({
                'group_value': row.group_value.value if hasattr(row.group_value, 'value') else str(row.group_value),
                'total_tickets': row.total_tickets or 0,
                'avg_resolution_hours': round(row.avg_resolution_hours or 0, 2),
                'avg_first_response_hours': round(row.avg_first_response_hours or 0, 2),
                'min_resolution_hours': round(row.min_resolution_hours or 0, 2),
                'max_resolution_hours': round(row.max_resolution_hours or 0, 2)
            })
        
        return {
            'period': {'start': start_date.isoformat(), 'end': end_date.isoformat()},
            'group_by': group_by,
            'analytics': analytics
        }
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting resolution time analytics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/distributions")
async def get_ticket_distributions(
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """Get ticket distributions by priority, status, and type"""
    try:
        from sqlalchemy import func, case
        
        start_dt = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        end_dt = datetime.combine(end_date, datetime.max.time()).replace(tzinfo=timezone.utc)
        
        # Priority distribution
        priority_stmt = select(
            Ticket.priority,
            func.count(Ticket.id).label('count')
        ).where(
            and_(
                Ticket.tenant_id == current_tenant.id,
                Ticket.created_at >= start_dt,
                Ticket.created_at <= end_dt
            )
        ).group_by(Ticket.priority)
        
        # Status distribution
        status_stmt = select(
            Ticket.status,
            func.count(Ticket.id).label('count')
        ).where(
            and_(
                Ticket.tenant_id == current_tenant.id,
                Ticket.created_at >= start_dt,
                Ticket.created_at <= end_dt
            )
        ).group_by(Ticket.status)
        
        # Type distribution
        type_stmt = select(
            Ticket.ticket_type,
            func.count(Ticket.id).label('count')
        ).where(
            and_(
                Ticket.tenant_id == current_tenant.id,
                Ticket.created_at >= start_dt,
                Ticket.created_at <= end_dt
            )
        ).group_by(Ticket.ticket_type)
        
        priority_result = await db.execute(priority_stmt)
        status_result = await db.execute(status_stmt)
        type_result = await db.execute(type_stmt)
        
        priority_dist = {
            row.priority.value if hasattr(row.priority, 'value') else str(row.priority): row.count
            for row in priority_result.all()
        }
        
        status_dist = {
            row.status.value if hasattr(row.status, 'value') else str(row.status): row.count
            for row in status_result.all()
        }
        
        type_dist = {
            row.ticket_type.value if hasattr(row.ticket_type, 'value') else str(row.ticket_type): row.count
            for row in type_result.all()
        }
        
        return {
            'period': {'start': start_date.isoformat(), 'end': end_date.isoformat()},
            'priority_distribution': priority_dist,
            'status_distribution': status_dist,
            'type_distribution': type_dist
        }
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting distributions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/customer-performance")
async def get_customer_performance(
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """Get ticket performance metrics by customer"""
    try:
        from sqlalchemy import func, extract
        from app.models.crm import Customer
        
        start_dt = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        end_dt = datetime.combine(end_date, datetime.max.time()).replace(tzinfo=timezone.utc)
        
        # Fetch tickets and calculate in Python to avoid SQLAlchemy type issues
        tickets_stmt = select(Ticket).where(
            and_(
                Ticket.tenant_id == current_tenant.id,
                Ticket.created_at >= start_dt,
                Ticket.created_at <= end_dt,
                Ticket.customer_id.isnot(None)
            )
        )
        tickets_result = await db.execute(tickets_stmt)
        tickets = tickets_result.scalars().all()
        
        # Get customer details
        customer_ids = list(set([t.customer_id for t in tickets if t.customer_id]))
        customers_stmt = select(Customer).where(Customer.id.in_(customer_ids)) if customer_ids else select(Customer).where(False)
        customers_result = await db.execute(customers_stmt)
        customers = {c.id: c for c in customers_result.scalars().all()}
        
        # Group by customer and calculate metrics
        customer_stats = {}
        for ticket in tickets:
            customer_id = ticket.customer_id
            if customer_id not in customer_stats:
                customer = customers.get(customer_id)
                customer_stats[customer_id] = {
                    'customer_id': customer_id,
                    'customer_name': customer.company_name if customer else 'Unknown',
                    'total_tickets': 0,
                    'fr_breaches': 0,
                    'res_breaches': 0,
                    'fr_times': [],
                    'res_times': []
                }
            
            stats = customer_stats[customer_id]
            stats['total_tickets'] += 1
            
            if ticket.sla_first_response_breached:
                stats['fr_breaches'] += 1
            if ticket.sla_resolution_breached:
                stats['res_breaches'] += 1
            
            # Calculate first response time
            if ticket.first_response_at and ticket.created_at:
                fr_hours = (ticket.first_response_at - ticket.created_at).total_seconds() / 3600
                stats['fr_times'].append(fr_hours)
            
            # Calculate resolution time
            if ticket.resolved_at and ticket.created_at:
                res_hours = (ticket.resolved_at - ticket.created_at).total_seconds() / 3600
                stats['res_times'].append(res_hours)
        
        # Build response data
        # Build performance data
        performance = []
        for customer_id, stats in customer_stats.items():
            total = stats['total_tickets']
            fr_breaches = stats['fr_breaches']
            res_breaches = stats['res_breaches']
            
            avg_fr_hours = sum(stats['fr_times']) / len(stats['fr_times']) if stats['fr_times'] else 0
            avg_res_hours = sum(stats['res_times']) / len(stats['res_times']) if stats['res_times'] else 0
            
            performance.append({
                'customer_id': customer_id,
                'customer_name': stats['customer_name'],
                'total_tickets': total,
                'avg_resolution_hours': round(avg_res_hours, 2),
                'avg_first_response_hours': round(avg_fr_hours, 2),
                'first_response_breaches': fr_breaches,
                'resolution_breaches': res_breaches,
                'first_response_compliance_rate': round(((total - fr_breaches) / total * 100) if total > 0 else 100, 2),
                'resolution_compliance_rate': round(((total - res_breaches) / total * 100) if total > 0 else 100, 2)
            })
        
        # Sort by total_tickets descending and limit
        performance = sorted(performance, key=lambda x: x['total_tickets'], reverse=True)[:limit]
        
        return {
            'period': {'start': start_date.isoformat(), 'end': end_date.isoformat()},
            'customer_performance': performance
        }
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting customer performance: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/agent-workload")
async def get_agent_workload(
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """Get agent workload distribution and metrics"""
    try:
        from sqlalchemy import func, case
        
        start_dt = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        end_dt = datetime.combine(end_date, datetime.max.time()).replace(tzinfo=timezone.utc)
        
        # Use func.concat to combine first_name and last_name, or fetch separately and combine in Python
        # Use cast to String to avoid enum type issues
        from sqlalchemy import String, cast
        
        stmt = select(
            Ticket.assigned_to_id,
            User.first_name,
            User.last_name,
            User.email.label('agent_email'),
            func.count(Ticket.id).label('total_tickets'),
            func.count(case((cast(Ticket.status, String) == "OPEN", 1))).label('open_tickets'),
            func.count(case((cast(Ticket.status, String) == "IN_PROGRESS", 1))).label('in_progress_tickets'),
            func.count(case((cast(Ticket.status, String) == "RESOLVED", 1))).label('resolved_tickets'),
            func.avg(
                func.extract('epoch', Ticket.resolved_at - Ticket.created_at) / 3600
            ).label('avg_resolution_hours')
        ).join(
            User, Ticket.assigned_to_id == User.id, isouter=True
        ).where(
            and_(
                Ticket.tenant_id == current_tenant.id,
                Ticket.created_at >= start_dt,
                Ticket.created_at <= end_dt
            )
        ).group_by(
            Ticket.assigned_to_id,
            User.first_name,
            User.last_name,
            User.email
        ).order_by(
            func.count(Ticket.id).desc()
        )
        
        result = await db.execute(stmt)
        rows = result.all()
        
        workload = []
        for row in rows:
            # Combine first_name and last_name
            agent_name = 'Unassigned'
            if row.first_name or row.last_name:
                parts = [p for p in [row.first_name, row.last_name] if p]
                agent_name = ' '.join(parts) if parts else 'Unassigned'
            
            workload.append({
                'agent_id': row.assigned_to_id,
                'agent_name': agent_name,
                'agent_email': row.agent_email,
                'total_tickets': row.total_tickets or 0,
                'open_tickets': row.open_tickets or 0,
                'in_progress_tickets': row.in_progress_tickets or 0,
                'resolved_tickets': row.resolved_tickets or 0,
                'avg_resolution_hours': round(row.avg_resolution_hours or 0, 2) if row.avg_resolution_hours else None
            })
        
        return {
            'period': {'start': start_date.isoformat(), 'end': end_date.isoformat()},
            'agent_workload': workload
        }
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting agent workload: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/export")
async def export_helpdesk_analytics(
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    format: str = Query("csv", regex="^(csv|pdf|excel)$", description="Export format"),
    report_type: str = Query("overview", regex="^(overview|agents|customers|resolution)$", description="Report type"),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """Export helpdesk analytics report"""
    try:
        from app.services.report_export_service import ReportExportService
        from fastapi.responses import Response
        
        export_service = ReportExportService()
        
        # Load data based on report type
        data = []
        summary = {
            "Period": f"{start_date} to {end_date}",
            "Report Type": report_type
        }
        
        # Import the data fetching functions (they're in the same file)
        # We'll duplicate the logic here to avoid circular imports
        from sqlalchemy import func, case, extract
        from app.models.helpdesk import Ticket
        from app.models.tenant import User
        from app.models.crm import Customer
        from datetime import timezone as tz
        
        start_dt = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=tz.utc)
        end_dt = datetime.combine(end_date, datetime.max.time()).replace(tzinfo=tz.utc)
        
        if report_type == "overview":
            # Get volume trends - use cast to String to avoid enum type issues
            from sqlalchemy import String, cast
            date_expr = func.date(Ticket.created_at).label('period')
            volume_stmt = select(
                date_expr,
                func.count(Ticket.id).label('total_tickets'),
                func.count(case((cast(Ticket.status, String) == "OPEN", 1))).label('open'),
                func.count(case((cast(Ticket.status, String) == "IN_PROGRESS", 1))).label('in_progress'),
                func.count(case((cast(Ticket.status, String) == "RESOLVED", 1))).label('resolved'),
                func.count(case((cast(Ticket.status, String) == "CLOSED", 1))).label('closed')
            ).where(
                and_(
                    Ticket.tenant_id == current_tenant.id,
                    Ticket.created_at >= start_dt,
                    Ticket.created_at <= end_dt
                )
            ).group_by(func.date(Ticket.created_at)).order_by(func.date(Ticket.created_at))
            
            volume_result = await db.execute(volume_stmt)
            for row in volume_result.all():
                data.append({
                    "Period": row.period.isoformat() if hasattr(row.period, 'isoformat') else str(row.period),
                    "Total Tickets": row.total_tickets or 0,
                    "Open": row.open or 0,
                    "In Progress": row.in_progress or 0,
                    "Resolved": row.resolved or 0,
                    "Closed": row.closed or 0
                })
        
        elif report_type == "agents":
            # Get agent performance from SLA endpoint logic
            from app.api.v1.endpoints.sla import get_sla_performance_by_agent
            agent_perf_response = await get_sla_performance_by_agent(start_date, end_date, current_user, current_tenant, db)
            
            for agent in agent_perf_response.get('performance_by_agent', []):
                data.append({
                    "Agent": agent['agent_name'],
                    "Email": agent.get('agent_email', ''),
                    "Total Tickets": agent['total_tickets'],
                    "FR Breaches": agent['first_response']['breaches'],
                    "FR Compliance": f"{agent['first_response']['compliance_rate']}%",
                    "Res Breaches": agent['resolution']['breaches'],
                    "Res Compliance": f"{agent['resolution']['compliance_rate']}%"
                })
        
        elif report_type == "customers":
            # Get customer performance
            customer_stmt = select(
                Ticket.customer_id,
                Customer.company_name.label('customer_name'),
                func.count(Ticket.id).label('total_tickets'),
                func.avg(extract('epoch', Ticket.resolved_at - Ticket.created_at) / 3600).label('avg_resolution_hours'),
                func.avg(extract('epoch', Ticket.first_response_at - Ticket.created_at) / 3600).label('avg_first_response_hours'),
                func.sum(func.cast(Ticket.sla_first_response_breached, int)).label('fr_breaches'),
                func.sum(func.cast(Ticket.sla_resolution_breached, int)).label('res_breaches')
            ).join(
                Customer, Ticket.customer_id == Customer.id, isouter=True
            ).where(
                and_(
                    Ticket.tenant_id == current_tenant.id,
                    Ticket.created_at >= start_dt,
                    Ticket.created_at <= end_dt,
                    Ticket.customer_id.isnot(None)
                )
            ).group_by(
                Ticket.customer_id,
                Customer.company_name
            ).order_by(
                func.count(Ticket.id).desc()
            ).limit(100)
            
            customer_result = await db.execute(customer_stmt)
            for row in customer_result.all():
                total = row.total_tickets or 0
                fr_breaches = row.fr_breaches or 0
                res_breaches = row.res_breaches or 0
                
                data.append({
                    "Customer": row.customer_name or 'Unknown',
                    "Total Tickets": total,
                    "Avg Resolution (hrs)": round(row.avg_resolution_hours or 0, 2),
                    "Avg First Response (hrs)": round(row.avg_first_response_hours or 0, 2),
                    "FR Breaches": fr_breaches,
                    "FR Compliance": f"{round(((total - fr_breaches) / total * 100) if total > 0 else 100, 2)}%",
                    "Res Breaches": res_breaches,
                    "Res Compliance": f"{round(((total - res_breaches) / total * 100) if total > 0 else 100, 2)}%"
                })
        
        elif report_type == "resolution":
            # Get resolution analytics
            group_expr = Ticket.priority
            resolution_stmt = select(
                group_expr.label('group_value'),
                func.count(Ticket.id).label('total_tickets'),
                func.avg(extract('epoch', Ticket.resolved_at - Ticket.created_at) / 3600).label('avg_resolution_hours'),
                func.avg(extract('epoch', Ticket.first_response_at - Ticket.created_at) / 3600).label('avg_first_response_hours'),
                func.min(extract('epoch', Ticket.resolved_at - Ticket.created_at) / 3600).label('min_resolution_hours'),
                func.max(extract('epoch', Ticket.resolved_at - Ticket.created_at) / 3600).label('max_resolution_hours')
            ).where(
                and_(
                    Ticket.tenant_id == current_tenant.id,
                    Ticket.created_at >= start_dt,
                    Ticket.created_at <= end_dt,
                    Ticket.resolved_at.isnot(None)
                )
            ).group_by(group_expr)
            
            resolution_result = await db.execute(resolution_stmt)
            for row in resolution_result.all():
                data.append({
                    "Priority": row.group_value.value if hasattr(row.group_value, 'value') else str(row.group_value),
                    "Total Tickets": row.total_tickets or 0,
                    "Avg Resolution (hrs)": round(row.avg_resolution_hours or 0, 2),
                    "Avg First Response (hrs)": round(row.avg_first_response_hours or 0, 2),
                    "Min Resolution (hrs)": round(row.min_resolution_hours or 0, 2),
                    "Max Resolution (hrs)": round(row.max_resolution_hours or 0, 2)
                })
        
        # Generate export
        if format == "csv":
            output = export_service.export_to_csv(data, "helpdesk_analytics")
            return Response(
                content=output.read(),
                media_type="text/csv",
                headers={"Content-Disposition": f'attachment; filename="helpdesk_analytics_{start_date}_{end_date}.csv"'}
            )
        elif format == "pdf":
            output = export_service.export_to_pdf(
                f"Helpdesk Analytics Report - {report_type.title()}",
                data,
                summary,
                "helpdesk_analytics"
            )
            return Response(
                content=output.read(),
                media_type="application/pdf",
                headers={"Content-Disposition": f'attachment; filename="helpdesk_analytics_{start_date}_{end_date}.pdf"'}
            )
        else:  # excel
            output = export_service.export_to_excel(data, summary, "helpdesk_analytics")
            return Response(
                content=output.read(),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f'attachment; filename="helpdesk_analytics_{start_date}_{end_date}.xlsx"'}
            )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error exporting helpdesk analytics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tickets/{ticket_id}/knowledge-base/generate-answer")
async def generate_answer_from_kb(
    ticket_id: str,
    article_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """Generate AI-powered answer from knowledge base articles (runs as Celery task)"""
    from app.tasks.helpdesk_ai_tasks import generate_kb_answer_task
    
    # Trigger Celery task
    task = generate_kb_answer_task.delay(
        ticket_id=ticket_id,
        tenant_id=current_tenant.id,
        article_id=article_id
    )
    
    # Wait for result (with timeout)
    try:
        result = task.get(timeout=60)  # 60 second timeout for answer generation
        return result
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error generating answer from KB: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating answer: {str(e)}"
        )


@router.post("/tickets/{ticket_id}/knowledge-base/quick-response")
async def generate_quick_response(
    ticket_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """Generate quick response template from knowledge base (runs as Celery task)"""
    from app.tasks.helpdesk_ai_tasks import generate_quick_response_task
    
    # Trigger Celery task
    task = generate_quick_response_task.delay(
        ticket_id=ticket_id,
        tenant_id=current_tenant.id
    )
    
    # Wait for result (with timeout)
    try:
        result = task.get(timeout=30)  # 30 second timeout for quick response
        return result
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error generating quick response: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating quick response: {str(e)}"
        )


@router.get("/tickets/{ticket_id}/npa")
async def get_ticket_npa(
    ticket_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """Get Next Point of Action for a ticket"""
    from app.core.database import SessionLocal
    from app.services.ticket_npa_service import TicketNPAService
    from app.models.helpdesk import Ticket
    
    sync_db = SessionLocal()
    try:
        ticket = sync_db.query(Ticket).filter(
            Ticket.id == ticket_id,
            Ticket.tenant_id == current_tenant.id
        ).first()
        
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        npa_service = TicketNPAService(sync_db, current_tenant.id)
        npa_status = await npa_service.ensure_npa_exists(ticket)
        
        # Return enhanced NPA data
        # Handle npa_state as string (not enum object)
        npa_state_value = None
        if ticket.npa_state:
            if isinstance(ticket.npa_state, str):
                npa_state_value = ticket.npa_state
            elif hasattr(ticket.npa_state, 'value'):
                npa_state_value = ticket.npa_state.value
            else:
                npa_state_value = str(ticket.npa_state)
        
        return {
            **npa_status,
            "npa_state": npa_state_value,
            "npa_original_text": ticket.npa_original_text,
            "npa_cleaned_text": ticket.npa_cleaned_text,
            "npa_date_override": ticket.npa_date_override,
            "npa_exclude_from_sla": ticket.npa_exclude_from_sla,
            "npa_ai_cleanup_status": ticket.npa_ai_cleanup_status,
            "npa_ai_cleanup_task_id": ticket.npa_ai_cleanup_task_id,
            "npa_answers_original_text": ticket.npa_answers_original_text,
            "npa_answers_cleaned_text": ticket.npa_answers_cleaned_text,
            "npa_answers_ai_cleanup_status": ticket.npa_answers_ai_cleanup_status,
            "npa_answers_ai_cleanup_task_id": ticket.npa_answers_ai_cleanup_task_id
        }
    finally:
        sync_db.close()


@router.get("/tickets/{ticket_id}/npa/ai-suggestions")
async def get_npa_ai_suggestions(
    ticket_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """Get AI-powered suggestions for agent assignment, issue diagnosis, and troubleshooting"""
    from app.core.database import SessionLocal
    from app.services.npa_ai_suggestions_service import NPAAISuggestionsService
    from app.models.helpdesk import Ticket
    
    sync_db = SessionLocal()
    try:
        ticket = sync_db.query(Ticket).filter(
            Ticket.id == ticket_id,
            Ticket.tenant_id == current_tenant.id
        ).first()
        
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        suggestions_service = NPAAISuggestionsService(sync_db, current_tenant.id)
        result = await suggestions_service.generate_suggestions(ticket)
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting AI suggestions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting AI suggestions: {str(e)}"
        )
    finally:
        sync_db.close()


class NPAUpdateRequest(BaseModel):
    npa: Optional[str] = None  # Made optional to allow partial updates
    npa_cleaned_text: Optional[str] = None  # Allow setting cleaned text directly
    due_date: Optional[str] = None
    assigned_to_id: Optional[str] = None
    npa_state: Optional[str] = None  # investigation, waiting_customer, waiting_vendor, waiting_parts, solution, etc.
    date_override: bool = False
    exclude_from_sla: Optional[bool] = None
    trigger_ai_cleanup: bool = True


@router.put("/tickets/{ticket_id}/npa")
async def update_ticket_npa(
    ticket_id: str,
    request: NPAUpdateRequest,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """Update Next Point of Action for a ticket"""
    from app.core.database import SessionLocal
    from app.services.ticket_npa_service import TicketNPAService
    from app.models.helpdesk import Ticket
    from datetime import datetime
    
    sync_db = SessionLocal()
    try:
        ticket = sync_db.query(Ticket).filter(
            Ticket.id == ticket_id,
            Ticket.tenant_id == current_tenant.id
        ).first()
        
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        # Parse due date if provided
        due_date_obj = None
        if request.due_date:
            try:
                due_date_obj = datetime.fromisoformat(request.due_date.replace('Z', '+00:00'))
            except:
                raise HTTPException(status_code=400, detail="Invalid due_date format")
        
        # Parse NPA state - convert to lowercase string to match database enum
        npa_state = None
        if request.npa_state:
            # Normalize to lowercase with underscores to match database enum
            npa_state = request.npa_state.lower().replace(' ', '_')
            # Validate it's a valid enum value
            valid_states = ['investigation', 'waiting_customer', 'waiting_vendor', 'waiting_parts', 'solution', 'implementation', 'testing', 'documentation', 'other']
            if npa_state not in valid_states:
                npa_state = None
        
        npa_service = TicketNPAService(sync_db, current_tenant.id)
        
        # If npa is not provided, use existing npa_original_text or next_point_of_action
        npa_text = request.npa
        if not npa_text:
            npa_text = ticket.npa_original_text or ticket.next_point_of_action or ""
        
        result = npa_service.update_npa(
            ticket=ticket,
            npa=npa_text,
            due_date=due_date_obj,
            assigned_to_id=request.assigned_to_id,
            npa_state=npa_state,
            date_override=request.date_override,
            exclude_from_sla=request.exclude_from_sla,
            trigger_ai_cleanup=request.trigger_ai_cleanup
        )
        
        # If cleaned text is provided directly, set it
        if request.npa_cleaned_text:
            ticket.npa_cleaned_text = request.npa_cleaned_text
            sync_db.commit()
            result["npa_cleaned_text"] = request.npa_cleaned_text
        
        return result
    finally:
        sync_db.close()


@router.get("/tickets/{ticket_id}/npa/history")
async def get_ticket_npa_history(
    ticket_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """Get NPA history (call history) for a ticket"""
    from app.core.database import SessionLocal
    from app.models.helpdesk import Ticket, NPAHistory
    
    sync_db = SessionLocal()
    try:
        ticket = sync_db.query(Ticket).filter(
            Ticket.id == ticket_id,
            Ticket.tenant_id == current_tenant.id
        ).first()
        
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        # Get all NPA history entries
        npa_history = sync_db.query(NPAHistory).filter(
            NPAHistory.ticket_id == ticket_id,
            NPAHistory.tenant_id == current_tenant.id
        ).order_by(NPAHistory.created_at).all()
        
        # Format response
        history_list = []
        for npa in npa_history:
            history_list.append({
                "id": npa.id,
                "npa_original_text": npa.npa_original_text,
                "npa_cleaned_text": npa.npa_cleaned_text,
                "npa_state": npa.npa_state,
                "assigned_to_id": npa.assigned_to_id,
                "assigned_to_name": f"{npa.assigned_to.first_name} {npa.assigned_to.last_name}" if npa.assigned_to else None,
                "due_date": npa.due_date.isoformat() if npa.due_date else None,
                "date_override": npa.date_override,
                "exclude_from_sla": npa.exclude_from_sla,
                "ai_cleanup_status": npa.ai_cleanup_status,
                "answers_to_questions": npa.answers_to_questions,
                "completed_at": npa.completed_at.isoformat() if npa.completed_at else None,
                "completed_by_id": npa.completed_by_id,
                "completed_by_name": f"{npa.completed_by.first_name} {npa.completed_by.last_name}" if npa.completed_by else None,
                "completion_notes": npa.completion_notes,
                "created_at": npa.created_at.isoformat() if npa.created_at else None,
                "updated_at": npa.updated_at.isoformat() if npa.updated_at else None
            })
        
        return {
            "ticket_id": ticket_id,
            "history": history_list,
            "current_npa": {
                "npa_original_text": ticket.npa_original_text,
                "npa_cleaned_text": ticket.npa_cleaned_text,
                "npa_state": ticket.npa_state,
                "due_date": ticket.next_point_of_action_due_date.isoformat() if ticket.next_point_of_action_due_date else None,
                "assigned_to_id": ticket.next_point_of_action_assigned_to_id
            } if ticket.npa_original_text else None
        }
    finally:
        sync_db.close()


@router.put("/tickets/{ticket_id}/npa/history/{npa_history_id}/answers")
async def update_npa_history_answers(
    ticket_id: str,
    npa_history_id: str,
    answers: str = Body(..., embed=True),
    trigger_ai_cleanup: bool = Body(True, embed=True),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """Update answers to questions in an NPA history entry with AI cleanup support"""
    from app.core.database import SessionLocal
    from app.models.helpdesk import Ticket, NPAHistory
    from app.tasks.npa_answers_tasks import cleanup_npa_answers_task
    
    sync_db = SessionLocal()
    try:
        ticket = sync_db.query(Ticket).filter(
            Ticket.id == ticket_id,
            Ticket.tenant_id == current_tenant.id
        ).first()
        
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        npa_entry = sync_db.query(NPAHistory).filter(
            NPAHistory.id == npa_history_id,
            NPAHistory.ticket_id == ticket_id,
            NPAHistory.tenant_id == current_tenant.id
        ).first()
        
        if not npa_entry:
            raise HTTPException(status_code=404, detail="NPA history entry not found")
        
        # Store original answers
        npa_entry.answers_to_questions = answers
        
        # Trigger AI cleanup if requested
        if trigger_ai_cleanup and answers.strip():
            npa_entry.answers_ai_cleanup_status = "pending"
            task = cleanup_npa_answers_task.delay(
                ticket_id=ticket_id,
                tenant_id=current_tenant.id,
                original_text=answers,
                npa_history_id=npa_history_id
            )
            npa_entry.answers_ai_cleanup_task_id = task.id
        else:
            # Use original as cleaned if no cleanup
            npa_entry.answers_cleaned_text = answers
            npa_entry.answers_ai_cleanup_status = "skipped"
        
        sync_db.commit()
        
        return {
            "success": True,
            "npa_history_id": npa_history_id,
            "answers_original_text": answers,
            "answers_cleaned_text": npa_entry.answers_cleaned_text,
            "ai_cleanup_status": npa_entry.answers_ai_cleanup_status,
            "ai_cleanup_task_id": npa_entry.answers_ai_cleanup_task_id
        }
    finally:
        sync_db.close()


@router.put("/tickets/{ticket_id}/npa/answers")
async def update_current_npa_answers(
    ticket_id: str,
    answers: str = Body(..., embed=True),
    trigger_ai_cleanup: bool = Body(True, embed=True),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """Update answers to questions in the current NPA with AI cleanup support"""
    from app.core.database import SessionLocal
    from app.models.helpdesk import Ticket
    from app.tasks.npa_answers_tasks import cleanup_npa_answers_task
    
    sync_db = SessionLocal()
    try:
        ticket = sync_db.query(Ticket).filter(
            Ticket.id == ticket_id,
            Ticket.tenant_id == current_tenant.id
        ).first()
        
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        # Store original answers
        ticket.npa_answers_original_text = answers
        
        # Trigger AI cleanup if requested
        if trigger_ai_cleanup and answers.strip():
            ticket.npa_answers_ai_cleanup_status = "processing"  # Set to processing immediately
            task = cleanup_npa_answers_task.delay(
                ticket_id=ticket.id,
                tenant_id=current_tenant.id,
                original_text=answers,
                npa_history_id=None  # Explicitly None for current NPA
            )
            ticket.npa_answers_ai_cleanup_task_id = task.id
        else:
            # Use original as cleaned if no cleanup
            ticket.npa_answers_cleaned_text = answers
            ticket.npa_answers_ai_cleanup_status = "skipped"
        
        sync_db.commit()
        sync_db.refresh(ticket)  # Refresh to get latest values
        
        return {
            "success": True,
            "answers_original_text": ticket.npa_answers_original_text,
            "answers_cleaned_text": ticket.npa_answers_cleaned_text,
            "ai_cleanup_status": ticket.npa_answers_ai_cleanup_status,
            "ai_cleanup_task_id": ticket.npa_answers_ai_cleanup_task_id
        }
    finally:
        sync_db.close()


@router.post("/tickets/{ticket_id}/npa/regenerate")
async def regenerate_ticket_npa(
    ticket_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """Regenerate Next Point of Action for a ticket using AI"""
    from app.core.database import SessionLocal
    from app.services.ticket_npa_service import TicketNPAService
    from app.models.helpdesk import Ticket
    
    sync_db = SessionLocal()
    try:
        ticket = sync_db.query(Ticket).filter(
            Ticket.id == ticket_id,
            Ticket.tenant_id == current_tenant.id
        ).first()
        
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        npa_service = TicketNPAService(sync_db, current_tenant.id)
        npa_result = await npa_service.generate_npa(ticket)
        
        if npa_result.get("success"):
            result = await npa_service.update_npa(
                ticket=ticket,
                npa=npa_result["npa"],
                due_date=npa_result.get("due_date"),
                assigned_to_id=npa_result.get("assigned_to_id"),
                trigger_ai_cleanup=True
            )
            return result
        else:
            raise HTTPException(status_code=500, detail=npa_result.get("error", "Failed to generate NPA"))
    finally:
        sync_db.close()


@router.get("/tickets/npa/overdue")
async def get_overdue_npas(
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """Get all tickets with overdue Next Point of Actions"""
    from app.core.database import SessionLocal
    from app.services.ticket_npa_service import TicketNPAService
    
    sync_db = SessionLocal()
    try:
        npa_service = TicketNPAService(sync_db, current_tenant.id)
        overdue = await npa_service.get_overdue_npas()
        
        return {
            "overdue_count": len(overdue),
            "tickets": overdue
        }
    finally:
        sync_db.close()


@router.get("/tickets/npa/missing")
async def get_tickets_without_npa(
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """Get all tickets that are missing Next Point of Action"""
    from app.core.database import SessionLocal
    from app.services.ticket_npa_service import TicketNPAService
    
    sync_db = SessionLocal()
    try:
        npa_service = TicketNPAService(sync_db, current_tenant.id)
        tickets = await npa_service.get_tickets_without_npa()
        
        return {
            "missing_count": len(tickets),
            "tickets": [
                {
                    "id": t.id,
                    "ticket_number": t.ticket_number,
                    "title": t.title,
                    "status": t.status.value if hasattr(t.status, 'value') else str(t.status),
                    "priority": t.priority.value if hasattr(t.priority, 'value') else str(t.priority)
                }
                for t in tickets
            ]
        }
    finally:
        sync_db.close()


@router.post("/tickets/npa/ensure-all")
async def ensure_all_tickets_have_npa(
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """Ensure all active tickets have Next Point of Action (batch operation)"""
    from app.core.database import SessionLocal
    from app.services.ticket_npa_service import TicketNPAService
    
    sync_db = SessionLocal()
    try:
        npa_service = TicketNPAService(sync_db, current_tenant.id)
        tickets = await npa_service.get_tickets_without_npa()
        
        results = {
            "processed": 0,
            "generated": 0,
            "errors": []
        }
        
        for ticket in tickets:
            try:
                result = await npa_service.ensure_npa_exists(ticket)
                results["processed"] += 1
                if result.get("auto_generated"):
                    results["generated"] += 1
            except Exception as e:
                results["errors"].append({
                    "ticket_id": ticket.id,
                    "error": str(e)
                })
        
        sync_db.commit()
        
        return results
    finally:
        sync_db.close()


class AgentChatMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str


class AgentChatRequest(BaseModel):
    messages: List[AgentChatMessage]
    attachments: Optional[List[Dict[str, Any]]] = None  # [{filename, content, type}]
    log_files: Optional[List[str]] = None  # Array of log file contents as strings


@router.post("/tickets/{ticket_id}/agent-chat")
async def agent_chat_with_ticket(
    ticket_id: str,
    request: AgentChatRequest,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """Agent chatbot - allows agents to ask questions about tickets with attachments and log files (uses Celery)"""
    from app.core.database import SessionLocal
    from app.models.helpdesk import Ticket, TicketAgentChat
    from app.tasks.ticket_agent_chat_tasks import agent_chat_task
    import uuid
    
    sync_db = SessionLocal()
    try:
        # Verify ticket exists
        ticket = sync_db.query(Ticket).filter(
            Ticket.id == ticket_id,
            Ticket.tenant_id == current_tenant.id
        ).first()
        
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        # Get last message (should be user message)
        messages_list = [msg.model_dump() for msg in request.messages]
        if not messages_list or messages_list[-1].get("role") != "user":
            raise HTTPException(status_code=400, detail="Last message must be from user")
        
        # Save user message to database
        user_message = TicketAgentChat(
            id=str(uuid.uuid4()),
            ticket_id=ticket_id,
            tenant_id=current_tenant.id,
            user_id=current_user.id,
            role="user",
            content=messages_list[-1]["content"],
            attachments=request.attachments,
            log_files=request.log_files,
            ai_status="pending"
        )
        sync_db.add(user_message)
        sync_db.commit()
        sync_db.refresh(user_message)
        
        # Trigger Celery task for AI response
        task = agent_chat_task.delay(
            ticket_id=ticket_id,
            tenant_id=current_tenant.id,
            user_id=current_user.id,
            user_message_id=user_message.id,
            messages=messages_list,
            attachments=request.attachments,
            log_files=request.log_files
        )
        
        return {
            "success": True,
            "user_message_id": user_message.id,
            "task_id": task.id,
            "status": "processing"
        }
    except HTTPException:
        raise
    except Exception as exc:
        import logging
        logger = logging.getLogger(__name__)
        logger.error("Failed to start agent chat: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start agent chat"
        ) from exc
    finally:
        sync_db.close()


@router.get("/tickets/{ticket_id}/agent-chat")
async def get_agent_chat_history(
    ticket_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """Get chat history for a ticket"""
    from app.core.database import SessionLocal
    from app.models.helpdesk import Ticket, TicketAgentChat
    
    sync_db = SessionLocal()
    try:
        # Verify ticket exists
        ticket = sync_db.query(Ticket).filter(
            Ticket.id == ticket_id,
            Ticket.tenant_id == current_tenant.id
        ).first()
        
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        # Get all chat messages
        messages = sync_db.query(TicketAgentChat).filter(
            TicketAgentChat.ticket_id == ticket_id,
            TicketAgentChat.tenant_id == current_tenant.id
        ).order_by(TicketAgentChat.created_at).all()
        
        return {
            "ticket_id": ticket_id,
            "messages": [
                {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.created_at.isoformat() if msg.created_at else None,
                    "ai_status": msg.ai_status,
                    "ai_model": msg.ai_model,
                    "attachments": msg.attachments,
                    "log_files": msg.log_files,
                    "linked_to_npa_id": msg.linked_to_npa_id,
                    "is_solution": msg.is_solution,
                    "solution_notes": msg.solution_notes
                }
                for msg in messages
            ]
        }
    finally:
        sync_db.close()


@router.get("/tickets/{ticket_id}/agent-chat/task/{task_id}")
async def get_agent_chat_task_status(
    ticket_id: str,
    task_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """Get status of agent chat Celery task"""
    from celery.result import AsyncResult
    from app.core.celery_app import celery_app
    
    task_result = AsyncResult(task_id, app=celery_app)
    
    if task_result.ready():
        if task_result.successful():
            return {
                "status": "completed",
                "result": task_result.result
            }
        else:
            return {
                "status": "failed",
                "error": str(task_result.result)
            }
    else:
        return {
            "status": "processing",
            "task_id": task_id
        }


@router.post("/tickets/{ticket_id}/agent-chat/{message_id}/save-to-npa")
async def save_chat_to_npa(
    ticket_id: str,
    message_id: str,
    npa_id: Optional[str] = Body(None, embed=True),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """Save chat message(s) to an NPA (existing or new)"""
    from app.core.database import SessionLocal
    from app.models.helpdesk import Ticket, TicketAgentChat, NPAHistory
    from app.services.ticket_npa_service import TicketNPAService
    
    sync_db = SessionLocal()
    try:
        # Get ticket and message
        ticket = sync_db.query(Ticket).filter(
            Ticket.id == ticket_id,
            Ticket.tenant_id == current_tenant.id
        ).first()
        
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        message = sync_db.query(TicketAgentChat).filter(
            TicketAgentChat.id == message_id,
            TicketAgentChat.ticket_id == ticket_id,
            TicketAgentChat.tenant_id == current_tenant.id
        ).first()
        
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        
        # Get all messages in conversation up to this point
        all_messages = sync_db.query(TicketAgentChat).filter(
            TicketAgentChat.ticket_id == ticket_id,
            TicketAgentChat.tenant_id == current_tenant.id,
            TicketAgentChat.created_at <= message.created_at
        ).order_by(TicketAgentChat.created_at).all()
        
        # Build conversation text
        conversation_text = "\n\n".join([
            f"{msg.role.upper()}: {msg.content}"
            for msg in all_messages
        ])
        
        if create_new:
            # Force create new NPA
            pass  # Will fall through to create new NPA logic
        elif npa_id:
            # Update existing NPA by ID
            npa = sync_db.query(NPAHistory).filter(
                NPAHistory.id == npa_id,
                NPAHistory.ticket_id == ticket_id,
                NPAHistory.tenant_id == current_tenant.id
            ).first()
            
            if not npa:
                raise HTTPException(status_code=404, detail="NPA not found")
            
            # Append conversation to answers
            if npa.answers_to_questions:
                npa.answers_to_questions += f"\n\n--- Agent Chat Conversation ---\n{conversation_text}"
            else:
                npa.answers_to_questions = f"--- Agent Chat Conversation ---\n{conversation_text}"
            
            # Link messages to NPA
            for msg in all_messages:
                msg.linked_to_npa_id = npa_id
            
            sync_db.commit()
            
            return {
                "success": True,
                "npa_id": npa_id,
                "message": "Chat saved to existing NPA"
            }
        elif ticket.npa_original_text:
            # Save to current NPA (find the active NPA history entry)
            current_npa = sync_db.query(NPAHistory).filter(
                NPAHistory.ticket_id == ticket_id,
                NPAHistory.tenant_id == current_tenant.id,
                NPAHistory.completed_at.is_(None)
            ).order_by(NPAHistory.created_at.desc()).first()
            
            if current_npa:
                # Append conversation to answers
                if current_npa.answers_to_questions:
                    current_npa.answers_to_questions += f"\n\n--- Agent Chat Conversation ---\n{conversation_text}"
                else:
                    current_npa.answers_to_questions = f"--- Agent Chat Conversation ---\n{conversation_text}"
                
                # Link messages to NPA
                for msg in all_messages:
                    msg.linked_to_npa_id = current_npa.id
                
                sync_db.commit()
                
                return {
                    "success": True,
                    "npa_id": current_npa.id,
                    "message": "Chat saved to current NPA"
                }
        
        # Create new NPA (if create_new=True or no current NPA)
        if True:
            # Create new NPA and close current one if exists
            npa_service = TicketNPAService(sync_db, current_tenant.id)
            
            # Close current NPA if exists
            if ticket.npa_original_text:
                # Mark current NPA as completed
                current_npa_history = sync_db.query(NPAHistory).filter(
                    NPAHistory.ticket_id == ticket_id,
                    NPAHistory.tenant_id == current_tenant.id,
                    NPAHistory.completed_at.is_(None)
                ).order_by(NPAHistory.created_at.desc()).first()
                
                if current_npa_history:
                    current_npa_history.completed_at = func.now()
                    current_npa_history.completed_by_id = current_user.id
                    current_npa_history.completion_notes = "Closed when creating new NPA from agent chat"
            
            # Create new NPA from chat
            result = await npa_service.update_npa(
                ticket=ticket,
                npa=f"Agent Chat Conversation:\n{conversation_text}",
                trigger_ai_cleanup=True
            )
            
            new_npa_id = result.get("npa_history_id")
            
            # Link messages to new NPA
            for msg in all_messages:
                msg.linked_to_npa_id = new_npa_id
            
            sync_db.commit()
            
            return {
                "success": True,
                "npa_id": new_npa_id,
                "message": "New NPA created from chat and previous NPA closed"
            }
    finally:
        sync_db.close()


@router.post("/tickets/{ticket_id}/agent-chat/{message_id}/mark-solution")
async def mark_chat_as_solution(
    ticket_id: str,
    message_id: str,
    notes: Optional[str] = Body(None, embed=True),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """Mark a chat message as the solution"""
    from app.core.database import SessionLocal
    from app.models.helpdesk import Ticket, TicketAgentChat
    
    sync_db = SessionLocal()
    try:
        # Get ticket and message
        ticket = sync_db.query(Ticket).filter(
            Ticket.id == ticket_id,
            Ticket.tenant_id == current_tenant.id
        ).first()
        
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        message = sync_db.query(TicketAgentChat).filter(
            TicketAgentChat.id == message_id,
            TicketAgentChat.ticket_id == ticket_id,
            TicketAgentChat.tenant_id == current_tenant.id
        ).first()
        
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        
        # Unmark other solutions
        sync_db.query(TicketAgentChat).filter(
            TicketAgentChat.ticket_id == ticket_id,
            TicketAgentChat.is_solution == True
        ).update({"is_solution": False})
        
        # Mark this as solution
        message.is_solution = True
        message.solution_notes = notes
        
        sync_db.commit()
        
        return {
            "success": True,
            "message_id": message_id,
            "message": "Chat marked as solution"
        }
    finally:
        sync_db.close()

