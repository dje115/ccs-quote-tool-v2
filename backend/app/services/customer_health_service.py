#!/usr/bin/env python3
"""
Customer Health Service

Monitors customer health by analyzing:
- Ticket trends
- Quote patterns
- SLA adherence
- Sentiment analysis
- Churn risk indicators
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, func, desc

from app.models.crm import Customer, CustomerStatus
from app.models.helpdesk import Ticket, TicketStatus, TicketPriority
from app.models.quotes import Quote, QuoteStatus
from app.services.ai_orchestration_service import AIOrchestrationService
from app.models.ai_prompt import PromptCategory

logger = logging.getLogger(__name__)


class CustomerHealthService:
    """
    Service for monitoring customer health
    
    Features:
    - Per-customer health monitoring
    - Issue trend summaries
    - Sentiment tracking
    - Churn risk assessment
    - Health digest generation
    """
    
    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.orchestration_service = AIOrchestrationService(db, tenant_id=tenant_id)
    
    async def analyze_customer_health(
        self,
        customer_id: str,
        days_back: int = 90,
        include_digest: bool = False
    ) -> Dict[str, Any]:
        """
        Analyze customer health and optionally generate health digest
        
        Args:
            customer_id: Customer ID to analyze
            days_back: Number of days to analyze
            include_digest: Whether to generate AI health digest (slow, defaults to False)
        
        Returns:
            Dict with health metrics and optional digest
        """
        customer = self.db.query(Customer).filter(
            Customer.id == customer_id,
            Customer.tenant_id == self.tenant_id
        ).first()
        
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")
        
        # Gather data
        start_date = datetime.now(timezone.utc) - timedelta(days=days_back)
        
        # Get tickets - optimized query with only necessary fields
        tickets = self.db.query(Ticket).filter(
            and_(
                Ticket.customer_id == customer_id,
                Ticket.tenant_id == self.tenant_id,
                Ticket.created_at >= start_date
            )
        ).order_by(desc(Ticket.created_at)).all()
        
        # Get quotes - optimized query with only necessary fields
        quotes = self.db.query(Quote).filter(
            and_(
                Quote.customer_id == customer_id,
                Quote.tenant_id == self.tenant_id,
                Quote.created_at >= start_date
            )
        ).order_by(desc(Quote.created_at)).all()
        
        # Analyze trends
        ticket_trends = self._analyze_ticket_trends(tickets)
        quote_trends = self._analyze_quote_trends(quotes)
        sla_adherence = self._analyze_sla_adherence(tickets)
        
        # Calculate health score
        health_score = self._calculate_health_score(
            ticket_trends,
            quote_trends,
            sla_adherence
        )
        
        # Assess churn risk
        churn_risk = self._assess_churn_risk(
            customer,
            ticket_trends,
            quote_trends,
            sla_adherence
        )
        
        # Build response without AI digest (fast)
        response = {
            "customer_id": customer_id,
            "customer_name": customer.company_name,
            "health_score": health_score,
            "churn_risk": churn_risk,
            "ticket_trends": ticket_trends,
            "quote_trends": quote_trends,
            "sla_adherence": sla_adherence,
            "analysis_date": datetime.now(timezone.utc).isoformat(),
            "period_days": days_back
        }
        
        # Generate AI health digest only if requested (slow)
        if include_digest:
            health_digest = await self._generate_health_digest(
                customer,
                ticket_trends,
                quote_trends,
                sla_adherence,
                health_score,
                churn_risk
            )
            response["health_digest"] = health_digest
        else:
            response["health_digest"] = None
        
        return response
    
    def _analyze_ticket_trends(self, tickets: List[Ticket]) -> Dict[str, Any]:
        """Analyze ticket trends"""
        if not tickets:
            return {
                "total": 0,
                "trend": "stable",
                "recurring_issues": [],
                "average_resolution_time_hours": None
            }
        
        total = len(tickets)
        
        # Calculate trend (comparing last 30 days vs previous 30 days)
        now = datetime.now(timezone.utc)
        last_30_days = [t for t in tickets if (now - t.created_at).days <= 30]
        previous_30_days = [t for t in tickets if 30 < (now - t.created_at).days <= 60]
        
        if len(previous_30_days) == 0:
            trend = "increasing" if len(last_30_days) > 0 else "stable"
        else:
            change = (len(last_30_days) - len(previous_30_days)) / len(previous_30_days)
            if change > 0.2:
                trend = "increasing"
            elif change < -0.2:
                trend = "decreasing"
            else:
                trend = "stable"
        
        # Find recurring issues (tickets with similar subjects)
        recurring_issues = self._find_recurring_issues(tickets)
        
        # Calculate average resolution time
        resolved_tickets = [t for t in tickets if t.resolved_at]
        if resolved_tickets:
            resolution_times = [
                (t.resolved_at - t.created_at).total_seconds() / 3600
                for t in resolved_tickets
            ]
            avg_resolution_time = sum(resolution_times) / len(resolution_times)
        else:
            avg_resolution_time = None
        
        return {
            "total": total,
            "trend": trend,
            "recurring_issues": recurring_issues,
            "average_resolution_time_hours": avg_resolution_time,
            "open_tickets": len([t for t in tickets if t.status == TicketStatus.OPEN]),
            "high_priority_tickets": len([t for t in tickets if t.priority == TicketPriority.HIGH or t.priority == TicketPriority.URGENT])
        }
    
    def _find_recurring_issues(self, tickets: List[Ticket]) -> List[Dict[str, Any]]:
        """Find recurring issues by analyzing ticket subjects"""
        # Simple keyword-based approach
        # In production, use more sophisticated NLP
        
        issue_counts = {}
        for ticket in tickets:
            # Extract keywords from subject
            keywords = ticket.subject.lower().split()
            # Remove common words
            keywords = [k for k in keywords if len(k) > 3 and k not in ["the", "and", "for", "with"]]
            
            # Group similar tickets
            key = " ".join(sorted(keywords[:3]))  # Use first 3 keywords as key
            
            if key not in issue_counts:
                issue_counts[key] = {
                    "pattern": ticket.subject,
                    "count": 0,
                    "ticket_ids": []
                }
            
            issue_counts[key]["count"] += 1
            issue_counts[key]["ticket_ids"].append(ticket.id)
        
        # Return issues that appear 3+ times
        recurring = [
            {
                "pattern": info["pattern"],
                "count": info["count"],
                "ticket_ids": info["ticket_ids"][:5]  # Limit to 5 examples
            }
            for key, info in issue_counts.items()
            if info["count"] >= 3
        ]
        
        return sorted(recurring, key=lambda x: x["count"], reverse=True)
    
    def _analyze_quote_trends(self, quotes: List[Quote]) -> Dict[str, Any]:
        """Analyze quote trends"""
        if not quotes:
            return {
                "total": 0,
                "trend": "stable",
                "win_rate": None,
                "average_value": None
            }
        
        total = len(quotes)
        
        # Calculate win rate
        won_quotes = [q for q in quotes if q.status == QuoteStatus.ACCEPTED]
        win_rate = len(won_quotes) / total if total > 0 else 0
        
        # Calculate average value
        values = [float(q.total_amount or 0) for q in quotes if q.total_amount]
        avg_value = sum(values) / len(values) if values else None
        
        # Calculate trend
        now = datetime.now(timezone.utc)
        last_30_days = [q for q in quotes if (now - q.created_at).days <= 30]
        previous_30_days = [q for q in quotes if 30 < (now - q.created_at).days <= 60]
        
        if len(previous_30_days) == 0:
            trend = "increasing" if len(last_30_days) > 0 else "stable"
        else:
            change = (len(last_30_days) - len(previous_30_days)) / len(previous_30_days)
            if change > 0.2:
                trend = "increasing"
            elif change < -0.2:
                trend = "decreasing"
            else:
                trend = "stable"
        
        return {
            "total": total,
            "trend": trend,
            "win_rate": win_rate,
            "average_value": avg_value,
            "pending_quotes": len([q for q in quotes if q.status == QuoteStatus.SENT]),
            "rejected_quotes": len([q for q in quotes if q.status == QuoteStatus.REJECTED])
        }
    
    def _analyze_sla_adherence(self, tickets: List[Ticket]) -> Dict[str, Any]:
        """Analyze SLA adherence"""
        if not tickets:
            return {
                "adherence_rate": None,
                "breaches": 0,
                "average_response_time_hours": None
            }
        
        # Calculate SLA breaches (simplified - would need SLA policies)
        breaches = 0
        response_times = []
        
        for ticket in tickets:
            if ticket.first_response_at:
                response_time = (ticket.first_response_at - ticket.created_at).total_seconds() / 3600
                response_times.append(response_time)
                
                # Assume 24-hour SLA for first response
                if response_time > 24:
                    breaches += 1
        
        adherence_rate = 1 - (breaches / len(tickets)) if tickets else None
        avg_response_time = sum(response_times) / len(response_times) if response_times else None
        
        return {
            "adherence_rate": adherence_rate,
            "breaches": breaches,
            "average_response_time_hours": avg_response_time
        }
    
    def _calculate_health_score(
        self,
        ticket_trends: Dict[str, Any],
        quote_trends: Dict[str, Any],
        sla_adherence: Dict[str, Any]
    ) -> float:
        """
        Calculate overall health score (0.0-1.0)
        
        Higher score = healthier customer
        """
        score = 0.5  # Base score
        
        # Ticket trends (lower is better)
        if ticket_trends["trend"] == "decreasing":
            score += 0.2
        elif ticket_trends["trend"] == "increasing":
            score -= 0.2
        
        # Quote trends (higher win rate is better)
        if quote_trends["win_rate"]:
            score += quote_trends["win_rate"] * 0.2
        
        # SLA adherence (higher is better)
        if sla_adherence["adherence_rate"]:
            score += sla_adherence["adherence_rate"] * 0.1
        
        # Clamp between 0 and 1
        return max(0.0, min(1.0, score))
    
    def _assess_churn_risk(
        self,
        customer: Customer,
        ticket_trends: Dict[str, Any],
        quote_trends: Dict[str, Any],
        sla_adherence: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess churn risk"""
        risk_factors = []
        risk_score = 0.0
        
        # High ticket volume trend
        if ticket_trends["trend"] == "increasing":
            risk_factors.append("Increasing ticket volume")
            risk_score += 0.2
        
        # Low quote win rate
        if quote_trends["win_rate"] and quote_trends["win_rate"] < 0.3:
            risk_factors.append("Low quote win rate")
            risk_score += 0.2
        
        # SLA breaches
        if sla_adherence["breaches"] > 0:
            risk_factors.append(f"{sla_adherence['breaches']} SLA breaches")
            risk_score += 0.2
        
        # Recurring issues
        if len(ticket_trends["recurring_issues"]) > 0:
            risk_factors.append("Recurring issues detected")
            risk_score += 0.1
        
        # Determine risk level
        if risk_score >= 0.6:
            risk_level = "high"
        elif risk_score >= 0.3:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        return {
            "level": risk_level,
            "score": risk_score,
            "factors": risk_factors,
            "recommended_actions": self._get_churn_mitigation_actions(risk_level, risk_factors)
        }
    
    def _get_churn_mitigation_actions(
        self,
        risk_level: str,
        risk_factors: List[str]
    ) -> List[str]:
        """Get recommended actions to mitigate churn risk"""
        actions = []
        
        if risk_level == "high":
            actions.append("⚠️ HIGH CHURN RISK: Schedule immediate account review meeting")
            actions.append("Assign dedicated account manager")
            actions.append("Create action plan to address recurring issues")
        
        elif risk_level == "medium":
            actions.append("Monitor customer closely")
            actions.append("Proactively reach out to address concerns")
        
        else:
            actions.append("Continue standard relationship management")
        
        return actions
    
    async def _generate_health_digest(
        self,
        customer: Customer,
        ticket_trends: Dict[str, Any],
        quote_trends: Dict[str, Any],
        sla_adherence: Dict[str, Any],
        health_score: float,
        churn_risk: Dict[str, Any]
    ) -> str:
        """Generate AI-powered health digest"""
        try:
            response = await self.orchestration_service.generate(
                category=PromptCategory.CUSTOMER_ANALYSIS.value,  # TODO: Use CUSTOMER_HEALTH_DIGEST
                variables={
                    "customer_name": customer.company_name,
                    "customer_status": customer.status.value if customer.status else "Unknown",
                    "ticket_trends": json.dumps(ticket_trends),
                    "quote_trends": json.dumps(quote_trends),
                    "sla_adherence": json.dumps(sla_adherence),
                    "health_score": health_score,
                    "churn_risk": churn_risk["level"],
                },
                use_cache=False
            )
            
            return response["content"]
        
        except Exception as e:
            logger.warning(f"Error generating health digest: {e}")
            # Return basic digest
            return f"""
Customer Health Summary for {customer.company_name}

Health Score: {health_score:.1%}
Churn Risk: {churn_risk['level'].upper()}

Ticket Trends: {ticket_trends['total']} tickets ({ticket_trends['trend']} trend)
Quote Trends: {quote_trends['total']} quotes, {quote_trends['win_rate']:.1%} win rate
SLA Adherence: {sla_adherence['adherence_rate']:.1% if sla_adherence['adherence_rate'] else 'N/A'}

Risk Factors: {', '.join(churn_risk['factors']) if churn_risk['factors'] else 'None'}
"""

