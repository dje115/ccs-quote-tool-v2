#!/usr/bin/env python3
"""
Lead Intelligence Service

Provides AI-powered lead analysis:
- Opportunity summary and risk assessment
- Outreach plan generation
- Similar leads analysis
- Conversion probability
"""

import logging
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, desc

from app.models.leads import Lead, LeadStatus
from app.models.crm import Customer
from app.models.quotes import Quote, QuoteStatus
from app.services.ai_orchestration_service import AIOrchestrationService
from app.models.ai_prompt import PromptCategory

logger = logging.getLogger(__name__)


class LeadIntelligenceService:
    """
    Service for lead intelligence and analysis
    
    Features:
    - Opportunity summary and risk assessment
    - Outreach plan generation
    - Similar leads analysis
    - Conversion probability
    """
    
    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.orchestration_service = AIOrchestrationService(db, tenant_id=tenant_id)
    
    async def analyze_lead(
        self,
        lead: Lead
    ) -> Dict[str, Any]:
        """
        Analyze lead and generate intelligence summary
        
        Returns:
            Dict with opportunity summary, risk assessment, and recommendations
        """
        try:
            # Build lead context
            context = await self._build_lead_context(lead)
            
            # Generate AI analysis
            response = await self.orchestration_service.generate(
                category=PromptCategory.LEAD_SCORING.value,
                variables={
                    "lead_name": lead.company_name or lead.contact_name or "Unknown",
                    "lead_status": lead.status.value if lead.status else "new",
                    "lead_source": lead.source or "unknown",
                    "lead_description": lead.description or "",
                    "company_info": context.get("company_info", ""),
                    "similar_leads": context.get("similar_leads", ""),
                },
                use_cache=False
            )
            
            # Parse analysis
            analysis = self._parse_lead_analysis(response["content"])
            
            # Calculate conversion probability
            conversion_probability = self._calculate_conversion_probability(lead, context)
            
            return {
                "success": True,
                "opportunity_summary": analysis.get("opportunity_summary", ""),
                "risk_assessment": analysis.get("risks", []),
                "recommendations": analysis.get("recommendations", []),
                "conversion_probability": conversion_probability,
                "next_steps": analysis.get("next_steps", [])
            }
        
        except Exception as e:
            logger.error(f"Error analyzing lead {lead.id}: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def generate_outreach_plan(
        self,
        lead: Lead
    ) -> Dict[str, Any]:
        """
        Generate outreach plan for lead
        
        Returns:
            Dict with suggested outreach sequence (email, call, meeting)
        """
        try:
            context = await self._build_lead_context(lead)
            
            response = await self.orchestration_service.generate(
                category=PromptCategory.LEAD_GENERATION.value,
                variables={
                    "lead_name": lead.company_name or lead.contact_name or "Unknown",
                    "lead_status": lead.status.value if lead.status else "new",
                    "lead_source": lead.source or "unknown",
                    "company_info": context.get("company_info", ""),
                },
                use_cache=False
            )
            
            # Parse outreach plan
            plan = self._parse_outreach_plan(response["content"])
            
            return plan
        
        except Exception as e:
            logger.warning(f"Error generating outreach plan: {e}")
            return {
                "sequence": [],
                "templates": []
            }
    
    async def find_similar_converted_leads(
        self,
        lead: Lead
    ) -> List[Dict[str, Any]]:
        """
        Find similar leads that recently converted
        
        Returns:
            List of similar leads with conversion details
        """
        # Find leads with similar characteristics
        # For now, simple matching by source/status
        # In production, use more sophisticated matching
        
        similar_leads = self.db.query(Lead).filter(
            and_(
                Lead.tenant_id == self.tenant_id,
                Lead.source == lead.source,
                Lead.status == LeadStatus.CONVERTED,
                Lead.id != lead.id
            )
        ).order_by(desc(Lead.updated_at)).limit(5).all()
        
        results = []
        for similar_lead in similar_leads:
            # Get quote that converted this lead
            quote = self.db.query(Quote).filter(
                and_(
                    Quote.lead_id == similar_lead.id,
                    Quote.status == QuoteStatus.ACCEPTED,
                    Quote.tenant_id == self.tenant_id
                )
            ).first()
            
            results.append({
                "lead_id": similar_lead.id,
                "company_name": similar_lead.company_name or similar_lead.contact_name,
                "converted_at": similar_lead.updated_at.isoformat() if similar_lead.updated_at else None,
                "quote_amount": str(quote.total_amount) if quote else None,
                "quote_title": quote.title if quote else None
            })
        
        return results
    
    async def _build_lead_context(self, lead: Lead) -> Dict[str, Any]:
        """Build context for lead analysis"""
        context = {}
        
        # Company info
        company_info = []
        if lead.company_name:
            company_info.append(f"Company: {lead.company_name}")
        if lead.contact_name:
            company_info.append(f"Contact: {lead.contact_name}")
        if lead.email:
            company_info.append(f"Email: {lead.email}")
        if lead.phone:
            company_info.append(f"Phone: {lead.phone}")
        if lead.description:
            company_info.append(f"Description: {lead.description}")
        
        context["company_info"] = "\n".join(company_info)
        
        # Similar leads
        similar_leads = await self.find_similar_converted_leads(lead)
        if similar_leads:
            context["similar_leads"] = "\n".join([
                f"- {sl['company_name']}: Converted with quote {sl['quote_title']}"
                for sl in similar_leads[:3]
            ])
        
        return context
    
    def _calculate_conversion_probability(
        self,
        lead: Lead,
        context: Dict[str, Any]
    ) -> float:
        """
        Calculate conversion probability (0.0-1.0)
        
        Factors:
        - Lead status
        - Lead source quality
        - Similar leads conversion rate
        - Contact information completeness
        """
        probability = 0.3  # Base probability
        
        # Status impact
        if lead.status == LeadStatus.CONVERTED:
            return 1.0
        elif lead.status == LeadStatus.QUALIFIED:
            probability += 0.3
        elif lead.status == LeadStatus.CONTACTED:
            probability += 0.2
        
        # Source quality (simplified)
        high_quality_sources = ["referral", "website", "event"]
        if lead.source in high_quality_sources:
            probability += 0.1
        
        # Contact completeness
        if lead.email and lead.phone:
            probability += 0.1
        
        # Similar leads conversion rate
        similar_leads = context.get("similar_leads", "")
        if similar_leads:
            probability += 0.1
        
        return min(1.0, probability)
    
    def _parse_lead_analysis(self, content: str) -> Dict[str, Any]:
        """Parse lead analysis from AI response"""
        return {
            "opportunity_summary": content[:500],
            "risks": [],
            "recommendations": [],
            "next_steps": []
        }
    
    def _parse_outreach_plan(self, content: str) -> Dict[str, Any]:
        """Parse outreach plan from AI response"""
        return {
            "sequence": [],
            "templates": []
        }

