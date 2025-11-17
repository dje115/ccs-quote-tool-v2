#!/usr/bin/env python3
"""
Helpdesk API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime

from app.core.dependencies import get_db, get_current_user, get_current_tenant, check_permission
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
    db: Session = Depends(get_db)
):
    """Create a new support ticket"""
    try:
        service = HelpdeskService(db, current_user.tenant_id)
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
        return ticket
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating ticket: {str(e)}"
        )


@router.post("/tickets/customer", status_code=status.HTTP_201_CREATED)
async def create_customer_ticket(
    ticket_data: CustomerTicketCreate,
    db: Session = Depends(get_db)
):
    """Create a ticket from customer portal (no auth required)"""
    try:
        # Get tenant from customer email domain or default tenant
        # For now, use default tenant
        from app.models.tenant import Tenant
        tenant = db.query(Tenant).filter(Tenant.code == "ccs").first()
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        service = HelpdeskService(db, tenant.id)
        
        # Find or create customer by email
        from app.models.customer import Customer
        customer = db.query(Customer).filter(
            Customer.tenant_id == tenant.id,
            Customer.email == ticket_data.contact_email
        ).first()
        
        customer_id = customer.id if customer else None
        
        ticket = await service.create_ticket(
            subject=ticket_data.subject,
            description=ticket_data.description,
            customer_id=customer_id,
            ticket_type=ticket_data.ticket_type,
            priority=ticket_data.priority,
            tags=None
        )
        
        # Add initial comment from customer
        service.add_comment(
            ticket_id=ticket.id,
            comment=ticket_data.description,
            author_name=ticket_data.contact_name,
            author_email=ticket_data.contact_email,
            is_internal=False
        )
        
        return ticket
    except HTTPException:
        raise
    except Exception as e:
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
    db: Session = Depends(get_db)
):
    """List tickets with filters"""
    try:
        service = HelpdeskService(db, current_user.tenant_id)
        tickets = service.get_tickets(
            status=status,
            priority=priority,
            assigned_to_id=assigned_to_id or (current_user.id if assigned_to_id == "me" else None),
            customer_id=customer_id,
            ticket_type=ticket_type,
            limit=limit,
            offset=offset
        )
        return {"tickets": tickets, "count": len(tickets)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing tickets: {str(e)}"
        )


@router.get("/tickets/{ticket_id}")
async def get_ticket(
    ticket_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Get ticket details"""
    try:
        from app.models.helpdesk import Ticket
        ticket = db.query(Ticket).filter(
            Ticket.id == ticket_id,
            Ticket.tenant_id == current_user.tenant_id
        ).first()
        
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        return ticket
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
    db: Session = Depends(get_db)
):
    """Add a comment to a ticket"""
    try:
        service = HelpdeskService(db, current_user.tenant_id)
        comment = service.add_comment(
            ticket_id=ticket_id,
            comment=comment_data.comment,
            author_id=current_user.id,
            is_internal=comment_data.is_internal,
            status_change=comment_data.status_change
        )
        return comment
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error adding comment: {str(e)}"
        )


@router.post("/tickets/{ticket_id}/assign")
async def assign_ticket(
    ticket_id: str,
    assigned_to_id: str,
    current_user: User = Depends(check_permission("ticket:assign")),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Assign a ticket to a user"""
    try:
        service = HelpdeskService(db, current_user.tenant_id)
        ticket = service.assign_ticket(
            ticket_id=ticket_id,
            assigned_to_id=assigned_to_id,
            assigned_by_id=current_user.id
        )
        return ticket
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
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
    db: Session = Depends(get_db)
):
    """Update ticket priority"""
    try:
        service = HelpdeskService(db, current_user.tenant_id)
        ticket = service.update_priority(
            ticket_id=ticket_id,
            priority=priority,
            changed_by_id=current_user.id
        )
        return ticket
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating priority: {str(e)}"
        )


@router.get("/tickets/stats")
async def get_ticket_stats(
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Get ticket statistics"""
    try:
        service = HelpdeskService(db, current_user.tenant_id)
        stats = service.get_ticket_stats()
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting stats: {str(e)}"
        )


@router.get("/knowledge-base/search")
async def search_knowledge_base(
    q: str = Query(..., min_length=1),
    category: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Search knowledge base using AI-powered semantic search"""
    try:
        service = HelpdeskService(db, current_user.tenant_id)
        results = await service.search_knowledge_base(
            query=q,
            category=category,
            limit=limit
        )
        return {"results": results, "query": q}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching knowledge base: {str(e)}"
        )


@router.post("/knowledge-base/articles", status_code=status.HTTP_201_CREATED)
async def create_knowledge_base_article(
    article_data: KnowledgeBaseArticleCreate,
    current_user: User = Depends(check_permission("kb:create")),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Create a knowledge base article"""
    try:
        service = HelpdeskService(db, current_user.tenant_id)
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
        return article
    except Exception as e:
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
    db: Session = Depends(get_db)
):
    """List knowledge base articles"""
    try:
        from app.models.helpdesk import KnowledgeBaseArticle
        query = db.query(KnowledgeBaseArticle).filter(
            KnowledgeBaseArticle.tenant_id == current_user.tenant_id
        )
        
        if published_only:
            query = query.filter(KnowledgeBaseArticle.is_published == True)
        
        if category:
            query = query.filter(KnowledgeBaseArticle.category == category)
        
        articles = query.order_by(KnowledgeBaseArticle.created_at.desc()).all()
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
    db: Session = Depends(get_db)
):
    """Get knowledge base article"""
    try:
        from app.models.helpdesk import KnowledgeBaseArticle
        article = db.query(KnowledgeBaseArticle).filter(
            KnowledgeBaseArticle.id == article_id,
            KnowledgeBaseArticle.tenant_id == current_user.tenant_id
        ).first()
        
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        
        # Increment view count
        article.view_count += 1
        db.commit()
        
        return article
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting article: {str(e)}"
        )

