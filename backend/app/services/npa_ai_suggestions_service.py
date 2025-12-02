#!/usr/bin/env python3
"""
AI Suggestions Service for NPA
Provides AI-powered suggestions for:
- Agent assignment
- Issue diagnosis
- Troubleshooting steps
"""

import logging
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from app.models.helpdesk import Ticket
from app.services.ai_orchestration_service import AIOrchestrationService
from app.models.ai_prompt import PromptCategory

logger = logging.getLogger(__name__)


class NPAAISuggestionsService:
    """Service for generating AI-powered suggestions for NPA"""
    
    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
    
    async def generate_suggestions(
        self,
        ticket: Ticket
    ) -> Dict[str, Any]:
        """
        Generate AI-powered suggestions for a ticket
        
        Returns:
            Dict with:
            - suggested_agent: Suggested agent to assign to (with reason)
            - issue_diagnosis: What the issue might be
            - troubleshooting_steps: List of troubleshooting steps
        """
        try:
            ai_service = AIOrchestrationService(self.db, self.tenant_id)
            
            # Build ticket context
            context = f"""
            Ticket Information:
            - Subject: {ticket.subject}
            - Description: {ticket.description or ticket.original_description or 'No description'}
            - Type: {ticket.ticket_type.value if hasattr(ticket.ticket_type, 'value') else ticket.ticket_type}
            - Priority: {ticket.priority.value if hasattr(ticket.priority, 'value') else ticket.priority}
            - Status: {ticket.status.value if hasattr(ticket.status, 'value') else ticket.status}
            - Customer: {ticket.customer_id or 'Unknown'}
            """
            
            prompt = f"""
            Based on the following helpdesk ticket, provide AI-powered suggestions:
            
            {context}
            
            Please provide a JSON response with the following structure:
            {{
                "suggested_agent": {{
                    "reason": "Brief explanation of why this agent type/skill is recommended",
                    "skills_needed": ["skill1", "skill2"],
                    "agent_type": "network_specialist" or "general_support" or "technical" etc.
                }},
                "issue_diagnosis": {{
                    "likely_cause": "What is the most likely cause of this issue?",
                    "confidence": 0.85,
                    "alternative_causes": ["alternative1", "alternative2"],
                    "complexity": "simple" or "moderate" or "complex"
                }},
                "troubleshooting_steps": [
                    {{
                        "step": 1,
                        "action": "First action to take",
                        "expected_result": "What to expect",
                        "if_fails": "What to do if this doesn't work"
                    }},
                    {{
                        "step": 2,
                        "action": "Second action",
                        "expected_result": "What to expect",
                        "if_fails": "What to do if this doesn't work"
                    }}
                ]
            }}
            
            Return ONLY valid JSON, no markdown formatting.
            """
            
            # Use the prompt-based generation with variables
            ticket_type_str = ticket.ticket_type.value if hasattr(ticket.ticket_type, 'value') else str(ticket.ticket_type or 'N/A')
            priority_str = ticket.priority.value if hasattr(ticket.priority, 'value') else str(ticket.priority or 'N/A')
            status_str = ticket.status.value if hasattr(ticket.status, 'value') else str(ticket.status or 'N/A')
            
            # Use the generate method with category and variables
            provider_response = await ai_service.generate(
                category=PromptCategory.HELPDESK_NPA_SUGGESTIONS.value,
                variables={
                    "ticket_subject": ticket.subject or '',
                    "ticket_description": ticket.description or ticket.original_description or '',
                    "ticket_type": ticket_type_str,
                    "ticket_priority": priority_str,
                    "ticket_status": status_str,
                    "customer_context": ticket.customer_id or 'Unknown'
                },
                max_tokens=1000
            )
            
            # Extract content from response
            content = provider_response.get("content", "") if isinstance(provider_response, dict) else (
                provider_response.content if hasattr(provider_response, 'content') else str(provider_response)
            )
            
            # Parse JSON response
            import json
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                suggestions = json.loads(json_match.group())
            else:
                suggestions = json.loads(content)
            
            return {
                "success": True,
                "suggestions": suggestions
            }
            
        except Exception as e:
            logger.error(f"Error generating AI suggestions: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "suggestions": {
                    "suggested_agent": {"reason": "Unable to generate suggestion", "skills_needed": [], "agent_type": "general_support"},
                    "issue_diagnosis": {"likely_cause": "Unable to diagnose", "confidence": 0.0, "alternative_causes": [], "complexity": "unknown"},
                    "troubleshooting_steps": []
                }
            }

