#!/usr/bin/env python3
"""
SLA Tracking Service
Handles SLA calculation, breach detection, and compliance tracking
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload

from app.models.helpdesk import Ticket, SLAPolicy, TicketPriority, TicketStatus
from app.models.sla_compliance import SLAComplianceRecord, SLABreachAlert
from app.models.support_contract import SupportContract
from sqlalchemy import update


class SLATrackingService:
    """Service for tracking and managing SLA compliance"""
    
    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
    
    async def get_sla_for_ticket(
        self,
        ticket: Ticket,
        contract: Optional[SupportContract] = None
    ) -> Optional[SLAPolicy]:
        """
        Determine which SLA policy applies to a ticket
        
        Priority:
        1. Ticket's explicit SLA policy
        2. Contract's SLA policy
        3. Default SLA policy for tenant
        4. Priority/type-based SLA policy
        """
        # 1. Check if ticket has explicit SLA policy
        if ticket.sla_policy_id:
            stmt = select(SLAPolicy).where(
                and_(
                    SLAPolicy.id == ticket.sla_policy_id,
                    SLAPolicy.tenant_id == self.tenant_id,
                    SLAPolicy.is_active == True
                )
            )
            result = await self.db.execute(stmt)
            policy = result.scalar_one_or_none()
            if policy:
                return policy
        
        # 2. Check contract's SLA policy
        if contract and contract.sla_policy_id:
            stmt = select(SLAPolicy).where(
                and_(
                    SLAPolicy.id == contract.sla_policy_id,
                    SLAPolicy.tenant_id == self.tenant_id,
                    SLAPolicy.is_active == True
                )
            )
            result = await self.db.execute(stmt)
            policy = result.scalar_one_or_none()
            if policy:
                return policy
        
        # 3. Get default SLA policy
        stmt = select(SLAPolicy).where(
            and_(
                SLAPolicy.tenant_id == self.tenant_id,
                SLAPolicy.is_active == True,
                SLAPolicy.is_default == True
            )
        )
        result = await self.db.execute(stmt)
        default_policy = result.scalar_one_or_none()
        if default_policy:
            return default_policy
        
        # 4. Find priority/type-based policy
        stmt = select(SLAPolicy).where(
            and_(
                SLAPolicy.tenant_id == self.tenant_id,
                SLAPolicy.is_active == True,
                or_(
                    SLAPolicy.priority == ticket.priority,
                    SLAPolicy.ticket_type == ticket.ticket_type
                )
            )
        ).order_by(SLAPolicy.priority.desc().nulls_last())
        result = await self.db.execute(stmt)
        policy = result.scalar_one_or_none()
        
        return policy
    
    def get_sla_targets(
        self,
        policy: SLAPolicy,
        priority: TicketPriority
    ) -> Dict[str, Optional[int]]:
        """Get SLA targets for a specific priority"""
        targets = {}
        
        # First response targets
        if priority == TicketPriority.URGENT and policy.first_response_hours_urgent:
            targets['first_response_hours'] = policy.first_response_hours_urgent
        elif priority == TicketPriority.HIGH and policy.first_response_hours_high:
            targets['first_response_hours'] = policy.first_response_hours_high
        elif priority == TicketPriority.MEDIUM and policy.first_response_hours_medium:
            targets['first_response_hours'] = policy.first_response_hours_medium
        elif priority == TicketPriority.LOW and policy.first_response_hours_low:
            targets['first_response_hours'] = policy.first_response_hours_low
        else:
            targets['first_response_hours'] = policy.first_response_hours
        
        # Resolution targets
        if priority == TicketPriority.URGENT and policy.resolution_hours_urgent:
            targets['resolution_hours'] = policy.resolution_hours_urgent
        elif priority == TicketPriority.HIGH and policy.resolution_hours_high:
            targets['resolution_hours'] = policy.resolution_hours_high
        elif priority == TicketPriority.MEDIUM and policy.resolution_hours_medium:
            targets['resolution_hours'] = policy.resolution_hours_medium
        elif priority == TicketPriority.LOW and policy.resolution_hours_low:
            targets['resolution_hours'] = policy.resolution_hours_low
        else:
            targets['resolution_hours'] = policy.resolution_hours
        
        return targets
    
    async def apply_sla_to_ticket(self, ticket: Ticket) -> bool:
        """
        Apply SLA policy to a ticket and calculate targets
        Returns True if SLA was applied, False otherwise
        """
        # Get contract if linked
        contract = None
        if ticket.related_contract_id:
            stmt = select(SupportContract).where(
                SupportContract.id == ticket.related_contract_id
            )
            result = await self.db.execute(stmt)
            contract = result.scalar_one_or_none()
        
        # Get SLA policy
        policy = await self.get_sla_for_ticket(ticket, contract)
        if not policy:
            return False
        
        # Get targets for this priority
        targets = self.get_sla_targets(policy, ticket.priority)
        
        # Update ticket with SLA info
        ticket.sla_policy_id = policy.id
        ticket.sla_first_response_hours = targets.get('first_response_hours')
        ticket.sla_target_hours = targets.get('resolution_hours')
        
        await self.db.commit()
        await self.db.refresh(ticket)
        
        return True
    
    async def check_ticket_sla_compliance(self, ticket: Ticket) -> Dict[str, Any]:
        """
        Check current SLA compliance for a ticket
        Returns compliance status and breach information
        """
        if not ticket.sla_policy_id or not ticket.sla_target_hours:
            return {
                'has_sla': False,
                'compliant': None
            }
        
        now = datetime.now(timezone.utc)
        compliance = {
            'has_sla': True,
            'first_response': {},
            'resolution': {},
            'breaches': []
        }
        
        # Check first response SLA
        if ticket.sla_first_response_hours:
            if ticket.first_response_at:
                # Calculate time taken
                time_taken = (ticket.first_response_at - ticket.created_at).total_seconds() / 3600
                target = ticket.sla_first_response_hours
                met = time_taken <= target
                
                compliance['first_response'] = {
                    'target_hours': target,
                    'actual_hours': round(time_taken, 2),
                    'met': met,
                    'breached': not met,
                    'percent_used': round((time_taken / target) * 100, 1) if target > 0 else 0
                }
                
                if not met and not ticket.sla_first_response_breached:
                    ticket.sla_first_response_breached = True
                    ticket.sla_first_response_breached_at = ticket.first_response_at
                    compliance['breaches'].append('first_response')
            else:
                # Check if we're approaching or have breached
                time_elapsed = (now - ticket.created_at).total_seconds() / 3600
                target = ticket.sla_first_response_hours
                percent_used = (time_elapsed / target) * 100 if target > 0 else 0
                breached = time_elapsed > target
                
                compliance['first_response'] = {
                    'target_hours': target,
                    'actual_hours': round(time_elapsed, 2),
                    'met': False,
                    'breached': breached,
                    'percent_used': round(percent_used, 1),
                    'time_remaining_hours': round(max(0, target - time_elapsed), 2)
                }
                
                if breached and not ticket.sla_first_response_breached:
                    ticket.sla_first_response_breached = True
                    ticket.sla_first_response_breached_at = now
                    compliance['breaches'].append('first_response')
        
        # Check resolution SLA
        if ticket.sla_target_hours:
            if ticket.resolved_at:
                # Calculate time taken
                time_taken = (ticket.resolved_at - ticket.created_at).total_seconds() / 3600
                target = ticket.sla_target_hours
                met = time_taken <= target
                
                compliance['resolution'] = {
                    'target_hours': target,
                    'actual_hours': round(time_taken, 2),
                    'met': met,
                    'breached': not met,
                    'percent_used': round((time_taken / target) * 100, 1) if target > 0 else 0
                }
                
                if not met and not ticket.sla_resolution_breached:
                    ticket.sla_resolution_breached = True
                    ticket.sla_resolution_breached_at = ticket.resolved_at
                    compliance['breaches'].append('resolution')
            else:
                # Check if we're approaching or have breached
                time_elapsed = (now - ticket.created_at).total_seconds() / 3600
                target = ticket.sla_target_hours
                percent_used = (time_elapsed / target) * 100 if target > 0 else 0
                breached = time_elapsed > target
                
                compliance['resolution'] = {
                    'target_hours': target,
                    'actual_hours': round(time_elapsed, 2),
                    'met': False,
                    'breached': breached,
                    'percent_used': round(percent_used, 1),
                    'time_remaining_hours': round(max(0, target - time_elapsed), 2)
                }
                
                if breached and not ticket.sla_resolution_breached:
                    ticket.sla_resolution_breached = True
                    ticket.sla_resolution_breached_at = now
                    compliance['breaches'].append('resolution')
                elif percent_used >= 80 and percent_used < 100:
                    # Send warning notification if approaching threshold
                    try:
                        from app.services.sla_notification_service import SLANotificationService
                        notification_service = SLANotificationService(self.db, self.tenant_id)
                        await notification_service.send_warning_notification(ticket, compliance, 'resolution')
                    except Exception as e:
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.warning(f"Failed to send SLA warning notification: {e}")
        
        # Update ticket if breaches detected
        if compliance['breaches']:
            await self.db.commit()
            await self.db.refresh(ticket)
            
            # Create breach alerts
            await self._create_breach_alerts(ticket, compliance)
        
        compliance['compliant'] = len(compliance['breaches']) == 0
        
        return compliance
    
    async def _create_breach_alerts(self, ticket: Ticket, compliance: Dict[str, Any]):
        """Create breach alert records and publish events"""
        policy = await self.db.get(SLAPolicy, ticket.sla_policy_id)
        if not policy:
            return
        
        alerts_to_create = []
        
        # First response breach
        if 'first_response' in compliance['breaches']:
            fr_data = compliance.get('first_response', {})
            breach_percent = int(fr_data.get('percent_used', 0))
            
            # Determine alert level
            alert_level = 'critical' if breach_percent >= policy.escalation_critical_percent else 'warning'
            
            alerts_to_create.append({
                'tenant_id': self.tenant_id,
                'ticket_id': ticket.id,
                'contract_id': ticket.related_contract_id,
                'sla_policy_id': ticket.sla_policy_id,
                'breach_type': 'first_response',
                'breach_percent': breach_percent,
                'alert_level': alert_level
            })
        
        # Resolution breach
        if 'resolution' in compliance['breaches']:
            res_data = compliance.get('resolution', {})
            breach_percent = int(res_data.get('percent_used', 0))
            
            # Determine alert level
            alert_level = 'critical' if breach_percent >= policy.escalation_critical_percent else 'warning'
            
            alerts_to_create.append({
                'tenant_id': self.tenant_id,
                'ticket_id': ticket.id,
                'contract_id': ticket.related_contract_id,
                'sla_policy_id': ticket.sla_policy_id,
                'breach_type': 'resolution',
                'breach_percent': breach_percent,
                'alert_level': alert_level
            })
        
        # Create alerts and publish events
        for alert_data in alerts_to_create:
            alert = SLABreachAlert(**alert_data)
            self.db.add(alert)
            
            # Publish WebSocket event
            try:
                from app.core.events import get_event_publisher
                event_publisher = get_event_publisher()
                await event_publisher.publish_sla_breach(
                    self.tenant_id,
                    alert.id,
                    ticket.id,
                    ticket.ticket_number,
                    alert_data['breach_type'],
                    alert_data['breach_percent'],
                    alert_data['alert_level'],
                    ticket.sla_policy_id,
                    policy.name if policy else None
                )
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to publish SLA breach event: {e}")
            
            # Send email notification
            try:
                from app.services.sla_notification_service import SLANotificationService
                notification_service = SLANotificationService(self.db, self.tenant_id)
                await notification_service.send_breach_notification(alert)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to send SLA breach email notification: {e}")
            
            # Workflow automation: Auto-escalate if policy allows
            if policy.auto_escalate_on_breach:
                await self._auto_escalate_ticket(ticket, alert_data, policy)
        
        await self.db.commit()
    
    async def _auto_escalate_ticket(self, ticket: Ticket, alert_data: Dict[str, Any], policy: SLAPolicy):
        """
        Automatically escalate ticket on SLA breach
        
        Actions:
        1. Increase priority (if not already urgent)
        2. Assign to admin/escalation team
        3. Add system comment about breach
        4. Update status if needed
        """
        try:
            from app.models.helpdesk import TicketComment, TicketPriority, TicketStatus
            from app.models.tenant import User
            from sqlalchemy import select
            
            changes_made = []
            
            # 1. Escalate priority
            if ticket.priority != TicketPriority.URGENT:
                old_priority = ticket.priority.value
                ticket.priority = TicketPriority.URGENT
                changes_made.append(f"Priority escalated from {old_priority} to URGENT")
            
            # 2. Assign to admin user if not assigned or assign to escalation team
            if not ticket.assigned_to_id:
                # Find admin users for this tenant
                admin_stmt = select(User).where(
                    User.tenant_id == self.tenant_id,
                    User.role == 'admin'
                ).limit(1)
                admin_result = await self.db.execute(admin_stmt)
                admin_user = admin_result.scalar_one_or_none()
                
                if admin_user:
                    ticket.assigned_to_id = admin_user.id
                    ticket.assigned_at = datetime.now(timezone.utc)
                    changes_made.append(f"Assigned to {admin_user.name or admin_user.email}")
            
            # 3. Update status if needed
            if ticket.status == TicketStatus.WAITING_CUSTOMER:
                ticket.status = TicketStatus.IN_PROGRESS
                changes_made.append("Status changed from WAITING_CUSTOMER to IN_PROGRESS")
            elif ticket.status == TicketStatus.OPEN:
                ticket.status = TicketStatus.IN_PROGRESS
                changes_made.append("Status changed from OPEN to IN_PROGRESS")
            
            # 4. Create system comment about breach and escalation
            if changes_made:
                breach_type_label = alert_data['breach_type'].replace('_', ' ').title()
                comment_text = (
                    f"🚨 SLA BREACH DETECTED - Auto-Escalation\n\n"
                    f"Breach Type: {breach_type_label}\n"
                    f"Breach Percentage: {alert_data['breach_percent']}%\n"
                    f"Alert Level: {alert_data['alert_level'].upper()}\n\n"
                    f"Automatic Actions Taken:\n"
                )
                for change in changes_made:
                    comment_text += f"• {change}\n"
                
                comment_text += (
                    f"\nThis ticket requires immediate attention to address the SLA breach. "
                    f"Please review and take appropriate action."
                )
                
                system_comment = TicketComment(
                    ticket_id=ticket.id,
                    comment=comment_text,
                    is_internal=True,
                    is_system=True,
                    author_id=None,  # System-generated
                    author_name="SLA Automation System"
                )
                self.db.add(system_comment)
                
                # Log to ticket history
                from app.models.helpdesk import TicketHistory
                history_entry = TicketHistory(
                    ticket_id=ticket.id,
                    action="sla_breach_escalation",
                    old_value=None,
                    new_value=f"{breach_type_label} breach - {alert_data['alert_level']}",
                    changed_by_user_id=None,
                    notes=f"Auto-escalated due to SLA breach: {', '.join(changes_made)}"
                )
                self.db.add(history_entry)
                
                # Publish escalation event via SLA breach event (already published above)
                # The ticket changes will be visible through normal ticket update mechanisms
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in auto-escalation workflow: {e}", exc_info=True)
    
    async def calculate_compliance_metrics(
        self,
        start_date: datetime,
        end_date: datetime,
        contract_id: Optional[str] = None,
        sla_policy_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculate SLA compliance metrics for a period
        """
        # Build query for tickets in period
        stmt = select(Ticket).where(
            and_(
                Ticket.tenant_id == self.tenant_id,
                Ticket.created_at >= start_date,
                Ticket.created_at <= end_date,
                Ticket.sla_policy_id.isnot(None)
            )
        )
        
        if contract_id:
            stmt = stmt.where(Ticket.related_contract_id == contract_id)
        if sla_policy_id:
            stmt = stmt.where(Ticket.sla_policy_id == sla_policy_id)
        
        result = await self.db.execute(stmt)
        tickets = result.scalars().all()
        
        total_tickets = len(tickets)
        first_response_met = 0
        resolution_met = 0
        first_response_breached = 0
        resolution_breached = 0
        
        total_fr_time = 0
        total_res_time = 0
        fr_count = 0
        res_count = 0
        
        for ticket in tickets:
            if ticket.first_response_at:
                fr_time = (ticket.first_response_at - ticket.created_at).total_seconds() / 3600
                total_fr_time += fr_time
                fr_count += 1
                
                if ticket.sla_first_response_hours and fr_time <= ticket.sla_first_response_hours:
                    first_response_met += 1
                else:
                    first_response_breached += 1
            
            if ticket.resolved_at:
                res_time = (ticket.resolved_at - ticket.created_at).total_seconds() / 3600
                total_res_time += res_time
                res_count += 1
                
                if ticket.sla_target_hours and res_time <= ticket.sla_target_hours:
                    resolution_met += 1
                else:
                    resolution_breached += 1
        
        avg_fr_time = total_fr_time / fr_count if fr_count > 0 else 0
        avg_res_time = total_res_time / res_count if res_count > 0 else 0
        
        fr_compliance_rate = (first_response_met / total_tickets * 100) if total_tickets > 0 else 0
        res_compliance_rate = (resolution_met / total_tickets * 100) if total_tickets > 0 else 0
        
        return {
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'total_tickets': total_tickets,
            'first_response': {
                'met': first_response_met,
                'breached': first_response_breached,
                'compliance_rate': round(fr_compliance_rate, 2),
                'average_time_hours': round(avg_fr_time, 2)
            },
            'resolution': {
                'met': resolution_met,
                'breached': resolution_breached,
                'compliance_rate': round(res_compliance_rate, 2),
                'average_time_hours': round(avg_res_time, 2)
            }
        }

