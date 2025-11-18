#!/usr/bin/env python3
"""
Trend Detection Service

Detects cross-customer trends:
- Recurring defects/issues
- Quote hurdles
- Emerging churn signals
- Product/service issues
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, func, desc
from collections import Counter

from app.models.helpdesk import Ticket, TicketStatus, TicketPriority
from app.models.quotes import Quote, QuoteStatus
from app.models.crm import Customer
from app.services.ai_orchestration_service import AIOrchestrationService
from app.models.ai_prompt import PromptCategory

logger = logging.getLogger(__name__)


class TrendDetectionService:
    """
    Service for detecting cross-customer trends
    
    Features:
    - Recurring defect detection
    - Quote hurdle identification
    - Churn signal detection
    - Product/service issue tracking
    """
    
    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.orchestration_service = AIOrchestrationService(db, tenant_id=tenant_id)
    
    async def detect_recurring_defects(
        self,
        days_back: int = 30,
        min_occurrences: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Detect recurring defects/issues across customers
        
        Returns:
            List of defect patterns with occurrence counts
        """
        start_date = datetime.now(timezone.utc) - timedelta(days=days_back)
        
        # Get all tickets in period
        tickets = self.db.query(Ticket).filter(
            and_(
                Ticket.tenant_id == self.tenant_id,
                Ticket.created_at >= start_date,
                Ticket.ticket_type.in_(["bug", "technical"])  # Focus on defects
            )
        ).all()
        
        # Group by subject patterns
        subject_patterns = Counter()
        pattern_details = {}
        
        for ticket in tickets:
            # Normalize subject (remove customer-specific info)
            pattern = self._normalize_subject(ticket.subject)
            subject_patterns[pattern] += 1
            
            if pattern not in pattern_details:
                pattern_details[pattern] = {
                    "pattern": pattern,
                    "example_subject": ticket.subject,
                    "ticket_ids": [],
                    "customer_ids": set(),
                    "first_seen": ticket.created_at,
                    "last_seen": ticket.created_at
                }
            
            pattern_details[pattern]["ticket_ids"].append(ticket.id)
            pattern_details[pattern]["customer_ids"].add(ticket.customer_id)
            
            if ticket.created_at < pattern_details[pattern]["first_seen"]:
                pattern_details[pattern]["first_seen"] = ticket.created_at
            if ticket.created_at > pattern_details[pattern]["last_seen"]:
                pattern_details[pattern]["last_seen"] = ticket.created_at
        
        # Filter by minimum occurrences
        recurring_defects = []
        for pattern, count in subject_patterns.items():
            if count >= min_occurrences:
                details = pattern_details[pattern]
                recurring_defects.append({
                    "pattern": pattern,
                    "occurrences": count,
                    "affected_customers": len(details["customer_ids"]),
                    "example_subject": details["example_subject"],
                    "first_seen": details["first_seen"].isoformat(),
                    "last_seen": details["last_seen"].isoformat(),
                    "ticket_ids": details["ticket_ids"][:10],  # Limit to 10 examples
                    "severity": self._calculate_severity(count, len(details["customer_ids"]))
                })
        
        # Sort by occurrences (descending)
        return sorted(recurring_defects, key=lambda x: x["occurrences"], reverse=True)
    
    def _normalize_subject(self, subject: str) -> str:
        """Normalize ticket subject to extract pattern"""
        # Remove customer-specific info, dates, ticket numbers, etc.
        normalized = subject.lower()
        
        # Remove common prefixes/suffixes
        normalized = normalized.replace("ticket", "").replace("issue", "").replace("problem", "")
        
        # Remove numbers (dates, IDs, etc.)
        import re
        normalized = re.sub(r'\d+', '', normalized)
        
        # Remove extra whitespace
        normalized = " ".join(normalized.split())
        
        # Take first 50 chars as pattern
        return normalized[:50].strip()
    
    def _calculate_severity(self, occurrences: int, affected_customers: int) -> str:
        """Calculate severity of recurring defect"""
        if occurrences >= 10 or affected_customers >= 5:
            return "critical"
        elif occurrences >= 5 or affected_customers >= 3:
            return "high"
        elif occurrences >= 3:
            return "medium"
        else:
            return "low"
    
    async def detect_quote_hurdles(
        self,
        days_back: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Detect quote hurdles (common reasons quotes stall/fail)
        
        Returns:
            List of hurdle patterns
        """
        start_date = datetime.now(timezone.utc) - timedelta(days=days_back)
        
        # Get rejected/stalled quotes
        quotes = self.db.query(Quote).filter(
            and_(
                Quote.tenant_id == self.tenant_id,
                Quote.created_at >= start_date,
                Quote.status.in_([QuoteStatus.REJECTED, QuoteStatus.SENT])  # Stalled or rejected
            )
        ).all()
        
        # Analyze patterns
        hurdles = []
        
        # Group by quote type
        quote_types = Counter([q.quote_type for q in quotes if q.quote_type])
        for quote_type, count in quote_types.most_common():
            if count >= 3:  # Minimum threshold
                hurdles.append({
                    "type": "quote_type",
                    "pattern": f"High rejection rate for {quote_type} quotes",
                    "occurrences": count,
                    "severity": "high" if count >= 5 else "medium"
                })
        
        # Analyze time-to-rejection
        rejected_quotes = [q for q in quotes if q.status == QuoteStatus.REJECTED]
        if rejected_quotes:
            avg_time_to_rejection = sum(
                [(q.updated_at - q.created_at).days for q in rejected_quotes if q.updated_at]
            ) / len(rejected_quotes)
            
            if avg_time_to_rejection < 7:  # Rejected within a week
                hurdles.append({
                    "type": "timing",
                    "pattern": "Quotes rejected quickly (average {:.1f} days)".format(avg_time_to_rejection),
                    "occurrences": len(rejected_quotes),
                    "severity": "high"
                })
        
        return hurdles
    
    async def detect_churn_signals(
        self,
        days_back: int = 90
    ) -> List[Dict[str, Any]]:
        """
        Detect emerging churn signals across customers
        
        Returns:
            List of churn signal patterns
        """
        start_date = datetime.now(timezone.utc) - timedelta(days=days_back)
        
        signals = []
        
        # Get customers with high ticket volume increase
        customers = self.db.query(Customer).filter(
            Customer.tenant_id == self.tenant_id
        ).all()
        
        for customer in customers:
            # Get tickets in last 30 days vs previous 30 days
            now = datetime.now(timezone.utc)
            last_30 = self.db.query(Ticket).filter(
                and_(
                    Ticket.customer_id == customer.id,
                    Ticket.created_at >= now - timedelta(days=30)
                )
            ).count()
            
            previous_30 = self.db.query(Ticket).filter(
                and_(
                    Ticket.customer_id == customer.id,
                    Ticket.created_at >= now - timedelta(days=60),
                    Ticket.created_at < now - timedelta(days=30)
                )
            ).count()
            
            if previous_30 > 0:
                increase = (last_30 - previous_30) / previous_30
                if increase > 0.5:  # 50%+ increase
                    signals.append({
                        "type": "ticket_spike",
                        "customer_id": customer.id,
                        "customer_name": customer.company_name,
                        "pattern": f"Ticket volume increased {increase:.0%}",
                        "severity": "high" if increase > 1.0 else "medium"
                    })
            
            # Check for quote rejection spike
            rejected_quotes = self.db.query(Quote).filter(
                and_(
                    Quote.customer_id == customer.id,
                    Quote.status == QuoteStatus.REJECTED,
                    Quote.created_at >= start_date
                )
            ).count()
            
            if rejected_quotes >= 3:
                signals.append({
                    "type": "quote_rejections",
                    "customer_id": customer.id,
                    "customer_name": customer.company_name,
                    "pattern": f"{rejected_quotes} quotes rejected",
                    "severity": "high" if rejected_quotes >= 5 else "medium"
                })
        
        return signals
    
    async def generate_trend_report(
        self,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """
        Generate comprehensive trend report
        
        Returns:
            Dict with all detected trends
        """
        recurring_defects = await self.detect_recurring_defects(days_back=days_back)
        quote_hurdles = await self.detect_quote_hurdles(days_back=days_back)
        churn_signals = await self.detect_churn_signals(days_back=days_back)
        
        # Generate AI summary
        summary = await self._generate_ai_summary(
            recurring_defects,
            quote_hurdles,
            churn_signals
        )
        
        return {
            "period_days": days_back,
            "analysis_date": datetime.now(timezone.utc).isoformat(),
            "recurring_defects": recurring_defects,
            "quote_hurdles": quote_hurdles,
            "churn_signals": churn_signals,
            "summary": summary,
            "critical_issues": [
                d for d in recurring_defects if d["severity"] == "critical"
            ] + [
                s for s in churn_signals if s["severity"] == "high"
            ]
        }
    
    async def _generate_ai_summary(
        self,
        recurring_defects: List[Dict[str, Any]],
        quote_hurdles: List[Dict[str, Any]],
        churn_signals: List[Dict[str, Any]]
    ) -> str:
        """Generate AI summary of trends"""
        try:
            response = await self.orchestration_service.generate(
                category=PromptCategory.CUSTOMER_ANALYSIS.value,  # TODO: Use TREND_ANALYSIS
                variables={
                    "recurring_defects": str(recurring_defects[:5]),  # Limit to top 5
                    "quote_hurdles": str(quote_hurdles),
                    "churn_signals": str(churn_signals[:5]),  # Limit to top 5
                },
                use_cache=False
            )
            
            return response["content"]
        
        except Exception as e:
            logger.warning(f"Error generating trend summary: {e}")
            return f"""
Trend Analysis Summary

Recurring Defects: {len(recurring_defects)} patterns detected
Quote Hurdles: {len(quote_hurdles)} hurdles identified
Churn Signals: {len(churn_signals)} signals detected

Critical Issues: {len([d for d in recurring_defects if d['severity'] == 'critical'])} critical defects
"""

