#!/usr/bin/env python3
"""
Support Contracts API Endpoints
Multi-tenant aware contract management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime, timedelta

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_tenant
from app.models.tenant import User, Tenant
from app.services.support_contract_service import SupportContractService
from app.schemas.support_contract import (
    SupportContractCreate, SupportContractUpdate, SupportContractResponse,
    ContractRenewalCreate, ContractRenewalResponse,
    ContractTemplateCreate, ContractTemplateResponse,
    ContractTypeEnum, ContractStatusEnum
)
from app.models.support_contract import ContractType, ContractStatus

router = APIRouter()


@router.get("/", response_model=List[SupportContractResponse])
async def list_contracts(
    customer_id: Optional[str] = Query(None),
    contract_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    expiring_soon: Optional[bool] = Query(None),
    days_ahead: int = Query(90, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """List support contracts with optional filters"""
    try:
        service = SupportContractService(db, current_tenant.id)
        
        # Convert string enums to enum types
        contract_type_enum = None
        if contract_type:
            try:
                contract_type_enum = ContractType(contract_type)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid contract_type: {contract_type}"
                )
        
        status_enum = None
        if status:
            try:
                status_enum = ContractStatus(status)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid status: {status}"
                )
        
        contracts = service.list_contracts(
            customer_id=customer_id,
            contract_type=contract_type_enum,
            status=status_enum,
            expiring_soon=expiring_soon,
            days_ahead=days_ahead
        )
        
        # Convert to response format
        result = []
        for contract in contracts:
            # Calculate computed fields
            days_until_renewal = None
            is_expiring_soon = False
            if contract.renewal_date:
                days_until_renewal = (contract.renewal_date - date.today()).days
                is_expiring_soon = 0 <= days_until_renewal <= 90
            
            total_value = None
            if contract.annual_value:
                total_value = float(contract.annual_value)
            elif contract.monthly_value:
                total_value = float(contract.monthly_value) * 12
            
            contract_response = SupportContractResponse(
                id=contract.id,
                tenant_id=contract.tenant_id,
                customer_id=contract.customer_id,
                contract_number=contract.contract_number,
                contract_name=contract.contract_name,
                description=contract.description,
                contract_type=contract.contract_type.value,
                status=contract.status.value,
                start_date=contract.start_date,
                end_date=contract.end_date,
                renewal_date=contract.renewal_date,
                renewal_frequency=contract.renewal_frequency.value if contract.renewal_frequency else None,
                auto_renew=contract.auto_renew,
                monthly_value=float(contract.monthly_value) if contract.monthly_value else None,
                annual_value=float(contract.annual_value) if contract.annual_value else None,
                setup_fee=float(contract.setup_fee),
                currency=contract.currency,
                terms=contract.terms,
                sla_level=contract.sla_level,
                included_services=contract.included_services,
                excluded_services=contract.excluded_services,
                support_hours_included=contract.support_hours_included,
                support_hours_used=contract.support_hours_used,
                renewal_notice_days=contract.renewal_notice_days,
                cancellation_notice_days=contract.cancellation_notice_days,
                cancellation_reason=contract.cancellation_reason,
                cancelled_at=contract.cancelled_at,
                cancelled_by=contract.cancelled_by,
                quote_id=contract.quote_id,
                opportunity_id=contract.opportunity_id,
                notes=contract.notes,
                contract_metadata=contract.contract_metadata,
                created_at=contract.created_at,
                updated_at=contract.updated_at,
                days_until_renewal=days_until_renewal,
                is_expiring_soon=is_expiring_soon,
                total_value=total_value
            )
            result.append(contract_response)
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error fetching contracts: {str(e)}")


@router.post("/", response_model=SupportContractResponse, status_code=status.HTTP_201_CREATED)
async def create_contract(
    contract_data: SupportContractCreate,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Create a new support contract"""
    try:
        service = SupportContractService(db, current_tenant.id)
        
        # Convert enum strings to enum types
        contract_type = ContractType(contract_data.contract_type.value)
        renewal_frequency = None
        if contract_data.renewal_frequency:
            from app.models.support_contract import RenewalFrequency
            renewal_frequency = RenewalFrequency(contract_data.renewal_frequency.value)
        
        contract = service.create_contract(
            customer_id=contract_data.customer_id,
            contract_name=contract_data.contract_name,
            contract_type=contract_type,
            start_date=contract_data.start_date,
            description=contract_data.description,
            end_date=contract_data.end_date,
            renewal_frequency=renewal_frequency,
            auto_renew=contract_data.auto_renew,
            monthly_value=contract_data.monthly_value,
            annual_value=contract_data.annual_value,
            setup_fee=contract_data.setup_fee,
            currency=contract_data.currency,
            terms=contract_data.terms,
            sla_level=contract_data.sla_level,
            included_services=contract_data.included_services,
            excluded_services=contract_data.excluded_services,
            support_hours_included=contract_data.support_hours_included,
            renewal_notice_days=contract_data.renewal_notice_days,
            cancellation_notice_days=contract_data.cancellation_notice_days,
            quote_id=contract_data.quote_id,
            opportunity_id=contract_data.opportunity_id,
            notes=contract_data.notes,
            contract_metadata=contract_data.contract_metadata
        )
        
        if not contract:
            raise HTTPException(status_code=400, detail="Invalid customer or contract creation failed")
        
        # Calculate computed fields
        days_until_renewal = None
        is_expiring_soon = False
        if contract.renewal_date:
            days_until_renewal = (contract.renewal_date - date.today()).days
            is_expiring_soon = 0 <= days_until_renewal <= 90
        
        total_value = None
        if contract.annual_value:
            total_value = float(contract.annual_value)
        elif contract.monthly_value:
            total_value = float(contract.monthly_value) * 12
        
        return SupportContractResponse(
            id=contract.id,
            tenant_id=contract.tenant_id,
            customer_id=contract.customer_id,
            contract_number=contract.contract_number,
            contract_name=contract.contract_name,
            description=contract.description,
            contract_type=contract.contract_type.value,
            status=contract.status.value,
            start_date=contract.start_date,
            end_date=contract.end_date,
            renewal_date=contract.renewal_date,
            renewal_frequency=contract.renewal_frequency.value if contract.renewal_frequency else None,
            auto_renew=contract.auto_renew,
            monthly_value=float(contract.monthly_value) if contract.monthly_value else None,
            annual_value=float(contract.annual_value) if contract.annual_value else None,
            setup_fee=float(contract.setup_fee),
            currency=contract.currency,
            terms=contract.terms,
            sla_level=contract.sla_level,
            included_services=contract.included_services,
            excluded_services=contract.excluded_services,
            support_hours_included=contract.support_hours_included,
            support_hours_used=contract.support_hours_used,
            renewal_notice_days=contract.renewal_notice_days,
            cancellation_notice_days=contract.cancellation_notice_days,
            cancellation_reason=contract.cancellation_reason,
            cancelled_at=contract.cancelled_at,
            cancelled_by=contract.cancelled_by,
            quote_id=contract.quote_id,
            opportunity_id=contract.opportunity_id,
            notes=contract.notes,
            contract_metadata=contract.contract_metadata,
            created_at=contract.created_at,
            updated_at=contract.updated_at,
            days_until_renewal=days_until_renewal,
            is_expiring_soon=is_expiring_soon,
            total_value=total_value
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error creating contract: {str(e)}")


@router.get("/{contract_id}", response_model=SupportContractResponse)
async def get_contract(
    contract_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Get a support contract"""
    service = SupportContractService(db, current_tenant.id)
    contract = service.get_contract(contract_id)
    
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    # Calculate computed fields
    days_until_renewal = None
    is_expiring_soon = False
    if contract.renewal_date:
        days_until_renewal = (contract.renewal_date - date.today()).days
        is_expiring_soon = 0 <= days_until_renewal <= 90
    
    total_value = None
    if contract.annual_value:
        total_value = float(contract.annual_value)
    elif contract.monthly_value:
        total_value = float(contract.monthly_value) * 12
    
    return SupportContractResponse(
        id=contract.id,
        tenant_id=contract.tenant_id,
        customer_id=contract.customer_id,
        contract_number=contract.contract_number,
        contract_name=contract.contract_name,
        description=contract.description,
        contract_type=contract.contract_type.value,
        status=contract.status.value,
        start_date=contract.start_date,
        end_date=contract.end_date,
        renewal_date=contract.renewal_date,
        renewal_frequency=contract.renewal_frequency.value if contract.renewal_frequency else None,
        auto_renew=contract.auto_renew,
        monthly_value=float(contract.monthly_value) if contract.monthly_value else None,
        annual_value=float(contract.annual_value) if contract.annual_value else None,
        setup_fee=float(contract.setup_fee),
        currency=contract.currency,
        terms=contract.terms,
        sla_level=contract.sla_level,
        included_services=contract.included_services,
        excluded_services=contract.excluded_services,
        support_hours_included=contract.support_hours_included,
        support_hours_used=contract.support_hours_used,
        renewal_notice_days=contract.renewal_notice_days,
        cancellation_notice_days=contract.cancellation_notice_days,
        cancellation_reason=contract.cancellation_reason,
        cancelled_at=contract.cancelled_at,
        cancelled_by=contract.cancelled_by,
        quote_id=contract.quote_id,
        opportunity_id=contract.opportunity_id,
        notes=contract.notes,
        metadata=contract.metadata,
        created_at=contract.created_at,
        updated_at=contract.updated_at,
        days_until_renewal=days_until_renewal,
        is_expiring_soon=is_expiring_soon,
        total_value=total_value
    )


@router.put("/{contract_id}", response_model=SupportContractResponse)
async def update_contract(
    contract_id: str,
    contract_data: SupportContractUpdate,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Update a support contract"""
    service = SupportContractService(db, current_tenant.id)
    
    # Convert enum strings to enum types if provided
    update_kwargs = contract_data.dict(exclude_unset=True)
    
    if 'status' in update_kwargs:
        update_kwargs['status'] = ContractStatus(update_kwargs['status'].value)
    
    if 'renewal_frequency' in update_kwargs and update_kwargs['renewal_frequency']:
        from app.models.support_contract import RenewalFrequency
        update_kwargs['renewal_frequency'] = RenewalFrequency(update_kwargs['renewal_frequency'].value)
    
    contract = service.update_contract(contract_id, **update_kwargs)
    
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    # Calculate computed fields
    days_until_renewal = None
    is_expiring_soon = False
    if contract.renewal_date:
        days_until_renewal = (contract.renewal_date - date.today()).days
        is_expiring_soon = 0 <= days_until_renewal <= 90
    
    total_value = None
    if contract.annual_value:
        total_value = float(contract.annual_value)
    elif contract.monthly_value:
        total_value = float(contract.monthly_value) * 12
    
    return SupportContractResponse(
        id=contract.id,
        tenant_id=contract.tenant_id,
        customer_id=contract.customer_id,
        contract_number=contract.contract_number,
        contract_name=contract.contract_name,
        description=contract.description,
        contract_type=contract.contract_type.value,
        status=contract.status.value,
        start_date=contract.start_date,
        end_date=contract.end_date,
        renewal_date=contract.renewal_date,
        renewal_frequency=contract.renewal_frequency.value if contract.renewal_frequency else None,
        auto_renew=contract.auto_renew,
        monthly_value=float(contract.monthly_value) if contract.monthly_value else None,
        annual_value=float(contract.annual_value) if contract.annual_value else None,
        setup_fee=float(contract.setup_fee),
        currency=contract.currency,
        terms=contract.terms,
        sla_level=contract.sla_level,
        included_services=contract.included_services,
        excluded_services=contract.excluded_services,
        support_hours_included=contract.support_hours_included,
        support_hours_used=contract.support_hours_used,
        renewal_notice_days=contract.renewal_notice_days,
        cancellation_notice_days=contract.cancellation_notice_days,
        cancellation_reason=contract.cancellation_reason,
        cancelled_at=contract.cancelled_at,
        cancelled_by=contract.cancelled_by,
        quote_id=contract.quote_id,
        opportunity_id=contract.opportunity_id,
        notes=contract.notes,
        metadata=contract.metadata,
        created_at=contract.created_at,
        updated_at=contract.updated_at,
        days_until_renewal=days_until_renewal,
        is_expiring_soon=is_expiring_soon,
        total_value=total_value
    )


@router.post("/{contract_id}/cancel", response_model=SupportContractResponse)
async def cancel_contract(
    contract_id: str,
    cancellation_reason: str = Query(...),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Cancel a support contract"""
    service = SupportContractService(db, current_tenant.id)
    contract = service.cancel_contract(contract_id, cancellation_reason, current_user.id)
    
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    # Return updated contract (similar to get_contract response)
    days_until_renewal = None
    is_expiring_soon = False
    if contract.renewal_date:
        days_until_renewal = (contract.renewal_date - date.today()).days
        is_expiring_soon = 0 <= days_until_renewal <= 90
    
    total_value = None
    if contract.annual_value:
        total_value = float(contract.annual_value)
    elif contract.monthly_value:
        total_value = float(contract.monthly_value) * 12
    
    return SupportContractResponse(
        id=contract.id,
        tenant_id=contract.tenant_id,
        customer_id=contract.customer_id,
        contract_number=contract.contract_number,
        contract_name=contract.contract_name,
        description=contract.description,
        contract_type=contract.contract_type.value,
        status=contract.status.value,
        start_date=contract.start_date,
        end_date=contract.end_date,
        renewal_date=contract.renewal_date,
        renewal_frequency=contract.renewal_frequency.value if contract.renewal_frequency else None,
        auto_renew=contract.auto_renew,
        monthly_value=float(contract.monthly_value) if contract.monthly_value else None,
        annual_value=float(contract.annual_value) if contract.annual_value else None,
        setup_fee=float(contract.setup_fee),
        currency=contract.currency,
        terms=contract.terms,
        sla_level=contract.sla_level,
        included_services=contract.included_services,
        excluded_services=contract.excluded_services,
        support_hours_included=contract.support_hours_included,
        support_hours_used=contract.support_hours_used,
        renewal_notice_days=contract.renewal_notice_days,
        cancellation_notice_days=contract.cancellation_notice_days,
        cancellation_reason=contract.cancellation_reason,
        cancelled_at=contract.cancelled_at,
        cancelled_by=contract.cancelled_by,
        quote_id=contract.quote_id,
        opportunity_id=contract.opportunity_id,
        notes=contract.notes,
        metadata=contract.metadata,
        created_at=contract.created_at,
        updated_at=contract.updated_at,
        days_until_renewal=days_until_renewal,
        is_expiring_soon=is_expiring_soon,
        total_value=total_value
    )


@router.get("/recurring-revenue/summary")
async def get_recurring_revenue_summary(
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Get total recurring revenue summary"""
    service = SupportContractService(db, current_tenant.id)
    return service.get_total_recurring_revenue()


@router.get("/expiring-soon/list")
async def get_expiring_contracts(
    days_ahead: int = Query(90, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Get contracts expiring soon"""
    service = SupportContractService(db, current_tenant.id)
    contracts = service.get_contracts_expiring_soon(days_ahead)
    
    # Convert to response format (similar to list_contracts)
    result = []
    for contract in contracts:
        days_until_renewal = None
        is_expiring_soon = False
        if contract.renewal_date:
            days_until_renewal = (contract.renewal_date - date.today()).days
            is_expiring_soon = 0 <= days_until_renewal <= 90
        
        total_value = None
        if contract.annual_value:
            total_value = float(contract.annual_value)
        elif contract.monthly_value:
            total_value = float(contract.monthly_value) * 12
        
        result.append(SupportContractResponse(
            id=contract.id,
            tenant_id=contract.tenant_id,
            customer_id=contract.customer_id,
            contract_number=contract.contract_number,
            contract_name=contract.contract_name,
            description=contract.description,
            contract_type=contract.contract_type.value,
            status=contract.status.value,
            start_date=contract.start_date,
            end_date=contract.end_date,
            renewal_date=contract.renewal_date,
            renewal_frequency=contract.renewal_frequency.value if contract.renewal_frequency else None,
            auto_renew=contract.auto_renew,
            monthly_value=float(contract.monthly_value) if contract.monthly_value else None,
            annual_value=float(contract.annual_value) if contract.annual_value else None,
            setup_fee=float(contract.setup_fee),
            currency=contract.currency,
            terms=contract.terms,
            sla_level=contract.sla_level,
            included_services=contract.included_services,
            excluded_services=contract.excluded_services,
            support_hours_included=contract.support_hours_included,
            support_hours_used=contract.support_hours_used,
            renewal_notice_days=contract.renewal_notice_days,
            cancellation_notice_days=contract.cancellation_notice_days,
            cancellation_reason=contract.cancellation_reason,
            cancelled_at=contract.cancelled_at,
            cancelled_by=contract.cancelled_by,
            quote_id=contract.quote_id,
            opportunity_id=contract.opportunity_id,
            notes=contract.notes,
            contract_metadata=contract.contract_metadata,
            created_at=contract.created_at,
            updated_at=contract.updated_at,
            days_until_renewal=days_until_renewal,
            is_expiring_soon=is_expiring_soon,
            total_value=total_value
        ))
    
    return result

