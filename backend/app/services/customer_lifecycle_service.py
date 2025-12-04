#!/usr/bin/env python3
"""
Customer Lifecycle Automation Service

Automatically manages customer status transitions based on business rules:
- Lead → Prospect: When opportunity stage = Qualified/Scoping/Proposal Sent
- Prospect → Customer: When opportunity stage = Closed Won OR first invoice created
- Any → Dormant: Last contact > 90 days + no open activities + no active deals
- Dormant → Closed Lost: Dormant > 180 days (auto-close all deals)

All automation can be disabled per customer via lifecycle_auto_managed flag.
"""

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import logging

from app.models.crm import Customer, CustomerStatus
from app.models.opportunities import Opportunity, OpportunityStage

logger = logging.getLogger(__name__)


class CustomerLifecycleService:
    """Service for managing customer lifecycle automation"""
    
    @staticmethod
    async def check_lifecycle_transitions(
        customer_id: str,
        db: AsyncSession,
        tenant_id: str
    ) -> Optional[CustomerStatus]:
        """
        Check if customer lifecycle should be updated based on current state.
        Returns the new status if a transition should occur, None otherwise.
        
        This is called after:
        - Opportunity stage changes
        - Activity creation/update
        - Quote status changes
        - Invoice creation
        """
        # Get customer
        stmt = select(Customer).where(
            and_(
                Customer.id == customer_id,
                Customer.tenant_id == tenant_id,
                Customer.is_deleted == False
            )
        )
        result = await db.execute(stmt)
        customer = result.scalar_one_or_none()
        
        if not customer:
            logger.warning(f"Customer {customer_id} not found for lifecycle check")
            return None
        
        # Skip if automation is disabled
        if not customer.lifecycle_auto_managed:
            logger.debug(f"Lifecycle automation disabled for customer {customer_id}")
            return None
        
        current_status = customer.status
        new_status = None
        
        # Rule 1: Lead → Prospect
        # When opportunity stage = Qualified/Scoping/Proposal Sent
        if current_status == CustomerStatus.LEAD:
            new_status = await CustomerLifecycleService._check_lead_to_prospect(
                customer_id, db, tenant_id
            )
        
        # Rule 2: Prospect → Customer
        # When opportunity stage = Closed Won OR first invoice created
        elif current_status == CustomerStatus.PROSPECT:
            new_status = await CustomerLifecycleService._check_prospect_to_customer(
                customer_id, db, tenant_id
            )
        
        # Rule 3: Any → Dormant
        # Last contact > 90 days + no open activities + no active deals
        elif current_status in [CustomerStatus.LEAD, CustomerStatus.PROSPECT, CustomerStatus.CUSTOMER]:
            new_status = await CustomerLifecycleService._check_to_dormant(
                customer, db, tenant_id
            )
        
        # Rule 4: Dormant → Closed Lost
        # Dormant > 180 days (auto-close all deals)
        elif current_status == CustomerStatus.DORMANT:
            new_status = await CustomerLifecycleService._check_dormant_to_closed_lost(
                customer, db, tenant_id
            )
        
        return new_status
    
    @staticmethod
    async def _check_lead_to_prospect(
        customer_id: str,
        db: AsyncSession,
        tenant_id: str
    ) -> Optional[CustomerStatus]:
        """Check if Lead should transition to Prospect"""
        # Check for opportunities in Qualified/Scoping/Proposal Sent stages
        stmt = select(Opportunity).where(
            and_(
                Opportunity.customer_id == customer_id,
                Opportunity.tenant_id == tenant_id,
                Opportunity.is_deleted == False,
                Opportunity.stage.in_([
                    OpportunityStage.QUALIFIED,
                    OpportunityStage.SCOPING,
                    OpportunityStage.PROPOSAL_SENT
                ])
            )
        )
        result = await db.execute(stmt)
        opportunities = result.scalars().all()
        
        if opportunities:
            logger.info(f"Customer {customer_id} has active opportunities, transitioning Lead → Prospect")
            return CustomerStatus.PROSPECT
        
        return None
    
    @staticmethod
    async def _check_prospect_to_customer(
        customer_id: str,
        db: AsyncSession,
        tenant_id: str
    ) -> Optional[CustomerStatus]:
        """Check if Prospect should transition to Customer"""
        # Check for opportunities in Closed Won stage
        stmt = select(Opportunity).where(
            and_(
                Opportunity.customer_id == customer_id,
                Opportunity.tenant_id == tenant_id,
                Opportunity.is_deleted == False,
                Opportunity.stage == OpportunityStage.CLOSED_WON
            )
        )
        result = await db.execute(stmt)
        opportunities = result.scalars().all()
        
        if opportunities:
            logger.info(f"Customer {customer_id} has Closed Won opportunity, transitioning Prospect → Customer")
            return CustomerStatus.CUSTOMER
        
        # TODO: Check for first invoice creation
        # This will be implemented when invoice system is integrated
        
        return None
    
    @staticmethod
    async def _check_to_dormant(
        customer: Customer,
        db: AsyncSession,
        tenant_id: str
    ) -> Optional[CustomerStatus]:
        """Check if customer should transition to Dormant"""
        # Need last contact date
        if not customer.last_contact_date:
            # If no contact date, use created_at as fallback
            last_contact = customer.created_at
        else:
            last_contact = customer.last_contact_date
        
        # Check if last contact > 90 days ago
        days_since_contact = (datetime.now(timezone.utc) - last_contact).days
        if days_since_contact < 90:
            return None
        
        # Check for active opportunities (not Closed Won/Lost)
        stmt = select(Opportunity).where(
            and_(
                Opportunity.customer_id == customer.id,
                Opportunity.tenant_id == tenant_id,
                Opportunity.is_deleted == False,
                ~Opportunity.stage.in_([
                    OpportunityStage.CLOSED_WON,
                    OpportunityStage.CLOSED_LOST
                ])
            )
        )
        result = await db.execute(stmt)
        active_opportunities = result.scalars().all()
        
        if active_opportunities:
            logger.debug(f"Customer {customer.id} has active opportunities, not transitioning to Dormant")
            return None
        
        # TODO: Check for open activities/tickets
        # This will be implemented when activity system is integrated
        
        logger.info(f"Customer {customer.id} has no contact for {days_since_contact} days, transitioning to Dormant")
        return CustomerStatus.DORMANT
    
    @staticmethod
    async def _check_dormant_to_closed_lost(
        customer: Customer,
        db: AsyncSession,
        tenant_id: str
    ) -> Optional[CustomerStatus]:
        """Check if Dormant customer should transition to Closed Lost"""
        # Need to determine when customer became dormant
        # For now, use last_contact_date or created_at as fallback
        if not customer.last_contact_date:
            dormant_since = customer.created_at
        else:
            dormant_since = customer.last_contact_date
        
        # Check if dormant > 180 days
        days_dormant = (datetime.now(timezone.utc) - dormant_since).days
        if days_dormant < 180:
            return None
        
        # Auto-close all open opportunities
        stmt = select(Opportunity).where(
            and_(
                Opportunity.customer_id == customer.id,
                Opportunity.tenant_id == tenant_id,
                Opportunity.is_deleted == False,
                ~Opportunity.stage.in_([
                    OpportunityStage.CLOSED_WON,
                    OpportunityStage.CLOSED_LOST
                ])
            )
        )
        result = await db.execute(stmt)
        open_opportunities = result.scalars().all()
        
        for opp in open_opportunities:
            opp.stage = OpportunityStage.CLOSED_LOST
            opp.updated_at = datetime.now(timezone.utc)
        
        if open_opportunities:
            logger.info(f"Auto-closed {len(open_opportunities)} opportunities for dormant customer {customer.id}")
        
        logger.info(f"Customer {customer.id} dormant for {days_dormant} days, transitioning to Closed Lost")
        return CustomerStatus.CLOSED_LOST
    
    @staticmethod
    async def update_customer_status(
        customer_id: str,
        new_status: CustomerStatus,
        db: AsyncSession,
        tenant_id: str
    ) -> bool:
        """Update customer status if transition is valid"""
        stmt = select(Customer).where(
            and_(
                Customer.id == customer_id,
                Customer.tenant_id == tenant_id,
                Customer.is_deleted == False
            )
        )
        result = await db.execute(stmt)
        customer = result.scalar_one_or_none()
        
        if not customer:
            return False
        
        old_status = customer.status
        customer.status = new_status
        customer.updated_at = datetime.now(timezone.utc)
        
        await db.commit()
        await db.refresh(customer)
        
        logger.info(f"Customer {customer_id} status updated: {old_status.value} → {new_status.value}")
        return True
    
    @staticmethod
    async def check_dormant_customers_batch(
        db: AsyncSession,
        tenant_id: str,
        batch_size: int = 100
    ) -> int:
        """
        Batch check for customers that should transition to Dormant or Closed Lost.
        This is called by a Celery task on a daily schedule.
        Returns the number of customers updated.
        """
        updated_count = 0
        
        # Get customers that might need dormancy checks
        stmt = select(Customer).where(
            and_(
                Customer.tenant_id == tenant_id,
                Customer.is_deleted == False,
                Customer.lifecycle_auto_managed == True,
                Customer.status.in_([
                    CustomerStatus.LEAD,
                    CustomerStatus.PROSPECT,
                    CustomerStatus.CUSTOMER,
                    CustomerStatus.DORMANT
                ])
            )
        ).limit(batch_size)
        
        result = await db.execute(stmt)
        customers = result.scalars().all()
        
        for customer in customers:
            new_status = await CustomerLifecycleService.check_lifecycle_transitions(
                customer.id, db, tenant_id
            )
            
            if new_status and new_status != customer.status:
                await CustomerLifecycleService.update_customer_status(
                    customer.id, new_status, db, tenant_id
                )
                updated_count += 1
        
        return updated_count




