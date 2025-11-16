#!/usr/bin/env python3
"""
Contract Renewal Service
Handles contract renewal logic, reminders, and CRM integration
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import date, datetime, timedelta
from decimal import Decimal
import logging

from app.models.support_contract import (
    SupportContract, ContractRenewal, ContractStatus, RenewalFrequency
)
from app.models.crm import Customer
from app.models.sales import SalesActivity, ActivityType, ActivityOutcome
from app.models.tenant import Tenant, User
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)


class ContractRenewalService:
    """Service for managing contract renewals"""
    
    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
    
    def check_expiring_contracts(
        self,
        days_ahead: int = 90,
        notice_days: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Check for contracts expiring soon that need renewal reminders
        
        Returns list of contracts with renewal information
        """
        cutoff_date = date.today() + timedelta(days=days_ahead)
        today = date.today()
        
        contracts = self.db.query(SupportContract).filter(
            and_(
                SupportContract.tenant_id == self.tenant_id,
                SupportContract.renewal_date <= cutoff_date,
                SupportContract.renewal_date >= today,
                SupportContract.status == ContractStatus.ACTIVE,
                SupportContract.auto_renew == True
            )
        ).all()
        
        results = []
        for contract in contracts:
            days_until_renewal = (contract.renewal_date - today).days
            
            # Check if reminder should be sent based on notice_days
            should_send_reminder = True
            if notice_days is not None:
                should_send_reminder = days_until_renewal <= notice_days
            
            # Check if reminder already sent recently (within last 7 days)
            recent_reminder = self.db.query(ContractRenewal).filter(
                and_(
                    ContractRenewal.contract_id == contract.id,
                    ContractRenewal.renewal_date == contract.renewal_date,
                    ContractRenewal.reminder_sent_at >= datetime.now() - timedelta(days=7),
                    ContractRenewal.status == "pending"
                )
            ).first()
            
            if recent_reminder:
                should_send_reminder = False
            
            results.append({
                'contract': contract,
                'days_until_renewal': days_until_renewal,
                'should_send_reminder': should_send_reminder,
                'recent_reminder': recent_reminder is not None
            })
        
        return results
    
    def create_renewal_record(
        self,
        contract_id: str,
        renewal_date: date,
        new_end_date: Optional[date] = None,
        new_monthly_value: Optional[float] = None,
        new_annual_value: Optional[float] = None,
        renewal_type: str = "auto"
    ) -> Optional[ContractRenewal]:
        """Create a renewal record for a contract"""
        contract = self.db.query(SupportContract).filter(
            and_(
                SupportContract.id == contract_id,
                SupportContract.tenant_id == self.tenant_id
            )
        ).first()
        
        if not contract:
            return None
        
        # Calculate new_end_date if not provided
        if not new_end_date and contract.renewal_frequency:
            new_end_date = self._calculate_renewal_end_date(
                renewal_date,
                contract.renewal_frequency
            )
        
        renewal = ContractRenewal(
            contract_id=contract_id,
            tenant_id=self.tenant_id,
            renewal_date=renewal_date,
            previous_end_date=contract.end_date,
            new_end_date=new_end_date,
            previous_monthly_value=float(contract.monthly_value) if contract.monthly_value else None,
            new_monthly_value=new_monthly_value,
            previous_annual_value=float(contract.annual_value) if contract.annual_value else None,
            new_annual_value=new_annual_value,
            status="pending",
            renewal_type=renewal_type
        )
        
        self.db.add(renewal)
        try:
            self.db.commit()
            self.db.refresh(renewal)
            return renewal
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating renewal record: {e}")
            raise
    
    def send_renewal_reminder(
        self,
        renewal_id: str,
        sent_to_user_id: str
    ) -> bool:
        """Mark a renewal reminder as sent"""
        renewal = self.db.query(ContractRenewal).filter(
            and_(
                ContractRenewal.id == renewal_id,
                ContractRenewal.tenant_id == self.tenant_id
            )
        ).first()
        
        if not renewal:
            return False
        
        renewal.reminder_sent_at = datetime.now()
        renewal.reminder_sent_to = sent_to_user_id
        
        try:
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating renewal reminder: {e}")
            return False
    
    def approve_renewal(
        self,
        renewal_id: str,
        approved_by_user_id: str
    ) -> Optional[ContractRenewal]:
        """Approve a contract renewal"""
        renewal = self.db.query(ContractRenewal).filter(
            and_(
                ContractRenewal.id == renewal_id,
                ContractRenewal.tenant_id == self.tenant_id
            )
        ).first()
        
        if not renewal:
            return None
        
        renewal.status = "approved"
        renewal.approved_at = datetime.now()
        renewal.approved_by = approved_by_user_id
        
        try:
            self.db.commit()
            self.db.refresh(renewal)
            return renewal
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error approving renewal: {e}")
            return None
    
    def complete_renewal(
        self,
        renewal_id: str
    ) -> Optional[SupportContract]:
        """Complete a contract renewal by updating the contract"""
        renewal = self.db.query(ContractRenewal).filter(
            and_(
                ContractRenewal.id == renewal_id,
                ContractRenewal.tenant_id == self.tenant_id,
                ContractRenewal.status == "approved"
            )
        ).first()
        
        if not renewal:
            return None
        
        contract = renewal.contract
        if not contract:
            return None
        
        # Update contract with new dates and values
        if renewal.new_end_date:
            contract.end_date = renewal.new_end_date
        
        if renewal.new_monthly_value is not None:
            contract.monthly_value = Decimal(str(renewal.new_monthly_value))
        
        if renewal.new_annual_value is not None:
            contract.annual_value = Decimal(str(renewal.new_annual_value))
        
        # Calculate next renewal date
        if contract.renewal_frequency and renewal.new_end_date:
            contract.renewal_date = self._calculate_renewal_date(
                renewal.new_end_date,
                contract.renewal_frequency
            )
        
        # Mark renewal as completed
        renewal.status = "completed"
        renewal.completed_at = datetime.now()
        
        try:
            self.db.commit()
            self.db.refresh(contract)
            return contract
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error completing renewal: {e}")
            return None
    
    def decline_renewal(
        self,
        renewal_id: str,
        reason: str
    ) -> bool:
        """Decline a contract renewal"""
        renewal = self.db.query(ContractRenewal).filter(
            and_(
                ContractRenewal.id == renewal_id,
                ContractRenewal.tenant_id == self.tenant_id
            )
        ).first()
        
        if not renewal:
            return False
        
        renewal.status = "declined"
        renewal.declined_at = datetime.now()
        renewal.declined_reason = reason
        
        # Optionally cancel the contract
        contract = renewal.contract
        if contract:
            contract.status = ContractStatus.CANCELLED
            contract.cancelled_at = datetime.now()
        
        try:
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error declining renewal: {e}")
            return False
    
    def create_crm_task_for_renewal(
        self,
        contract: SupportContract,
        renewal: ContractRenewal,
        assigned_to_user_id: Optional[str] = None
    ) -> Optional[SalesActivity]:
        """Create a CRM task/activity for contract renewal"""
        # Get customer
        customer = contract.customer
        if not customer:
            return None
        
        # Get tenant admin if no user assigned
        if not assigned_to_user_id:
            admin_user = self.db.query(User).filter(
                and_(
                    User.tenant_id == self.tenant_id,
                    User.is_active == True
                )
            ).order_by(User.created_at.asc()).first()
            
            if admin_user:
                assigned_to_user_id = admin_user.id
        
        if not assigned_to_user_id:
            return None
        
        # Create activity
        activity = SalesActivity(
            tenant_id=self.tenant_id,
            customer_id=customer.id,
            user_id=assigned_to_user_id,
            activity_type=ActivityType.TASK,
            title=f"Contract Renewal: {contract.contract_name}",
            description=f"Contract {contract.contract_number} is due for renewal on {renewal.renewal_date.strftime('%Y-%m-%d')}. "
                        f"Days until renewal: {(renewal.renewal_date - date.today()).days}",
            outcome=ActivityOutcome.FOLLOW_UP_REQUIRED,
            due_date=renewal.renewal_date,
            metadata={
                'contract_id': contract.id,
                'contract_number': contract.contract_number,
                'renewal_id': renewal.id,
                'renewal_date': renewal.renewal_date.isoformat(),
                'contract_type': contract.contract_type.value,
                'monthly_value': float(contract.monthly_value) if contract.monthly_value else None,
                'annual_value': float(contract.annual_value) if contract.annual_value else None
            }
        )
        
        self.db.add(activity)
        try:
            self.db.commit()
            self.db.refresh(activity)
            return activity
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating CRM task for renewal: {e}")
            return None
    
    def _calculate_renewal_date(
        self,
        start_date: date,
        renewal_frequency: RenewalFrequency
    ) -> date:
        """Calculate renewal date based on frequency"""
        if renewal_frequency == RenewalFrequency.MONTHLY:
            return start_date + timedelta(days=30)
        elif renewal_frequency == RenewalFrequency.QUARTERLY:
            return start_date + timedelta(days=90)
        elif renewal_frequency == RenewalFrequency.SEMI_ANNUAL:
            return start_date + timedelta(days=180)
        elif renewal_frequency == RenewalFrequency.ANNUAL:
            return start_date + timedelta(days=365)
        elif renewal_frequency == RenewalFrequency.BIENNIAL:
            return start_date + timedelta(days=730)
        elif renewal_frequency == RenewalFrequency.TRIENNIAL:
            return start_date + timedelta(days=1095)
        else:
            return None
    
    def _calculate_renewal_end_date(
        self,
        renewal_date: date,
        renewal_frequency: RenewalFrequency
    ) -> date:
        """Calculate end date for renewal period"""
        return self._calculate_renewal_date(renewal_date, renewal_frequency)

