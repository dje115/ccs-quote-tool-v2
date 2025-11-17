#!/usr/bin/env python3
"""
Reporting & Analytics Service
Provides comprehensive reporting and analytics for CRM, quotes, tickets, and revenue
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, extract, desc
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import logging

from app.models.quotes import Quote, QuoteStatus
from app.models.customer import Customer, CustomerStatus
from app.models.lead import Lead, LeadStatus
from app.models.helpdesk import Ticket, TicketStatus
from app.models.sales import SalesActivity
from app.models.support_contract import SupportContract

logger = logging.getLogger(__name__)


class ReportingService:
    """Service for generating reports and analytics"""
    
    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
    
    def get_sales_pipeline_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get sales pipeline report
        
        Returns:
            Dictionary with pipeline metrics
        """
        if not start_date:
            start_date = datetime.now(timezone.utc) - timedelta(days=90)
        if not end_date:
            end_date = datetime.now(timezone.utc)
        
        # Lead counts
        total_leads = self.db.query(func.count(Lead.id)).filter(
            and_(
                Lead.tenant_id == self.tenant_id,
                Lead.created_at >= start_date,
                Lead.created_at <= end_date,
                Lead.is_deleted == False
            )
        ).scalar() or 0
        
        # Prospect counts
        prospects = self.db.query(func.count(Customer.id)).filter(
            and_(
                Customer.tenant_id == self.tenant_id,
                Customer.status == CustomerStatus.PROSPECT,
                Customer.created_at >= start_date,
                Customer.created_at <= end_date,
                Customer.is_deleted == False
            )
        ).scalar() or 0
        
        # Customer counts
        customers = self.db.query(func.count(Customer.id)).filter(
            and_(
                Customer.tenant_id == self.tenant_id,
                Customer.status == CustomerStatus.CUSTOMER,
                Customer.created_at >= start_date,
                Customer.created_at <= end_date,
                Customer.is_deleted == False
            )
        ).scalar() or 0
        
        # Quote metrics
        quotes_sent = self.db.query(func.count(Quote.id)).filter(
            and_(
                Quote.tenant_id == self.tenant_id,
                Quote.status == QuoteStatus.SENT,
                Quote.created_at >= start_date,
                Quote.created_at <= end_date,
                Quote.is_deleted == False
            )
        ).scalar() or 0
        
        quotes_accepted = self.db.query(func.count(Quote.id)).filter(
            and_(
                Quote.tenant_id == self.tenant_id,
                Quote.status == QuoteStatus.ACCEPTED,
                Quote.created_at >= start_date,
                Quote.created_at <= end_date,
                Quote.is_deleted == False
            )
        ).scalar() or 0
        
        # Revenue
        revenue_result = self.db.query(func.sum(Quote.total_amount)).filter(
            and_(
                Quote.tenant_id == self.tenant_id,
                Quote.status == QuoteStatus.ACCEPTED,
                Quote.created_at >= start_date,
                Quote.created_at <= end_date,
                Quote.is_deleted == False
            )
        ).scalar()
        total_revenue = float(revenue_result) if revenue_result else 0.0
        
        # Conversion rates
        conversion_rate = (customers / total_leads * 100) if total_leads > 0 else 0.0
        quote_acceptance_rate = (quotes_accepted / quotes_sent * 100) if quotes_sent > 0 else 0.0
        
        return {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'pipeline': {
                'leads': total_leads,
                'prospects': prospects,
                'customers': customers,
                'conversion_rate': round(conversion_rate, 2)
            },
            'quotes': {
                'sent': quotes_sent,
                'accepted': quotes_accepted,
                'acceptance_rate': round(quote_acceptance_rate, 2)
            },
            'revenue': {
                'total': total_revenue,
                'average_deal_value': round(total_revenue / quotes_accepted, 2) if quotes_accepted > 0 else 0.0
            }
        }
    
    def get_revenue_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        group_by: str = "month"  # day, week, month, year
    ) -> Dict[str, Any]:
        """
        Get revenue report with time series data
        
        Args:
            start_date: Start date
            end_date: End date
            group_by: Grouping period
        
        Returns:
            Dictionary with revenue breakdown
        """
        if not start_date:
            start_date = datetime.now(timezone.utc) - timedelta(days=365)
        if not end_date:
            end_date = datetime.now(timezone.utc)
        
        # Get accepted quotes
        quotes = self.db.query(Quote).filter(
            and_(
                Quote.tenant_id == self.tenant_id,
                Quote.status == QuoteStatus.ACCEPTED,
                Quote.created_at >= start_date,
                Quote.created_at <= end_date,
                Quote.is_deleted == False
            )
        ).all()
        
        # Group by period
        revenue_by_period = {}
        total_revenue = 0.0
        
        for quote in quotes:
            quote_date = quote.created_at
            
            if group_by == "day":
                period_key = quote_date.strftime("%Y-%m-%d")
            elif group_by == "week":
                week_start = quote_date - timedelta(days=quote_date.weekday())
                period_key = week_start.strftime("%Y-W%W")
            elif group_by == "month":
                period_key = quote_date.strftime("%Y-%m")
            elif group_by == "year":
                period_key = quote_date.strftime("%Y")
            else:
                period_key = quote_date.strftime("%Y-%m")
            
            if period_key not in revenue_by_period:
                revenue_by_period[period_key] = {
                    'period': period_key,
                    'revenue': 0.0,
                    'quote_count': 0
                }
            
            revenue_by_period[period_key]['revenue'] += float(quote.total_amount or 0)
            revenue_by_period[period_key]['quote_count'] += 1
            total_revenue += float(quote.total_amount or 0)
        
        # Convert to list and sort
        revenue_data = sorted(revenue_by_period.values(), key=lambda x: x['period'])
        
        return {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'group_by': group_by
            },
            'total_revenue': total_revenue,
            'total_quotes': len(quotes),
            'average_deal_value': round(total_revenue / len(quotes), 2) if quotes else 0.0,
            'revenue_by_period': revenue_data
        }
    
    def get_helpdesk_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get helpdesk performance report
        
        Returns:
            Dictionary with helpdesk metrics
        """
        if not start_date:
            start_date = datetime.now(timezone.utc) - timedelta(days=30)
        if not end_date:
            end_date = datetime.now(timezone.utc)
        
        # Ticket counts by status
        open_tickets = self.db.query(func.count(Ticket.id)).filter(
            and_(
                Ticket.tenant_id == self.tenant_id,
                Ticket.status == TicketStatus.OPEN,
                Ticket.created_at >= start_date,
                Ticket.created_at <= end_date
            )
        ).scalar() or 0
        
        resolved_tickets = self.db.query(func.count(Ticket.id)).filter(
            and_(
                Ticket.tenant_id == self.tenant_id,
                Ticket.status == TicketStatus.RESOLVED,
                Ticket.resolved_at >= start_date,
                Ticket.resolved_at <= end_date
            )
        ).scalar() or 0
        
        closed_tickets = self.db.query(func.count(Ticket.id)).filter(
            and_(
                Ticket.tenant_id == self.tenant_id,
                Ticket.status == TicketStatus.CLOSED,
                Ticket.closed_at >= start_date,
                Ticket.closed_at <= end_date
            )
        ).scalar() or 0
        
        # Average resolution time
        resolved = self.db.query(Ticket).filter(
            and_(
                Ticket.tenant_id == self.tenant_id,
                Ticket.status.in_([TicketStatus.RESOLVED, TicketStatus.CLOSED]),
                Ticket.resolved_at >= start_date,
                Ticket.resolved_at <= end_date
            )
        ).all()
        
        resolution_times = []
        for ticket in resolved:
            if ticket.resolved_at and ticket.created_at:
                resolution_time = (ticket.resolved_at - ticket.created_at).total_seconds() / 3600  # Hours
                resolution_times.append(resolution_time)
        
        avg_resolution_hours = sum(resolution_times) / len(resolution_times) if resolution_times else 0.0
        
        # First response time
        tickets_with_response = self.db.query(Ticket).filter(
            and_(
                Ticket.tenant_id == self.tenant_id,
                Ticket.first_response_at.isnot(None),
                Ticket.created_at >= start_date,
                Ticket.created_at <= end_date
            )
        ).all()
        
        first_response_times = []
        for ticket in tickets_with_response:
            if ticket.first_response_at and ticket.created_at:
                response_time = (ticket.first_response_at - ticket.created_at).total_seconds() / 3600  # Hours
                first_response_times.append(response_time)
        
        avg_first_response_hours = sum(first_response_times) / len(first_response_times) if first_response_times else 0.0
        
        return {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'tickets': {
                'open': open_tickets,
                'resolved': resolved_tickets,
                'closed': closed_tickets,
                'total': open_tickets + resolved_tickets + closed_tickets
            },
            'performance': {
                'avg_resolution_hours': round(avg_resolution_hours, 2),
                'avg_first_response_hours': round(avg_first_response_hours, 2),
                'resolution_rate': round((resolved_tickets + closed_tickets) / (open_tickets + resolved_tickets + closed_tickets) * 100, 2) if (open_tickets + resolved_tickets + closed_tickets) > 0 else 0.0
            }
        }
    
    def get_activity_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get sales activity report
        
        Returns:
            Dictionary with activity metrics
        """
        if not start_date:
            start_date = datetime.now(timezone.utc) - timedelta(days=30)
        if not end_date:
            end_date = datetime.now(timezone.utc)
        
        query = self.db.query(SalesActivity).filter(
            and_(
                SalesActivity.tenant_id == self.tenant_id,
                SalesActivity.activity_date >= start_date,
                SalesActivity.activity_date <= end_date
            )
        )
        
        if user_id:
            query = query.filter(SalesActivity.user_id == user_id)
        
        activities = query.all()
        
        # Group by type
        activities_by_type = {}
        for activity in activities:
            activity_type = activity.activity_type.value if hasattr(activity.activity_type, 'value') else str(activity.activity_type)
            if activity_type not in activities_by_type:
                activities_by_type[activity_type] = 0
            activities_by_type[activity_type] += 1
        
        return {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'total_activities': len(activities),
            'activities_by_type': activities_by_type
        }
    
    def get_customer_lifetime_value(
        self,
        customer_id: str
    ) -> Dict[str, Any]:
        """
        Calculate customer lifetime value
        
        Args:
            customer_id: Customer ID
        
        Returns:
            Dictionary with CLV metrics
        """
        # Get all accepted quotes for customer
        quotes = self.db.query(Quote).filter(
            and_(
                Quote.tenant_id == self.tenant_id,
                Quote.customer_id == customer_id,
                Quote.status == QuoteStatus.ACCEPTED,
                Quote.is_deleted == False
            )
        ).all()
        
        total_revenue = sum(float(q.total_amount or 0) for q in quotes)
        quote_count = len(quotes)
        
        # Get support contracts
        contracts = self.db.query(SupportContract).filter(
            and_(
                SupportContract.tenant_id == self.tenant_id,
                SupportContract.customer_id == customer_id,
                SupportContract.is_active == True
            )
        ).all()
        
        monthly_recurring = sum(float(c.monthly_value or 0) for c in contracts)
        annual_recurring = monthly_recurring * 12
        
        # Get tickets
        tickets = self.db.query(Ticket).filter(
            and_(
                Ticket.tenant_id == self.tenant_id,
                Ticket.customer_id == customer_id
            )
        ).all()
        
        return {
            'customer_id': customer_id,
            'total_revenue': total_revenue,
            'quote_count': quote_count,
            'average_deal_value': round(total_revenue / quote_count, 2) if quote_count > 0 else 0.0,
            'monthly_recurring_revenue': monthly_recurring,
            'annual_recurring_revenue': annual_recurring,
            'ticket_count': len(tickets),
            'customer_since': quotes[0].created_at.isoformat() if quotes else None
        }

