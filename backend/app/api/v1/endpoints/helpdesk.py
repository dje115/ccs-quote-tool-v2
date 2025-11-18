#!/usr/bin/env python3
"""
Helpdesk API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime

from app.core.dependencies import get_current_user, get_current_tenant, check_permission
from app.core.database import get_async_db, SessionLocal
from app.models.tenant import User, Tenant
from app.models.helpdesk import TicketStatus, TicketPriority, TicketType
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
    status: Optional[TicketStatus] = Query(None),
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
                status=status,
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
        stmt = select(Ticket).options(
            joinedload(Ticket.comments),
            joinedload(Ticket.history),
            joinedload(Ticket.assigned_to)
        ).where(
            Ticket.id == ticket_id,
            Ticket.tenant_id == current_user.tenant_id
        )
        result = await db.execute(stmt)
        ticket = result.scalar_one_or_none()
        
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        # Get assigned user name if available
        assigned_to_name = None
        if ticket.assigned_to_id and ticket.assigned_to:
            assigned_to_name = ticket.assigned_to.name if hasattr(ticket.assigned_to, 'name') else ticket.assigned_to.email if hasattr(ticket.assigned_to, 'email') else None
        
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
            "ai_suggestions": ai_suggestions,
            "ai_analysis_date": ticket.ai_analysis_date.isoformat() if ticket.ai_analysis_date else None,
            "status": ticket.status.value if ticket.status else None,
            "priority": ticket.priority.value if ticket.priority else None,
            "ticket_type": ticket.ticket_type.value if ticket.ticket_type else None,
            "customer_id": ticket.customer_id,
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
    Manually trigger AI analysis for a ticket
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        from app.models.helpdesk import Ticket
        from sqlalchemy import select
        
        stmt = select(Ticket).where(
            Ticket.id == ticket_id,
            Ticket.tenant_id == current_user.tenant_id
        )
        result = await db.execute(stmt)
        ticket = result.scalar_one_or_none()
        
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        # HelpdeskService currently expects sync session - use sync wrapper
        from app.core.database import SessionLocal
        sync_db = SessionLocal()
        try:
            service = HelpdeskService(sync_db, current_user.tenant_id)
            await service._analyze_ticket_with_full_history(ticket)
            
            # Reload ticket to get updated AI analysis
            sync_db.refresh(ticket)
        finally:
            sync_db.close()
        
        return {
            "success": True,
            "message": "AI analysis completed successfully",
            "ticket": {
                "id": ticket.id,
                "ai_suggestions": ticket.ai_suggestions,
                "improved_description": ticket.improved_description,
                "ai_analysis_date": ticket.ai_analysis_date.isoformat() if ticket.ai_analysis_date else None
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error analyzing ticket: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing ticket: {str(e)}"
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
        from app.models.helpdesk import KnowledgeBaseArticle
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
        from app.models.helpdesk import KnowledgeBaseArticle
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

