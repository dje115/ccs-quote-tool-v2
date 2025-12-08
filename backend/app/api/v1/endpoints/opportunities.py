#!/usr/bin/env python3
"""
Opportunity management endpoints for CRM pipeline
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime, timezone
from decimal import Decimal
import uuid

from app.core.database import get_async_db
from app.core.dependencies import get_current_user, get_current_tenant, check_permission
from app.models.opportunities import Opportunity, OpportunityStage
from app.models.crm import Customer
from app.models.tenant import User, Tenant

router = APIRouter()


# Pydantic schemas
class OpportunityCreate(BaseModel):
    customer_id: str
    title: str
    description: Optional[str] = None
    stage: Optional[OpportunityStage] = OpportunityStage.QUALIFIED
    conversion_probability: Optional[int] = 20  # 0-100
    potential_deal_date: Optional[datetime] = None
    estimated_value: Optional[float] = None
    notes: Optional[str] = None


class OpportunityUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    stage: Optional[OpportunityStage] = None
    conversion_probability: Optional[int] = None
    potential_deal_date: Optional[datetime] = None
    estimated_value: Optional[float] = None
    quote_ids: Optional[List[str]] = None
    support_contract_ids: Optional[List[str]] = None
    notes: Optional[str] = None
    recurring_quote_schedule: Optional[Dict[str, Any]] = None


class AttachQuoteRequest(BaseModel):
    quote_id: str


class UpdateStageRequest(BaseModel):
    stage: OpportunityStage


class OpportunityResponse(BaseModel):
    id: str
    customer_id: str
    tenant_id: str
    title: str
    description: Optional[str] = None
    stage: str
    conversion_probability: int
    potential_deal_date: Optional[datetime] = None
    estimated_value: Optional[float] = None
    quote_ids: Optional[List[str]] = None
    support_contract_ids: Optional[List[str]] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    notes: Optional[str] = None
    recurring_quote_schedule: Optional[Dict[str, Any]] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


@router.get("/", response_model=List[OpportunityResponse])
async def list_opportunities(
    customer_id: Optional[str] = Query(None, description="Filter by customer ID"),
    stage: Optional[OpportunityStage] = Query(None, description="Filter by stage"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    _: None = Depends(lambda: check_permission("opportunities:read"))
):
    """List all opportunities for the current tenant"""
    stmt = select(Opportunity).where(
        and_(
            Opportunity.tenant_id == current_tenant.id,
            Opportunity.is_deleted == False
        )
    )
    
    if customer_id:
        stmt = stmt.where(Opportunity.customer_id == customer_id)
    if stage:
        stmt = stmt.where(Opportunity.stage == stage)
    
    stmt = stmt.order_by(Opportunity.created_at.desc())
    
    result = await db.execute(stmt)
    opportunities = result.scalars().all()
    
    # Convert stage enum to string for each opportunity
    result = []
    for opp in opportunities:
        opp_dict = {
            "id": opp.id,
            "customer_id": opp.customer_id,
            "tenant_id": opp.tenant_id,
            "title": opp.title,
            "description": opp.description,
            "stage": opp.stage.value if hasattr(opp.stage, 'value') else str(opp.stage),
            "conversion_probability": opp.conversion_probability,
            "potential_deal_date": opp.potential_deal_date,
            "estimated_value": float(opp.estimated_value) if opp.estimated_value else None,
            "quote_ids": opp.quote_ids,
            "support_contract_ids": opp.support_contract_ids,
            "attachments": opp.attachments,
            "notes": opp.notes,
            "recurring_quote_schedule": opp.recurring_quote_schedule,
            "created_by": opp.created_by,
            "updated_by": opp.updated_by,
            "created_at": opp.created_at,
            "updated_at": opp.updated_at
        }
        result.append(OpportunityResponse(**opp_dict))
    return result


@router.get("/customer/{customer_id}", response_model=List[OpportunityResponse])
async def get_customer_opportunities(
    customer_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    _: None = Depends(lambda: check_permission("opportunities:read"))
):
    """Get all opportunities for a specific customer"""
    # Verify customer belongs to tenant
    customer_stmt = select(Customer).where(
        and_(
            Customer.id == customer_id,
            Customer.tenant_id == current_tenant.id
        )
    )
    customer_result = await db.execute(customer_stmt)
    customer = customer_result.scalar_one_or_none()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    stmt = select(Opportunity).where(
        and_(
            Opportunity.customer_id == customer_id,
            Opportunity.tenant_id == current_tenant.id,
            Opportunity.is_deleted == False
        )
    ).order_by(Opportunity.created_at.desc())
    
    result = await db.execute(stmt)
    opportunities = result.scalars().all()
    
    # Convert stage enum to string for each opportunity
    result = []
    for opp in opportunities:
        opp_dict = {
            "id": opp.id,
            "customer_id": opp.customer_id,
            "tenant_id": opp.tenant_id,
            "title": opp.title,
            "description": opp.description,
            "stage": opp.stage.value if hasattr(opp.stage, 'value') else str(opp.stage),
            "conversion_probability": opp.conversion_probability,
            "potential_deal_date": opp.potential_deal_date,
            "estimated_value": float(opp.estimated_value) if opp.estimated_value else None,
            "quote_ids": opp.quote_ids,
            "support_contract_ids": opp.support_contract_ids,
            "attachments": opp.attachments,
            "notes": opp.notes,
            "recurring_quote_schedule": opp.recurring_quote_schedule,
            "created_by": opp.created_by,
            "updated_by": opp.updated_by,
            "created_at": opp.created_at,
            "updated_at": opp.updated_at
        }
        result.append(OpportunityResponse(**opp_dict))
    return result


@router.post("/", response_model=OpportunityResponse, status_code=status.HTTP_201_CREATED)
async def create_opportunity(
    opportunity_data: OpportunityCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    _: None = Depends(lambda: check_permission("opportunities:create"))
):
    """Create a new opportunity"""
    # Verify customer belongs to tenant
    customer_stmt = select(Customer).where(
        and_(
            Customer.id == opportunity_data.customer_id,
            Customer.tenant_id == current_tenant.id
        )
    )
    customer_result = await db.execute(customer_stmt)
    customer = customer_result.scalar_one_or_none()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    opportunity = Opportunity(
        id=str(uuid.uuid4()),
        customer_id=opportunity_data.customer_id,
        tenant_id=current_tenant.id,
        title=opportunity_data.title,
        description=opportunity_data.description,
        stage=opportunity_data.stage or OpportunityStage.QUALIFIED,
        conversion_probability=opportunity_data.conversion_probability or 20,
        potential_deal_date=opportunity_data.potential_deal_date,
        estimated_value=Decimal(str(opportunity_data.estimated_value)) if opportunity_data.estimated_value else None,
        notes=opportunity_data.notes,
        created_by=current_user.id
    )
    
    db.add(opportunity)
    await db.commit()
    await db.refresh(opportunity)
    
    return opportunity_to_response(opportunity)


@router.get("/{opportunity_id}", response_model=OpportunityResponse)
async def get_opportunity(
    opportunity_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    _: None = Depends(lambda: check_permission("opportunities:read"))
):
    """Get a specific opportunity"""
    stmt = select(Opportunity).where(
        and_(
            Opportunity.id == opportunity_id,
            Opportunity.tenant_id == current_tenant.id,
            Opportunity.is_deleted == False
        )
    )
    
    result = await db.execute(stmt)
    opportunity = result.scalar_one_or_none()
    
    if not opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opportunity not found"
        )
    
    return opportunity_to_response(opportunity)


@router.put("/{opportunity_id}", response_model=OpportunityResponse)
async def update_opportunity(
    opportunity_id: str,
    opportunity_data: OpportunityUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    _: None = Depends(lambda: check_permission("opportunities:update"))
):
    """Update an opportunity"""
    stmt = select(Opportunity).where(
        and_(
            Opportunity.id == opportunity_id,
            Opportunity.tenant_id == current_tenant.id,
            Opportunity.is_deleted == False
        )
    )
    
    result = await db.execute(stmt)
    opportunity = result.scalar_one_or_none()
    
    if not opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opportunity not found"
        )
    
    # Track if stage changed for lifecycle automation
    stage_changed = opportunity_data.stage is not None and opportunity_data.stage != opportunity.stage
    
    # Update fields
    if opportunity_data.title is not None:
        opportunity.title = opportunity_data.title
    if opportunity_data.description is not None:
        opportunity.description = opportunity_data.description
    if opportunity_data.stage is not None:
        opportunity.stage = opportunity_data.stage
    if opportunity_data.conversion_probability is not None:
        opportunity.conversion_probability = opportunity_data.conversion_probability
    if opportunity_data.potential_deal_date is not None:
        opportunity.potential_deal_date = opportunity_data.potential_deal_date
    if opportunity_data.estimated_value is not None:
        opportunity.estimated_value = Decimal(str(opportunity_data.estimated_value))
    if opportunity_data.quote_ids is not None:
        opportunity.quote_ids = opportunity_data.quote_ids
    if opportunity_data.support_contract_ids is not None:
        opportunity.support_contract_ids = opportunity_data.support_contract_ids
    if opportunity_data.notes is not None:
        opportunity.notes = opportunity_data.notes
    if opportunity_data.recurring_quote_schedule is not None:
        opportunity.recurring_quote_schedule = opportunity_data.recurring_quote_schedule
    
    opportunity.updated_by = current_user.id
    opportunity.updated_at = datetime.now(timezone.utc)
    
    await db.commit()
    await db.refresh(opportunity)
    
    # Trigger lifecycle automation check if stage changed
    if stage_changed:
        try:
            from app.services.customer_lifecycle_service import CustomerLifecycleService
            new_status = await CustomerLifecycleService.check_lifecycle_transitions(
                opportunity.customer_id, db, current_tenant.id
            )
            if new_status:
                await CustomerLifecycleService.update_customer_status(
                    opportunity.customer_id, new_status, db, current_tenant.id
                )
        except Exception as e:
            # Log but don't fail the request if lifecycle check fails
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Lifecycle check failed for customer {opportunity.customer_id}: {e}")
    
    return opportunity_to_response(opportunity)


@router.put("/{opportunity_id}/stage", response_model=OpportunityResponse)
async def update_opportunity_stage(
    opportunity_id: str,
    request: UpdateStageRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    _: None = Depends(lambda: check_permission("opportunities:update"))
):
    """Update opportunity stage (triggers lifecycle automation)"""
    stage = request.stage
    stmt = select(Opportunity).where(
        and_(
            Opportunity.id == opportunity_id,
            Opportunity.tenant_id == current_tenant.id,
            Opportunity.is_deleted == False
        )
    )
    
    result = await db.execute(stmt)
    opportunity = result.scalar_one_or_none()
    
    if not opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opportunity not found"
        )
    
    opportunity.stage = stage
    opportunity.updated_by = current_user.id
    opportunity.updated_at = datetime.now(timezone.utc)
    
    await db.commit()
    await db.refresh(opportunity)
    
    # Trigger lifecycle automation check
    try:
        from app.services.customer_lifecycle_service import CustomerLifecycleService
        new_status = await CustomerLifecycleService.check_lifecycle_transitions(
            opportunity.customer_id, db, current_tenant.id
        )
        if new_status:
            await CustomerLifecycleService.update_customer_status(
                opportunity.customer_id, new_status, db, current_tenant.id
            )
    except Exception as e:
        # Log but don't fail the request if lifecycle check fails
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Lifecycle check failed for customer {opportunity.customer_id}: {e}")
    
    return opportunity_to_response(opportunity)


@router.post("/{opportunity_id}/attach-quote")
async def attach_quote_to_opportunity(
    opportunity_id: str,
    request: AttachQuoteRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    _: None = Depends(lambda: check_permission("opportunities:update"))
):
    """Link an existing quote to an opportunity"""
    stmt = select(Opportunity).where(
        and_(
            Opportunity.id == opportunity_id,
            Opportunity.tenant_id == current_tenant.id,
            Opportunity.is_deleted == False
        )
    )
    
    result = await db.execute(stmt)
    opportunity = result.scalar_one_or_none()
    
    if not opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opportunity not found"
        )
    
    # Add quote_id to quote_ids array
    quote_ids = opportunity.quote_ids or []
    if request.quote_id not in quote_ids:
        quote_ids.append(request.quote_id)
        opportunity.quote_ids = quote_ids
        opportunity.updated_by = current_user.id
        opportunity.updated_at = datetime.now(timezone.utc)
        await db.commit()
    
    await db.refresh(opportunity)
    return opportunity_to_response(opportunity)


@router.delete("/{opportunity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_opportunity(
    opportunity_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    _: None = Depends(lambda: check_permission("opportunities:delete"))
):
    """Soft delete an opportunity"""
    stmt = select(Opportunity).where(
        and_(
            Opportunity.id == opportunity_id,
            Opportunity.tenant_id == current_tenant.id,
            Opportunity.is_deleted == False
        )
    )
    
    result = await db.execute(stmt)
    opportunity = result.scalar_one_or_none()
    
    if not opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opportunity not found"
        )
    
    opportunity.is_deleted = True
    opportunity.deleted_at = datetime.now(timezone.utc)
    opportunity.updated_by = current_user.id
    
    await db.commit()
    return None

