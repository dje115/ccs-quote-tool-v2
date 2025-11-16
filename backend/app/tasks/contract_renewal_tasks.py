#!/usr/bin/env python3
"""
Celery tasks for contract renewal reminders and processing
"""

import asyncio
from typing import Dict, Any, List
from datetime import date, datetime, timedelta
import logging

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.services.contract_renewal_service import ContractRenewalService
from app.services.email_service import EmailService
from app.models.support_contract import (
    SupportContract, ContractRenewal, ContractStatus
)
from app.models.tenant import Tenant

logger = logging.getLogger(__name__)


@celery_app.task(
    name="contract_renewal.check_expiring_contracts",
    bind=True,
    max_retries=3,
    default_retry_delay=300
)
def check_expiring_contracts_task(self, days_ahead: int = 90):
    """
    Periodic task to check for contracts expiring soon and send reminders
    
    Args:
        days_ahead: Number of days ahead to check for expiring contracts
    
    Returns:
        dict: Results with contracts checked and reminders sent
    """
    logger.info(f"🔔 Starting contract renewal check (days_ahead={days_ahead})...")
    
    db = SessionLocal()
    email_service = EmailService()
    
    try:
        # Get all active tenants
        tenants = db.query(Tenant).filter(Tenant.is_active == True).all()
        
        total_contracts_checked = 0
        total_reminders_sent = 0
        total_renewals_created = 0
        total_crm_tasks_created = 0
        errors = []
        
        for tenant in tenants:
            try:
                renewal_service = ContractRenewalService(db, tenant.id)
                
                # Check expiring contracts
                expiring_contracts = renewal_service.check_expiring_contracts(
                    days_ahead=days_ahead,
                    notice_days=None  # Check all contracts within days_ahead
                )
                
                total_contracts_checked += len(expiring_contracts)
                
                for contract_info in expiring_contracts:
                    contract = contract_info['contract']
                    days_until_renewal = contract_info['days_until_renewal']
                    should_send_reminder = contract_info['should_send_reminder']
                    
                    if not should_send_reminder:
                        continue
                    
                    try:
                        # Create renewal record if it doesn't exist
                        existing_renewal = db.query(ContractRenewal).filter(
                            and_(
                                ContractRenewal.contract_id == contract.id,
                                ContractRenewal.renewal_date == contract.renewal_date,
                                ContractRenewal.status == "pending"
                            )
                        ).first()
                        
                        if not existing_renewal:
                            renewal = renewal_service.create_renewal_record(
                                contract_id=contract.id,
                                renewal_date=contract.renewal_date,
                                renewal_type="auto"
                            )
                            if renewal:
                                total_renewals_created += 1
                            else:
                                continue
                        else:
                            renewal = existing_renewal
                        
                        # Send email reminder (run async function in sync context)
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            email_sent = loop.run_until_complete(
                                send_renewal_reminder_email(
                                    db,
                                    email_service,
                                    contract,
                                    renewal,
                                    tenant
                                )
                            )
                        finally:
                            loop.close()
                        
                        if email_sent:
                            # Mark reminder as sent
                            # Get tenant admin user for reminder tracking
                            from app.models.tenant import User
                            admin_user = db.query(User).filter(
                                and_(
                                    User.tenant_id == tenant.id,
                                    User.is_active == True
                                )
                            ).order_by(User.created_at.asc()).first()
                            
                            if admin_user:
                                renewal_service.send_renewal_reminder(
                                    renewal.id,
                                    admin_user.id
                                )
                                total_reminders_sent += 1
                            
                            # Create CRM task
                            crm_task = renewal_service.create_crm_task_for_renewal(
                                contract,
                                renewal
                            )
                            if crm_task:
                                total_crm_tasks_created += 1
                        
                    except Exception as e:
                        error_msg = f"Error processing contract {contract.contract_number}: {str(e)}"
                        logger.error(error_msg)
                        errors.append(error_msg)
                        continue
                
            except Exception as e:
                error_msg = f"Error processing tenant {tenant.name}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
                continue
        
        result = {
            'success': True,
            'tenants_processed': len(tenants),
            'contracts_checked': total_contracts_checked,
            'reminders_sent': total_reminders_sent,
            'renewals_created': total_renewals_created,
            'crm_tasks_created': total_crm_tasks_created,
            'errors': errors
        }
        
        logger.info(f"✅ Contract renewal check completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Error in contract renewal check task: {e}")
        import traceback
        traceback.print_exc()
        raise self.retry(exc=e)
    
    finally:
        db.close()


async def send_renewal_reminder_email(
    db: SessionLocal,
    email_service: EmailService,
    contract: SupportContract,
    renewal: ContractRenewal,
    tenant: Tenant
) -> bool:
    """Send renewal reminder email"""
    try:
        customer = contract.customer
        if not customer or not customer.main_email:
            logger.warning(f"No email for customer {customer.id if customer else 'unknown'}")
            return False
        
        # Get tenant admin email for CC
        from app.models.tenant import User
        admin_users = db.query(User).filter(
            and_(
                User.tenant_id == tenant.id,
                User.is_active == True
            )
        ).limit(3).all()
        
        cc_emails = [user.email for user in admin_users if user.email]
        
        # Calculate days until renewal
        days_until = (renewal.renewal_date - date.today()).days
        
        # Format contract value
        contract_value = ""
        if contract.annual_value:
            contract_value = f"£{float(contract.annual_value):,.2f} per year"
        elif contract.monthly_value:
            contract_value = f"£{float(contract.monthly_value):,.2f} per month"
        
        # Email subject
        subject = f"Contract Renewal Reminder: {contract.contract_name} ({contract.contract_number})"
        
        # Email body (HTML)
        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2563eb;">Contract Renewal Reminder</h2>
                
                <p>Dear {customer.company_name},</p>
                
                <p>This is a reminder that your support contract is due for renewal soon.</p>
                
                <div style="background-color: #f3f4f6; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="margin-top: 0;">Contract Details</h3>
                    <p><strong>Contract Number:</strong> {contract.contract_number}</p>
                    <p><strong>Contract Name:</strong> {contract.contract_name}</p>
                    <p><strong>Contract Type:</strong> {contract.contract_type.value.replace('_', ' ').title()}</p>
                    <p><strong>Renewal Date:</strong> {renewal.renewal_date.strftime('%B %d, %Y')}</p>
                    <p><strong>Days Until Renewal:</strong> {days_until} days</p>
                    {f'<p><strong>Contract Value:</strong> {contract_value}</p>' if contract_value else ''}
                </div>
                
                {f'<p><strong>Auto-Renewal:</strong> {"Enabled" if contract.auto_renew else "Disabled"}</p>' if contract.auto_renew is not None else ''}
                
                <p>If you have any questions or would like to discuss renewal terms, please contact us.</p>
                
                <p>Best regards,<br>{tenant.name}</p>
            </div>
        </body>
        </html>
        """
        
        # Plain text version
        body_text = f"""
Contract Renewal Reminder

Dear {customer.company_name},

This is a reminder that your support contract is due for renewal soon.

Contract Details:
- Contract Number: {contract.contract_number}
- Contract Name: {contract.contract_name}
- Contract Type: {contract.contract_type.value.replace('_', ' ').title()}
- Renewal Date: {renewal.renewal_date.strftime('%B %d, %Y')}
- Days Until Renewal: {days_until} days
{f'- Contract Value: {contract_value}' if contract_value else ''}

{f'Auto-Renewal: {"Enabled" if contract.auto_renew else "Disabled"}' if contract.auto_renew is not None else ''}

If you have any questions or would like to discuss renewal terms, please contact us.

Best regards,
{tenant.name}
        """
        
        # Send email
        success = await email_service.send_email(
            to=customer.main_email,
            subject=subject,
            body=body_text,
            body_html=body_html,
            cc=cc_emails if cc_emails else None
        )
        
        if success:
            logger.info(f"✅ Renewal reminder email sent for contract {contract.contract_number}")
        else:
            logger.warning(f"⚠️ Failed to send renewal reminder email for contract {contract.contract_number}")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ Error sending renewal reminder email: {e}")
        import traceback
        traceback.print_exc()
        return False


@celery_app.task(
    name="contract_renewal.process_auto_renewals",
    bind=True,
    max_retries=3,
    default_retry_delay=300
)
def process_auto_renewals_task(self):
    """
    Process contracts that are due for auto-renewal today
    
    Returns:
        dict: Results with contracts renewed
    """
    logger.info("🔄 Starting auto-renewal processing...")
    
    db = SessionLocal()
    
    try:
        # Get all approved renewals due today
        today = date.today()
        pending_renewals = db.query(ContractRenewal).filter(
            and_(
                ContractRenewal.renewal_date == today,
                ContractRenewal.status == "approved"
            )
        ).all()
        
        total_renewed = 0
        errors = []
        
        for renewal in pending_renewals:
            try:
                contract = renewal.contract
                if not contract or contract.tenant_id != renewal.tenant_id:
                    continue
                
                renewal_service = ContractRenewalService(db, renewal.tenant_id)
                renewed_contract = renewal_service.complete_renewal(renewal.id)
                
                if renewed_contract:
                    total_renewed += 1
                    logger.info(f"✅ Auto-renewed contract {renewed_contract.contract_number}")
                
            except Exception as e:
                error_msg = f"Error auto-renewing contract {renewal.contract_id}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
                continue
        
        result = {
            'success': True,
            'renewals_processed': len(pending_renewals),
            'contracts_renewed': total_renewed,
            'errors': errors
        }
        
        logger.info(f"✅ Auto-renewal processing completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Error in auto-renewal processing task: {e}")
        import traceback
        traceback.print_exc()
        raise self.retry(exc=e)
    
    finally:
        db.close()

