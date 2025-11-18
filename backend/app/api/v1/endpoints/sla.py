#!/usr/bin/env python3
"""
SLA Management API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel
import asyncio

from app.core.database import get_async_db, SessionLocal
from app.core.dependencies import get_current_user, get_current_tenant, check_permission
from app.models.tenant import User, Tenant
from app.models.helpdesk import TicketPriority, TicketType, SLAPolicy
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
    db: AsyncSession = Depends(get_async_db)
):
    """
    Check for SLA violations
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    Note: Wraps sync service calls in executor.
    """
    try:
        def _check_violations():
            sync_db = SessionLocal()
            try:
                service = SLAService(sync_db, current_user.tenant_id)
                return service.check_sla_violations()
            finally:
                sync_db.close()
        
        loop = asyncio.get_event_loop()
        violations = await loop.run_in_executor(None, _check_violations)
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
    db: AsyncSession = Depends(get_async_db)
):
    """
    Escalate a ticket
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    Note: Wraps sync service calls in executor.
    """
    try:
        def _escalate():
            sync_db = SessionLocal()
            try:
                service = SLAService(sync_db, current_user.tenant_id)
                return service.escalate_ticket(
                    ticket_id=ticket_id,
                    escalation_reason=escalation_reason,
                    escalated_by_id=current_user.id
                )
            finally:
                sync_db.close()
        
        loop = asyncio.get_event_loop()
        ticket = await loop.run_in_executor(None, _escalate)
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
    db: AsyncSession = Depends(get_async_db)
):
    """
    Automatically escalate tickets with SLA violations
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    Note: Wraps sync service calls in executor.
    """
    try:
        def _auto_escalate():
            sync_db = SessionLocal()
            try:
                service = SLAService(sync_db, current_user.tenant_id)
                return service.auto_escalate_violations()
            finally:
                sync_db.close()
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _auto_escalate)
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
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get SLA performance metrics
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    Note: Wraps sync service calls in executor.
    """
    try:
        def _get_metrics():
            sync_db = SessionLocal()
            try:
                service = SLAService(sync_db, current_user.tenant_id)
                return service.get_sla_metrics()
            finally:
                sync_db.close()
        
        loop = asyncio.get_event_loop()
        metrics = await loop.run_in_executor(None, _get_metrics)
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
    db: AsyncSession = Depends(get_async_db)
):
    """
    Create an SLA policy
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    Note: Wraps sync service calls in executor.
    """
    try:
        def _create_policy():
            sync_db = SessionLocal()
            try:
                service = SLAService(sync_db, current_user.tenant_id)
                return service.create_sla_policy(
                    name=policy_data.name,
                    description=policy_data.description,
                    first_response_hours=policy_data.first_response_hours,
                    resolution_hours=policy_data.resolution_hours,
                    priority=policy_data.priority,
                    ticket_type=policy_data.ticket_type,
                    customer_ids=policy_data.customer_ids
                )
            finally:
                sync_db.close()
        
        loop = asyncio.get_event_loop()
        policy = await loop.run_in_executor(None, _create_policy)
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
    db: AsyncSession = Depends(get_async_db)
):
    """
    List SLA policies
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        stmt = select(SLAPolicy).where(
            SLAPolicy.tenant_id == current_user.tenant_id
        )
        result = await db.execute(stmt)
        policies = result.scalars().all()
        return {"policies": policies}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing SLA policies: {str(e)}"
        )

