#!/usr/bin/env python3
"""
Customer Portal API Endpoints
Public-facing endpoints for customers to view their contracts and manage tickets
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

from app.core.dependencies import get_db
from app.models.support_contract import SupportContract, ContractStatus
from app.models.helpdesk import Ticket, TicketStatus
from app.models.crm import Customer
from app.services.support_contract_service import SupportContractService
from app.services.helpdesk_service import HelpdeskService

router = APIRouter(prefix="/customer-portal", tags=["Customer Portal"])


def get_customer_by_token(
    x_customer_token: Optional[str] = Header(None, alias="X-Customer-Token"),
    db: Session = Depends(get_db)
) -> Customer:
    """
    Authenticate customer using token (for now, we'll use customer ID as token)
    In production, this should use a proper JWT or API key system
    """
    if not x_customer_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Customer token required"
        )
    
    # For now, use customer ID directly (in production, decode JWT or validate API key)
    customer = db.query(Customer).filter(
        Customer.id == x_customer_token,
        Customer.is_deleted == False
    ).first()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid customer token"
        )
    
    return customer


@router.get("/contracts")
async def get_customer_contracts(
    customer: Customer = Depends(get_customer_by_token),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db)
):
    """Get all support contracts for the authenticated customer"""
    try:
        service = SupportContractService(db, customer.tenant_id)
        
        # Get contracts for customer
        query = db.query(SupportContract).filter(
            and_(
                SupportContract.tenant_id == customer.tenant_id,
                SupportContract.customer_id == customer.id
            )
        )
        
        if status_filter:
            try:
                status_enum = ContractStatus[status_filter.upper()]
                query = query.filter(SupportContract.status == status_enum)
            except KeyError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {status_filter}"
                )
        
        contracts = query.all()
        
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
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific contract"""
    try:
        service = SupportContractService(db, customer.tenant_id)
        contract = service.get_contract(contract_id)
        
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
    db: Session = Depends(get_db)
):
    """Get all tickets for the authenticated customer"""
    try:
        service = HelpdeskService(db, customer.tenant_id)
        
        # Get tickets for customer
        query = db.query(Ticket).filter(
            and_(
                Ticket.tenant_id == customer.tenant_id,
                Ticket.customer_id == customer.id
            )
        )
        
        if status_filter:
            try:
                status_enum = TicketStatus[status_filter.upper()]
                query = query.filter(Ticket.status == status_enum)
            except KeyError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {status_filter}"
                )
        
        tickets = query.order_by(Ticket.created_at.desc()).all()
        
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
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific ticket"""
    try:
        service = HelpdeskService(db, customer.tenant_id)
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
        
        # Get ticket history
        from app.models.helpdesk import TicketHistory
        history = db.query(TicketHistory).filter(
            TicketHistory.ticket_id == ticket_id
        ).order_by(TicketHistory.created_at.desc()).all()
        
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
    db: Session = Depends(get_db)
):
    """Create a new support ticket"""
    try:
        from app.models.helpdesk import TicketPriority, TicketCategory
        
        service = HelpdeskService(db, customer.tenant_id)
        
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
        
        from app.models.helpdesk import TicketType
        
        ticket = service.create_ticket(
            subject=subject,
            description=description,
            customer_id=customer.id,
            ticket_type=TicketType.SUPPORT,
            priority=ticket_priority
        )
        
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
    db: Session = Depends(get_db)
):
    """Add a comment to a ticket"""
    try:
        service = HelpdeskService(db, customer.tenant_id)
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

