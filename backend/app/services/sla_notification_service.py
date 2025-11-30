#!/usr/bin/env python3
"""
SLA Notification Service
Handles email notifications for SLA breaches and compliance updates
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.helpdesk import Ticket, SLAPolicy
from app.models.sla_compliance import SLABreachAlert
from app.models.tenant import Tenant, User
from app.models.crm import Customer

logger = logging.getLogger(__name__)


class SLANotificationService:
    """Service for sending SLA-related notifications"""
    
    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
    
    async def send_breach_notification(self, alert: SLABreachAlert) -> bool:
        """
        Send email notification for SLA breach
        
        Args:
            alert: SLA breach alert record
        
        Returns:
            True if notification sent successfully, False otherwise
        """
        try:
            # Get ticket details
            ticket = None
            if alert.ticket_id:
                ticket_stmt = select(Ticket).where(Ticket.id == alert.ticket_id)
                ticket_result = await self.db.execute(ticket_stmt)
                ticket = ticket_result.scalar_one_or_none()
            
            # Get SLA policy
            policy = None
            if alert.sla_policy_id:
                policy_stmt = select(SLAPolicy).where(SLAPolicy.id == alert.sla_policy_id)
                policy_result = await self.db.execute(policy_stmt)
                policy = policy_result.scalar_one_or_none()
            
            # Get tenant
            tenant_stmt = select(Tenant).where(Tenant.id == self.tenant_id)
            tenant_result = await self.db.execute(tenant_stmt)
            tenant = tenant_result.scalar_one_or_none()
            
            if not tenant:
                logger.error(f"Tenant {self.tenant_id} not found for SLA breach notification")
                return False
            
            # Get customer if ticket exists
            customer = None
            if ticket and ticket.customer_id:
                customer_stmt = select(Customer).where(Customer.id == ticket.customer_id)
                customer_result = await self.db.execute(customer_stmt)
                customer = customer_result.scalar_one_or_none()
            
            # Get assigned user if ticket exists
            assigned_user = None
            if ticket and ticket.assigned_to_id:
                user_stmt = select(User).where(User.id == ticket.assigned_to_id)
                user_result = await self.db.execute(user_stmt)
                assigned_user = user_result.scalar_one_or_none()
            
            # Determine recipients
            recipients = []
            
            # Add assigned user
            if assigned_user and assigned_user.email:
                recipients.append(assigned_user.email)
            
            # Add tenant admin users (users with admin role)
            admin_stmt = select(User).where(
                User.tenant_id == self.tenant_id,
                User.role == 'admin'
            )
            admin_result = await self.db.execute(admin_stmt)
            admins = admin_result.scalars().all()
            for admin in admins:
                if admin.email and admin.email not in recipients:
                    recipients.append(admin.email)
            
            if not recipients:
                logger.warning(f"No recipients found for SLA breach notification {alert.id}")
                return False
            
            # Prepare email content
            breach_type_label = "First Response" if alert.breach_type == "first_response" else "Resolution"
            severity = "CRITICAL" if alert.alert_level == "critical" else "WARNING"
            
            subject = f"[{severity}] SLA Breach Alert: {breach_type_label} - {ticket.ticket_number if ticket else 'N/A'}"
            
            # Build email body
            body_lines = [
                f"SLA Breach Alert - {severity}",
                "",
                f"Breach Type: {breach_type_label}",
                f"Breach Percentage: {alert.breach_percent}%",
                f"Alert Level: {alert.alert_level.upper()}",
                ""
            ]
            
            if ticket:
                body_lines.extend([
                    f"Ticket Number: {ticket.ticket_number}",
                    f"Ticket Subject: {ticket.subject}",
                    f"Ticket Priority: {ticket.priority.value if ticket.priority else 'N/A'}",
                    ""
                ])
            
            if customer:
                body_lines.append(f"Customer: {customer.company_name}")
            
            if policy:
                body_lines.extend([
                    f"SLA Policy: {policy.name}",
                    ""
                ])
            
            body_lines.extend([
                f"Time of Breach: {alert.created_at.strftime('%Y-%m-%d %H:%M:%S UTC') if alert.created_at else 'N/A'}",
                "",
                "Please review this ticket immediately to address the SLA breach.",
                "",
                f"View Ticket: {ticket.ticket_number if ticket else 'N/A'}"
            ])
            
            email_body = "\n".join(body_lines)
            
            # Send email using fastapi-mail
            try:
                from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
                from app.core.config import settings
                
                # Create email configuration
                conf = ConnectionConfig(
                    MAIL_USERNAME=settings.SMTP_USERNAME,
                    MAIL_PASSWORD=settings.SMTP_PASSWORD,
                    MAIL_FROM=settings.SMTP_FROM_EMAIL,
                    MAIL_PORT=settings.SMTP_PORT,
                    MAIL_SERVER=settings.SMTP_HOST,
                    MAIL_FROM_NAME=settings.SMTP_FROM_NAME,
                    MAIL_STARTTLS=settings.SMTP_TLS,
                    MAIL_SSL_TLS=False,
                    USE_CREDENTIALS=True,
                    VALIDATE_CERTS=False
                )
                
                message = MessageSchema(
                    subject=subject,
                    recipients=recipients,
                    body=email_body,
                    subtype="plain"
                )
                
                fm = FastMail(conf)
                await fm.send_message(message)
                
                logger.info(f"SLA breach notification sent to {len(recipients)} recipient(s) for alert {alert.id}")
                return True
                
            except ImportError:
                logger.warning("fastapi-mail not available, skipping email notification")
                return False
            except Exception as e:
                logger.error(f"Failed to send SLA breach email: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending SLA breach notification: {e}", exc_info=True)
            return False
    
    async def send_warning_notification(self, ticket: Ticket, compliance: Dict[str, Any], warning_type: str) -> bool:
        """
        Send warning notification when approaching SLA threshold
        
        Args:
            ticket: Ticket that's approaching SLA breach
            compliance: Current compliance data
            warning_type: 'first_response' or 'resolution'
        
        Returns:
            True if notification sent successfully, False otherwise
        """
        try:
            # Get SLA policy
            policy = None
            if ticket.sla_policy_id:
                policy_stmt = select(SLAPolicy).where(SLAPolicy.id == ticket.sla_policy_id)
                policy_result = await self.db.execute(policy_stmt)
                policy = policy_result.scalar_one_or_none()
            
            if not policy:
                return False
            
            # Check if we're in warning threshold
            warning_data = compliance.get(warning_type, {})
            percent_used = warning_data.get('percent_used', 0)
            
            if percent_used < policy.escalation_warning_percent:
                return False  # Not yet at warning threshold
            
            # Get assigned user
            assigned_user = None
            if ticket.assigned_to_id:
                user_stmt = select(User).where(User.id == ticket.assigned_to_id)
                user_result = await self.db.execute(user_stmt)
                assigned_user = user_result.scalar_one_or_none()
            
            recipients = []
            if assigned_user and assigned_user.email:
                recipients.append(assigned_user.email)
            
            if not recipients:
                return False
            
            # Prepare email
            warning_type_label = "First Response" if warning_type == "first_response" else "Resolution"
            time_remaining = warning_data.get('time_remaining_hours', 0)
            
            subject = f"[WARNING] Approaching SLA Limit: {warning_type_label} - {ticket.ticket_number}"
            
            body_lines = [
                f"SLA Warning - {warning_type_label}",
                "",
                f"Ticket {ticket.ticket_number} is approaching its SLA limit.",
                "",
                f"Current Usage: {percent_used:.1f}% of SLA time",
                f"Time Remaining: {time_remaining:.1f} hours",
                "",
                f"Ticket Subject: {ticket.subject}",
                f"Ticket Priority: {ticket.priority.value if ticket.priority else 'N/A'}",
                "",
                "Please take action to ensure SLA compliance.",
                "",
                f"View Ticket: {ticket.ticket_number}"
            ]
            
            email_body = "\n".join(body_lines)
            
            # Send email
            try:
                from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
                from app.core.config import settings
                
                conf = ConnectionConfig(
                    MAIL_USERNAME=settings.SMTP_USERNAME,
                    MAIL_PASSWORD=settings.SMTP_PASSWORD,
                    MAIL_FROM=settings.SMTP_FROM_EMAIL,
                    MAIL_PORT=settings.SMTP_PORT,
                    MAIL_SERVER=settings.SMTP_HOST,
                    MAIL_FROM_NAME=settings.SMTP_FROM_NAME,
                    MAIL_STARTTLS=settings.SMTP_TLS,
                    MAIL_SSL_TLS=False,
                    USE_CREDENTIALS=True,
                    VALIDATE_CERTS=False
                )
                
                message = MessageSchema(
                    subject=subject,
                    recipients=recipients,
                    body=email_body,
                    subtype="plain"
                )
                
                fm = FastMail(conf)
                await fm.send_message(message)
                
                logger.info(f"SLA warning notification sent for ticket {ticket.ticket_number}")
                return True
                
            except ImportError:
                logger.warning("fastapi-mail not available, skipping email notification")
                return False
            except Exception as e:
                logger.error(f"Failed to send SLA warning email: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending SLA warning notification: {e}", exc_info=True)
            return False

