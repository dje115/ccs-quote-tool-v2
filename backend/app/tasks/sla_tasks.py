#!/usr/bin/env python3
"""
SLA Tasks
Celery tasks for SLA monitoring and auto-escalation
"""

from celery import shared_task
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import SessionLocal, get_async_db
from app.services.sla_service import SLAService
from app.services.sla_tracking_service import SLATrackingService
from app.services.sla_notification_service import SLANotificationService
from app.models.tenant import Tenant, User
from app.models.sla_compliance import SLAComplianceRecord, SLABreachAlert
from app.models.helpdesk import Ticket, SLAPolicy
from datetime import datetime, timedelta, date, timezone
from typing import Dict, Any, List
import logging
import asyncio

logger = logging.getLogger(__name__)


@shared_task(name="check_sla_violations")
def check_sla_violations_task(tenant_id: str = None):
    """
    Check for SLA violations and escalate if needed
    
    Args:
        tenant_id: Tenant ID to check (if None, check all tenants)
    
    Returns:
        Dictionary with violation check results
    """
    db: Session = SessionLocal()
    try:
        from app.models.tenant import Tenant
        
        if tenant_id:
            tenants = [db.query(Tenant).filter(Tenant.id == tenant_id).first()]
        else:
            tenants = db.query(Tenant).all()
        
        all_violations = []
        for tenant in tenants:
            if not tenant:
                continue
            service = SLAService(db, tenant.id)
            violations = service.check_sla_violations()
            
            logger.info(f"Found {len(violations)} SLA violations for tenant {tenant.id}")
            
            for violation in violations:
                violation['tenant_id'] = tenant.id
                all_violations.append(violation)
        
        return {
            'violations_count': len(all_violations),
            'violations': all_violations
        }
    except Exception as e:
        logger.error(f"Error checking SLA violations: {e}")
        raise
    finally:
        db.close()


@shared_task(name="auto_escalate_sla_violations")
def auto_escalate_sla_violations_task(tenant_id: str = None):
    """
    Automatically escalate tickets with SLA violations
    
    Args:
        tenant_id: Tenant ID (if None, process all tenants)
    
    Returns:
        Dictionary with escalation results
    """
    db: Session = SessionLocal()
    try:
        from app.models.tenant import Tenant
        
        if tenant_id:
            tenants = [db.query(Tenant).filter(Tenant.id == tenant_id).first()]
        else:
            tenants = db.query(Tenant).all()
        
        total_escalated = 0
        total_violations = 0
        
        for tenant in tenants:
            if not tenant:
                continue
            service = SLAService(db, tenant.id)
            result = service.auto_escalate_violations()
            
            total_escalated += result.get('escalated', 0)
            total_violations += result.get('violations_found', 0)
            
            logger.info(f"Auto-escalated {result['escalated']} tickets for tenant {tenant.id}")
        
        return {
            'total_violations_found': total_violations,
            'total_escalated': total_escalated
        }
    except Exception as e:
        logger.error(f"Error auto-escalating SLA violations: {e}")
        raise
    finally:
        db.close()


@shared_task(name="generate_sla_compliance_report")
def generate_sla_compliance_report_task(tenant_id: str = None, report_period: str = "daily"):
    """
    Generate and email SLA compliance reports
    
    Args:
        tenant_id: Tenant ID (if None, process all tenants)
        report_period: 'daily', 'weekly', or 'monthly'
    
    Returns:
        Dictionary with report generation results
    """
    db: Session = SessionLocal()
    try:
        from app.models.tenant import Tenant
        
        if tenant_id:
            tenants = [db.query(Tenant).filter(Tenant.id == tenant_id).first()]
        else:
            tenants = db.query(Tenant).all()
        
        results = []
        
        for tenant in tenants:
            if not tenant:
                continue
            
            try:
                # Calculate date range based on period
                end_date = date.today()
                if report_period == "daily":
                    start_date = end_date - timedelta(days=1)
                elif report_period == "weekly":
                    start_date = end_date - timedelta(days=7)
                elif report_period == "monthly":
                    start_date = end_date - timedelta(days=30)
                else:
                    start_date = end_date - timedelta(days=1)
                
                # Get compliance metrics using async service
                # Create a new async event loop for this task
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    async def get_compliance_metrics():
                        from app.core.database import async_session_maker
                        async with async_session_maker() as async_db:
                            tracking_service = SLATrackingService(async_db, tenant.id)
                            metrics = await tracking_service.calculate_compliance_metrics(
                                datetime.combine(start_date, datetime.min.time()).replace(tzinfo=timezone.utc),
                                datetime.combine(end_date, datetime.max.time()).replace(tzinfo=timezone.utc),
                                None, None
                            )
                            return metrics
                    
                    metrics = loop.run_until_complete(get_compliance_metrics())
                finally:
                    loop.close()
                
                # Get breach alerts
                breach_alerts = db.query(SLABreachAlert).filter(
                    SLABreachAlert.tenant_id == tenant.id,
                    SLABreachAlert.created_at >= datetime.combine(start_date, datetime.min.time()),
                    SLABreachAlert.created_at <= datetime.combine(end_date, datetime.max.time())
                ).all()
                
                # Get total tickets with SLA
                total_tickets = db.query(Ticket).filter(
                    Ticket.tenant_id == tenant.id,
                    Ticket.sla_policy_id.isnot(None),
                    Ticket.created_at >= datetime.combine(start_date, datetime.min.time()),
                    Ticket.created_at <= datetime.combine(end_date, datetime.max.time())
                ).count()
                
                # Get tenant admin users for email recipients
                admin_users = db.query(User).filter(
                    User.tenant_id == tenant.id,
                    User.role == 'admin'
                ).all()
                
                recipients = [user.email for user in admin_users if user.email]
                
                if not recipients:
                    logger.warning(f"No admin users found for tenant {tenant.id}, skipping report")
                    continue
                
                # Generate report email
                compliance_rate = metrics.get('compliance_rate', 0.0)
                total_breaches = len(breach_alerts)
                unacknowledged_breaches = len([a for a in breach_alerts if not a.acknowledged])
                
                # Build email content
                subject = f"SLA Compliance Report - {report_period.capitalize()} ({start_date} to {end_date})"
                
                body_lines = [
                    f"SLA Compliance Report - {report_period.capitalize()}",
                    f"Period: {start_date} to {end_date}",
                    "",
                    "=== Summary ===",
                    f"Compliance Rate: {compliance_rate:.1f}%",
                    f"Total Tickets with SLA: {total_tickets}",
                    f"Total Breaches: {total_breaches}",
                    f"Unacknowledged Breaches: {unacknowledged_breaches}",
                    "",
                    "=== First Response SLA ===",
                    f"Compliant: {metrics.get('first_response_compliant', 0)}",
                    f"Breached: {metrics.get('first_response_breached', 0)}",
                    f"Compliance Rate: {metrics.get('first_response_compliance_rate', 0.0):.1f}%",
                    "",
                    "=== Resolution SLA ===",
                    f"Compliant: {metrics.get('resolution_compliant', 0)}",
                    f"Breached: {metrics.get('resolution_breached', 0)}",
                    f"Compliance Rate: {metrics.get('resolution_compliance_rate', 0.0):.1f}%",
                    ""
                ]
                
                if unacknowledged_breaches > 0:
                    body_lines.extend([
                        "",
                        "=== Unacknowledged Breaches ===",
                    ])
                    for alert in breach_alerts[:10]:  # Limit to 10 most recent
                        if not alert.acknowledged:
                            body_lines.append(
                                f"- {alert.breach_type.replace('_', ' ').title()}: "
                                f"Ticket {alert.ticket_id[:8] if alert.ticket_id else 'N/A'} "
                                f"({alert.alert_level.upper()})"
                            )
                
                body_lines.extend([
                    "",
                    "---",
                    f"This is an automated {report_period} report from CCS Quote Tool.",
                    "For more details, please visit the SLA Dashboard."
                ])
                
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
                    
                    # Send email synchronously
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        fm = FastMail(conf)
                        loop.run_until_complete(fm.send_message(message))
                        logger.info(f"SLA compliance report sent to {len(recipients)} recipient(s) for tenant {tenant.id}")
                    finally:
                        loop.close()
                    
                    results.append({
                        'tenant_id': tenant.id,
                        'tenant_name': tenant.name,
                        'status': 'sent',
                        'recipients_count': len(recipients),
                        'compliance_rate': compliance_rate,
                        'total_breaches': total_breaches
                    })
                    
                except ImportError:
                    logger.warning("fastapi-mail not available, skipping email report")
                    results.append({
                        'tenant_id': tenant.id,
                        'tenant_name': tenant.name,
                        'status': 'skipped',
                        'reason': 'email_service_unavailable'
                    })
                except Exception as e:
                    logger.error(f"Failed to send SLA compliance report email for tenant {tenant.id}: {e}")
                    results.append({
                        'tenant_id': tenant.id,
                        'tenant_name': tenant.name,
                        'status': 'failed',
                        'error': str(e)
                    })
                    
            except Exception as e:
                logger.error(f"Error generating SLA report for tenant {tenant.id}: {e}", exc_info=True)
                results.append({
                    'tenant_id': tenant.id,
                    'tenant_name': tenant.name if tenant else 'Unknown',
                    'status': 'error',
                    'error': str(e)
                })
        
        return {
            'report_period': report_period,
            'total_tenants': len(tenants),
            'results': results
        }
        
    except Exception as e:
        logger.error(f"Error generating SLA compliance reports: {e}", exc_info=True)
        raise
    finally:
        db.close()

