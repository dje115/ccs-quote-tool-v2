#!/usr/bin/env python3
"""
Quote AI Copilot Service

Provides AI assistance during quote drafting:
- Scope summary and risk analysis
- Clarifying questions
- Recommended upsells
- Cross-sell suggestions
- Executive summaries
- Email copy generation
"""

import logging
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from app.models.quotes import Quote, QuoteStatus
from app.models.crm import Customer
from app.models.product import Product
from app.services.ai_orchestration_service import AIOrchestrationService
from app.models.ai_prompt import PromptCategory

logger = logging.getLogger(__name__)


class QuoteAICopilotService:
    """
    AI copilot service for quote assistance
    
    Features:
    - Scope summary and risk analysis
    - Clarifying questions
    - Upsell recommendations
    - Cross-sell suggestions
    - Executive summaries
    - Email copy generation
    """
    
    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.orchestration_service = AIOrchestrationService(db, tenant_id=tenant_id)
    
    async def analyze_quote_scope(
        self,
        quote: Quote
    ) -> Dict[str, Any]:
        """
        Analyze quote scope and provide summary
        
        Returns:
            Dict with scope summary, risks, and recommendations
        """
        try:
            # Get customer context
            customer = None
            if quote.customer_id:
                customer = self.db.query(Customer).filter(
                    Customer.id == quote.customer_id,
                    Customer.tenant_id == self.tenant_id
                ).first()
            
            # Build quote context
            quote_context = self._build_quote_context(quote, customer)
            
            # Generate analysis
            response = await self.orchestration_service.generate(
                category=PromptCategory.QUOTE_ANALYSIS.value,
                quote_type=quote.quote_type,
                variables={
                    "quote_title": quote.title,
                    "quote_description": quote.description or "",
                    "quote_type": quote.quote_type or "general",
                    "project_details": quote_context.get("project_details", ""),
                    "customer_context": quote_context.get("customer_info", ""),
                    "quote_amount": str(quote.total_amount or 0),
                },
                use_cache=False
            )
            
            # Parse response
            analysis = self._parse_scope_analysis(response["content"])
            
            return {
                "success": True,
                "scope_summary": analysis.get("scope_summary", ""),
                "risks": analysis.get("risks", []),
                "recommendations": analysis.get("recommendations", []),
                "complexity": analysis.get("complexity", "medium")
            }
        
        except Exception as e:
            logger.error(f"Error analyzing quote scope: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def generate_clarifying_questions(
        self,
        quote: Quote
    ) -> List[Dict[str, Any]]:
        """
        Generate clarifying questions for quote
        
        Returns:
            List of question dicts with question text and category
        """
        try:
            quote_context = self._build_quote_context(quote)
            
            response = await self.orchestration_service.generate(
                category=PromptCategory.QUOTE_ANALYSIS.value,
                quote_type=quote.quote_type,
                variables={
                    "quote_title": quote.title,
                    "quote_description": quote.description or "",
                    "quote_type": quote.quote_type or "general",
                    "project_details": quote_context.get("project_details", ""),
                },
                use_cache=False
            )
            
            # Parse questions from response
            questions = self._parse_questions(response["content"])
            
            return questions
        
        except Exception as e:
            logger.warning(f"Error generating clarifying questions: {e}")
            return []
    
    async def suggest_upsells(
        self,
        quote: Quote
    ) -> List[Dict[str, Any]]:
        """
        Suggest upsell opportunities
        
        Returns:
            List of upsell suggestions with product/service recommendations
        """
        try:
            # Get related products/services
            # TODO: Query product catalog based on quote type
            
            quote_context = self._build_quote_context(quote)
            
            response = await self.orchestration_service.generate(
                category=PromptCategory.QUOTE_ANALYSIS.value,
                quote_type=quote.quote_type,
                variables={
                    "quote_title": quote.title,
                    "quote_description": quote.description or "",
                    "quote_type": quote.quote_type or "general",
                    "current_quote_amount": str(quote.total_amount or 0),
                    "project_details": quote_context.get("project_details", ""),
                },
                use_cache=False
            )
            
            # Parse upsell suggestions
            upsells = self._parse_upsells(response["content"])
            
            return upsells
        
        except Exception as e:
            logger.warning(f"Error suggesting upsells: {e}")
            return []
    
    async def suggest_cross_sells(
        self,
        quote: Quote
    ) -> List[Dict[str, Any]]:
        """
        Suggest cross-sell opportunities based on customer industry and similar wins
        
        Returns:
            List of cross-sell suggestions
        """
        try:
            customer = None
            if quote.customer_id:
                customer = self.db.query(Customer).filter(
                    Customer.id == quote.customer_id,
                    Customer.tenant_id == self.tenant_id
                ).first()
            
            # Get similar successful quotes
            similar_quotes = self._get_similar_quotes(quote, customer)
            
            quote_context = self._build_quote_context(quote, customer)
            
            response = await self.orchestration_service.generate(
                category=PromptCategory.QUOTE_ANALYSIS.value,
                quote_type=quote.quote_type,
                variables={
                    "quote_title": quote.title,
                    "quote_description": quote.description or "",
                    "customer_industry": customer.business_sector.value if customer and customer.business_sector else "Unknown",
                    "similar_quotes": str(similar_quotes),
                    "project_details": quote_context.get("project_details", ""),
                },
                use_cache=False
            )
            
            # Parse cross-sell suggestions
            cross_sells = self._parse_cross_sells(response["content"])
            
            return cross_sells
        
        except Exception as e:
            logger.warning(f"Error suggesting cross-sells: {e}")
            return []
    
    async def generate_executive_summary(
        self,
        quote: Quote
    ) -> str:
        """
        Generate executive summary for quote
        
        Returns:
            Executive summary text
        """
        try:
            quote_context = self._build_quote_context(quote)
            
            response = await self.orchestration_service.generate(
                category=PromptCategory.QUOTE_ANALYSIS.value,
                quote_type=quote.quote_type,
                variables={
                    "quote_title": quote.title,
                    "quote_description": quote.description or "",
                    "quote_amount": str(quote.total_amount or 0),
                    "project_details": quote_context.get("project_details", ""),
                },
                use_cache=False
            )
            
            return response["content"]
        
        except Exception as e:
            logger.warning(f"Error generating executive summary: {e}")
            return f"Executive Summary for {quote.title}\n\n{quote.description or 'No description available.'}"
    
    async def generate_email_copy(
        self,
        quote: Quote,
        email_type: str = "send_quote"
    ) -> Dict[str, str]:
        """
        Generate email copy for quote
        
        Args:
            quote: Quote object
            email_type: Type of email ("send_quote", "follow_up", "reminder")
        
        Returns:
            Dict with subject and body
        """
        try:
            customer = None
            if quote.customer_id:
                customer = self.db.query(Customer).filter(
                    Customer.id == quote.customer_id,
                    Customer.tenant_id == self.tenant_id
                ).first()
            
            quote_context = self._build_quote_context(quote, customer)
            
            response = await self.orchestration_service.generate(
                category=PromptCategory.QUOTE_ANALYSIS.value,
                quote_type=quote.quote_type,
                variables={
                    "quote_title": quote.title,
                    "quote_amount": str(quote.total_amount or 0),
                    "customer_name": customer.company_name if customer else "Customer",
                    "email_type": email_type,
                    "project_details": quote_context.get("project_details", ""),
                },
                use_cache=False
            )
            
            # Parse email subject and body
            email_parts = self._parse_email_copy(response["content"])
            
            return {
                "subject": email_parts.get("subject", f"Quote: {quote.title}"),
                "body": email_parts.get("body", response["content"])
            }
        
        except Exception as e:
            logger.warning(f"Error generating email copy: {e}")
            return {
                "subject": f"Quote: {quote.title}",
                "body": f"Please find attached quote for {quote.title}."
            }
    
    def _build_quote_context(
        self,
        quote: Quote,
        customer: Optional[Customer] = None
    ) -> Dict[str, Any]:
        """Build context for quote analysis"""
        context = {}
        
        # Project details
        project_details = []
        if quote.project_title:
            project_details.append(f"Project: {quote.project_title}")
        if quote.project_description:
            project_details.append(f"Description: {quote.project_description}")
        if quote.site_address:
            project_details.append(f"Site: {quote.site_address}")
        if quote.building_type:
            project_details.append(f"Building Type: {quote.building_type}")
        if quote.special_requirements:
            project_details.append(f"Special Requirements: {quote.special_requirements}")
        
        context["project_details"] = "\n".join(project_details)
        
        # Customer info
        if customer:
            context["customer_info"] = f"""
Customer: {customer.company_name}
Industry: {customer.business_sector.value if customer.business_sector else 'Unknown'}
Status: {customer.status.value if customer.status else 'Unknown'}
"""
        
        return context
    
    def _get_similar_quotes(
        self,
        quote: Quote,
        customer: Optional[Customer] = None
    ) -> List[Dict[str, Any]]:
        """Get similar successful quotes"""
        # Query for similar quotes (same type, won status)
        similar = self.db.query(Quote).filter(
            Quote.tenant_id == self.tenant_id,
            Quote.quote_type == quote.quote_type,
            Quote.status == QuoteStatus.ACCEPTED,
            Quote.id != quote.id
        ).limit(5).all()
        
        return [
            {
                "title": q.title,
                "amount": str(q.total_amount or 0),
                "status": q.status.value
            }
            for q in similar
        ]
    
    def _parse_scope_analysis(self, content: str) -> Dict[str, Any]:
        """Parse scope analysis from AI response"""
        # Basic parsing - in production, use structured output
        return {
            "scope_summary": content[:500],
            "risks": [],
            "recommendations": [],
            "complexity": "medium"
        }
    
    def _parse_questions(self, content: str) -> List[Dict[str, Any]]:
        """Parse questions from AI response"""
        questions = []
        lines = content.split("\n")
        
        for line in lines:
            line = line.strip()
            if line and ("?" in line or line.startswith("Q:") or line.startswith("-")):
                question_text = line.lstrip("Q:-* ").strip()
                if question_text:
                    questions.append({
                        "question": question_text,
                        "category": "general"
                    })
        
        return questions[:10]  # Limit to 10 questions
    
    def _parse_upsells(self, content: str) -> List[Dict[str, Any]]:
        """Parse upsell suggestions from AI response"""
        upsells = []
        lines = content.split("\n")
        
        for line in lines:
            line = line.strip()
            if line and (line.startswith("-") or line.startswith("*")):
                suggestion = line.lstrip("-* ").strip()
                if suggestion:
                    upsells.append({
                        "suggestion": suggestion,
                        "estimated_value": None,
                        "confidence": 0.5
                    })
        
        return upsells[:5]  # Limit to 5 upsells
    
    def _parse_cross_sells(self, content: str) -> List[Dict[str, Any]]:
        """Parse cross-sell suggestions from AI response"""
        return self._parse_upsells(content)  # Same format
    
    def _parse_email_copy(self, content: str) -> Dict[str, str]:
        """Parse email subject and body from AI response"""
        lines = content.split("\n")
        subject = None
        body_lines = []
        
        for line in lines:
            if line.lower().startswith("subject:"):
                subject = line.split(":", 1)[1].strip()
            elif line.lower().startswith("body:"):
                # Body starts here
                continue
            else:
                body_lines.append(line)
        
        return {
            "subject": subject or "Quote",
            "body": "\n".join(body_lines).strip()
        }

