#!/usr/bin/env python3
"""
SLA Service
Manages SLA tracking, escalation workflows, and SLA policy enforcement
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from datetime import datetime, timedelta, timezone
import logging
import uuid

from app.models.helpdesk import Ticket, SLAPolicy, TicketStatus, TicketPriority, TicketType
from app.models.tenant import User

logger = logging.getLogger(__name__)


class SLAService:
    """Service for managing SLA policies and tracking"""
    
    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
    
    def check_sla_violations(self) -> List[Dict[str, Any]]:
        """
        Check for SLA violations across all open tickets
        
        Returns:
            List of tickets with SLA violations
        """
        violations = []
        
        # Get all open tickets with SLA targets
        tickets = self.db.query(Ticket).filter(
            and_(
                Ticket.tenant_id == self.tenant_id,
                Ticket.status.in_([TicketStatus.OPEN, TicketStatus.IN_PROGRESS, TicketStatus.WAITING_CUSTOMER]),
                Ticket.sla_target_hours.isnot(None)
            )
        ).all()
        
        now = datetime.now(timezone.utc)
        
        for ticket in tickets:
            violation = self._check_ticket_sla(ticket, now)
            if violation:
                violations.append(violation)
        
        return violations
    
    def _check_ticket_sla(self, ticket: Ticket, now: datetime) -> Optional[Dict[str, Any]]:
        """Check if a ticket violates SLA"""
        if not ticket.sla_target_hours:
            return None
        
        # Check first response SLA
        if not ticket.first_response_at:
            hours_since_creation = (now - ticket.created_at).total_seconds() / 3600
            
            # Get first response target from policy
            policy = self._get_ticket_sla_policy(ticket)
            first_response_hours = policy.first_response_hours if policy else None
            
            if first_response_hours and hours_since_creation > first_response_hours:
                return {
                    'ticket_id': ticket.id,
                    'ticket_number': ticket.ticket_number,
                    'violation_type': 'first_response',
                    'target_hours': first_response_hours,
                    'actual_hours': round(hours_since_creation, 2),
                    'overdue_hours': round(hours_since_creation - first_response_hours, 2),
                    'priority': ticket.priority.value,
                    'assigned_to_id': ticket.assigned_to_id
                }
        
        # Check resolution SLA
        if ticket.status not in [TicketStatus.RESOLVED, TicketStatus.CLOSED]:
            hours_since_creation = (now - ticket.created_at).total_seconds() / 3600
            
            if hours_since_creation > ticket.sla_target_hours:
                return {
                    'ticket_id': ticket.id,
                    'ticket_number': ticket.ticket_number,
                    'violation_type': 'resolution',
                    'target_hours': ticket.sla_target_hours,
                    'actual_hours': round(hours_since_creation, 2),
                    'overdue_hours': round(hours_since_creation - ticket.sla_target_hours, 2),
                    'priority': ticket.priority.value,
                    'assigned_to_id': ticket.assigned_to_id
                }
        
        return None
    
    def escalate_ticket(self, ticket_id: str, escalation_reason: str, escalated_by_id: str) -> Ticket:
        """
        Escalate a ticket (increase priority or assign to manager)
        
        Args:
            ticket_id: Ticket ID
            escalation_reason: Reason for escalation
            escalated_by_id: User ID who escalated
        
        Returns:
            Updated ticket
        """
        ticket = self.db.query(Ticket).filter(
            and_(
                Ticket.id == ticket_id,
                Ticket.tenant_id == self.tenant_id
            )
        ).first()
        
        if not ticket:
            raise ValueError(f"Ticket {ticket_id} not found")
        
        # Increase priority if not already urgent
        if ticket.priority != TicketPriority.URGENT:
            old_priority = ticket.priority.value
            
            # Upgrade priority
            if ticket.priority == TicketPriority.LOW:
                ticket.priority = TicketPriority.MEDIUM
            elif ticket.priority == TicketPriority.MEDIUM:
                ticket.priority = TicketPriority.HIGH
            elif ticket.priority == TicketPriority.HIGH:
                ticket.priority = TicketPriority.URGENT
            
            # Add comment about escalation
            from app.services.helpdesk_service import HelpdeskService
            helpdesk_service = HelpdeskService(self.db, self.tenant_id)
            helpdesk_service.add_comment(
                ticket_id=ticket_id,
                comment=f"Ticket escalated: {escalation_reason}",
                author_id=escalated_by_id,
                is_internal=True
            )
            
            # Add history
            helpdesk_service._add_history(
                ticket,
                "priority",
                old_priority,
                ticket.priority.value,
                escalated_by_id
            )
        
        self.db.commit()
        self.db.refresh(ticket)
        
        return ticket
    
    def auto_escalate_violations(self) -> Dict[str, Any]:
        """
        Automatically escalate tickets with SLA violations
        
        Returns:
            Dictionary with escalation results
        """
        violations = self.check_sla_violations()
        escalated_count = 0
        
        for violation in violations:
            try:
                # Only escalate if not already urgent
                ticket = self.db.query(Ticket).filter(
                    Ticket.id == violation['ticket_id']
                ).first()
                
                if ticket and ticket.priority != TicketPriority.URGENT:
                    self.escalate_ticket(
                        ticket_id=ticket.id,
                        escalation_reason=f"SLA violation: {violation['violation_type']} overdue by {violation['overdue_hours']} hours",
                        escalated_by_id=None  # System escalation
                    )
                    escalated_count += 1
            except Exception as e:
                logger.error(f"Error escalating ticket {violation['ticket_id']}: {e}")
        
        return {
            'violations_found': len(violations),
            'escalated': escalated_count,
            'violations': violations
        }
    
    def get_sla_metrics(self) -> Dict[str, Any]:
        """
        Get SLA performance metrics
        
        Returns:
            Dictionary with SLA metrics
        """
        # Get all tickets with SLA targets
        tickets = self.db.query(Ticket).filter(
            and_(
                Ticket.tenant_id == self.tenant_id,
                Ticket.sla_target_hours.isnot(None)
            )
        ).all()
        
        total_tickets = len(tickets)
        met_first_response = 0
        met_resolution = 0
        violations = 0
        
        for ticket in tickets:
            # Check first response
            if ticket.first_response_at:
                response_time = (ticket.first_response_at - ticket.created_at).total_seconds() / 3600
                policy = self._get_ticket_sla_policy(ticket)
                if policy and policy.first_response_hours:
                    if response_time <= policy.first_response_hours:
                        met_first_response += 1
            
            # Check resolution
            if ticket.status in [TicketStatus.RESOLVED, TicketStatus.CLOSED] and ticket.resolved_at:
                resolution_time = (ticket.resolved_at - ticket.created_at).total_seconds() / 3600
                if resolution_time <= ticket.sla_target_hours:
                    met_resolution += 1
        
        # Count violations
        violations_list = self.check_sla_violations()
        violations = len(violations_list)
        
        return {
            'total_tickets_with_sla': total_tickets,
            'first_response_sla_met': met_first_response,
            'first_response_sla_rate': round((met_first_response / total_tickets * 100), 2) if total_tickets > 0 else 0.0,
            'resolution_sla_met': met_resolution,
            'resolution_sla_rate': round((met_resolution / total_tickets * 100), 2) if total_tickets > 0 else 0.0,
            'current_violations': violations,
            'violation_rate': round((violations / total_tickets * 100), 2) if total_tickets > 0 else 0.0
        }
    
    def create_sla_policy(
        self,
        name: str,
        description: Optional[str] = None,
        first_response_hours: Optional[int] = None,
        resolution_hours: Optional[int] = None,
        priority: Optional[TicketPriority] = None,
        ticket_type: Optional[TicketType] = None,
        customer_ids: Optional[List[str]] = None
    ) -> SLAPolicy:
        """
        Create an SLA policy
        
        Args:
            name: Policy name
            description: Policy description
            first_response_hours: Target first response time in hours
            resolution_hours: Target resolution time in hours
            priority: Apply to specific priority
            ticket_type: Apply to specific type
            customer_ids: Apply to specific customers
        
        Returns:
            Created SLA policy
        """
        policy = SLAPolicy(
            id=str(uuid.uuid4()),
            tenant_id=self.tenant_id,
            name=name,
            description=description,
            first_response_hours=first_response_hours,
            resolution_hours=resolution_hours,
            priority=priority,
            ticket_type=ticket_type,
            customer_ids=customer_ids or [],
            is_active=True
        )
        
        self.db.add(policy)
        self.db.commit()
        self.db.refresh(policy)
        
        return policy
    
    def _get_ticket_sla_policy(self, ticket: Ticket) -> Optional[SLAPolicy]:
        """Get applicable SLA policy for a ticket"""
        policies = self.db.query(SLAPolicy).filter(
            and_(
                SLAPolicy.tenant_id == self.tenant_id,
                SLAPolicy.is_active == True
            )
        ).all()
        
        for policy in policies:
            if policy.priority and policy.priority != ticket.priority:
                continue
            if policy.ticket_type and policy.ticket_type != ticket.ticket_type:
                continue
            if policy.customer_ids and ticket.customer_id not in policy.customer_ids:
                continue
            
            return policy
        
        return None

