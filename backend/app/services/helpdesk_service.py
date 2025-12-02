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
    Ticket, TicketComment, TicketAttachment, TicketHistory, NPAHistory,
    SLAPolicy,
    TicketStatus, TicketPriority, TicketType
)
from app.models.knowledge_base import KnowledgeBaseArticle
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
    
    async def create_ticket(
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
        sla_first_response_hours = sla_policy.first_response_hours if sla_policy else None
        sla_policy_id = sla_policy.id if sla_policy else None
        
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
            sla_policy_id=sla_policy_id,
            sla_target_hours=sla_target_hours,
            sla_first_response_hours=sla_first_response_hours,
            related_quote_id=related_quote_id,
            related_contract_id=related_contract_id,
            tags=tags or []
        )
        
        # Store original description
        if not original_description and description:
            ticket.original_description = description
        
        self.db.add(ticket)
        self.db.commit()
        self.db.refresh(ticket)
        
        # Create history entry
        self._add_history(ticket, "status", None, TicketStatus.OPEN.value, created_by_user_id)
        
        # Trigger AI cleanup for description (background task)
        if description:
            try:
                from app.tasks.ticket_description_tasks import cleanup_ticket_description_task
                ticket.description_ai_cleanup_status = "pending"
                task = cleanup_ticket_description_task.delay(
                    ticket_id=ticket.id,
                    tenant_id=self.tenant_id,
                    original_description=description
                )
                ticket.description_ai_cleanup_task_id = task.id
                self.db.commit()
            except Exception as e:
                logger.warning(f"Failed to queue description cleanup for ticket {ticket_number}: {e}")
        
        # Generate Next Point of Action (NPA)
        try:
            from app.services.ticket_npa_service import TicketNPAService
            npa_service = TicketNPAService(self.db, self.tenant_id)
            await npa_service.ensure_npa_exists(ticket)
            self.db.commit()
        except Exception as e:
            logger.warning(f"Failed to generate NPA for ticket {ticket_number}: {e}")
            # Continue without NPA - will be generated later
        
        logger.info(f"Created ticket {ticket_number} for tenant {self.tenant_id}")
        
        return ticket
    
    async def add_comment(
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
        Add a comment to a ticket and trigger AI analysis
        
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
        old_status_obj = None
        if status_change:
            old_status_obj = ticket.status  # Capture old status before change
            old_status = ticket.status.value
            ticket.status = TicketStatus[status_change.upper()]
            self._add_history(ticket, "status", old_status, status_change, author_id)
            
            if ticket.status == TicketStatus.RESOLVED and not ticket.resolved_at:
                ticket.resolved_at = datetime.now(timezone.utc)
            elif ticket.status == TicketStatus.CLOSED and not ticket.closed_at:
                ticket.closed_at = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(comment_obj)
        
        # Update NPA if status changed
        if status_change and old_status_obj:
            try:
                from app.services.ticket_npa_service import TicketNPAService
                npa_service = TicketNPAService(self.db, self.tenant_id)
                await npa_service.auto_update_npa_on_status_change(ticket, old_status_obj, ticket.status)
                self.db.commit()
            except Exception as e:
                logger.warning(f"Failed to update NPA on status change: {e}")
        
        # Ensure NPA exists (if status didn't change or update failed)
        try:
            from app.services.ticket_npa_service import TicketNPAService
            npa_service = TicketNPAService(self.db, self.tenant_id)
            await npa_service.ensure_npa_exists(ticket)
            self.db.commit()
        except Exception as e:
            logger.warning(f"Failed to ensure NPA exists: {e}")
        
        # Trigger AI analysis with full ticket history after comment is added
        try:
            await self._analyze_ticket_with_full_history(ticket)
        except Exception as e:
            logger.warning(f"AI analysis failed after adding comment to ticket {ticket.ticket_number}: {str(e)}")
            # Continue even if AI analysis fails
        
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
            
            # Get prompt from database
            from app.services.ai_prompt_service import AIPromptService
            prompt_service = AIPromptService(self.db, tenant_id=self.tenant_id)
            prompt_obj = await prompt_service.get_prompt(
                category=PromptCategory.KNOWLEDGE_BASE_SEARCH.value,
                tenant_id=self.tenant_id
            )
            
            # For now, skip AI search if no prompt (fallback to keyword search)
            if not prompt_obj:
                prompt_result = None
            else:
                prompt_result = await self.ai_service.generate(
                    prompt=prompt_obj,
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
            Dictionary with ticket statistics including SLA metrics
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
        
        closed_count = self.db.query(func.count(Ticket.id)).filter(
            and_(
                Ticket.tenant_id == self.tenant_id,
                Ticket.status == TicketStatus.CLOSED
            )
        ).scalar() or 0
        
        # SLA Metrics
        from app.models.sla_compliance import SLABreachAlert
        
        tickets_with_sla = self.db.query(func.count(Ticket.id)).filter(
            and_(
                Ticket.tenant_id == self.tenant_id,
                Ticket.sla_policy_id.isnot(None)
            )
        ).scalar() or 0
        
        sla_breached_count = self.db.query(func.count(Ticket.id)).filter(
            and_(
                Ticket.tenant_id == self.tenant_id,
                or_(
                    Ticket.sla_first_response_breached == True,
                    Ticket.sla_resolution_breached == True
                )
            )
        ).scalar() or 0
        
        active_breach_alerts = self.db.query(func.count(SLABreachAlert.id)).filter(
            and_(
                SLABreachAlert.tenant_id == self.tenant_id,
                SLABreachAlert.acknowledged == False
            )
        ).scalar() or 0
        
        # Calculate compliance rate
        sla_compliant_count = tickets_with_sla - sla_breached_count
        sla_compliance_rate = (sla_compliant_count / tickets_with_sla * 100) if tickets_with_sla > 0 else 100.0
        
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
            'closed': closed_count,
            'urgent': urgent_count,
            'sla': {
                'tickets_with_sla': tickets_with_sla,
                'breached_count': sla_breached_count,
                'compliance_rate': round(sla_compliance_rate, 1),
                'active_breach_alerts': active_breach_alerts
            }
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
        # Priority: NULL means match any priority
        # Type: NULL means match any type
        # Customer: NULL means match any customer
        for policy in policies:
            # Skip if priority is specified and doesn't match
            if policy.priority is not None and policy.priority != priority:
                continue
            # Skip if ticket_type is specified and doesn't match
            if policy.ticket_type is not None and policy.ticket_type != ticket_type:
                continue
            # Skip if customer_ids is specified and customer not in list
            if policy.customer_ids and customer_id and customer_id not in policy.customer_ids:
                continue
            
            return policy
        
        # If no matching policy found, return None (no default fallback)
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
        Analyze ticket with AI to improve description and suggest actions (initial creation)
        
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

            # Get prompt from database
            from app.services.ai_prompt_service import AIPromptService
            prompt_service = AIPromptService(self.db, tenant_id=self.tenant_id)
            prompt_obj = await prompt_service.get_prompt(
                category=PromptCategory.CUSTOMER_SERVICE.value,
                tenant_id=self.tenant_id
            )
            
            # Render prompt with variables
            if prompt_obj:
                rendered = prompt_service.render_prompt(prompt_obj, {
                    "ticket_subject": subject,
                    "ticket_description": description,
                    "customer_context": customer_context,
                    "ticket_history": ""  # No history on initial creation
                })
                system_prompt = rendered.get('system_prompt', '')
                user_prompt = rendered.get('user_prompt', prompt)
            else:
                # Fallback to hardcoded prompt if no database prompt
                system_prompt = ''
                user_prompt = prompt
            
            # Generate with AI provider service
            if prompt_obj:
                result = await self.ai_service.generate(
                    prompt=prompt_obj,
                    variables={
                        "ticket_subject": subject,
                        "ticket_description": description,
                        "customer_context": customer_context,
                        "ticket_history": ""
                    },
                    temperature=0.7,
                    max_tokens=1000
                )
            else:
                # Fallback: use hardcoded prompt with system default provider
                # Create a minimal prompt object for fallback
                from app.models.ai_prompt import AIPrompt
                fallback_prompt = AIPrompt(
                    id="fallback",
                    category=PromptCategory.CUSTOMER_SERVICE.value,
                    system_prompt="",
                    user_prompt_template=prompt,
                    model="gpt-4",
                    temperature=0.7,
                    max_tokens=1000
                )
                result = await self.ai_service.generate_with_rendered_prompts(
                    prompt=fallback_prompt,
                    system_prompt="",
                    user_prompt=prompt,
                    temperature=0.7,
                    max_tokens=1000
                )
            
            # Handle result - it could be AIProviderResponse or dict
            content = None
            if result:
                if hasattr(result, 'content'):
                    content = result.content
                elif isinstance(result, dict):
                    content = result.get("content")
            
            if content:
                import json
                try:
                    # Try to parse JSON response
                    content = content.strip()
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
                    lines = content.split("\n")
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
    
    async def _analyze_ticket_with_full_history(
        self,
        ticket: Ticket
    ) -> None:
        """
        Analyze ticket with full history (comments, status changes) and update AI suggestions
        
        This runs after comments are added to provide updated next actions/solutions
        based on the complete ticket context.
        """
        try:
            # Get all comments (excluding system comments)
            comments = self.db.query(TicketComment).filter(
                TicketComment.ticket_id == ticket.id,
                TicketComment.is_system == False
            ).order_by(TicketComment.created_at).all()
            
            # Get all history entries
            history = self.db.query(TicketHistory).filter(
                TicketHistory.ticket_id == ticket.id
            ).order_by(TicketHistory.created_at).all()
            
            # Build ticket history context
            ticket_history = ""
            if comments or history:
                ticket_history = "\n\n=== TICKET HISTORY ===\n"
                
                # Add status changes
                if history:
                    ticket_history += "\nStatus Changes:\n"
                    for hist in history:
                        if hist.field_name == "status":
                            ticket_history += f"- {hist.created_at.strftime('%Y-%m-%d %H:%M')}: Changed from {hist.old_value or 'N/A'} to {hist.new_value}\n"
                
                # Add comments
                if comments:
                    ticket_history += "\nComments:\n"
                    for comment in comments:
                        author = comment.author_name or comment.author_email or (f"User {comment.author_id}" if comment.author_id else "System")
                        internal_note = " [INTERNAL]" if comment.is_internal else ""
                        ticket_history += f"- {comment.created_at.strftime('%Y-%m-%d %H:%M')} by {author}{internal_note}: {comment.comment[:200]}\n"
            
            # Get NPA history (call history - this is critical for AI analysis)
            npa_history = self.db.query(NPAHistory).filter(
                NPAHistory.ticket_id == ticket.id
            ).order_by(NPAHistory.created_at).all()
            
            # Build NPA history context (call history - this is the complete action history)
            npa_history_text = ""
            if npa_history:
                npa_history_text = "\n\n=== NEXT POINT OF ACTION (NPA) HISTORY (CALL HISTORY) ===\n"
                npa_history_text += "This is the complete history of all actions taken on this ticket. Each NPA represents a step in resolving the issue.\n\n"
                for idx, npa in enumerate(npa_history, 1):
                    state_label = npa.npa_state.replace('_', ' ').title()
                    completed_label = f" (COMPLETED: {npa.completed_at.strftime('%Y-%m-%d %H:%M')})" if npa.completed_at else " (ACTIVE)"
                    npa_history_text += f"\n--- NPA #{idx} - {state_label}{completed_label} ---\n"
                    npa_history_text += f"Created: {npa.created_at.strftime('%Y-%m-%d %H:%M')}\n"
                    if npa.assigned_to:
                        npa_history_text += f"Assigned to: {npa.assigned_to.first_name} {npa.assigned_to.last_name}\n"
                    if npa.due_date:
                        npa_history_text += f"Due: {npa.due_date.strftime('%Y-%m-%d %H:%M')}\n"
                    npa_history_text += f"Original Text: {npa.npa_original_text}\n"
                    if npa.npa_cleaned_text and npa.npa_cleaned_text != npa.npa_original_text:
                        npa_history_text += f"Cleaned Text (Customer-Facing): {npa.npa_cleaned_text}\n"
                    if npa.answers_to_questions:
                        npa_history_text += f"Answers to Questions: {npa.answers_to_questions}\n"
                    if npa.completion_notes:
                        npa_history_text += f"Completion Notes: {npa.completion_notes}\n"
                    npa_history_text += "\n"
            
            # Add current NPA if it exists
            if ticket.npa_original_text:
                npa_history_text += "\n--- CURRENT NPA (ACTIVE) ---\n"
                npa_history_text += f"State: {ticket.npa_state.replace('_', ' ').title() if ticket.npa_state else 'Investigation'}\n"
                npa_history_text += f"Original Text: {ticket.npa_original_text}\n"
                if ticket.npa_cleaned_text and ticket.npa_cleaned_text != ticket.npa_original_text:
                    npa_history_text += f"Cleaned Text (Customer-Facing): {ticket.npa_cleaned_text}\n"
                if ticket.next_point_of_action_due_date:
                    npa_history_text += f"Due: {ticket.next_point_of_action_due_date.strftime('%Y-%m-%d %H:%M')}\n"
                npa_history_text += "\n"
            
            # Get customer context if available
            customer_context = ""
            if ticket.customer_id:
                customer = self.db.query(Customer).filter(
                    Customer.id == ticket.customer_id,
                    Customer.tenant_id == self.tenant_id
                ).first()
                if customer:
                    customer_context = f"\n\nCustomer: {customer.company_name}"
                    if customer.business_sector:
                        customer_context += f"\nBusiness Sector: {customer.business_sector.value}"
                    if customer.description:
                        customer_context += f"\nCustomer Description: {customer.description[:200]}"
            
            # Build enhanced prompt with history
            prompt = f"""You are a customer service assistant. Analyze this support ticket with its complete history and:

1. Review the improved description (keep it updated if new information changes the context)
2. Based on ALL ticket history (comments, status changes), suggest NEXT ACTIONS that should be taken NOW
3. Suggest QUESTIONS that should be asked to gather more information or clarify the situation
4. Suggest SOLUTIONS based on the complete ticket history - if enough information is available, provide specific solutions

Original Ticket:
Subject: {ticket.subject}
Original Description: {ticket.original_description or ticket.description}
Current Status: {ticket.status.value}
Priority: {ticket.priority.value}
{customer_context}
{ticket_history}
{npa_history_text}

IMPORTANT:
- Analyze the COMPLETE ticket history AND NPA history (call history) to understand:
  * What actions have been taken (from NPA history)
  * What information has been gathered
  * What questions were asked and answered
  * What the current state is
  * What worked and what didn't work
- Provide NEXT ACTIONS based on what needs to happen next given the current state
- If solutions have been attempted (mentioned in comments), suggest alternative solutions
- If the ticket is progressing well, suggest next steps to resolution
- If information is missing, suggest questions to gather it
- Base your suggestions on the FULL context, not just the initial description

Provide your response in JSON format:
{{
    "improved_description": "The improved description (update if history changes context)",
    "suggestions": {{
        "next_actions": [
            "Specific next action 1 based on ticket history",
            "Specific next action 2 based on current state"
        ],
        "questions": [
            "Question 1 to gather missing information or clarify",
            "Question 2 based on what's been discussed"
        ],
        "solutions": [
            "Solution 1 if enough info is available from history",
            "Solution 2 if applicable based on what's been tried"
        ]
    }}
}}"""

            # Get prompt from database
            from app.services.ai_prompt_service import AIPromptService
            prompt_service = AIPromptService(self.db, tenant_id=self.tenant_id)
            prompt_obj = await prompt_service.get_prompt(
                category=PromptCategory.CUSTOMER_SERVICE.value,
                tenant_id=self.tenant_id
            )
            
            # Render prompt with variables
            if prompt_obj:
                rendered = prompt_service.render_prompt(prompt_obj, {
                    "ticket_subject": ticket.subject,
                    "ticket_description": ticket.original_description or ticket.description,
                    "customer_context": customer_context,
                    "ticket_history": ticket_history,
                    "npa_history": npa_history_text
                })
                system_prompt = rendered.get('system_prompt', '')
                user_prompt = rendered.get('user_prompt', prompt)
            else:
                # Fallback to hardcoded prompt if no database prompt
                system_prompt = ''
                user_prompt = prompt
            
            # Generate with AI provider service
            if prompt_obj:
                result = await self.ai_service.generate(
                    prompt=prompt_obj,
                    variables={
                        "ticket_subject": ticket.subject,
                        "ticket_description": ticket.original_description or ticket.description,
                        "customer_context": customer_context,
                        "ticket_history": ticket_history,
                        "npa_history": npa_history_text
                    },
                    temperature=0.7,
                    max_tokens=2000
                )
            else:
                # Fallback: use hardcoded prompt
                from app.models.ai_prompt import AIPrompt
                fallback_prompt = AIPrompt(
                    id="fallback",
                    category=PromptCategory.CUSTOMER_SERVICE.value,
                    system_prompt="",
                    user_prompt_template=prompt,
                    model="gpt-4",
                    temperature=0.7,
                    max_tokens=2000
                )
                result = await self.ai_service.generate_with_rendered_prompts(
                    prompt=fallback_prompt,
                    system_prompt="",
                    user_prompt=prompt,
                    temperature=0.7,
                    max_tokens=2000
                )
            
            # Handle result - it could be AIProviderResponse or dict
            content = None
            if result:
                if hasattr(result, 'content'):
                    content = result.content
                elif isinstance(result, dict):
                    content = result.get("content")
            
            if content:
                import json
                try:
                    # Try to parse JSON response
                    content = content.strip()
                    # Remove markdown code blocks if present
                    if content.startswith("```"):
                        content = content.split("```")[1]
                        if content.startswith("json"):
                            content = content[4:]
                    content = content.strip()
                    
                    analysis = json.loads(content)
                    
                    # Update ticket with new AI analysis
                    if analysis.get("improved_description"):
                        ticket.improved_description = analysis.get("improved_description")
                    ticket.ai_suggestions = analysis.get("suggestions", {})
                    ticket.ai_analysis_date = datetime.now(timezone.utc)
                    
                    self.db.commit()
                    logger.info(f"Updated AI analysis for ticket {ticket.ticket_number}")
                    
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse AI response for ticket {ticket.ticket_number}: {str(e)}")
                    # Don't update if parsing fails
            
        except Exception as e:
            logger.error(f"Error in AI ticket analysis with history: {str(e)}")
            import traceback
            traceback.print_exc()

