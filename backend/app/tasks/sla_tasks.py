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

