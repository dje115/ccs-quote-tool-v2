#!/usr/bin/env python3
"""
Ticket Pattern Detection Service
Uses AI to identify patterns and similarities in tickets
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.helpdesk import Ticket
from app.services.ai_provider_service import AIProviderService
from app.services.ai_prompt_service import AIPromptService
from app.models.ai_prompt import PromptCategory, AIPrompt
import json
import logging
import uuid

logger = logging.getLogger(__name__)


class TicketPatternDetectionService:
    """Service for detecting patterns in tickets using AI"""
    
    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.ai_service = AIProviderService(db, tenant_id)
        self.prompt_service = AIPromptService(db, tenant_id=tenant_id)
    
    async def detect_customer_patterns(
        self,
        customer_id: str,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Detect patterns in tickets for a specific customer
        
        Returns:
            {
                "patterns": [
                    {
                        "pattern_name": str,
                        "description": str,
                        "ticket_ids": List[str],
                        "common_themes": List[str],
                        "frequency": int,
                        "severity": str
                    }
                ],
                "similar_tickets": [
                    {
                        "ticket_id": str,
                        "ticket_number": str,
                        "subject": str,
                        "similarity_score": float,
                        "similar_ticket_id": str
                    }
                ]
            }
        """
        try:
            # Get all tickets for the customer
            tickets = self.db.query(Ticket).filter(
                Ticket.tenant_id == self.tenant_id,
                Ticket.customer_id == customer_id
            ).order_by(Ticket.created_at.desc()).limit(limit).all()
            
            if len(tickets) < 2:
                return {
                    "patterns": [],
                    "similar_tickets": [],
                    "message": "Not enough tickets to detect patterns"
                }
            
            # Prepare ticket data for AI analysis
            ticket_data = []
            for ticket in tickets:
                ticket_data.append({
                    "id": ticket.id,
                    "ticket_number": ticket.ticket_number,
                    "subject": ticket.subject,
                    "description": ticket.description or "",
                    "status": ticket.status.value if ticket.status else "unknown",
                    "priority": ticket.priority.value if ticket.priority else "medium",
                    "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
                    "tags": ticket.tags or []
                })
            
            # Get AI prompt for pattern detection (database-driven)
            prompt_obj = await self.prompt_service.get_prompt(
                category=PromptCategory.HELPDESK_PATTERN_DETECTION.value,
                tenant_id=self.tenant_id
            )
            
            if prompt_obj:
                # Use database prompt with ticket data as variable
                analysis_prompt = prompt_obj.user_prompt_template
            else:
                # Fallback prompt if not in database
                analysis_prompt = """Analyze the following tickets for a customer and identify:
1. Recurring patterns or themes
2. Similar tickets that might be duplicates or related issues
3. Common problems or root causes
4. Frequency of issues

For each pattern found, provide:
- Pattern name
- Description
- List of ticket IDs that match this pattern
- Common themes
- Frequency count
- Severity (low, medium, high, critical)

For similar tickets, provide pairs with similarity scores.

Return the analysis as JSON with this structure:
{
    "patterns": [
        {
            "pattern_name": "string",
            "description": "string",
            "ticket_ids": ["id1", "id2"],
            "common_themes": ["theme1", "theme2"],
            "frequency": 5,
            "severity": "medium"
        }
    ],
    "similar_tickets": [
        {
            "ticket_id": "id1",
            "similar_ticket_id": "id2",
            "similarity_score": 0.85,
            "reason": "Both tickets about same issue"
        }
    ]
}"""
            
            # Build context for AI
            if prompt_obj:
                # Use database prompt with variables
                try:
                    provider_response = await self.ai_service.generate(
                        prompt=prompt_obj,
                        variables={"ticket_data": json.dumps(ticket_data, indent=2)},
                        temperature=0.3,
                        max_tokens=2000
                    )
                    response_text = provider_response.content
                except Exception as e:
                    logger.error(f"Error calling AI service: {e}", exc_info=True)
                    raise
            else:
                # Fallback: build context manually
                context = f"""Analyze the following tickets for customer pattern detection:

Tickets:
{json.dumps(ticket_data, indent=2)}

{analysis_prompt}"""
                
                # Create a temporary prompt object for fallback
                temp_prompt = AIPrompt(
                    id=str(uuid.uuid4()),
                    tenant_id=self.tenant_id,
                    category=PromptCategory.HELPDESK_PATTERN_DETECTION,
                    name="Pattern Detection",
                    system_prompt="You are an expert helpdesk analyst specializing in identifying patterns and trends in support tickets.",
                    user_prompt_template=context,
                    model="gpt-4",
                    max_tokens=2000
                )
                
                try:
                    ai_response = await self.ai_service.generate_with_rendered_prompts(
                        prompt=temp_prompt,
                        system_prompt="You are an expert helpdesk analyst specializing in identifying patterns and trends in support tickets.",
                        user_prompt=context,
                        model="gpt-4",
                        temperature=0.3,
                        max_tokens=2000,
                        use_responses_api=False
                    )
                    response_text = ai_response.content
                except Exception as e:
                    logger.error(f"Error calling AI service: {e}", exc_info=True)
                    raise
            
            # Parse AI response
            try:
                # Try to find JSON in the response
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    analysis_result = json.loads(json_match.group())
                else:
                    # Try parsing the whole response
                    analysis_result = json.loads(response_text)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse AI response as JSON: {response_text}")
                # Return empty result
                analysis_result = {
                    "patterns": [],
                    "similar_tickets": []
                }
            
            # Validate and enrich results with actual ticket data
            validated_patterns = []
            for pattern in analysis_result.get("patterns", []):
                # Verify ticket IDs exist
                valid_ticket_ids = []
                for ticket_id in pattern.get("ticket_ids", []):
                    if any(t.id == ticket_id for t in tickets):
                        valid_ticket_ids.append(ticket_id)
                
                if valid_ticket_ids:
                    validated_patterns.append({
                        "pattern_name": pattern.get("pattern_name", "Unnamed Pattern"),
                        "description": pattern.get("description", ""),
                        "ticket_ids": valid_ticket_ids,
                        "common_themes": pattern.get("common_themes", []),
                        "frequency": len(valid_ticket_ids),
                        "severity": pattern.get("severity", "medium")
                    })
            
            validated_similar = []
            for similar in analysis_result.get("similar_tickets", []):
                ticket_id = similar.get("ticket_id")
                similar_ticket_id = similar.get("similar_ticket_id")
                
                # Verify both tickets exist
                if any(t.id == ticket_id for t in tickets) and any(t.id == similar_ticket_id for t in tickets):
                    validated_similar.append({
                        "ticket_id": ticket_id,
                        "similar_ticket_id": similar_ticket_id,
                        "similarity_score": float(similar.get("similarity_score", 0.0)),
                        "reason": similar.get("reason", "")
                    })
            
            return {
                "patterns": validated_patterns,
                "similar_tickets": validated_similar,
                "total_tickets_analyzed": len(tickets)
            }
            
        except Exception as e:
            logger.error(f"Error detecting customer patterns: {e}", exc_info=True)
            raise
    
    async def detect_cross_customer_patterns(
        self,
        limit_per_customer: int = 20,
        min_tickets_per_pattern: int = 3
    ) -> Dict[str, Any]:
        """
        Detect patterns across all customers to identify widespread issues
        
        Returns:
            {
                "patterns": [
                    {
                        "pattern_name": str,
                        "description": str,
                        "customer_ids": List[str],
                        "ticket_count": int,
                        "common_themes": List[str],
                        "severity": str
                    }
                ]
            }
        """
        try:
            # Get recent tickets from all customers
            tickets = self.db.query(Ticket).filter(
                Ticket.tenant_id == self.tenant_id
            ).order_by(Ticket.created_at.desc()).limit(500).all()
            
            if len(tickets) < min_tickets_per_pattern:
                return {
                    "patterns": [],
                    "message": "Not enough tickets to detect cross-customer patterns"
                }
            
            # Group tickets by customer
            customer_tickets: Dict[str, List[Ticket]] = {}
            for ticket in tickets:
                if ticket.customer_id:
                    if ticket.customer_id not in customer_tickets:
                        customer_tickets[ticket.customer_id] = []
                    if len(customer_tickets[ticket.customer_id]) < limit_per_customer:
                        customer_tickets[ticket.customer_id].append(ticket)
            
            # Prepare data for AI analysis
            analysis_data = []
            for customer_id, customer_ticket_list in customer_tickets.items():
                for ticket in customer_ticket_list:
                    analysis_data.append({
                        "customer_id": customer_id,
                        "ticket_id": ticket.id,
                        "ticket_number": ticket.ticket_number,
                        "subject": ticket.subject,
                        "description": ticket.description or "",
                        "status": ticket.status.value if ticket.status else "unknown",
                        "priority": ticket.priority.value if ticket.priority else "medium",
                        "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
                        "tags": ticket.tags or []
                    })
            
            # Get AI prompt for pattern detection (database-driven)
            prompt_obj = await self.prompt_service.get_prompt(
                category=PromptCategory.HELPDESK_PATTERN_DETECTION.value,
                tenant_id=self.tenant_id
            )
            
            if prompt_obj:
                # Use database prompt with ticket data as variable
                analysis_prompt = prompt_obj.user_prompt_template
            else:
                # Fallback prompt if not in database
                analysis_prompt = """Analyze tickets across multiple customers to identify:
1. Widespread issues affecting multiple customers
2. Common problems that appear frequently
3. Patterns that suggest systemic issues

For each pattern found, provide:
- Pattern name
- Description
- List of customer IDs affected
- Total ticket count
- Common themes
- Severity (low, medium, high, critical)

Return as JSON:
{
    "patterns": [
        {
            "pattern_name": "string",
            "description": "string",
            "customer_ids": ["id1", "id2"],
            "ticket_count": 10,
            "common_themes": ["theme1"],
            "severity": "high"
        }
    ]
}"""
            
            # Build context for AI
            if prompt_obj:
                # Use database prompt with variables
                try:
                    provider_response = await self.ai_service.generate(
                        prompt=prompt_obj,
                        variables={"ticket_data": json.dumps(analysis_data, indent=2)},
                        temperature=0.3,
                        max_tokens=2000
                    )
                    response_text = provider_response.content
                except Exception as e:
                    logger.error(f"Error calling AI service: {e}", exc_info=True)
                    raise
            else:
                # Fallback: build context manually
                context = f"""Analyze tickets across multiple customers for cross-customer pattern detection:

Tickets (grouped by customer):
{json.dumps(analysis_data, indent=2)}

{analysis_prompt}"""
                
                # Create a temporary prompt object for fallback
                temp_prompt = AIPrompt(
                    id=str(uuid.uuid4()),
                    tenant_id=self.tenant_id,
                    category=PromptCategory.HELPDESK_PATTERN_DETECTION,
                    name="Cross-Customer Pattern Detection",
                    system_prompt="You are an expert helpdesk analyst specializing in identifying widespread patterns and systemic issues across multiple customers.",
                    user_prompt_template=context,
                    model="gpt-4",
                    max_tokens=2000
                )
                
                try:
                    ai_response = await self.ai_service.generate_with_rendered_prompts(
                        prompt=temp_prompt,
                        system_prompt="You are an expert helpdesk analyst specializing in identifying widespread patterns and systemic issues across multiple customers.",
                        user_prompt=context,
                        model="gpt-4",
                        temperature=0.3,
                        max_tokens=2000,
                        use_responses_api=False
                    )
                    response_text = ai_response.content
                except Exception as e:
                    logger.error(f"Error calling AI service: {e}", exc_info=True)
                    raise
            
            # Parse response
            try:
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    analysis_result = json.loads(json_match.group())
                else:
                    analysis_result = json.loads(response_text)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse AI response as JSON: {response_text}")
                analysis_result = {"patterns": []}
            
            # Validate and enrich results
            validated_patterns = []
            for pattern in analysis_result.get("patterns", []):
                customer_ids = pattern.get("customer_ids", [])
                ticket_count = pattern.get("ticket_count", 0)
                
                # Only include patterns that meet minimum threshold
                if ticket_count >= min_tickets_per_pattern and customer_ids:
                    validated_patterns.append({
                        "pattern_name": pattern.get("pattern_name", "Unnamed Pattern"),
                        "description": pattern.get("description", ""),
                        "customer_ids": customer_ids,
                        "ticket_count": ticket_count,
                        "common_themes": pattern.get("common_themes", []),
                        "severity": pattern.get("severity", "medium")
                    })
            
            return {
                "patterns": validated_patterns,
                "total_tickets_analyzed": len(analysis_data),
                "total_customers_analyzed": len(customer_tickets)
            }
            
        except Exception as e:
            logger.error(f"Error detecting cross-customer patterns: {e}", exc_info=True)
            raise

