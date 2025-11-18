#!/usr/bin/env python3
"""
Customer Portal API Endpoints
Public-facing endpoints for customers to view their contracts and manage tickets
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import Optional, List
from datetime import datetime, timezone
import uuid
import asyncio

from app.core.database import get_async_db, SessionLocal
from app.models.support_contract import SupportContract, ContractStatus
from app.models.helpdesk import Ticket, TicketStatus
from app.models.crm import Customer
from app.models.quotes import Quote, QuoteStatus
from app.models.orders import Order
from app.services.support_contract_service import SupportContractService
from app.services.helpdesk_service import HelpdeskService
from app.services.reporting_service import ReportingService

router = APIRouter(prefix="/customer-portal", tags=["Customer Portal"])


async def get_customer_by_token(
    x_customer_token: Optional[str] = Header(None, alias="X-Customer-Token"),
    db: AsyncSession = Depends(get_async_db)
) -> Customer:
    """
    Authenticate customer using portal access token
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    if not x_customer_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Customer token required"
        )
    
    # Find customer by portal access token
    stmt = select(Customer).where(
        and_(
            Customer.portal_access_token == x_customer_token,
            Customer.portal_access_enabled == True,
            Customer.is_deleted == False
        )
    )
    result = await db.execute(stmt)
    customer = result.scalars().first()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid customer token or portal access disabled"
        )
    
    return customer


@router.get("/contracts")
async def get_customer_contracts(
    customer: Customer = Depends(get_customer_by_token),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get all support contracts for the authenticated customer
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        # Get contracts for customer
        stmt = select(SupportContract).where(
            and_(
                SupportContract.tenant_id == customer.tenant_id,
                SupportContract.customer_id == customer.id
            )
        )
        
        if status_filter:
            try:
                status_enum = ContractStatus[status_filter.upper()]
                stmt = stmt.where(SupportContract.status == status_enum)
            except KeyError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {status_filter}"
                )
        
        result = await db.execute(stmt)
        contracts = result.scalars().all()
        
        # Format response
        return {
            'customer_id': customer.id,
            'customer_name': customer.company_name,
            'contracts': [
                {
                    'id': c.id,
                    'contract_number': c.contract_number,
                    'contract_name': c.contract_name,
                    'contract_type': c.contract_type.value,
                    'status': c.status.value,
                    'start_date': c.start_date.isoformat() if c.start_date else None,
                    'end_date': c.end_date.isoformat() if c.end_date else None,
                    'renewal_date': c.renewal_date.isoformat() if c.renewal_date else None,
                    'monthly_value': float(c.monthly_value) if c.monthly_value else None,
                    'annual_value': float(c.annual_value) if c.annual_value else None,
                    'currency': c.currency,
                    'sla_level': c.sla_level,
                    'included_services': c.included_services,
                    'support_hours_included': c.support_hours_included,
                    'support_hours_used': c.support_hours_used,
                    'auto_renew': c.auto_renew
                }
                for c in contracts
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching contracts: {str(e)}"
        )


@router.get("/contracts/{contract_id}")
async def get_contract_details(
    contract_id: str,
    customer: Customer = Depends(get_customer_by_token),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get detailed information about a specific contract
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    Note: Wraps sync service calls in executor.
    """
    try:
        def _get_contract():
            sync_db = SessionLocal()
            try:
                service = SupportContractService(sync_db, customer.tenant_id)
                return service.get_contract(contract_id)
            finally:
                sync_db.close()
        
        loop = asyncio.get_event_loop()
        contract = await loop.run_in_executor(None, _get_contract)
        
        if not contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contract not found"
            )
        
        # Verify contract belongs to customer
        if contract.customer_id != customer.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return {
            'id': contract.id,
            'contract_number': contract.contract_number,
            'contract_name': contract.contract_name,
            'description': contract.description,
            'contract_type': contract.contract_type.value,
            'status': contract.status.value,
            'start_date': contract.start_date.isoformat() if contract.start_date else None,
            'end_date': contract.end_date.isoformat() if contract.end_date else None,
            'renewal_date': contract.renewal_date.isoformat() if contract.renewal_date else None,
            'renewal_frequency': contract.renewal_frequency.value if contract.renewal_frequency else None,
            'auto_renew': contract.auto_renew,
            'monthly_value': float(contract.monthly_value) if contract.monthly_value else None,
            'annual_value': float(contract.annual_value) if contract.annual_value else None,
            'setup_fee': float(contract.setup_fee) if contract.setup_fee else None,
            'currency': contract.currency,
            'terms': contract.terms,
            'sla_level': contract.sla_level,
            'included_services': contract.included_services,
            'excluded_services': contract.excluded_services,
            'support_hours_included': contract.support_hours_included,
            'support_hours_used': contract.support_hours_used,
            'renewal_notice_days': contract.renewal_notice_days,
            'cancellation_notice_days': contract.cancellation_notice_days,
            'notes': contract.notes
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching contract details: {str(e)}"
        )


@router.get("/tickets")
async def get_customer_tickets(
    customer: Customer = Depends(get_customer_by_token),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get all tickets for the authenticated customer
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        # Get tickets for customer
        stmt = select(Ticket).where(
            and_(
                Ticket.tenant_id == customer.tenant_id,
                Ticket.customer_id == customer.id
            )
        )
        
        if status_filter:
            try:
                status_enum = TicketStatus[status_filter.upper()]
                stmt = stmt.where(Ticket.status == status_enum)
            except KeyError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {status_filter}"
                )
        
        stmt = stmt.order_by(Ticket.created_at.desc())
        result = await db.execute(stmt)
        tickets = result.scalars().all()
        
        # Format response
        return {
            'customer_id': customer.id,
            'customer_name': customer.company_name,
            'tickets': [
                {
                    'id': t.id,
                    'ticket_number': t.ticket_number,
                    'subject': t.subject,
                    'description': t.description,
                    'status': t.status.value,
                    'priority': t.priority.value,
                    'category': t.category.value if t.category else None,
                    'created_at': t.created_at.isoformat() if t.created_at else None,
                    'updated_at': t.updated_at.isoformat() if t.updated_at else None,
                    'resolved_at': t.resolved_at.isoformat() if t.resolved_at else None,
                    'assigned_to': t.assigned_to,
                    'sla_response_due': t.sla_response_due.isoformat() if t.sla_response_due else None,
                    'sla_resolution_due': t.sla_resolution_due.isoformat() if t.sla_resolution_due else None
                }
                for t in tickets
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching tickets: {str(e)}"
        )


@router.get("/tickets/{ticket_id}")
async def get_ticket_details(
    ticket_id: str,
    customer: Customer = Depends(get_customer_by_token),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get detailed information about a specific ticket
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    Note: Wraps sync service calls in executor.
    """
    try:
        def _get_ticket():
            sync_db = SessionLocal()
            try:
                service = HelpdeskService(sync_db, customer.tenant_id)
                return service.get_ticket(ticket_id)
            finally:
                sync_db.close()
        
        loop = asyncio.get_event_loop()
        ticket = await loop.run_in_executor(None, _get_ticket)
        
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket not found"
            )
        
        # Verify ticket belongs to customer
        if ticket.customer_id != customer.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Get ticket history
        from app.models.helpdesk import TicketHistory
        history_stmt = select(TicketHistory).where(
            TicketHistory.ticket_id == ticket_id
        ).order_by(TicketHistory.created_at.desc())
        history_result = await db.execute(history_stmt)
        history = history_result.scalars().all()
        
        return {
            'id': ticket.id,
            'ticket_number': ticket.ticket_number,
            'subject': ticket.subject,
            'description': ticket.description,
            'status': ticket.status.value,
            'priority': ticket.priority.value,
            'category': ticket.category.value if ticket.category else None,
            'created_at': ticket.created_at.isoformat() if ticket.created_at else None,
            'updated_at': ticket.updated_at.isoformat() if ticket.updated_at else None,
            'resolved_at': ticket.resolved_at.isoformat() if ticket.resolved_at else None,
            'assigned_to': ticket.assigned_to,
            'sla_response_due': ticket.sla_response_due.isoformat() if ticket.sla_response_due else None,
            'sla_resolution_due': ticket.sla_resolution_due.isoformat() if ticket.sla_resolution_due else None,
            'history': [
                {
                    'id': h.id,
                    'action': h.action,
                    'description': h.description,
                    'created_at': h.created_at.isoformat() if h.created_at else None,
                    'created_by': h.created_by
                }
                for h in history
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching ticket details: {str(e)}"
        )


@router.post("/tickets")
async def create_ticket(
    subject: str,
    description: str,
    priority: str = Query("medium", regex="^(low|medium|high|urgent)$"),
    category: Optional[str] = Query(None),
    customer: Customer = Depends(get_customer_by_token),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Create a new support ticket
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    Note: Service method is async, but service uses sync db.
    """
    try:
        from app.models.helpdesk import TicketPriority, TicketCategory, TicketType
        
        # Parse priority
        try:
            ticket_priority = TicketPriority[priority.upper()]
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid priority: {priority}"
            )
        
        # Parse category if provided
        ticket_category = None
        if category:
            try:
                ticket_category = TicketCategory[category.upper()]
            except KeyError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid category: {category}"
                )
        
        sync_db = SessionLocal()
        try:
            service = HelpdeskService(sync_db, customer.tenant_id)
            ticket = await service.create_ticket(
                subject=subject,
                description=description,
                customer_id=customer.id,
                ticket_type=TicketType.SUPPORT,
                priority=ticket_priority
            )
        finally:
            sync_db.close()
        
        return {
            'id': ticket.id,
            'ticket_number': ticket.ticket_number,
            'subject': ticket.subject,
            'status': ticket.status.value,
            'priority': ticket.priority.value,
            'created_at': ticket.created_at.isoformat() if ticket.created_at else None
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating ticket: {str(e)}"
        )


@router.post("/tickets/{ticket_id}/comments")
async def add_ticket_comment(
    ticket_id: str,
    comment: str,
    customer: Customer = Depends(get_customer_by_token),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Add a comment to a ticket
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    Note: Wraps sync service calls in executor.
    """
    try:
        def _get_and_add_comment():
            sync_db = SessionLocal()
            try:
                service = HelpdeskService(sync_db, customer.tenant_id)
                ticket = service.get_ticket(ticket_id)
                
                if not ticket:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Ticket not found"
                    )
                
                # Verify ticket belongs to customer
                if ticket.customer_id != customer.id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Access denied"
                    )
                
                # Add comment (using customer ID as author_id for now)
                service.add_comment(
                    ticket_id=ticket_id,
                    comment=comment,
                    author_id=customer.id,
                    author_name=customer.company_name,
                    is_internal=False
                )
            finally:
                sync_db.close()
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _get_and_add_comment)
        
        return {
            'success': True,
            'message': 'Comment added successfully'
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error adding comment: {str(e)}"
        )

