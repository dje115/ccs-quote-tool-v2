#!/usr/bin/env python3
"""
Ticket Next Point of Action (NPA) Service

Manages Next Point of Action for tickets:
- Every ticket must have an NPA unless closed/resolved
- Auto-generate NPA when ticket is created/updated
- Track NPA due dates and assignments
- Alert on overdue NPAs
"""

import logging
import uuid
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_
from datetime import datetime, timedelta, timezone

from app.models.helpdesk import Ticket, TicketStatus, TicketPriority, NPAHistory

logger = logging.getLogger(__name__)


class TicketNPAService:
    """
    Service for managing Next Point of Action (NPA) for tickets
    
    Features:
    - Auto-generate NPA based on ticket context
    - Ensure every ticket has an NPA
    - Track NPA due dates
    - Alert on overdue NPAs
    - AI-powered NPA suggestions
    """
    
    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
    
    async def ensure_npa_exists(
        self,
        ticket: Ticket
    ) -> Dict[str, Any]:
        """
        Ensure ticket has a Next Point of Action
        
        If ticket is closed/resolved, NPA is not required.
        Otherwise, generates or validates NPA exists.
        
        Args:
            ticket: Ticket to check
        
        Returns:
            Dict with NPA status and action taken
        """
        # Closed/resolved tickets don't need NPA
        if ticket.status in [TicketStatus.CLOSED, TicketStatus.RESOLVED, TicketStatus.CANCELLED]:
            if ticket.next_point_of_action:
                # Clear NPA for closed tickets
                ticket.next_point_of_action = None
                ticket.next_point_of_action_due_date = None
                ticket.next_point_of_action_assigned_to_id = None
                self.db.commit()
            return {
                "has_npa": False,
                "required": False,
                "reason": "Ticket is closed/resolved"
            }
        
        # Check if NPA exists
        if ticket.next_point_of_action:
            return {
                "has_npa": True,
                "required": True,
                "npa": ticket.next_point_of_action,
                "due_date": ticket.next_point_of_action_due_date.isoformat() if ticket.next_point_of_action_due_date else None,
                "assigned_to": ticket.next_point_of_action_assigned_to_id
            }
        
        # Generate NPA if missing
        npa_result = await self.generate_npa(ticket)
        
        if npa_result.get("success"):
            # Use update_npa to set all fields properly
            update_result = await self.update_npa(
                ticket=ticket,
                npa=npa_result["npa"],
                due_date=npa_result.get("due_date"),
                assigned_to_id=npa_result.get("assigned_to_id"),
                trigger_ai_cleanup=True  # Auto-cleanup for new NPAs
            )
            
            return {
                "has_npa": True,
                "required": True,
                "npa": ticket.npa_cleaned_text or ticket.next_point_of_action,
                "npa_original": ticket.npa_original_text,
                "npa_state": ticket.npa_state.value if ticket.npa_state else None,
                "due_date": ticket.next_point_of_action_due_date.isoformat() if ticket.next_point_of_action_due_date else None,
                "assigned_to": ticket.next_point_of_action_assigned_to_id,
                "exclude_from_sla": ticket.npa_exclude_from_sla,
                "ai_cleanup_status": ticket.npa_ai_cleanup_status,
                "auto_generated": True
            }
        
        return {
            "has_npa": False,
            "required": True,
            "error": npa_result.get("error", "Failed to generate NPA")
        }
    
    async def generate_npa(
        self,
        ticket: Ticket
    ) -> Dict[str, Any]:
        """
        Generate Next Point of Action for a ticket using AI
        
        Args:
            ticket: Ticket to generate NPA for
        
        Returns:
            Dict with generated NPA
        """
        from app.services.ai_orchestration_service import AIOrchestrationService
        from app.models.ai_prompt import PromptCategory
        
        try:
            ai_service = AIOrchestrationService(self.db, self.tenant_id)
            
            # Build context
            context = f"""
            Ticket Information:
            - Subject: {ticket.subject}
            - Description: {ticket.description or 'No description'}
            - Status: {ticket.status.value if hasattr(ticket.status, 'value') else ticket.status}
            - Priority: {ticket.priority.value if hasattr(ticket.priority, 'value') else ticket.priority}
            - Type: {ticket.ticket_type.value if hasattr(ticket.ticket_type, 'value') else ticket.ticket_type}
            - Assigned to: {'Assigned' if ticket.assigned_to_id else 'Unassigned'}
            - Created: {ticket.created_at.isoformat() if ticket.created_at else 'Unknown'}
            """
            
            prompt_text = f"""
            Based on the following ticket, determine the Next Point of Action (NPA).
            
            {context}
            
            The Next Point of Action should be:
            1. A clear, actionable step that moves the ticket forward
            2. Specific and measurable
            3. Appropriate for the ticket's current status and priority
            4. Include who should do it (if applicable)
            
            Examples:
            - "Contact customer to gather more information about the issue"
            - "Investigate the error logs and identify root cause"
            - "Schedule a call with the customer to demonstrate the solution"
            - "Wait for customer to provide additional details (due: 2 days)"
            - "Assign to technical team for resolution"
            
            Return ONLY the Next Point of Action text (1-2 sentences, clear and actionable).
            """
            
            response = await ai_service.generate_response(
                prompt_text=prompt_text,
                category=PromptCategory.CUSTOMER_SERVICE.value,
                max_tokens=150
            )
            
            npa_text = response.strip() if response else None
            
            if not npa_text:
                # Fallback to default NPA based on status
                npa_text = self._generate_default_npa(ticket)
            
            # Calculate due date based on priority
            due_date = self._calculate_npa_due_date(ticket)
            
            # Determine assignment
            assigned_to_id = ticket.assigned_to_id or None
            
            return {
                "success": True,
                "npa": npa_text,
                "due_date": due_date,
                "assigned_to_id": assigned_to_id
            }
            
        except Exception as e:
            logger.error(f"Error generating NPA: {e}")
            # Fallback to default
            return {
                "success": True,
                "npa": self._generate_default_npa(ticket),
                "due_date": self._calculate_npa_due_date(ticket),
                "assigned_to_id": ticket.assigned_to_id
            }
    
    def _generate_default_npa(self, ticket: Ticket) -> str:
        """Generate default NPA based on ticket status"""
        if ticket.status == TicketStatus.OPEN:
            if not ticket.assigned_to_id:
                return "Assign ticket to appropriate agent and begin investigation"
            return "Review ticket details and begin investigation"
        
        elif ticket.status == TicketStatus.IN_PROGRESS:
            return "Continue working on ticket and provide update to customer"
        
        elif ticket.status == TicketStatus.WAITING_CUSTOMER:
            return "Wait for customer response and follow up if no response within 2 days"
        
        return "Review ticket and determine next steps"
    
    def _calculate_npa_due_date(self, ticket: Ticket) -> Optional[datetime]:
        """Calculate NPA due date based on priority"""
        now = datetime.now(timezone.utc)
        
        # Due dates based on priority
        priority_hours = {
            TicketPriority.URGENT: 2,  # 2 hours
            TicketPriority.HIGH: 4,     # 4 hours
            TicketPriority.MEDIUM: 24, # 1 day
            TicketPriority.LOW: 48     # 2 days
        }
        
        hours = priority_hours.get(ticket.priority, 24)
        return now + timedelta(hours=hours)
    
    def update_npa(
        self,
        ticket: Ticket,
        npa: str,
        due_date: Optional[datetime] = None,
        assigned_to_id: Optional[str] = None,
        npa_state: Optional[str] = None,  # String value matching database enum (e.g., 'investigation', 'waiting_customer')
        date_override: bool = False,
        exclude_from_sla: Optional[bool] = None,
        trigger_ai_cleanup: bool = True,
        completed_by_id: Optional[str] = None,  # If completing an existing NPA
        completion_notes: Optional[str] = None  # Notes on completion
    ) -> Dict[str, Any]:
        """
        Update Next Point of Action for a ticket
        
        IMPORTANT: This method saves the current NPA to history before updating.
        This preserves the complete call history for AI analysis.
        
        Args:
            ticket: Ticket to update
            npa: Next Point of Action text (original as typed)
            due_date: Optional due date (if None, auto-calculated unless date_override=True)
            assigned_to_id: Optional user ID to assign NPA to
            npa_state: Optional NPA state (investigation, waiting_customer, etc.)
            date_override: Whether the due date was manually overridden
            exclude_from_sla: Whether to exclude from SLA (auto-set based on state if None)
            trigger_ai_cleanup: Whether to trigger AI cleanup for customer-facing text
            completed_by_id: If completing an existing NPA, the user who completed it
            completion_notes: Notes on how/why the NPA was completed
        
        Returns:
            Dict with update result
        """
        from app.tasks.npa_tasks import cleanup_npa_text_task
        
        # Save current NPA to history ONLY if:
        # 1. There's existing NPA text AND
        # 2. The new NPA text is different (actual change) OR
        # 3. We're explicitly completing it (completed_by_id provided)
        # This prevents duplicate history entries from state-only updates
        should_save_to_history = False
        if ticket.npa_original_text:
            # Save if text is actually changing
            if npa.strip() != ticket.npa_original_text.strip():
                should_save_to_history = True
            # Or if we're explicitly completing it
            elif completed_by_id:
                should_save_to_history = True
        
        if should_save_to_history:
            npa_history_entry = NPAHistory(
                id=str(uuid.uuid4()),
                ticket_id=ticket.id,
                tenant_id=ticket.tenant_id,
                npa_original_text=ticket.npa_original_text,
                npa_cleaned_text=ticket.npa_cleaned_text,
                npa_state=ticket.npa_state if isinstance(ticket.npa_state, str) else (ticket.npa_state.value if hasattr(ticket.npa_state, 'value') else str(ticket.npa_state)) if ticket.npa_state else 'investigation',
                assigned_to_id=ticket.next_point_of_action_assigned_to_id,
                due_date=ticket.next_point_of_action_due_date,
                date_override=ticket.npa_date_override,
                exclude_from_sla=ticket.npa_exclude_from_sla,
                ai_cleanup_status=ticket.npa_ai_cleanup_status,
                ai_cleanup_task_id=ticket.npa_ai_cleanup_task_id,
                answers_to_questions=ticket.npa_answers_original_text,
                answers_cleaned_text=ticket.npa_answers_cleaned_text,
                answers_ai_cleanup_status=ticket.npa_answers_ai_cleanup_status,
                answers_ai_cleanup_task_id=ticket.npa_answers_ai_cleanup_task_id,
                completed_at=datetime.now(timezone.utc) if completed_by_id else None,
                completed_by_id=completed_by_id,
                completion_notes=completion_notes
            )
            self.db.add(npa_history_entry)
        
        # Store original text
        ticket.npa_original_text = npa
        
        # Set state (default to investigation if not provided)
        # Convert enum to string value if needed
        if npa_state:
            if hasattr(npa_state, 'value'):
                ticket.npa_state = npa_state.value
            else:
                ticket.npa_state = str(npa_state)
        elif not ticket.npa_state:
            ticket.npa_state = 'investigation'
        
        # Auto-set exclude_from_sla based on state if not explicitly provided
        if exclude_from_sla is None:
            waiting_states = ['waiting_customer', 'waiting_vendor', 'waiting_parts']
            current_state = ticket.npa_state if isinstance(ticket.npa_state, str) else (ticket.npa_state.value if hasattr(ticket.npa_state, 'value') else str(ticket.npa_state))
            ticket.npa_exclude_from_sla = current_state in waiting_states
        else:
            ticket.npa_exclude_from_sla = exclude_from_sla
        
        # Set due date
        if date_override and due_date:
            ticket.next_point_of_action_due_date = due_date
            ticket.npa_date_override = True
        elif not date_override:
            ticket.next_point_of_action_due_date = due_date or self._calculate_npa_due_date(ticket)
            ticket.npa_date_override = False
        else:
            ticket.npa_date_override = date_override
        
        ticket.next_point_of_action_assigned_to_id = assigned_to_id
        ticket.npa_last_updated_at = datetime.now(timezone.utc)
        
        # Trigger AI cleanup if needed (for customer-facing states)
        customer_facing_states = ['solution', 'waiting_customer', 'implementation']
        current_state = ticket.npa_state if isinstance(ticket.npa_state, str) else (ticket.npa_state.value if hasattr(ticket.npa_state, 'value') else str(ticket.npa_state))
        
        if trigger_ai_cleanup and current_state in customer_facing_states:
            # Queue AI cleanup task
            ticket.npa_ai_cleanup_status = "pending"
            task = cleanup_npa_text_task.delay(
                ticket_id=ticket.id,
                tenant_id=self.tenant_id,
                original_text=npa
            )
            ticket.npa_ai_cleanup_task_id = task.id
        else:
            # Use original text as cleaned text if no cleanup needed
            ticket.npa_cleaned_text = npa
            ticket.npa_ai_cleanup_status = "skipped"
        
        # Update legacy field for backward compatibility
        ticket.next_point_of_action = ticket.npa_cleaned_text or npa
        
        self.db.commit()
        
        return {
            "success": True,
            "npa": ticket.npa_cleaned_text or npa,
            "npa_original": npa,
            "npa_state": ticket.npa_state if isinstance(ticket.npa_state, str) else (ticket.npa_state.value if hasattr(ticket.npa_state, 'value') else str(ticket.npa_state)) if ticket.npa_state else None,
            "exclude_from_sla": ticket.npa_exclude_from_sla,
            "ai_cleanup_status": ticket.npa_ai_cleanup_status,
            "ai_cleanup_task_id": ticket.npa_ai_cleanup_task_id,
            "due_date": ticket.next_point_of_action_due_date.isoformat() if ticket.next_point_of_action_due_date else None,
            "assigned_to": assigned_to_id
        }
    
    async def get_tickets_without_npa(
        self
    ) -> List[Ticket]:
        """Get all tickets that need an NPA"""
        stmt = select(Ticket).where(
            and_(
                Ticket.tenant_id == self.tenant_id,
                Ticket.status.notin_([TicketStatus.CLOSED, TicketStatus.RESOLVED, TicketStatus.CANCELLED]),
                or_(
                    Ticket.next_point_of_action.is_(None),
                    Ticket.next_point_of_action == ""
                )
            )
        )
        
        tickets = self.db.execute(stmt).scalars().all()
        return tickets
    
    async def get_overdue_npas(
        self
    ) -> List[Dict[str, Any]]:
        """Get all tickets with overdue NPAs"""
        now = datetime.now(timezone.utc)
        
        stmt = select(Ticket).where(
            and_(
                Ticket.tenant_id == self.tenant_id,
                Ticket.status.notin_([TicketStatus.CLOSED, TicketStatus.RESOLVED, TicketStatus.CANCELLED]),
                Ticket.next_point_of_action.isnot(None),
                Ticket.next_point_of_action_due_date.isnot(None),
                Ticket.next_point_of_action_due_date < now
            )
        )
        
        tickets = self.db.execute(stmt).scalars().all()
        
        return [
            {
                "ticket_id": ticket.id,
                "ticket_number": ticket.ticket_number,
                "title": ticket.subject,
                "npa": ticket.next_point_of_action,
                "due_date": ticket.next_point_of_action_due_date.isoformat() if ticket.next_point_of_action_due_date else None,
                "overdue_hours": (now - ticket.next_point_of_action_due_date).total_seconds() / 3600 if ticket.next_point_of_action_due_date else 0,
                "assigned_to": ticket.next_point_of_action_assigned_to_id
            }
            for ticket in tickets
        ]
    
    async def auto_update_npa_on_status_change(
        self,
        ticket: Ticket,
        old_status: TicketStatus,
        new_status: TicketStatus
    ) -> Dict[str, Any]:
        """
        Auto-update NPA when ticket status changes
        
        Args:
            ticket: Ticket that changed status
            old_status: Previous status
            new_status: New status
        
        Returns:
            Dict with update result
        """
        # If closed/resolved, clear NPA
        if new_status in [TicketStatus.CLOSED, TicketStatus.RESOLVED, TicketStatus.CANCELLED]:
            ticket.next_point_of_action = None
            ticket.next_point_of_action_due_date = None
            ticket.next_point_of_action_assigned_to_id = None
            self.db.commit()
            return {"success": True, "action": "cleared"}
        
        # If status changed, regenerate NPA
        if old_status != new_status:
            return await self.ensure_npa_exists(ticket)
        
        return {"success": True, "action": "no_change"}

