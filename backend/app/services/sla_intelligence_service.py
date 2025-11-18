#!/usr/bin/env python3
"""
SLA Intelligence Service

Provides SLA monitoring and risk assessment:
- Auto-assign ticket type, priority, and SLA breach risk
- SLA timer tracking
- Risk indicators
- Auto-response/close for low-complexity tickets
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, func

from app.models.helpdesk import Ticket, TicketStatus, TicketPriority, TicketType, SLAPolicy
from app.models.tenant import User

logger = logging.getLogger(__name__)


class SLAIntelligenceService:
    """
    Service for SLA monitoring and intelligence
    
    Features:
    - Auto-assign ticket type, priority, SLA breach risk
    - SLA timer tracking
    - Risk indicators
    - Auto-response/close for low-complexity tickets
    """
    
    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
    
    async def assess_sla_risk(
        self,
        ticket: Ticket
    ) -> Dict[str, Any]:
        """
        Assess SLA breach risk for ticket
        
        Returns:
            Dict with:
            - risk_level: "low", "medium", "high", "critical"
            - time_remaining_hours: Hours until SLA breach
            - breach_probability: Probability of breach (0.0-1.0)
            - recommended_actions: List of recommended actions
        """
        # Get SLA policy for ticket
        sla_policy = await self._get_sla_policy(ticket)
        
        if not sla_policy:
            return {
                "risk_level": "low",
                "time_remaining_hours": None,
                "breach_probability": 0.0,
                "recommended_actions": []
            }
        
        # Calculate time remaining
        target_hours = sla_policy.resolution_hours or sla_policy.first_response_hours or 24
        time_elapsed = (datetime.now(timezone.utc) - ticket.created_at).total_seconds() / 3600
        time_remaining_hours = target_hours - time_elapsed
        
        # Calculate breach probability based on:
        # - Time remaining
        # - Ticket priority
        # - Ticket status
        # - Assigned agent availability
        
        breach_probability = self._calculate_breach_probability(
            time_remaining_hours,
            ticket.priority,
            ticket.status,
            ticket.assigned_to_id is not None
        )
        
        # Determine risk level
        if breach_probability >= 0.8:
            risk_level = "critical"
        elif breach_probability >= 0.6:
            risk_level = "high"
        elif breach_probability >= 0.4:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        # Generate recommended actions
        recommended_actions = self._generate_recommended_actions(
            risk_level,
            time_remaining_hours,
            ticket
        )
        
        return {
            "risk_level": risk_level,
            "time_remaining_hours": max(0, time_remaining_hours),
            "breach_probability": breach_probability,
            "recommended_actions": recommended_actions,
            "sla_target_hours": target_hours,
            "time_elapsed_hours": time_elapsed
        }
    
    async def _get_sla_policy(self, ticket: Ticket) -> Optional[SLAPolicy]:
        """Get applicable SLA policy for ticket"""
        # Query SLA policies matching ticket criteria
        stmt = select(SLAPolicy).where(
            and_(
                SLAPolicy.tenant_id == self.tenant_id,
                SLAPolicy.is_active == True
            )
        )
        
        # Try to find policy matching priority and type
        policies = self.db.execute(stmt).scalars().all()
        
        for policy in policies:
            # Check if policy matches ticket priority
            if policy.priority and policy.priority != ticket.priority:
                continue
            
            # Check if policy matches ticket type
            if policy.ticket_type and policy.ticket_type != ticket.ticket_type:
                continue
            
            # Check if policy applies to specific customers
            if policy.customer_ids:
                if ticket.customer_id not in policy.customer_ids:
                    continue
            
            return policy
        
        # Return first active policy as default
        if policies:
            return policies[0]
        
        return None
    
    def _calculate_breach_probability(
        self,
        time_remaining_hours: float,
        priority: TicketPriority,
        status: TicketStatus,
        is_assigned: bool
    ) -> float:
        """
        Calculate probability of SLA breach
        
        Returns:
            Probability between 0.0 and 1.0
        """
        probability = 0.0
        
        # Base probability from time remaining
        if time_remaining_hours <= 0:
            probability = 1.0  # Already breached
        elif time_remaining_hours < 1:
            probability = 0.9  # Less than 1 hour remaining
        elif time_remaining_hours < 4:
            probability = 0.7  # Less than 4 hours remaining
        elif time_remaining_hours < 8:
            probability = 0.5  # Less than 8 hours remaining
        elif time_remaining_hours < 24:
            probability = 0.3  # Less than 24 hours remaining
        else:
            probability = 0.1  # More than 24 hours remaining
        
        # Adjust based on priority
        if priority == TicketPriority.URGENT:
            probability += 0.2
        elif priority == TicketPriority.HIGH:
            probability += 0.1
        elif priority == TicketPriority.LOW:
            probability -= 0.1
        
        # Adjust based on status
        if status == TicketStatus.OPEN and not is_assigned:
            probability += 0.2  # Unassigned open tickets are higher risk
        elif status == TicketStatus.WAITING_CUSTOMER:
            probability -= 0.1  # Waiting on customer reduces risk
        
        # Clamp between 0 and 1
        return max(0.0, min(1.0, probability))
    
    def _generate_recommended_actions(
        self,
        risk_level: str,
        time_remaining_hours: float,
        ticket: Ticket
    ) -> List[str]:
        """Generate recommended actions based on risk level"""
        actions = []
        
        if risk_level == "critical":
            actions.append("⚠️ CRITICAL: SLA breach imminent - escalate immediately")
            if not ticket.assigned_to_id:
                actions.append("Assign ticket to available agent immediately")
            actions.append("Notify manager and customer of potential delay")
            actions.append("Consider temporary workaround or partial resolution")
        
        elif risk_level == "high":
            actions.append("⚠️ HIGH RISK: Monitor closely - escalate if no progress")
            if not ticket.assigned_to_id:
                actions.append("Assign ticket to specialist")
            actions.append("Set reminder to check progress in 2 hours")
        
        elif risk_level == "medium":
            actions.append("Monitor ticket progress")
            if not ticket.assigned_to_id:
                actions.append("Consider assigning ticket")
        
        else:
            actions.append("Ticket is on track - continue monitoring")
        
        # Add time-specific actions
        if time_remaining_hours and time_remaining_hours < 4:
            actions.append(f"⏰ Only {time_remaining_hours:.1f} hours remaining until SLA target")
        
        return actions
    
    async def auto_assign_ticket(
        self,
        ticket: Ticket
    ) -> Optional[str]:
        """
        Auto-assign ticket to appropriate agent
        
        Returns:
            User ID of assigned agent or None
        """
        # TODO: Implement intelligent auto-assignment based on:
        # - Agent workload
        # - Agent skills/expertise
        # - Ticket type/priority
        # - Agent availability
        
        # For now, return None (no auto-assignment)
        return None
    
    async def should_auto_close(
        self,
        ticket: Ticket,
        ai_confidence: float = 0.0
    ) -> bool:
        """
        Determine if ticket should be auto-closed
        
        Args:
            ticket: Ticket object
            ai_confidence: AI confidence score (0.0-1.0)
        
        Returns:
            True if ticket should be auto-closed
        """
        # Only auto-close if:
        # - Low complexity (low priority, simple type)
        # - High AI confidence (>0.8)
        # - No customer interaction needed
        # - Not assigned to specific agent
        
        if ticket.priority != TicketPriority.LOW:
            return False
        
        if ai_confidence < 0.8:
            return False
        
        if ticket.status == TicketStatus.WAITING_CUSTOMER:
            return False
        
        if ticket.assigned_to_id:
            return False
        
        # Check if ticket has been resolved
        if ticket.status == TicketStatus.RESOLVED:
            return True
        
        return False
    
    async def get_sla_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get SLA metrics for tenant
        
        Returns:
            Dict with SLA statistics
        """
        if not start_date:
            start_date = datetime.now(timezone.utc) - timedelta(days=30)
        if not end_date:
            end_date = datetime.now(timezone.utc)
        
        # Query tickets in date range
        stmt = select(Ticket).where(
            and_(
                Ticket.tenant_id == self.tenant_id,
                Ticket.created_at >= start_date,
                Ticket.created_at <= end_date
            )
        )
        
        tickets = self.db.execute(stmt).scalars().all()
        
        total_tickets = len(tickets)
        breached_tickets = 0
        on_time_tickets = 0
        
        for ticket in tickets:
            sla_assessment = await self.assess_sla_risk(ticket)
            
            if sla_assessment["time_remaining_hours"] is not None:
                if sla_assessment["time_remaining_hours"] <= 0:
                    breached_tickets += 1
                else:
                    on_time_tickets += 1
        
        breach_rate = (breached_tickets / total_tickets * 100) if total_tickets > 0 else 0
        
        return {
            "total_tickets": total_tickets,
            "breached_tickets": breached_tickets,
            "on_time_tickets": on_time_tickets,
            "breach_rate_percent": breach_rate,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
        }

