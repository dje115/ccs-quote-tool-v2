#!/usr/bin/env python3
"""
SLA Management API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.core.dependencies import get_db, get_current_user, get_current_tenant, check_permission
from app.models.tenant import User, Tenant
from app.models.helpdesk import TicketPriority, TicketType
from app.services.sla_service import SLAService

router = APIRouter(prefix="/sla", tags=["SLA"])


class SLAPolicyCreate(BaseModel):
    name: str
    description: Optional[str] = None
    first_response_hours: Optional[int] = None
    resolution_hours: Optional[int] = None
    priority: Optional[TicketPriority] = None
    ticket_type: Optional[TicketType] = None
    customer_ids: Optional[List[str]] = None


@router.get("/violations")
async def check_sla_violations(
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Check for SLA violations"""
    try:
        service = SLAService(db, current_user.tenant_id)
        violations = service.check_sla_violations()
        return {"violations": violations, "count": len(violations)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking SLA violations: {str(e)}"
        )


@router.post("/escalate/{ticket_id}")
async def escalate_ticket(
    ticket_id: str,
    escalation_reason: str = Query(..., min_length=1),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Escalate a ticket"""
    try:
        service = SLAService(db, current_user.tenant_id)
        ticket = service.escalate_ticket(
            ticket_id=ticket_id,
            escalation_reason=escalation_reason,
            escalated_by_id=current_user.id
        )
        return ticket
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error escalating ticket: {str(e)}"
        )


@router.post("/auto-escalate")
async def auto_escalate_violations(
    current_user: User = Depends(check_permission("sla:manage")),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Automatically escalate tickets with SLA violations"""
    try:
        service = SLAService(db, current_user.tenant_id)
        result = service.auto_escalate_violations()
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error auto-escalating violations: {str(e)}"
        )


@router.get("/metrics")
async def get_sla_metrics(
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Get SLA performance metrics"""
    try:
        service = SLAService(db, current_user.tenant_id)
        metrics = service.get_sla_metrics()
        return metrics
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting SLA metrics: {str(e)}"
        )


@router.post("/policies", status_code=status.HTTP_201_CREATED)
async def create_sla_policy(
    policy_data: SLAPolicyCreate,
    current_user: User = Depends(check_permission("sla:manage")),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Create an SLA policy"""
    try:
        service = SLAService(db, current_user.tenant_id)
        policy = service.create_sla_policy(
            name=policy_data.name,
            description=policy_data.description,
            first_response_hours=policy_data.first_response_hours,
            resolution_hours=policy_data.resolution_hours,
            priority=policy_data.priority,
            ticket_type=policy_data.ticket_type,
            customer_ids=policy_data.customer_ids
        )
        return policy
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating SLA policy: {str(e)}"
        )


@router.get("/policies")
async def list_sla_policies(
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """List SLA policies"""
    try:
        from app.models.helpdesk import SLAPolicy
        policies = db.query(SLAPolicy).filter(
            SLAPolicy.tenant_id == current_user.tenant_id
        ).all()
        return {"policies": policies}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing SLA policies: {str(e)}"
        )

