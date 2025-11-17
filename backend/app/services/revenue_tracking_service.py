#!/usr/bin/env python3
"""
Revenue Tracking Service
Tracks revenue from support contracts, quotes, and provides forecasting
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, extract, desc
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import logging

from app.models.support_contract import SupportContract
from app.models.quotes import Quote, QuoteStatus
from app.models.crm import Customer

logger = logging.getLogger(__name__)


class RevenueTrackingService:
    """Service for tracking and forecasting revenue"""
    
    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
    
    def get_recurring_revenue(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get recurring revenue from support contracts
        
        Args:
            start_date: Start date for period
            end_date: End date for period
        
        Returns:
            Dictionary with recurring revenue metrics
        """
        if not start_date:
            start_date = datetime.now(timezone.utc).replace(day=1)  # First day of current month
        if not end_date:
            end_date = datetime.now(timezone.utc) + timedelta(days=365)  # Next year
        
        # Get active support contracts
        contracts = self.db.query(SupportContract).filter(
            and_(
                SupportContract.tenant_id == self.tenant_id,
                SupportContract.is_active == True,
                or_(
                    SupportContract.end_date.is_(None),
                    SupportContract.end_date >= start_date
                ),
                SupportContract.start_date <= end_date
            )
        ).all()
        
        monthly_recurring_revenue = Decimal('0.00')
        annual_recurring_revenue = Decimal('0.00')
        contract_count = len(contracts)
        
        for contract in contracts:
            if contract.monthly_value:
                monthly_recurring_revenue += Decimal(str(contract.monthly_value))
        
        annual_recurring_revenue = monthly_recurring_revenue * Decimal('12')
        
        # Calculate contract value over period
        period_revenue = Decimal('0.00')
        for contract in contracts:
            if contract.monthly_value:
                # Calculate months in period
                contract_start = max(contract.start_date, start_date)
                contract_end = min(contract.end_date or end_date, end_date)
                
                if contract_end > contract_start:
                    months = (contract_end.year - contract_start.year) * 12 + (contract_end.month - contract_start.month)
                    if contract_end.day >= contract_start.day:
                        months += 1
                    period_revenue += Decimal(str(contract.monthly_value)) * Decimal(str(months))
        
        return {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'monthly_recurring_revenue': float(monthly_recurring_revenue),
            'annual_recurring_revenue': float(annual_recurring_revenue),
            'period_revenue': float(period_revenue),
            'contract_count': contract_count,
            'average_contract_value': float(monthly_recurring_revenue / Decimal(str(contract_count))) if contract_count > 0 else 0.0
        }
    
    def get_revenue_forecast(
        self,
        months_ahead: int = 12
    ) -> Dict[str, Any]:
        """
        Forecast revenue for the next N months
        
        Args:
            months_ahead: Number of months to forecast
        
        Returns:
            Dictionary with revenue forecast
        """
        now = datetime.now(timezone.utc)
        forecast_data = []
        
        # Get active contracts
        contracts = self.db.query(SupportContract).filter(
            and_(
                SupportContract.tenant_id == self.tenant_id,
                SupportContract.is_active == True
            )
        ).all()
        
        # Get historical quote acceptance rate
        quotes_sent = self.db.query(func.count(Quote.id)).filter(
            and_(
                Quote.tenant_id == self.tenant_id,
                Quote.status == QuoteStatus.SENT,
                Quote.created_at >= now - timedelta(days=90),
                Quote.is_deleted == False
            )
        ).scalar() or 0
        
        quotes_accepted = self.db.query(func.count(Quote.id)).filter(
            and_(
                Quote.tenant_id == self.tenant_id,
                Quote.status == QuoteStatus.ACCEPTED,
                Quote.created_at >= now - timedelta(days=90),
                Quote.is_deleted == False
            )
        ).scalar() or 0
        
        acceptance_rate = (quotes_accepted / quotes_sent * 100) if quotes_sent > 0 else 0.0
        
        # Average deal value
        avg_deal_result = self.db.query(func.avg(Quote.total_amount)).filter(
            and_(
                Quote.tenant_id == self.tenant_id,
                Quote.status == QuoteStatus.ACCEPTED,
                Quote.created_at >= now - timedelta(days=90),
                Quote.is_deleted == False
            )
        ).scalar()
        avg_deal_value = float(avg_deal_result) if avg_deal_result else 0.0
        
        # Calculate recurring revenue per month
        monthly_recurring = Decimal('0.00')
        for contract in contracts:
            if contract.monthly_value:
                monthly_recurring += Decimal(str(contract.monthly_value))
        
        # Forecast each month
        for month_offset in range(months_ahead):
            month_start = (now + timedelta(days=30 * month_offset)).replace(day=1)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            # Recurring revenue (contracts active in this month)
            month_recurring = Decimal('0.00')
            for contract in contracts:
                if contract.monthly_value:
                    if (not contract.start_date or contract.start_date <= month_end) and \
                       (not contract.end_date or contract.end_date >= month_start):
                        month_recurring += Decimal(str(contract.monthly_value))
            
            # Projected one-time revenue (based on historical acceptance rate)
            # Assume same quote volume as last 3 months
            quotes_per_month = quotes_sent / 3 if quotes_sent > 0 else 0
            projected_one_time = Decimal(str(quotes_per_month * (acceptance_rate / 100) * avg_deal_value))
            
            forecast_data.append({
                'month': month_start.strftime('%Y-%m'),
                'recurring_revenue': float(month_recurring),
                'projected_one_time_revenue': float(projected_one_time),
                'total_projected': float(month_recurring + projected_one_time)
            })
        
        total_forecast = sum(item['total_projected'] for item in forecast_data)
        
        return {
            'forecast_months': months_ahead,
            'current_monthly_recurring': float(monthly_recurring),
            'acceptance_rate': round(acceptance_rate, 2),
            'average_deal_value': avg_deal_value,
            'monthly_forecast': forecast_data,
            'total_forecast': total_forecast,
            'annualized_recurring_revenue': float(monthly_recurring * 12)
        }
    
    def get_contract_renewal_revenue(
        self,
        months_ahead: int = 12
    ) -> Dict[str, Any]:
        """
        Get revenue from contracts renewing in the next N months
        
        Args:
            months_ahead: Number of months to look ahead
        
        Returns:
            Dictionary with renewal revenue data
        """
        now = datetime.now(timezone.utc)
        end_date = now + timedelta(days=30 * months_ahead)
        
        # Get contracts expiring in the period
        expiring_contracts = self.db.query(SupportContract).filter(
            and_(
                SupportContract.tenant_id == self.tenant_id,
                SupportContract.is_active == True,
                SupportContract.end_date.isnot(None),
                SupportContract.end_date >= now,
                SupportContract.end_date <= end_date
            )
        ).order_by(SupportContract.end_date).all()
        
        renewal_revenue = Decimal('0.00')
        renewal_by_month = {}
        
        for contract in expiring_contracts:
            if contract.monthly_value:
                renewal_revenue += Decimal(str(contract.monthly_value)) * Decimal('12')  # Annual value
                
                # Group by month
                renewal_month = contract.end_date.strftime('%Y-%m')
                if renewal_month not in renewal_by_month:
                    renewal_by_month[renewal_month] = {
                        'month': renewal_month,
                        'contract_count': 0,
                        'annual_value': 0.0
                    }
                
                renewal_by_month[renewal_month]['contract_count'] += 1
                renewal_by_month[renewal_month]['annual_value'] += float(contract.monthly_value * 12)
        
        return {
            'period_months': months_ahead,
            'total_renewal_value': float(renewal_revenue),
            'contracts_expiring': len(expiring_contracts),
            'renewals_by_month': list(renewal_by_month.values())
        }
    
    def get_customer_revenue_summary(
        self,
        customer_id: str
    ) -> Dict[str, Any]:
        """
        Get revenue summary for a specific customer
        
        Args:
            customer_id: Customer ID
        
        Returns:
            Dictionary with customer revenue metrics
        """
        # Get support contracts
        contracts = self.db.query(SupportContract).filter(
            and_(
                SupportContract.tenant_id == self.tenant_id,
                SupportContract.customer_id == customer_id,
                SupportContract.is_active == True
            )
        ).all()
        
        monthly_recurring = sum(Decimal(str(c.monthly_value or 0)) for c in contracts)
        annual_recurring = monthly_recurring * Decimal('12')
        
        # Get accepted quotes
        quotes = self.db.query(Quote).filter(
            and_(
                Quote.tenant_id == self.tenant_id,
                Quote.customer_id == customer_id,
                Quote.status == QuoteStatus.ACCEPTED,
                Quote.is_deleted == False
            )
        ).all()
        
        total_one_time = sum(Decimal(str(q.total_amount or 0)) for q in quotes)
        
        # Get customer since date
        customer = self.db.query(Customer).filter(
            Customer.id == customer_id,
            Customer.tenant_id == self.tenant_id
        ).first()
        
        return {
            'customer_id': customer_id,
            'customer_name': customer.company_name if customer else None,
            'monthly_recurring_revenue': float(monthly_recurring),
            'annual_recurring_revenue': float(annual_recurring),
            'total_one_time_revenue': float(total_one_time),
            'total_revenue': float(monthly_recurring * 12 + total_one_time),
            'active_contracts': len(contracts),
            'accepted_quotes': len(quotes),
            'customer_since': customer.created_at.isoformat() if customer else None
        }

