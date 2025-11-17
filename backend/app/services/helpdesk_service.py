#!/usr/bin/env python3
"""
Helpdesk Service
Manages tickets, knowledge base, and SLA tracking
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from datetime import datetime, timedelta, timezone
import logging
import uuid

from app.models.helpdesk import (
    Ticket, TicketComment, TicketAttachment, TicketHistory,
    KnowledgeBaseArticle, SLAPolicy,
    TicketStatus, TicketPriority, TicketType
)
from app.models.tenant import User
from app.models.crm import Customer
from app.services.ai_provider_service import AIProviderService
from app.models.ai_prompt import PromptCategory

logger = logging.getLogger(__name__)


class HelpdeskService:
    """Service for managing helpdesk tickets and knowledge base"""
    
    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.ai_service = AIProviderService(db, tenant_id=tenant_id)
    
    def create_ticket(
        self,
        subject: str,
        description: str,
        customer_id: Optional[str] = None,
        contact_id: Optional[str] = None,
        ticket_type: TicketType = TicketType.SUPPORT,
        priority: TicketPriority = TicketPriority.MEDIUM,
        created_by_user_id: Optional[str] = None,
        related_quote_id: Optional[str] = None,
        related_contract_id: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Ticket:
        """
        Create a new support ticket
        
        Args:
            subject: Ticket subject
            description: Ticket description
            customer_id: Customer ID (optional)
            contact_id: Contact ID (optional)
            ticket_type: Type of ticket
            priority: Ticket priority
            created_by_user_id: Internal user who created (if internal)
            related_quote_id: Related quote ID
            related_contract_id: Related contract ID
            tags: List of tags
        
        Returns:
            Created ticket
        """
        # Generate ticket number
        ticket_count = self.db.query(Ticket).filter_by(tenant_id=self.tenant_id).count()
        ticket_number = f"TKT-{datetime.now().strftime('%Y%m')}-{ticket_count + 1:05d}"
        
        # Get SLA policy
        sla_policy = self._get_sla_policy(priority, ticket_type, customer_id)
        sla_target_hours = sla_policy.resolution_hours if sla_policy else None
        
        # Store original description
        original_description = description
        
        # Perform AI analysis to improve description and get suggestions
        improved_description = None
        ai_suggestions = None
        ai_analysis_date = None
        
        try:
            ai_result = await self._analyze_ticket_with_ai(subject, description, customer_id)
            if ai_result:
                improved_description = ai_result.get("improved_description")
                ai_suggestions = ai_result.get("suggestions", {})
                ai_analysis_date = datetime.now(timezone.utc)
                
                # Use improved description if available
                if improved_description:
                    description = improved_description
        except Exception as e:
            logger.warning(f"AI analysis failed for ticket {ticket_number}: {str(e)}")
            # Continue without AI improvements
        
        ticket = Ticket(
            id=str(uuid.uuid4()),
            tenant_id=self.tenant_id,
            ticket_number=ticket_number,
            customer_id=customer_id,
            contact_id=contact_id,
            created_by_user_id=created_by_user_id,
            subject=subject,
            description=description,  # Use improved version if available
            original_description=original_description,
            improved_description=improved_description,
            ai_suggestions=ai_suggestions,
            ai_analysis_date=ai_analysis_date,
            ticket_type=ticket_type,
            status=TicketStatus.OPEN,
            priority=priority,
            sla_target_hours=sla_target_hours,
            related_quote_id=related_quote_id,
            related_contract_id=related_contract_id,
            tags=tags or []
        )
        
        self.db.add(ticket)
        self.db.commit()
        self.db.refresh(ticket)
        
        # Create history entry
        self._add_history(ticket, "status", None, TicketStatus.OPEN.value, created_by_user_id)
        
        logger.info(f"Created ticket {ticket_number} for tenant {self.tenant_id}")
        
        return ticket
    
    def add_comment(
        self,
        ticket_id: str,
        comment: str,
        author_id: Optional[str] = None,
        author_name: Optional[str] = None,
        author_email: Optional[str] = None,
        is_internal: bool = False,
        status_change: Optional[str] = None
    ) -> TicketComment:
        """
        Add a comment to a ticket
        
        Args:
            ticket_id: Ticket ID
            comment: Comment text
            author_id: Internal user ID (if internal comment)
            author_name: Author name (for customer comments)
            author_email: Author email (for customer comments)
            is_internal: Whether this is an internal note
            status_change: New status if this comment changes status
        
        Returns:
            Created comment
        """
        ticket = self.db.query(Ticket).filter(
            and_(
                Ticket.id == ticket_id,
                Ticket.tenant_id == self.tenant_id
            )
        ).first()
        
        if not ticket:
            raise ValueError(f"Ticket {ticket_id} not found")
        
        comment_obj = TicketComment(
            id=str(uuid.uuid4()),
            ticket_id=ticket_id,
            comment=comment,
            author_id=author_id,
            author_name=author_name,
            author_email=author_email,
            is_internal=is_internal,
            is_system=False,
            status_change=status_change
        )
        
        self.db.add(comment_obj)
        
        # Update ticket first response time if this is the first response
        if not ticket.first_response_at and author_id:  # Internal response
            ticket.first_response_at = datetime.now(timezone.utc)
        
        # Update status if changed
        if status_change:
            old_status = ticket.status.value
            ticket.status = TicketStatus[status_change.upper()]
            self._add_history(ticket, "status", old_status, status_change, author_id)
            
            if ticket.status == TicketStatus.RESOLVED and not ticket.resolved_at:
                ticket.resolved_at = datetime.now(timezone.utc)
            elif ticket.status == TicketStatus.CLOSED and not ticket.closed_at:
                ticket.closed_at = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(comment_obj)
        
        return comment_obj
    
    def assign_ticket(
        self,
        ticket_id: str,
        assigned_to_id: str,
        assigned_by_id: str
    ) -> Ticket:
        """
        Assign a ticket to a user
        
        Args:
            ticket_id: Ticket ID
            assigned_to_id: User ID to assign to
            assigned_by_id: User ID who made the assignment
        
        Returns:
            Updated ticket
        """
        ticket = self.db.query(Ticket).filter(
            and_(
                Ticket.id == ticket_id,
                Ticket.tenant_id == self.tenant_id
            )
        ).first()
        
        if not ticket:
            raise ValueError(f"Ticket {ticket_id} not found")
        
        old_assigned = ticket.assigned_to_id
        ticket.assigned_to_id = assigned_to_id
        ticket.assigned_at = datetime.now(timezone.utc)
        
        self._add_history(ticket, "assigned_to_id", old_assigned, assigned_to_id, assigned_by_id)
        
        self.db.commit()
        self.db.refresh(ticket)
        
        return ticket
    
    def update_priority(
        self,
        ticket_id: str,
        priority: TicketPriority,
        changed_by_id: str
    ) -> Ticket:
        """
        Update ticket priority
        
        Args:
            ticket_id: Ticket ID
            priority: New priority
            changed_by_id: User ID who made the change
        
        Returns:
            Updated ticket
        """
        ticket = self.db.query(Ticket).filter(
            and_(
                Ticket.id == ticket_id,
                Ticket.tenant_id == self.tenant_id
            )
        ).first()
        
        if not ticket:
            raise ValueError(f"Ticket {ticket_id} not found")
        
        old_priority = ticket.priority.value
        ticket.priority = priority
        
        # Update SLA if priority changed
        sla_policy = self._get_sla_policy(priority, ticket.ticket_type, ticket.customer_id)
        if sla_policy:
            ticket.sla_target_hours = sla_policy.resolution_hours
        
        self._add_history(ticket, "priority", old_priority, priority.value, changed_by_id)
        
        self.db.commit()
        self.db.refresh(ticket)
        
        return ticket
    
    async def search_knowledge_base(
        self,
        query: str,
        category: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search knowledge base using AI-powered semantic search
        
        Args:
            query: Search query
            category: Optional category filter
            limit: Maximum results
        
        Returns:
            List of matching articles with relevance scores
        """
        # Get published articles
        articles_query = self.db.query(KnowledgeBaseArticle).filter(
            and_(
                KnowledgeBaseArticle.tenant_id == self.tenant_id,
                KnowledgeBaseArticle.is_published == True
            )
        )
        
        if category:
            articles_query = articles_query.filter(
                KnowledgeBaseArticle.category == category
            )
        
        articles = articles_query.all()
        
        if not articles:
            return []
        
        # Use AI to rank articles by relevance
        try:
            # Build context for AI
            articles_context = []
            for article in articles:
                articles_context.append({
                    'id': article.id,
                    'title': article.title,
                    'summary': article.summary or article.content[:200],
                    'category': article.category
                })
            
            # Use database-driven AI prompt for knowledge base search
            prompt_result = await self.ai_service.generate_with_rendered_prompts(
                category=PromptCategory.KNOWLEDGE_BASE_SEARCH,
                variables={
                    'query': query,
                    'articles': str(articles_context),
                    'limit': str(limit)
                }
            )
            
            # Parse AI response to get ranked articles
            # For now, return articles sorted by view count (fallback)
            # In production, parse AI response for relevance scores
            
            results = []
            for article in sorted(articles, key=lambda x: x.view_count, reverse=True)[:limit]:
                results.append({
                    'id': article.id,
                    'title': article.title,
                    'summary': article.summary or article.content[:200],
                    'category': article.category,
                    'view_count': article.view_count,
                    'helpful_count': article.helpful_count,
                    'relevance_score': 0.8  # Placeholder - would come from AI
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error in AI knowledge base search: {e}")
            # Fallback: simple text search
            results = []
            query_lower = query.lower()
            for article in articles:
                if query_lower in article.title.lower() or query_lower in article.content.lower():
                    results.append({
                        'id': article.id,
                        'title': article.title,
                        'summary': article.summary or article.content[:200],
                        'category': article.category,
                        'view_count': article.view_count,
                        'helpful_count': article.helpful_count,
                        'relevance_score': 0.7
                    })
            
            return results[:limit]
    
    def create_knowledge_base_article(
        self,
        title: str,
        content: str,
        summary: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        author_id: Optional[str] = None,
        is_published: bool = False,
        is_featured: bool = False
    ) -> KnowledgeBaseArticle:
        """
        Create a knowledge base article
        
        Args:
            title: Article title
            content: Article content
            summary: Article summary
            category: Article category
            tags: List of tags
            author_id: Author user ID
            is_published: Whether to publish immediately
            is_featured: Whether to feature this article
        
        Returns:
            Created article
        """
        article = KnowledgeBaseArticle(
            id=str(uuid.uuid4()),
            tenant_id=self.tenant_id,
            title=title,
            content=content,
            summary=summary,
            category=category,
            tags=tags or [],
            author_id=author_id,
            is_published=is_published,
            is_featured=is_featured
        )
        
        self.db.add(article)
        self.db.commit()
        self.db.refresh(article)
        
        return article
    
    def get_tickets(
        self,
        status: Optional[TicketStatus] = None,
        priority: Optional[TicketPriority] = None,
        assigned_to_id: Optional[str] = None,
        customer_id: Optional[str] = None,
        ticket_type: Optional[TicketType] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Ticket]:
        """
        Get tickets with filters
        
        Args:
            status: Filter by status
            priority: Filter by priority
            assigned_to_id: Filter by assigned user
            customer_id: Filter by customer
            ticket_type: Filter by type
            limit: Maximum results
            offset: Offset for pagination
        
        Returns:
            List of tickets
        """
        query = self.db.query(Ticket).filter(
            Ticket.tenant_id == self.tenant_id
        )
        
        if status:
            query = query.filter(Ticket.status == status)
        if priority:
            query = query.filter(Ticket.priority == priority)
        if assigned_to_id:
            query = query.filter(Ticket.assigned_to_id == assigned_to_id)
        if customer_id:
            query = query.filter(Ticket.customer_id == customer_id)
        if ticket_type:
            query = query.filter(Ticket.ticket_type == ticket_type)
        
        return query.order_by(desc(Ticket.created_at)).limit(limit).offset(offset).all()
    
    def get_ticket_stats(self) -> Dict[str, Any]:
        """
        Get ticket statistics for dashboard
        
        Returns:
            Dictionary with ticket statistics
        """
        total = self.db.query(func.count(Ticket.id)).filter(
            Ticket.tenant_id == self.tenant_id
        ).scalar() or 0
        
        open_count = self.db.query(func.count(Ticket.id)).filter(
            and_(
                Ticket.tenant_id == self.tenant_id,
                Ticket.status == TicketStatus.OPEN
            )
        ).scalar() or 0
        
        in_progress_count = self.db.query(func.count(Ticket.id)).filter(
            and_(
                Ticket.tenant_id == self.tenant_id,
                Ticket.status == TicketStatus.IN_PROGRESS
            )
        ).scalar() or 0
        
        resolved_count = self.db.query(func.count(Ticket.id)).filter(
            and_(
                Ticket.tenant_id == self.tenant_id,
                Ticket.status == TicketStatus.RESOLVED
            )
        ).scalar() or 0
        
        urgent_count = self.db.query(func.count(Ticket.id)).filter(
            and_(
                Ticket.tenant_id == self.tenant_id,
                Ticket.priority == TicketPriority.URGENT,
                Ticket.status.in_([TicketStatus.OPEN, TicketStatus.IN_PROGRESS])
            )
        ).scalar() or 0
        
        return {
            'total': total,
            'open': open_count,
            'in_progress': in_progress_count,
            'resolved': resolved_count,
            'urgent': urgent_count
        }
    
    def _get_sla_policy(
        self,
        priority: TicketPriority,
        ticket_type: TicketType,
        customer_id: Optional[str]
    ) -> Optional[SLAPolicy]:
        """Get applicable SLA policy"""
        policies = self.db.query(SLAPolicy).filter(
            and_(
                SLAPolicy.tenant_id == self.tenant_id,
                SLAPolicy.is_active == True
            )
        ).all()
        
        # Find matching policy (priority, type, customer)
        for policy in policies:
            if policy.priority and policy.priority != priority:
                continue
            if policy.ticket_type and policy.ticket_type != ticket_type:
                continue
            if policy.customer_ids and customer_id not in policy.customer_ids:
                continue
            
            return policy
        
        return None
    
    def _add_history(
        self,
        ticket: Ticket,
        field_name: str,
        old_value: Optional[str],
        new_value: str,
        changed_by_id: Optional[str]
    ):
        """Add history entry for ticket change"""
        history = TicketHistory(
            id=str(uuid.uuid4()),
            ticket_id=ticket.id,
            field_name=field_name,
            old_value=old_value,
            new_value=new_value,
            changed_by_id=changed_by_id
        )
        self.db.add(history)
    
    def get_sla_policy(
        self,
        priority: TicketPriority,
        ticket_type: TicketType,
        customer_id: Optional[str]
    ) -> Optional[SLAPolicy]:
        """Get applicable SLA policy (public method)"""
        return self._get_sla_policy(priority, ticket_type, customer_id)
    
    async def _analyze_ticket_with_ai(
        self,
        subject: str,
        description: str,
        customer_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze ticket with AI to improve description and suggest actions
        
        Returns:
            Dictionary with improved_description and suggestions
        """
        try:
            # Get customer context if available
            customer_context = ""
            if customer_id:
                customer = self.db.query(Customer).filter(
                    Customer.id == customer_id,
                    Customer.tenant_id == self.tenant_id
                ).first()
                if customer:
                    customer_context = f"\n\nCustomer: {customer.company_name}"
                    if customer.business_sector:
                        customer_context += f"\nBusiness Sector: {customer.business_sector.value}"
                    if customer.description:
                        customer_context += f"\nCustomer Description: {customer.description[:200]}"
            
            # Build prompt for ticket analysis
            prompt = f"""You are a customer service assistant. Analyze the following support ticket and:

1. Improve the description to be clear, professional, and customer-friendly (this will be shown to the customer)
2. Suggest next actions/questions that should be asked to gather more information
3. Suggest potential solutions if enough information is available

Original Ticket:
Subject: {subject}
Description: {description}
{customer_context}

Provide your response in JSON format:
{{
    "improved_description": "The improved, professional description",
    "suggestions": {{
        "next_actions": ["action 1", "action 2"],
        "questions": ["question 1", "question 2"],
        "solutions": ["solution 1", "solution 2"]
    }}
}}"""

            # Use database-driven AI prompt if available, otherwise use fallback
            result = await self.ai_service.generate_with_rendered_prompts(
                category=PromptCategory.CUSTOMER_SERVICE,
                variables={
                    "ticket_subject": subject,
                    "ticket_description": description,
                    "customer_context": customer_context
                },
                fallback_prompt=prompt,
                model_preference=None,
                temperature=0.7,
                max_tokens=1000
            )
            
            if result and result.get("content"):
                import json
                try:
                    # Try to parse JSON response
                    content = result["content"].strip()
                    # Remove markdown code blocks if present
                    if content.startswith("```"):
                        content = content.split("```")[1]
                        if content.startswith("json"):
                            content = content[4:]
                    content = content.strip()
                    
                    analysis = json.loads(content)
                    return {
                        "improved_description": analysis.get("improved_description", description),
                        "suggestions": analysis.get("suggestions", {})
                    }
                except json.JSONDecodeError:
                    # If not JSON, try to extract improved description from text
                    lines = result["content"].split("\n")
                    improved = description
                    for line in lines:
                        if "improved" in line.lower() or "description" in line.lower():
                            # Try to extract the improved description
                            if ":" in line:
                                improved = line.split(":", 1)[1].strip()
                                break
                    
                    return {
                        "improved_description": improved,
                        "suggestions": {}
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error in AI ticket analysis: {str(e)}")
            return None

