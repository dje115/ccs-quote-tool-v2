#!/usr/bin/env python3
"""
SLA Tasks
Celery tasks for SLA monitoring and auto-escalation
"""

from celery import shared_task
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.services.sla_service import SLAService
import logging

logger = logging.getLogger(__name__)


@shared_task(name="check_sla_violations")
def check_sla_violations_task(tenant_id: str):
    """
    Check for SLA violations and escalate if needed
    
    Args:
        tenant_id: Tenant ID to check
    
    Returns:
        Dictionary with violation check results
    """
    db: Session = SessionLocal()
    try:
        service = SLAService(db, tenant_id)
        violations = service.check_sla_violations()
        
        logger.info(f"Found {len(violations)} SLA violations for tenant {tenant_id}")
        
        return {
            'tenant_id': tenant_id,
            'violations_count': len(violations),
            'violations': violations
        }
    except Exception as e:
        logger.error(f"Error checking SLA violations: {e}")
        raise
    finally:
        db.close()


@shared_task(name="auto_escalate_sla_violations")
def auto_escalate_sla_violations_task(tenant_id: str):
    """
    Automatically escalate tickets with SLA violations
    
    Args:
        tenant_id: Tenant ID
    
    Returns:
        Dictionary with escalation results
    """
    db: Session = SessionLocal()
    try:
        service = SLAService(db, tenant_id)
        result = service.auto_escalate_violations()
        
        logger.info(f"Auto-escalated {result['escalated']} tickets for tenant {tenant_id}")
        
        return result
    except Exception as e:
        logger.error(f"Error auto-escalating SLA violations: {e}")
        raise
    finally:
        db.close()

