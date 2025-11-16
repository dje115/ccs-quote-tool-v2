#!/usr/bin/env python3
"""
Support Contract Service for managing service contracts, maintenance, and subscriptions
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, extract
from datetime import date, datetime, timedelta
from decimal import Decimal

from app.models.support_contract import (
    SupportContract, ContractRenewal, ContractTemplate,
    ContractType, ContractStatus, RenewalFrequency
)
from app.models.crm import Customer
from app.models.tenant import Tenant


class SupportContractService:
    """Service for managing support contracts"""
    
    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
    
    def generate_contract_number(self) -> str:
        """Generate a unique contract number"""
        # Get tenant slug
        tenant = self.db.query(Tenant).filter(Tenant.id == self.tenant_id).first()
        tenant_slug = tenant.slug if tenant else "TENANT"
        
        # Generate contract number: TENANT-CON-YYYY-#####
        year = datetime.now().year
        counter = 1
        
        while True:
            contract_number = f"{tenant_slug.upper()}-CON-{year}-{str(counter).zfill(5)}"
            existing = self.db.query(SupportContract).filter(
                SupportContract.contract_number == contract_number
            ).first()
            
            if not existing:
                return contract_number
            
            counter += 1
            if counter > 99999:
                raise ValueError("Unable to generate unique contract number")
    
    def create_contract(
        self,
        customer_id: str,
        contract_name: str,
        contract_type: ContractType,
        start_date: date,
        **kwargs
    ) -> Optional[SupportContract]:
        """Create a new support contract"""
        # Verify customer belongs to tenant
        customer = self.db.query(Customer).filter(
            and_(
                Customer.id == customer_id,
                Customer.tenant_id == self.tenant_id
            )
        ).first()
        
        if not customer:
            return None
        
        # Generate contract number
        contract_number = self.generate_contract_number()
        
        # Calculate renewal date if renewal_frequency is provided
        renewal_date = None
        if kwargs.get('renewal_frequency'):
            renewal_date = self._calculate_renewal_date(
                start_date,
                kwargs.get('renewal_frequency')
            )
        
        # Calculate annual_value from monthly_value if not provided
        annual_value = kwargs.get('annual_value')
        if not annual_value and kwargs.get('monthly_value'):
            annual_value = Decimal(str(kwargs['monthly_value'])) * 12
        
        contract = SupportContract(
            tenant_id=self.tenant_id,
            customer_id=customer_id,
            contract_number=contract_number,
            contract_name=contract_name,
            description=kwargs.get('description'),
            contract_type=contract_type,
            status=ContractStatus.DRAFT,
            start_date=start_date,
            end_date=kwargs.get('end_date'),
            renewal_date=renewal_date,
            renewal_frequency=kwargs.get('renewal_frequency'),
            auto_renew=kwargs.get('auto_renew', True),
            monthly_value=kwargs.get('monthly_value'),
            annual_value=annual_value,
            setup_fee=kwargs.get('setup_fee', 0),
            currency=kwargs.get('currency', 'GBP'),
            terms=kwargs.get('terms'),
            sla_level=kwargs.get('sla_level'),
            included_services=kwargs.get('included_services'),
            excluded_services=kwargs.get('excluded_services'),
            support_hours_included=kwargs.get('support_hours_included'),
            renewal_notice_days=kwargs.get('renewal_notice_days', 90),
            cancellation_notice_days=kwargs.get('cancellation_notice_days', 30),
            quote_id=kwargs.get('quote_id'),
            opportunity_id=kwargs.get('opportunity_id'),
            notes=kwargs.get('notes'),
            contract_metadata=kwargs.get('contract_metadata')
        )
        
        self.db.add(contract)
        try:
            self.db.commit()
            self.db.refresh(contract)
            return contract
        except Exception as e:
            self.db.rollback()
            print(f"[SUPPORT CONTRACT SERVICE] Error creating contract: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def get_contract(self, contract_id: str) -> Optional[SupportContract]:
        """Get a support contract"""
        return self.db.query(SupportContract).filter(
            and_(
                SupportContract.id == contract_id,
                SupportContract.tenant_id == self.tenant_id
            )
        ).first()
    
    def list_contracts(
        self,
        customer_id: Optional[str] = None,
        contract_type: Optional[ContractType] = None,
        status: Optional[ContractStatus] = None,
        expiring_soon: Optional[bool] = None,
        days_ahead: int = 90
    ) -> List[SupportContract]:
        """List support contracts with optional filters"""
        query = self.db.query(SupportContract).filter(
            SupportContract.tenant_id == self.tenant_id
        )
        
        if customer_id:
            query = query.filter(SupportContract.customer_id == customer_id)
        
        if contract_type:
            query = query.filter(SupportContract.contract_type == contract_type)
        
        if status:
            query = query.filter(SupportContract.status == status)
        
        if expiring_soon:
            cutoff_date = date.today() + timedelta(days=days_ahead)
            query = query.filter(
                and_(
                    SupportContract.renewal_date <= cutoff_date,
                    SupportContract.renewal_date >= date.today(),
                    SupportContract.status == ContractStatus.ACTIVE
                )
            )
        
        return query.order_by(SupportContract.renewal_date.asc()).all()
    
    def update_contract(
        self,
        contract_id: str,
        **kwargs
    ) -> Optional[SupportContract]:
        """Update a support contract"""
        contract = self.get_contract(contract_id)
        if not contract:
            return None
        
        # Update fields
        updatable_fields = [
            'contract_name', 'description', 'status', 'end_date',
            'renewal_date', 'renewal_frequency', 'auto_renew',
            'monthly_value', 'annual_value', 'setup_fee', 'currency',
            'terms', 'sla_level', 'included_services', 'excluded_services',
            'support_hours_included', 'support_hours_used',
            'renewal_notice_days', 'cancellation_notice_days',
            'notes', 'contract_metadata'
        ]
        
        for field in updatable_fields:
            if field in kwargs and kwargs[field] is not None:
                setattr(contract, field, kwargs[field])
        
        # Recalculate renewal_date if renewal_frequency changed
        if 'renewal_frequency' in kwargs and kwargs['renewal_frequency']:
            if contract.start_date:
                contract.renewal_date = self._calculate_renewal_date(
                    contract.start_date,
                    kwargs['renewal_frequency']
                )
        
        # Recalculate annual_value if monthly_value changed
        if 'monthly_value' in kwargs and kwargs['monthly_value']:
            contract.annual_value = Decimal(str(kwargs['monthly_value'])) * 12
        
        try:
            self.db.commit()
            self.db.refresh(contract)
            return contract
        except Exception as e:
            self.db.rollback()
            print(f"[SUPPORT CONTRACT SERVICE] Error updating contract: {e}")
            raise
    
    def cancel_contract(
        self,
        contract_id: str,
        cancellation_reason: str,
        cancelled_by: str
    ) -> Optional[SupportContract]:
        """Cancel a support contract"""
        contract = self.update_contract(
            contract_id,
            status=ContractStatus.CANCELLED,
            cancellation_reason=cancellation_reason,
            cancelled_at=datetime.now(),
            cancelled_by=cancelled_by
        )
        return contract
    
    def activate_contract(self, contract_id: str) -> Optional[SupportContract]:
        """Activate a support contract"""
        contract = self.update_contract(contract_id, status=ContractStatus.ACTIVE)
        return contract
    
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
    
    def get_contracts_expiring_soon(self, days_ahead: int = 90) -> List[SupportContract]:
        """Get contracts expiring within specified days"""
        cutoff_date = date.today() + timedelta(days=days_ahead)
        return self.db.query(SupportContract).filter(
            and_(
                SupportContract.tenant_id == self.tenant_id,
                SupportContract.renewal_date <= cutoff_date,
                SupportContract.renewal_date >= date.today(),
                SupportContract.status == ContractStatus.ACTIVE,
                SupportContract.auto_renew == True
            )
        ).order_by(SupportContract.renewal_date.asc()).all()
    
    def get_total_recurring_revenue(self) -> Dict[str, Any]:
        """Calculate total recurring revenue from active contracts"""
        active_contracts = self.list_contracts(status=ContractStatus.ACTIVE)
        
        total_monthly = Decimal('0')
        total_annual = Decimal('0')
        
        for contract in active_contracts:
            if contract.monthly_value:
                total_monthly += Decimal(str(contract.monthly_value))
            if contract.annual_value:
                total_annual += Decimal(str(contract.annual_value))
        
        return {
            'total_monthly_recurring_revenue': float(total_monthly),
            'total_annual_recurring_revenue': float(total_annual),
            'active_contracts_count': len(active_contracts)
        }

