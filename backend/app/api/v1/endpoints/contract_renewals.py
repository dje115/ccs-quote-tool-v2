#!/usr/bin/env python3
"""
Contract Renewals API Endpoints
Multi-tenant aware renewal management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
import asyncio

from app.core.database import get_async_db, SessionLocal
from app.core.dependencies import get_current_user, get_current_tenant
from app.models.tenant import User, Tenant
from app.services.contract_renewal_service import ContractRenewalService
from app.schemas.support_contract import (
    ContractRenewalCreate, ContractRenewalResponse
)

router = APIRouter()


@router.get("/contracts/{contract_id}/renewals", response_model=List[ContractRenewalResponse])
async def list_contract_renewals(
    contract_id: str,
    status_filter: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    List renewals for a contract
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        from app.models.support_contract import SupportContract, ContractRenewal
        
        # Verify contract belongs to tenant
        contract_stmt = select(SupportContract).where(
            and_(
                SupportContract.id == contract_id,
                SupportContract.tenant_id == current_tenant.id
            )
        )
        contract_result = await db.execute(contract_stmt)
        contract = contract_result.scalars().first()
        
        if not contract:
            raise HTTPException(status_code=404, detail="Contract not found")
        
        # Get renewals
        renewals_stmt = select(ContractRenewal).where(
            ContractRenewal.contract_id == contract_id
        )
        
        if status_filter:
            renewals_stmt = renewals_stmt.where(ContractRenewal.status == status_filter)
        
        renewals_stmt = renewals_stmt.order_by(ContractRenewal.renewal_date.desc())
        renewals_result = await db.execute(renewals_stmt)
        renewals = renewals_result.scalars().all()
        
        # Convert to response format
        result = []
        for renewal in renewals:
            result.append(ContractRenewalResponse(
                id=renewal.id,
                contract_id=renewal.contract_id,
                tenant_id=renewal.tenant_id,
                renewal_date=renewal.renewal_date,
                previous_end_date=renewal.previous_end_date,
                new_end_date=renewal.new_end_date,
                previous_monthly_value=float(renewal.previous_monthly_value) if renewal.previous_monthly_value else None,
                new_monthly_value=float(renewal.new_monthly_value) if renewal.new_monthly_value else None,
                previous_annual_value=float(renewal.previous_annual_value) if renewal.previous_annual_value else None,
                new_annual_value=float(renewal.new_annual_value) if renewal.new_annual_value else None,
                status=renewal.status,
                renewal_type=renewal.renewal_type,
                reminder_sent_at=renewal.reminder_sent_at,
                reminder_sent_to=renewal.reminder_sent_to,
                approved_at=renewal.approved_at,
                approved_by=renewal.approved_by,
                completed_at=renewal.completed_at,
                declined_at=renewal.declined_at,
                declined_reason=renewal.declined_reason,
                notes=renewal.notes,
                created_at=renewal.created_at,
                updated_at=renewal.updated_at
            ))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error fetching renewals: {str(e)}")


@router.post("/contracts/{contract_id}/renewals", response_model=ContractRenewalResponse, status_code=status.HTTP_201_CREATED)
async def create_renewal(
    contract_id: str,
    renewal_data: ContractRenewalCreate,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Create a renewal record for a contract
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    Note: Wraps sync service calls in executor.
    """
    try:
        def _create_renewal():
            sync_db = SessionLocal()
            try:
                service = ContractRenewalService(sync_db, current_tenant.id)
                return service.create_renewal_record(
                    contract_id=contract_id,
                    renewal_date=renewal_data.renewal_date,
                    new_end_date=renewal_data.new_end_date,
                    new_monthly_value=renewal_data.new_monthly_value,
                    new_annual_value=renewal_data.new_annual_value,
                    renewal_type=renewal_data.renewal_type or "manual"
                )
            finally:
                sync_db.close()
        
        loop = asyncio.get_event_loop()
        renewal = await loop.run_in_executor(None, _create_renewal)
        
        if not renewal:
            raise HTTPException(status_code=404, detail="Contract not found")
        
        return ContractRenewalResponse(
            id=renewal.id,
            contract_id=renewal.contract_id,
            tenant_id=renewal.tenant_id,
            renewal_date=renewal.renewal_date,
            previous_end_date=renewal.previous_end_date,
            new_end_date=renewal.new_end_date,
            previous_monthly_value=float(renewal.previous_monthly_value) if renewal.previous_monthly_value else None,
            new_monthly_value=float(renewal.new_monthly_value) if renewal.new_monthly_value else None,
            previous_annual_value=float(renewal.previous_annual_value) if renewal.previous_annual_value else None,
            new_annual_value=float(renewal.new_annual_value) if renewal.new_annual_value else None,
            status=renewal.status,
            renewal_type=renewal.renewal_type,
            reminder_sent_at=renewal.reminder_sent_at,
            reminder_sent_to=renewal.reminder_sent_to,
            approved_at=renewal.approved_at,
            approved_by=renewal.approved_by,
            completed_at=renewal.completed_at,
            declined_at=renewal.declined_at,
            declined_reason=renewal.declined_reason,
            notes=renewal.notes,
            created_at=renewal.created_at,
            updated_at=renewal.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error creating renewal: {str(e)}")


@router.post("/renewals/{renewal_id}/approve", response_model=ContractRenewalResponse)
async def approve_renewal(
    renewal_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Approve a contract renewal
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    Note: Wraps sync service calls in executor.
    """
    try:
        def _approve_renewal():
            sync_db = SessionLocal()
            try:
                service = ContractRenewalService(sync_db, current_tenant.id)
                return service.approve_renewal(renewal_id, current_user.id)
            finally:
                sync_db.close()
        
        loop = asyncio.get_event_loop()
        renewal = await loop.run_in_executor(None, _approve_renewal)
        
        if not renewal:
            raise HTTPException(status_code=404, detail="Renewal not found")
        
        return ContractRenewalResponse(
            id=renewal.id,
            contract_id=renewal.contract_id,
            tenant_id=renewal.tenant_id,
            renewal_date=renewal.renewal_date,
            previous_end_date=renewal.previous_end_date,
            new_end_date=renewal.new_end_date,
            previous_monthly_value=float(renewal.previous_monthly_value) if renewal.previous_monthly_value else None,
            new_monthly_value=float(renewal.new_monthly_value) if renewal.new_monthly_value else None,
            previous_annual_value=float(renewal.previous_annual_value) if renewal.previous_annual_value else None,
            new_annual_value=float(renewal.new_annual_value) if renewal.new_annual_value else None,
            status=renewal.status,
            renewal_type=renewal.renewal_type,
            reminder_sent_at=renewal.reminder_sent_at,
            reminder_sent_to=renewal.reminder_sent_to,
            approved_at=renewal.approved_at,
            approved_by=renewal.approved_by,
            completed_at=renewal.completed_at,
            declined_at=renewal.declined_at,
            declined_reason=renewal.declined_reason,
            notes=renewal.notes,
            created_at=renewal.created_at,
            updated_at=renewal.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error approving renewal: {str(e)}")


@router.post("/renewals/{renewal_id}/complete", response_model=dict)
async def complete_renewal(
    renewal_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Complete a contract renewal
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    Note: Wraps sync service calls in executor.
    """
    try:
        def _complete_renewal():
            sync_db = SessionLocal()
            try:
                service = ContractRenewalService(sync_db, current_tenant.id)
                return service.complete_renewal(renewal_id)
            finally:
                sync_db.close()
        
        loop = asyncio.get_event_loop()
        contract = await loop.run_in_executor(None, _complete_renewal)
        
        if not contract:
            raise HTTPException(status_code=404, detail="Renewal not found or not approved")
        
        return {
            "success": True,
            "message": "Contract renewed successfully",
            "contract_id": contract.id,
            "contract_number": contract.contract_number,
            "new_renewal_date": contract.renewal_date.isoformat() if contract.renewal_date else None
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error completing renewal: {str(e)}")


@router.post("/renewals/{renewal_id}/decline", response_model=dict)
async def decline_renewal(
    renewal_id: str,
    reason: str = Query(...),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Decline a contract renewal
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    Note: Wraps sync service calls in executor.
    """
    try:
        def _decline_renewal():
            sync_db = SessionLocal()
            try:
                service = ContractRenewalService(sync_db, current_tenant.id)
                return service.decline_renewal(renewal_id, reason)
            finally:
                sync_db.close()
        
        loop = asyncio.get_event_loop()
        success = await loop.run_in_executor(None, _decline_renewal)
        
        if not success:
            raise HTTPException(status_code=404, detail="Renewal not found")
        
        return {
            "success": True,
            "message": "Renewal declined successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error declining renewal: {str(e)}")



