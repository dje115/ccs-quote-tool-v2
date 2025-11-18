#!/usr/bin/env python3
"""
Metrics Service

Provides metrics and analytics:
- SLA adherence
- AI usage/acceptance
- Lead velocity
- Quote cycle time
- CSAT scores
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, func, desc

from app.models.helpdesk import Ticket, TicketStatus
from app.models.quotes import Quote, QuoteStatus
from app.models.crm import Customer, Lead, LeadStatus
from app.models.sales import SalesActivity

logger = logging.getLogger(__name__)


class MetricsService:
    """
    Service for metrics and analytics
    
    Features:
    - SLA metrics
    - AI usage metrics
    - Lead velocity
    - Quote cycle time
    - CSAT tracking
    """
    
    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
    
    async def get_sla_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get SLA adherence metrics
        
        Returns:
            Dict with SLA statistics
        """
        if not start_date:
            start_date = datetime.now(timezone.utc) - timedelta(days=30)
        if not end_date:
            end_date = datetime.now(timezone.utc)
        
        tickets = self.db.query(Ticket).filter(
            and_(
                Ticket.tenant_id == self.tenant_id,
                Ticket.created_at >= start_date,
                Ticket.created_at <= end_date
            )
        ).all()
        
        total = len(tickets)
        breached = 0
        on_time = 0
        
        for ticket in tickets:
            # Simplified SLA check (24-hour first response)
            if ticket.first_response_at:
                response_time = (ticket.first_response_at - ticket.created_at).total_seconds() / 3600
                if response_time > 24:
                    breached += 1
                else:
                    on_time += 1
        
        adherence_rate = (on_time / total * 100) if total > 0 else 0
        
        return {
            "total_tickets": total,
            "breached": breached,
            "on_time": on_time,
            "adherence_rate_percent": adherence_rate,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
        }
    
    async def get_ai_usage_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get AI usage and acceptance metrics
        
        Returns:
            Dict with AI usage statistics
        """
        if not start_date:
            start_date = datetime.now(timezone.utc) - timedelta(days=30)
        if not end_date:
            end_date = datetime.now(timezone.utc)
        
        # Count tickets with AI suggestions
        tickets_with_ai = self.db.query(Ticket).filter(
            and_(
                Ticket.tenant_id == self.tenant_id,
                Ticket.created_at >= start_date,
                Ticket.created_at <= end_date,
                Ticket.ai_suggestions.isnot(None)
            )
        ).count()
        
        total_tickets = self.db.query(Ticket).filter(
            and_(
                Ticket.tenant_id == self.tenant_id,
                Ticket.created_at >= start_date,
                Ticket.created_at <= end_date
            )
        ).count()
        
        ai_usage_rate = (tickets_with_ai / total_tickets * 100) if total_tickets > 0 else 0
        
        # Count quotes with AI analysis
        quotes_with_ai = self.db.query(Quote).filter(
            and_(
                Quote.tenant_id == self.tenant_id,
                Quote.created_at >= start_date,
                Quote.created_at <= end_date,
                Quote.ai_analysis.isnot(None)
            )
        ).count()
        
        total_quotes = self.db.query(Quote).filter(
            and_(
                Quote.tenant_id == self.tenant_id,
                Quote.created_at >= start_date,
                Quote.created_at <= end_date
            )
        ).count()
        
        quote_ai_usage_rate = (quotes_with_ai / total_quotes * 100) if total_quotes > 0 else 0
        
        return {
            "tickets_with_ai": tickets_with_ai,
            "total_tickets": total_tickets,
            "ticket_ai_usage_rate_percent": ai_usage_rate,
            "quotes_with_ai": quotes_with_ai,
            "total_quotes": total_quotes,
            "quote_ai_usage_rate_percent": quote_ai_usage_rate,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
        }
    
    async def get_lead_velocity_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get lead velocity metrics
        
        Returns:
            Dict with lead velocity statistics
        """
        if not start_date:
            start_date = datetime.now(timezone.utc) - timedelta(days=30)
        if not end_date:
            end_date = datetime.now(timezone.utc)
        
        # Get leads created in period
        leads = self.db.query(Lead).filter(
            and_(
                Lead.tenant_id == self.tenant_id,
                Lead.created_at >= start_date,
                Lead.created_at <= end_date
            )
        ).all()
        
        total_leads = len(leads)
        converted_leads = len([l for l in leads if l.status == LeadStatus.CONVERTED])
        conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0
        
        # Calculate average time to conversion
        converted_with_dates = [
            l for l in leads
            if l.status == LeadStatus.CONVERTED and l.updated_at
        ]
        
        if converted_with_dates:
            conversion_times = [
                (l.updated_at - l.created_at).total_seconds() / 86400  # Days
                for l in converted_with_dates
            ]
            avg_conversion_time_days = sum(conversion_times) / len(conversion_times)
        else:
            avg_conversion_time_days = None
        
        return {
            "total_leads": total_leads,
            "converted_leads": converted_leads,
            "conversion_rate_percent": conversion_rate,
            "average_conversion_time_days": avg_conversion_time_days,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
        }
    
    async def get_quote_cycle_time_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get quote cycle time metrics
        
        Returns:
            Dict with quote cycle time statistics
        """
        if not start_date:
            start_date = datetime.now(timezone.utc) - timedelta(days=30)
        if not end_date:
            end_date = datetime.now(timezone.utc)
        
        quotes = self.db.query(Quote).filter(
            and_(
                Quote.tenant_id == self.tenant_id,
                Quote.created_at >= start_date,
                Quote.created_at <= end_date
            )
        ).all()
        
        # Calculate cycle times for different stages
        draft_to_sent = []
        sent_to_accepted = []
        
        for quote in quotes:
            if quote.status == QuoteStatus.SENT and quote.updated_at:
                draft_time = (quote.updated_at - quote.created_at).total_seconds() / 86400
                draft_to_sent.append(draft_time)
            
            if quote.status == QuoteStatus.ACCEPTED and quote.updated_at:
                sent_time = (quote.updated_at - quote.created_at).total_seconds() / 86400
                sent_to_accepted.append(sent_time)
        
        avg_draft_to_sent = sum(draft_to_sent) / len(draft_to_sent) if draft_to_sent else None
        avg_sent_to_accepted = sum(sent_to_accepted) / len(sent_to_accepted) if sent_to_accepted else None
        
        return {
            "total_quotes": len(quotes),
            "average_draft_to_sent_days": avg_draft_to_sent,
            "average_sent_to_accepted_days": avg_sent_to_accepted,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
        }
    
    async def get_csat_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get Customer Satisfaction (CSAT) metrics
        
        Returns:
            Dict with CSAT statistics
        """
        if not start_date:
            start_date = datetime.now(timezone.utc) - timedelta(days=30)
        if not end_date:
            end_date = datetime.now(timezone.utc)
        
        tickets = self.db.query(Ticket).filter(
            and_(
                Ticket.tenant_id == self.tenant_id,
                Ticket.created_at >= start_date,
                Ticket.created_at <= end_date,
                Ticket.customer_satisfaction_rating.isnot(None)
            )
        ).all()
        
        if not tickets:
            return {
                "total_ratings": 0,
                "average_rating": None,
                "distribution": {}
            }
        
        ratings = [t.customer_satisfaction_rating for t in tickets]
        avg_rating = sum(ratings) / len(ratings)
        
        # Distribution
        distribution = {}
        for rating in range(1, 6):
            distribution[rating] = len([r for r in ratings if r == rating])
        
        return {
            "total_ratings": len(ratings),
            "average_rating": avg_rating,
            "distribution": distribution,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
        }
    
    async def get_dashboard_metrics(
        self
    ) -> Dict[str, Any]:
        """
        Get comprehensive dashboard metrics
        
        Returns:
            Dict with all key metrics
        """
        now = datetime.now(timezone.utc)
        last_30_days = now - timedelta(days=30)
        
        sla_metrics = await self.get_sla_metrics(start_date=last_30_days, end_date=now)
        ai_metrics = await self.get_ai_usage_metrics(start_date=last_30_days, end_date=now)
        lead_metrics = await self.get_lead_velocity_metrics(start_date=last_30_days, end_date=now)
        quote_metrics = await self.get_quote_cycle_time_metrics(start_date=last_30_days, end_date=now)
        csat_metrics = await self.get_csat_metrics(start_date=last_30_days, end_date=now)
        
        return {
            "sla": sla_metrics,
            "ai_usage": ai_metrics,
            "lead_velocity": lead_metrics,
            "quote_cycle_time": quote_metrics,
            "csat": csat_metrics,
            "generated_at": now.isoformat()
        }

