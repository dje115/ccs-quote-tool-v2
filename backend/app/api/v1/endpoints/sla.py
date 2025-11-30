#!/usr/bin/env python3
"""
SLA Management API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, update, func
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timezone, timedelta
from pydantic import BaseModel, Field
import uuid

from app.core.database import get_async_db
from app.core.dependencies import get_current_user, get_current_tenant
from app.models.tenant import User, Tenant
from app.models.helpdesk import SLAPolicy, TicketPriority, TicketType
from app.models.sla_compliance import SLAComplianceRecord, SLABreachAlert
from app.models.support_contract import SupportContract
from app.models.helpdesk import Ticket
from app.services.sla_tracking_service import SLATrackingService

router = APIRouter(prefix="/sla", tags=["sla"])


# Pydantic Models
class SLAPolicyCreate(BaseModel):
    name: str
    description: Optional[str] = None
    sla_level: Optional[str] = None
    
    # Response time targets
    first_response_hours: Optional[int] = None
    first_response_hours_urgent: Optional[int] = None
    first_response_hours_high: Optional[int] = None
    first_response_hours_medium: Optional[int] = None
    first_response_hours_low: Optional[int] = None
    
    # Resolution time targets
    resolution_hours: Optional[int] = None
    resolution_hours_urgent: Optional[int] = None
    resolution_hours_high: Optional[int] = None
    resolution_hours_medium: Optional[int] = None
    resolution_hours_low: Optional[int] = None
    
    # Availability
    uptime_target: Optional[int] = None  # e.g., 9990 for 99.90%
    availability_hours: Optional[str] = None
    
    # Business hours
    business_hours_start: Optional[str] = None
    business_hours_end: Optional[str] = None
    business_days: Optional[List[str]] = None
    timezone: str = "Europe/London"
    
    # Escalation
    escalation_warning_percent: int = 80
    escalation_critical_percent: int = 95
    auto_escalate_on_breach: bool = True
    
    # Conditions
    priority: Optional[str] = None
    ticket_type: Optional[str] = None
    customer_ids: Optional[List[str]] = None
    contract_type: Optional[str] = None
    
    is_active: bool = True
    is_default: bool = False


class SLAPolicyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    sla_level: Optional[str] = None
    first_response_hours: Optional[int] = None
    first_response_hours_urgent: Optional[int] = None
    first_response_hours_high: Optional[int] = None
    first_response_hours_medium: Optional[int] = None
    first_response_hours_low: Optional[int] = None
    resolution_hours: Optional[int] = None
    resolution_hours_urgent: Optional[int] = None
    resolution_hours_high: Optional[int] = None
    resolution_hours_medium: Optional[int] = None
    resolution_hours_low: Optional[int] = None
    uptime_target: Optional[int] = None
    availability_hours: Optional[str] = None
    business_hours_start: Optional[str] = None
    business_hours_end: Optional[str] = None
    business_days: Optional[List[str]] = None
    timezone: Optional[str] = None
    escalation_warning_percent: Optional[int] = None
    escalation_critical_percent: Optional[int] = None
    auto_escalate_on_breach: Optional[bool] = None
    priority: Optional[str] = None
    ticket_type: Optional[str] = None
    customer_ids: Optional[List[str]] = None
    contract_type: Optional[str] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class SLAPolicyResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    sla_level: Optional[str]
    first_response_hours: Optional[int]
    first_response_hours_urgent: Optional[int]
    first_response_hours_high: Optional[int]
    first_response_hours_medium: Optional[int]
    first_response_hours_low: Optional[int]
    resolution_hours: Optional[int]
    resolution_hours_urgent: Optional[int]
    resolution_hours_high: Optional[int]
    resolution_hours_medium: Optional[int]
    resolution_hours_low: Optional[int]
    uptime_target: Optional[int]
    availability_hours: Optional[str]
    business_hours_start: Optional[str]
    business_hours_end: Optional[str]
    business_days: Optional[List[str]]
    timezone: str
    escalation_warning_percent: int
    escalation_critical_percent: int
    auto_escalate_on_breach: bool
    priority: Optional[str]
    ticket_type: Optional[str]
    customer_ids: Optional[List[str]]
    contract_type: Optional[str]
    is_active: bool
    is_default: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SLAComplianceResponse(BaseModel):
    period: Dict[str, str]
    total_tickets: int
    first_response: Dict[str, Any]
    resolution: Dict[str, Any]


class SLABreachAlertResponse(BaseModel):
    id: str
    ticket_id: Optional[str]
    contract_id: Optional[str]
    sla_policy_id: str
    breach_type: str
    breach_percent: int
    alert_level: str
    acknowledged: bool
    acknowledged_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# Endpoints
@router.get("/policies", response_model=List[SLAPolicyResponse])
async def list_sla_policies(
    is_active: Optional[bool] = Query(None),
    is_default: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """List SLA policies for current tenant"""
    try:
        stmt = select(SLAPolicy).where(
            SLAPolicy.tenant_id == current_tenant.id
        )
        
        if is_active is not None:
            stmt = stmt.where(SLAPolicy.is_active == is_active)
        if is_default is not None:
            stmt = stmt.where(SLAPolicy.is_default == is_default)
        
        stmt = stmt.order_by(SLAPolicy.is_default.desc(), SLAPolicy.name)
        
        result = await db.execute(stmt)
        policies = result.scalars().all()
        
        return [SLAPolicyResponse.model_validate(p) for p in policies]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/policies/{policy_id}", response_model=SLAPolicyResponse)
async def get_sla_policy(
    policy_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """Get a specific SLA policy"""
    try:
        stmt = select(SLAPolicy).where(
            and_(
                SLAPolicy.id == policy_id,
                SLAPolicy.tenant_id == current_tenant.id
            )
        )
        result = await db.execute(stmt)
        policy = result.scalar_one_or_none()
        
        if not policy:
            raise HTTPException(status_code=404, detail="SLA policy not found")
        
        return SLAPolicyResponse.model_validate(policy)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/policies", response_model=SLAPolicyResponse, status_code=status.HTTP_201_CREATED)
async def create_sla_policy(
    policy_data: SLAPolicyCreate,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """Create a new SLA policy"""
    try:
        # If setting as default, unset other defaults
        if policy_data.is_default:
            stmt = update(SLAPolicy).where(
                and_(
                    SLAPolicy.tenant_id == current_tenant.id,
                    SLAPolicy.is_default == True
                )
            ).values(is_default=False)
            await db.execute(stmt)
        
        policy = SLAPolicy(
            tenant_id=current_tenant.id,
            name=policy_data.name,
            description=policy_data.description,
            sla_level=policy_data.sla_level,
            first_response_hours=policy_data.first_response_hours,
            first_response_hours_urgent=policy_data.first_response_hours_urgent,
            first_response_hours_high=policy_data.first_response_hours_high,
            first_response_hours_medium=policy_data.first_response_hours_medium,
            first_response_hours_low=policy_data.first_response_hours_low,
            resolution_hours=policy_data.resolution_hours,
            resolution_hours_urgent=policy_data.resolution_hours_urgent,
            resolution_hours_high=policy_data.resolution_hours_high,
            resolution_hours_medium=policy_data.resolution_hours_medium,
            resolution_hours_low=policy_data.resolution_hours_low,
            uptime_target=policy_data.uptime_target,
            availability_hours=policy_data.availability_hours,
            business_hours_start=policy_data.business_hours_start,
            business_hours_end=policy_data.business_hours_end,
            business_days=policy_data.business_days,
            timezone=policy_data.timezone,
            escalation_warning_percent=policy_data.escalation_warning_percent,
            escalation_critical_percent=policy_data.escalation_critical_percent,
            auto_escalate_on_breach=policy_data.auto_escalate_on_breach,
            priority=TicketPriority(policy_data.priority) if policy_data.priority else None,
            ticket_type=TicketType(policy_data.ticket_type) if policy_data.ticket_type else None,
            customer_ids=policy_data.customer_ids,
            contract_type=policy_data.contract_type,
            is_active=policy_data.is_active,
            is_default=policy_data.is_default
        )
        
        db.add(policy)
        await db.commit()
        await db.refresh(policy)
        
        return SLAPolicyResponse.model_validate(policy)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/policies/{policy_id}", response_model=SLAPolicyResponse)
async def update_sla_policy(
    policy_id: str,
    policy_data: SLAPolicyUpdate,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """Update an SLA policy"""
    try:
        stmt = select(SLAPolicy).where(
            and_(
                SLAPolicy.id == policy_id,
                SLAPolicy.tenant_id == current_tenant.id
            )
        )
        result = await db.execute(stmt)
        policy = result.scalar_one_or_none()
        
        if not policy:
            raise HTTPException(status_code=404, detail="SLA policy not found")
        
        # If setting as default, unset other defaults
        if policy_data.is_default is True:
            update_stmt = update(SLAPolicy).where(
                and_(
                    SLAPolicy.tenant_id == current_tenant.id,
                    SLAPolicy.is_default == True,
                    SLAPolicy.id != policy_id
                )
            ).values(is_default=False)
            await db.execute(update_stmt)
        
        # Update fields
        update_data = policy_data.model_dump(exclude_unset=True)
        if 'priority' in update_data and update_data['priority']:
            update_data['priority'] = TicketPriority(update_data['priority'])
        if 'ticket_type' in update_data and update_data['ticket_type']:
            update_data['ticket_type'] = TicketType(update_data['ticket_type'])
        
        for key, value in update_data.items():
            if value is not None:
                setattr(policy, key, value)
        
        await db.commit()
        await db.refresh(policy)
        
        return SLAPolicyResponse.model_validate(policy)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/policies/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sla_policy(
    policy_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """Delete an SLA policy"""
    try:
        stmt = select(SLAPolicy).where(
            and_(
                SLAPolicy.id == policy_id,
                SLAPolicy.tenant_id == current_tenant.id
            )
        )
        result = await db.execute(stmt)
        policy = result.scalar_one_or_none()
        
        if not policy:
            raise HTTPException(status_code=404, detail="SLA policy not found")
        
        await db.delete(policy)
        await db.commit()
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compliance", response_model=SLAComplianceResponse)
async def get_sla_compliance(
    start_date: date = Query(..., description="Start date for compliance period"),
    end_date: date = Query(..., description="End date for compliance period"),
    contract_id: Optional[str] = Query(None),
    sla_policy_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """Get SLA compliance metrics for a period"""
    try:
        start_dt = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        end_dt = datetime.combine(end_date, datetime.max.time()).replace(tzinfo=timezone.utc)
        
        tracking_service = SLATrackingService(db, current_tenant.id)
        metrics = await tracking_service.calculate_compliance_metrics(
            start_dt, end_dt, contract_id, sla_policy_id
        )
        
        return SLAComplianceResponse(**metrics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/breach-alerts", response_model=List[SLABreachAlertResponse])
async def list_breach_alerts(
    acknowledged: Optional[bool] = Query(None),
    alert_level: Optional[str] = Query(None),
    ticket_id: Optional[str] = Query(None),
    contract_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """List SLA breach alerts"""
    try:
        stmt = select(SLABreachAlert).where(
            SLABreachAlert.tenant_id == current_tenant.id
        )
        
        if acknowledged is not None:
            # Handle string "false" or "true" from query params
            if isinstance(acknowledged, str):
                acknowledged = acknowledged.lower() == 'true'
            stmt = stmt.where(SLABreachAlert.acknowledged == acknowledged)
        if alert_level:
            stmt = stmt.where(SLABreachAlert.alert_level == alert_level)
        if ticket_id:
            stmt = stmt.where(SLABreachAlert.ticket_id == ticket_id)
        if contract_id:
            stmt = stmt.where(SLABreachAlert.contract_id == contract_id)
        
        stmt = stmt.order_by(SLABreachAlert.created_at.desc())
        
        result = await db.execute(stmt)
        alerts = result.scalars().all()
        
        return [SLABreachAlertResponse.model_validate(a) for a in alerts]
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error listing breach alerts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error listing breach alerts: {str(e)}")


@router.post("/breach-alerts/{alert_id}/acknowledge", response_model=SLABreachAlertResponse)
async def acknowledge_breach_alert(
    alert_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """Acknowledge a breach alert"""
    try:
        stmt = select(SLABreachAlert).where(
            and_(
                SLABreachAlert.id == alert_id,
                SLABreachAlert.tenant_id == current_tenant.id
            )
        )
        result = await db.execute(stmt)
        alert = result.scalar_one_or_none()
        
        if not alert:
            raise HTTPException(status_code=404, detail="Breach alert not found")
        
        alert.acknowledged = True
        alert.acknowledged_at = datetime.now(timezone.utc)
        alert.acknowledged_by = current_user.id
        
        await db.commit()
        await db.refresh(alert)
        
        return SLABreachAlertResponse.model_validate(alert)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tickets/{ticket_id}/compliance")
async def get_ticket_sla_compliance(
    ticket_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """Get SLA compliance status for a specific ticket"""
    try:
        stmt = select(Ticket).where(
            and_(
                Ticket.id == ticket_id,
                Ticket.tenant_id == current_tenant.id
            )
        )
        result = await db.execute(stmt)
        ticket = result.scalar_one_or_none()
        
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        tracking_service = SLATrackingService(db, current_tenant.id)
        compliance = await tracking_service.check_ticket_sla_compliance(ticket)
        
        return compliance
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance/by-agent", response_model=Dict[str, Any])
async def get_sla_performance_by_agent(
    start_date: date = Query(..., description="Start date for performance period"),
    end_date: date = Query(..., description="End date for performance period"),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """Get SLA performance metrics grouped by agent/team"""
    try:
        from sqlalchemy import func
        from app.models.helpdesk import Ticket
        from app.models.tenant import User
        
        start_dt = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        end_dt = datetime.combine(end_date, datetime.max.time()).replace(tzinfo=timezone.utc)
        
        # Query tickets with assigned users
        stmt = select(
            Ticket.assigned_to_id,
            User.name.label('agent_name'),
            User.email.label('agent_email'),
            func.count(Ticket.id).label('total_tickets'),
            func.sum(func.cast(Ticket.sla_first_response_breached, int)).label('fr_breaches'),
            func.sum(func.cast(Ticket.sla_resolution_breached, int)).label('res_breaches'),
            func.avg(
                func.extract('epoch', Ticket.first_response_at - Ticket.created_at) / 3600
            ).label('avg_fr_hours'),
            func.avg(
                func.extract('epoch', Ticket.resolved_at - Ticket.created_at) / 3600
            ).label('avg_res_hours')
        ).join(
            User, Ticket.assigned_to_id == User.id, isouter=True
        ).where(
            and_(
                Ticket.tenant_id == current_tenant.id,
                Ticket.created_at >= start_dt,
                Ticket.created_at <= end_dt,
                Ticket.assigned_to_id.isnot(None)
            )
        ).group_by(
            Ticket.assigned_to_id,
            User.name,
            User.email
        )
        
        result = await db.execute(stmt)
        rows = result.all()
        
        performance_data = []
        for row in rows:
            total = row.total_tickets or 0
            fr_breaches = row.fr_breaches or 0
            res_breaches = row.res_breaches or 0
            
            fr_compliance = ((total - fr_breaches) / total * 100) if total > 0 else 0
            res_compliance = ((total - res_breaches) / total * 100) if total > 0 else 0
            
            performance_data.append({
                'agent_id': row.assigned_to_id,
                'agent_name': row.agent_name or 'Unassigned',
                'agent_email': row.agent_email,
                'total_tickets': total,
                'first_response': {
                    'breaches': fr_breaches,
                    'compliance_rate': round(fr_compliance, 2),
                    'average_hours': round(row.avg_fr_hours or 0, 2)
                },
                'resolution': {
                    'breaches': res_breaches,
                    'compliance_rate': round(res_compliance, 2),
                    'average_hours': round(row.avg_res_hours or 0, 2)
                }
            })
        
        return {
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'performance_by_agent': performance_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notification-rules")
async def get_notification_rules(
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """Get SLA notification rules for the tenant"""
    try:
        # Get all active SLA policies with their notification settings
        stmt = select(SLAPolicy).where(
            and_(
                SLAPolicy.tenant_id == current_tenant.id,
                SLAPolicy.is_active == True
            )
        )
        result = await db.execute(stmt)
        policies = result.scalars().all()
        
        rules = []
        for policy in policies:
            rules.append({
                'policy_id': policy.id,
                'policy_name': policy.name,
                'warning_threshold': policy.escalation_warning_percent,
                'critical_threshold': policy.escalation_critical_percent,
                'auto_escalate': policy.auto_escalate_on_breach,
                'email_notifications': True,  # Default enabled
                'webhook_notifications': False  # Future feature
            })
        
        return {
            'rules': rules,
            'default_warning_threshold': 80,
            'default_critical_threshold': 95
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/policies/{policy_id}/notification-settings")
async def update_notification_settings(
    policy_id: str,
    warning_threshold: Optional[int] = Body(None, ge=0, le=100),
    critical_threshold: Optional[int] = Body(None, ge=0, le=100),
    auto_escalate: Optional[bool] = Body(None),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """Update notification settings for an SLA policy"""
    try:
        stmt = select(SLAPolicy).where(
            and_(
                SLAPolicy.id == policy_id,
                SLAPolicy.tenant_id == current_tenant.id
            )
        )
        result = await db.execute(stmt)
        policy = result.scalar_one_or_none()
        
        if not policy:
            raise HTTPException(status_code=404, detail="SLA policy not found")
        
        # Validate thresholds
        if warning_threshold is not None:
            if critical_threshold is not None and warning_threshold >= critical_threshold:
                raise HTTPException(
                    status_code=400,
                    detail="Warning threshold must be less than critical threshold"
                )
            policy.escalation_warning_percent = warning_threshold
        
        if critical_threshold is not None:
            if warning_threshold is not None and warning_threshold >= critical_threshold:
                raise HTTPException(
                    status_code=400,
                    detail="Warning threshold must be less than critical threshold"
                )
            policy.escalation_critical_percent = critical_threshold
        
        if auto_escalate is not None:
            policy.auto_escalate_on_breach = auto_escalate
        
        await db.commit()
        await db.refresh(policy)
        
        return SLAPolicyResponse.model_validate(policy)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/customers/{customer_id}/summary")
async def get_customer_sla_summary(
    customer_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """Get SLA summary for a specific customer"""
    try:
        from app.models.crm import Customer
        
        # Verify customer exists and belongs to tenant
        customer_stmt = select(Customer).where(
            and_(
                Customer.id == customer_id,
                Customer.tenant_id == current_tenant.id,
                Customer.is_deleted == False
            )
        )
        customer_result = await db.execute(customer_stmt)
        customer = customer_result.scalar_one_or_none()
        
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Get all tickets for this customer
        tickets_stmt = select(Ticket).where(
            and_(
                Ticket.customer_id == customer_id,
                Ticket.tenant_id == current_tenant.id,
            )
        )
        tickets_result = await db.execute(tickets_stmt)
        tickets = tickets_result.scalars().all()
        
        # Calculate metrics
        total_tickets = len(tickets)
        tickets_with_sla = len([t for t in tickets if t.sla_policy_id])
        
        # Get active breach alerts
        breach_alerts_stmt = select(SLABreachAlert).join(
            Ticket, SLABreachAlert.ticket_id == Ticket.id
        ).where(
            and_(
                Ticket.customer_id == customer_id,
                Ticket.tenant_id == current_tenant.id,
,
                SLABreachAlert.acknowledged == False
            )
        )
        breach_result = await db.execute(breach_alerts_stmt)
        breach_alerts = breach_result.scalars().all()
        
        critical_breaches = len([a for a in breach_alerts if a.alert_level == 'critical'])
        warning_breaches = len([a for a in breach_alerts if a.alert_level == 'warning'])
        
        # Calculate compliance rate
        compliant_tickets = 0
        for ticket in tickets:
            if ticket.sla_policy_id:
                if ticket.resolved_at:
                    # Check if resolution SLA was met
                    if not ticket.sla_resolution_breached:
                        compliant_tickets += 1
                elif ticket.first_response_at:
                    # Check if first response SLA was met
                    if not ticket.sla_first_response_breached:
                        compliant_tickets += 1
        
        compliance_rate = (compliant_tickets / tickets_with_sla * 100) if tickets_with_sla > 0 else 100.0
        
        # Get recent tickets with SLA status
        recent_tickets = []
        for ticket in sorted(tickets, key=lambda t: t.created_at, reverse=True)[:10]:
            ticket_breaches = [a for a in breach_alerts if a.ticket_id == ticket.id]
            recent_tickets.append({
                'id': ticket.id,
                'ticket_number': ticket.ticket_number,
                'subject': ticket.subject,
                'status': ticket.status.value if hasattr(ticket.status, 'value') else str(ticket.status),
                'priority': ticket.priority.value if hasattr(ticket.priority, 'value') else str(ticket.priority),
                'created_at': ticket.created_at.isoformat() if ticket.created_at else None,
                'sla_policy_id': ticket.sla_policy_id,
                'sla_first_response_breached': ticket.sla_first_response_breached,
                'sla_resolution_breached': ticket.sla_resolution_breached,
                'active_breaches': len(ticket_breaches),
                'critical_breaches': len([a for a in ticket_breaches if a.alert_level == 'critical'])
            })
        
        return {
            'customer_id': customer_id,
            'customer_name': customer.company_name,
            'total_tickets': total_tickets,
            'tickets_with_sla': tickets_with_sla,
            'active_breaches': {
                'total': len(breach_alerts),
                'critical': critical_breaches,
                'warning': warning_breaches
            },
            'compliance_rate': round(compliance_rate, 1),
            'recent_tickets': recent_tickets,
            'overall_status': 'critical' if critical_breaches > 0 else ('warning' if warning_breaches > 0 else 'none')
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates")
async def list_sla_templates(
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """List available SLA policy templates"""
    from app.models.sla_templates import list_templates
    
    templates = list_templates()
    return templates


@router.post("/templates/{template_id}/create-policy")
async def create_policy_from_template(
    template_id: str,
    name: str = Body(..., description="Name for the new policy"),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """Create an SLA policy from a template"""
    from app.models.sla_templates import create_policy_from_template
    from app.models.helpdesk import TicketPriority, TicketType
    
    try:
        policy_data = create_policy_from_template(template_id, name, current_tenant.id)
        
        # Convert string enums to enum objects
        if 'priority' in policy_data and policy_data['priority']:
            policy_data['priority'] = TicketPriority(policy_data['priority'])
        if 'ticket_type' in policy_data and policy_data['ticket_type']:
            policy_data['ticket_type'] = TicketType(policy_data['ticket_type'])
        
        # Filter out None values and invalid keys
        valid_keys = {
            'name', 'description', 'sla_level', 'first_response_hours',
            'first_response_hours_urgent', 'first_response_hours_high',
            'first_response_hours_medium', 'first_response_hours_low',
            'resolution_hours', 'resolution_hours_urgent', 'resolution_hours_high',
            'resolution_hours_medium', 'resolution_hours_low', 'uptime_target',
            'availability_hours', 'business_hours_start', 'business_hours_end',
            'business_days', 'timezone', 'escalation_warning_percent',
            'escalation_critical_percent', 'auto_escalate_on_breach', 'priority',
            'ticket_type', 'customer_ids', 'contract_type', 'is_active', 'is_default'
        }
        
        policy_kwargs = {
            'tenant_id': current_tenant.id,
            **{k: v for k, v in policy_data.items() if k in valid_keys and v is not None}
        }
        
        # Create the policy
        new_policy = SLAPolicy(**policy_kwargs)
        
        db.add(new_policy)
        await db.commit()
        await db.refresh(new_policy)
        
        return SLAPolicyResponse.model_validate(new_policy)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        await db.rollback()
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error creating policy from template: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/customers/{customer_id}/compliance-history")
async def get_customer_sla_compliance_history(
    customer_id: str,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """Get SLA compliance history for a customer"""
    try:
        from app.models.crm import Customer
        from datetime import datetime, timezone, timedelta
        
        # Verify customer exists
        customer_stmt = select(Customer).where(
            and_(
                Customer.id == customer_id,
                Customer.tenant_id == current_tenant.id,
                Customer.is_deleted == False
            )
        )
        customer_result = await db.execute(customer_stmt)
        customer = customer_result.scalar_one_or_none()
        
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Default to last 30 days if not specified
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        start_dt = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        end_dt = datetime.combine(end_date, datetime.max.time()).replace(tzinfo=timezone.utc)
        
        # Get compliance records for customer's tickets
        compliance_stmt = select(SLAComplianceRecord).join(
            Ticket, SLAComplianceRecord.ticket_id == Ticket.id
        ).where(
            and_(
                Ticket.customer_id == customer_id,
                Ticket.tenant_id == current_tenant.id,
,
                SLAComplianceRecord.recorded_at >= start_dt,
                SLAComplianceRecord.recorded_at <= end_dt
            )
        ).order_by(SLAComplianceRecord.recorded_at.desc())
        
        compliance_result = await db.execute(compliance_stmt)
        compliance_records = compliance_result.scalars().all()
        
        # Group by date
        daily_compliance = {}
        for record in compliance_records:
            record_date = record.recorded_at.date().isoformat()
            if record_date not in daily_compliance:
                daily_compliance[record_date] = {
                    'date': record_date,
                    'total_checks': 0,
                    'compliant': 0,
                    'breached': 0
                }
            
            daily_compliance[record_date]['total_checks'] += 1
            if record.compliant:
                daily_compliance[record_date]['compliant'] += 1
            else:
                daily_compliance[record_date]['breached'] += 1
        
        history = list(daily_compliance.values())
        history.sort(key=lambda x: x['date'], reverse=True)
        
        return {
            'customer_id': customer_id,
            'customer_name': customer.company_name,
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'daily_compliance': history,
            'total_records': len(compliance_records)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
