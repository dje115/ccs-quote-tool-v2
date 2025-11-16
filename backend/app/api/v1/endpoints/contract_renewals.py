#!/usr/bin/env python3
"""
Contract Renewals API Endpoints
Multi-tenant aware renewal management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
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
    db: Session = Depends(get_db)
):
    """List renewals for a contract"""
    try:
        from app.models.support_contract import SupportContract, ContractRenewal
        
        # Verify contract belongs to tenant
        contract = db.query(SupportContract).filter(
            and_(
                SupportContract.id == contract_id,
                SupportContract.tenant_id == current_tenant.id
            )
        ).first()
        
        if not contract:
            raise HTTPException(status_code=404, detail="Contract not found")
        
        # Get renewals
        query = db.query(ContractRenewal).filter(
            ContractRenewal.contract_id == contract_id
        )
        
        if status_filter:
            query = query.filter(ContractRenewal.status == status_filter)
        
        renewals = query.order_by(ContractRenewal.renewal_date.desc()).all()
        
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
    db: Session = Depends(get_db)
):
    """Create a renewal record for a contract"""
    try:
        service = ContractRenewalService(db, current_tenant.id)
        
        renewal = service.create_renewal_record(
            contract_id=contract_id,
            renewal_date=renewal_data.renewal_date,
            new_end_date=renewal_data.new_end_date,
            new_monthly_value=renewal_data.new_monthly_value,
            new_annual_value=renewal_data.new_annual_value,
            renewal_type=renewal_data.renewal_type or "manual"
        )
        
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
    db: Session = Depends(get_db)
):
    """Approve a contract renewal"""
    try:
        service = ContractRenewalService(db, current_tenant.id)
        renewal = service.approve_renewal(renewal_id, current_user.id)
        
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
    db: Session = Depends(get_db)
):
    """Complete a contract renewal"""
    try:
        service = ContractRenewalService(db, current_tenant.id)
        contract = service.complete_renewal(renewal_id)
        
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
    db: Session = Depends(get_db)
):
    """Decline a contract renewal"""
    try:
        service = ContractRenewalService(db, current_tenant.id)
        success = service.decline_renewal(renewal_id, reason)
        
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


