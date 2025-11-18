#!/usr/bin/env python3
"""
Activity Timeline Service

Merges activities from multiple sources into chronological timeline:
- Emails
- Calls
- Tickets
- Quotes
- AI-generated notes
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_, union_all, desc

from app.models.crm import Customer
from app.models.sales import SalesActivity, ActivityType
from app.models.helpdesk import Ticket, TicketComment
from app.models.quotes import Quote
from app.models.contacts import Contact

logger = logging.getLogger(__name__)


class ActivityTimelineService:
    """
    Service for building unified activity timeline
    
    Features:
    - Merge activities from multiple sources
    - Chronological ordering
    - Activity type filtering
    - AI-generated summaries
    """
    
    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
    
    async def get_customer_timeline(
        self,
        customer_id: str,
        limit: int = 50,
        activity_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get unified timeline for customer
        
        Args:
            customer_id: Customer ID
            limit: Maximum number of activities to return
            activity_types: Optional list of activity types to filter
        
        Returns:
            List of timeline entries in chronological order (newest first)
        """
        timeline = []
        
        # Get sales activities
        sales_activities = self.db.query(SalesActivity).filter(
            and_(
                SalesActivity.customer_id == customer_id,
                SalesActivity.tenant_id == self.tenant_id
            )
        ).order_by(desc(SalesActivity.activity_date)).limit(limit).all()
        
        for activity in sales_activities:
            if not activity_types or activity.activity_type.value in activity_types:
                timeline.append({
                    "id": activity.id,
                    "type": "sales_activity",
                    "activity_type": activity.activity_type.value,
                    "timestamp": activity.activity_date.isoformat(),
                    "title": activity.subject or f"{activity.activity_type.value.title()} Activity",
                    "description": activity.notes,
                    "user_id": activity.user_id,
                    "contact_id": activity.contact_id,
                    "metadata": {
                        "duration_minutes": activity.duration_minutes,
                        "outcome": activity.outcome.value if activity.outcome else None
                    }
                })
        
        # Get tickets
        tickets = self.db.query(Ticket).filter(
            and_(
                Ticket.customer_id == customer_id,
                Ticket.tenant_id == self.tenant_id
            )
        ).order_by(desc(Ticket.created_at)).limit(limit).all()
        
        for ticket in tickets:
            if not activity_types or "ticket" in activity_types:
                timeline.append({
                    "id": ticket.id,
                    "type": "ticket",
                    "activity_type": "ticket",
                    "timestamp": ticket.created_at.isoformat(),
                    "title": f"Ticket: {ticket.ticket_number}",
                    "description": ticket.subject,
                    "metadata": {
                        "ticket_number": ticket.ticket_number,
                        "status": ticket.status.value,
                        "priority": ticket.priority.value
                    }
                })
        
        # Get ticket comments
        ticket_ids = [t.id for t in tickets]
        if ticket_ids:
            comments = self.db.query(TicketComment).filter(
                TicketComment.ticket_id.in_(ticket_ids)
            ).order_by(desc(TicketComment.created_at)).limit(limit).all()
            
            for comment in comments:
                if not activity_types or "comment" in activity_types:
                    timeline.append({
                        "id": comment.id,
                        "type": "ticket_comment",
                        "activity_type": "comment",
                        "timestamp": comment.created_at.isoformat(),
                        "title": "Ticket Comment",
                        "description": comment.comment,
                        "metadata": {
                            "ticket_id": comment.ticket_id,
                            "is_internal": comment.is_internal
                        }
                    })
        
        # Get quotes
        quotes = self.db.query(Quote).filter(
            and_(
                Quote.customer_id == customer_id,
                Quote.tenant_id == self.tenant_id
            )
        ).order_by(desc(Quote.created_at)).limit(limit).all()
        
        for quote in quotes:
            if not activity_types or "quote" in activity_types:
                timeline.append({
                    "id": quote.id,
                    "type": "quote",
                    "activity_type": "quote",
                    "timestamp": quote.created_at.isoformat(),
                    "title": f"Quote: {quote.quote_number}",
                    "description": quote.title,
                    "metadata": {
                        "quote_number": quote.quote_number,
                        "status": quote.status.value,
                        "total_amount": str(quote.total_amount or 0)
                    }
                })
        
        # Sort by timestamp (newest first)
        timeline.sort(key=lambda x: x["timestamp"], reverse=True)
        
        # Limit results
        return timeline[:limit]
    
    async def generate_daily_summary(
        self,
        customer_id: str,
        date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate daily AI summary of customer activities
        
        Args:
            customer_id: Customer ID
            date: Date to summarize (default: today)
        
        Returns:
            Dict with summary text and key highlights
        """
        if not date:
            date = datetime.now(timezone.utc)
        
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Get activities for the day
        timeline = await self.get_customer_timeline(
            customer_id,
            limit=100
        )
        
        # Filter to date
        day_activities = [
            a for a in timeline
            if start_of_day.isoformat() <= a["timestamp"] <= end_of_day.isoformat()
        ]
        
        # Generate summary
        summary = {
            "date": date.date().isoformat(),
            "total_activities": len(day_activities),
            "activity_types": {},
            "highlights": [],
            "summary_text": ""
        }
        
        # Count activity types
        for activity in day_activities:
            activity_type = activity["activity_type"]
            summary["activity_types"][activity_type] = summary["activity_types"].get(activity_type, 0) + 1
        
        # Generate highlights
        for activity in day_activities[:5]:  # Top 5 activities
            summary["highlights"].append({
                "type": activity["activity_type"],
                "title": activity["title"],
                "timestamp": activity["timestamp"]
            })
        
        # Generate summary text
        summary["summary_text"] = self._generate_summary_text(day_activities)
        
        return summary
    
    def _generate_summary_text(self, activities: List[Dict[str, Any]]) -> str:
        """Generate human-readable summary text"""
        if not activities:
            return "No activities recorded for this day."
        
        activity_counts = {}
        for activity in activities:
            activity_type = activity["activity_type"]
            activity_counts[activity_type] = activity_counts.get(activity_type, 0) + 1
        
        parts = [f"Summary of {len(activities)} activities:"]
        
        for activity_type, count in activity_counts.items():
            parts.append(f"- {count} {activity_type}(s)")
        
        return " ".join(parts)

