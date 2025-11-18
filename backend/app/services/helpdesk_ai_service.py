#!/usr/bin/env python3
"""
Helpdesk AI Service

Provides AI-powered analysis and suggestions for helpdesk tickets:
- Auto-analysis on ticket creation/updates
- Actionable chips (Next Actions, Questions, Solutions)
- Ticket rewriting and improvement
- Knowledge base suggestions
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.helpdesk import Ticket, TicketStatus, TicketPriority, TicketType
from app.models.crm import Customer
from app.models.quotes import Quote
from app.models.support_contracts import SupportContract
from app.services.ai_orchestration_service import AIOrchestrationService
from app.models.ai_prompt import PromptCategory

logger = logging.getLogger(__name__)


class HelpdeskAIService:
    """
    AI service for helpdesk ticket analysis and suggestions
    
    Features:
    - Auto-analysis on ticket creation/updates
    - Ticket rewriting and improvement
    - Actionable suggestions (next actions, questions, solutions)
    - Knowledge base recommendations
    - SLA risk assessment
    """
    
    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.orchestration_service = AIOrchestrationService(db, tenant_id=tenant_id)
    
    async def analyze_ticket(
        self,
        ticket: Ticket,
        update_fields: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze ticket and generate AI suggestions
        
        Args:
            ticket: Ticket object to analyze
            update_fields: Optional dict of fields being updated (for incremental analysis)
        
        Returns:
            Dict with:
            - improved_description: AI-improved description
            - suggestions: Dict with next_actions, questions, solutions
            - ticket_type_suggestion: Suggested ticket type
            - priority_suggestion: Suggested priority
            - sla_risk: SLA breach risk assessment
        """
        try:
            # Gather context
            context = await self._build_ticket_context(ticket, update_fields)
            
            # Get AI prompt for ticket analysis
            # TODO: Add TICKET_ANALYSIS to PromptCategory enum
            # For now, use CUSTOMER_ANALYSIS as fallback
            try:
                response = await self.orchestration_service.generate(
                    category=PromptCategory.CUSTOMER_ANALYSIS.value,  # TODO: Use TICKET_ANALYSIS
                    variables={
                        "ticket_subject": ticket.subject,
                        "ticket_description": ticket.description or ticket.original_description or "",
                        "ticket_type": ticket.ticket_type.value if ticket.ticket_type else "support",
                        "ticket_priority": ticket.priority.value if ticket.priority else "medium",
                        "customer_context": context.get("customer_info", ""),
                        "related_quote_context": context.get("quote_info", ""),
                        "related_contract_context": context.get("contract_info", ""),
                        "recent_tickets": context.get("recent_tickets", ""),
                    },
                    use_cache=False  # Don't cache ticket analysis (too specific)
                )
                
                ai_content = response["content"]
                
                # Parse AI response
                analysis = self._parse_ai_response(ai_content)
                
                # Generate improved description
                improved_description = await self._improve_description(
                    ticket.description or ticket.original_description or "",
                    context
                )
                
                return {
                    "success": True,
                    "improved_description": improved_description,
                    "suggestions": analysis.get("suggestions", {
                        "next_actions": [],
                        "questions": [],
                        "solutions": []
                    }),
                    "ticket_type_suggestion": analysis.get("ticket_type"),
                    "priority_suggestion": analysis.get("priority"),
                    "sla_risk": analysis.get("sla_risk", "low"),
                    "auto_assign_suggestion": analysis.get("auto_assign"),
                    "auto_respond_suggestion": analysis.get("auto_respond"),
                    "confidence": analysis.get("confidence", 0.5)
                }
            
            except ValueError as e:
                # Prompt not found - return basic analysis
                logger.warning(f"AI prompt not found for ticket analysis: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "improved_description": ticket.description,
                    "suggestions": {
                        "next_actions": [],
                        "questions": [],
                        "solutions": []
                    }
                }
        
        except Exception as e:
            logger.error(f"Error analyzing ticket {ticket.id}: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "improved_description": ticket.description,
                "suggestions": {
                    "next_actions": [],
                    "questions": [],
                    "solutions": []
                }
            }
    
    async def _build_ticket_context(
        self,
        ticket: Ticket,
        update_fields: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build context for AI analysis"""
        context = {}
        
        # Customer context
        if ticket.customer_id:
            customer = self.db.query(Customer).filter(
                Customer.id == ticket.customer_id,
                Customer.tenant_id == self.tenant_id
            ).first()
            
            if customer:
                context["customer_info"] = f"""
Customer: {customer.company_name}
Status: {customer.status.value if customer.status else 'Unknown'}
Sector: {customer.business_sector.value if customer.business_sector else 'Unknown'}
Lead Score: {customer.lead_score or 'N/A'}
"""
                if customer.description:
                    context["customer_info"] += f"Description: {customer.description[:200]}...\n"
        
        # Related quote context
        if ticket.related_quote_id:
            quote = self.db.query(Quote).filter(
                Quote.id == ticket.related_quote_id,
                Quote.tenant_id == self.tenant_id
            ).first()
            
            if quote:
                context["quote_info"] = f"""
Related Quote: {quote.quote_number} - {quote.title}
Status: {quote.status.value if quote.status else 'Unknown'}
Total Amount: £{quote.total_amount or 0}
"""
        
        # Related contract context
        if ticket.related_contract_id:
            contract = self.db.query(SupportContract).filter(
                SupportContract.id == ticket.related_contract_id,
                SupportContract.tenant_id == self.tenant_id
            ).first()
            
            if contract:
                context["contract_info"] = f"""
Related Contract: {contract.contract_number or contract.id}
Status: {contract.status.value if contract.status else 'Unknown'}
"""
        
        # Recent tickets for same customer
        if ticket.customer_id:
            recent_tickets = self.db.query(Ticket).filter(
                Ticket.customer_id == ticket.customer_id,
                Ticket.tenant_id == self.tenant_id,
                Ticket.id != ticket.id
            ).order_by(Ticket.created_at.desc()).limit(5).all()
            
            if recent_tickets:
                context["recent_tickets"] = "\n".join([
                    f"- {t.ticket_number}: {t.subject} ({t.status.value})"
                    for t in recent_tickets
                ])
        
        return context
    
    async def _improve_description(
        self,
        original_description: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Improve ticket description using AI
        
        This creates a professional, clear description suitable for customer portal
        """
        if not original_description:
            return ""
        
        try:
            # Use AI to improve description
            # TODO: Add TICKET_REWRITE to PromptCategory
            response = await self.orchestration_service.generate(
                category=PromptCategory.CUSTOMER_ANALYSIS.value,  # TODO: Use TICKET_REWRITE
                variables={
                    "original_description": original_description,
                    "customer_context": context.get("customer_info", ""),
                },
                use_cache=False
            )
            
            # Extract improved description from response
            # For now, return the AI content as improved description
            # In production, parse structured response
            return response["content"][:5000]  # Limit length
        
        except Exception as e:
            logger.warning(f"Error improving description: {e}")
            return original_description
    
    def _parse_ai_response(self, ai_content: str) -> Dict[str, Any]:
        """
        Parse AI response into structured format
        
        Expected format (JSON or structured text):
        {
            "suggestions": {
                "next_actions": ["Action 1", "Action 2"],
                "questions": ["Question 1", "Question 2"],
                "solutions": ["Solution 1", "Solution 2"]
            },
            "ticket_type": "bug",
            "priority": "high",
            "sla_risk": "medium",
            "auto_assign": true,
            "auto_respond": false,
            "confidence": 0.8
        }
        """
        try:
            # Try to parse as JSON first
            if ai_content.strip().startswith("{"):
                return json.loads(ai_content)
            
            # Otherwise, try to extract structured data from text
            # This is a basic parser - in production, use more sophisticated parsing
            analysis = {
                "suggestions": {
                    "next_actions": [],
                    "questions": [],
                    "solutions": []
                },
                "confidence": 0.5
            }
            
            # Look for structured sections
            lines = ai_content.split("\n")
            current_section = None
            
            for line in lines:
                line_lower = line.lower().strip()
                
                if "next action" in line_lower or "action" in line_lower:
                    current_section = "next_actions"
                elif "question" in line_lower:
                    current_section = "questions"
                elif "solution" in line_lower:
                    current_section = "solutions"
                elif line.strip().startswith("-") or line.strip().startswith("*"):
                    if current_section:
                        item = line.strip().lstrip("-* ").strip()
                        if item:
                            analysis["suggestions"][current_section].append(item)
            
            return analysis
        
        except Exception as e:
            logger.warning(f"Error parsing AI response: {e}")
            return {
                "suggestions": {
                    "next_actions": [],
                    "questions": [],
                    "solutions": []
                },
                "confidence": 0.3
            }
    
    async def suggest_knowledge_base_articles(
        self,
        ticket: Ticket,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Suggest relevant knowledge base articles
        
        Returns:
            List of article dicts with id, title, summary, relevance_score
        """
        # TODO: Implement knowledge base search using AI
        # For now, return empty list
        return []
    
    async def generate_auto_response(
        self,
        ticket: Ticket,
        response_type: str = "acknowledgment"
    ) -> Optional[str]:
        """
        Generate auto-response for ticket
        
        Args:
            ticket: Ticket object
            response_type: Type of response ("acknowledgment", "solution", "question")
        
        Returns:
            Generated response text or None
        """
        try:
            context = await self._build_ticket_context(ticket)
            
            response = await self.orchestration_service.generate(
                category=PromptCategory.CUSTOMER_ANALYSIS.value,  # TODO: Use TICKET_AUTO_RESPONSE
                variables={
                    "ticket_subject": ticket.subject,
                    "ticket_description": ticket.description or "",
                    "response_type": response_type,
                    "customer_context": context.get("customer_info", ""),
                },
                use_cache=False
            )
            
            return response["content"]
        
        except Exception as e:
            logger.warning(f"Error generating auto-response: {e}")
            return None

