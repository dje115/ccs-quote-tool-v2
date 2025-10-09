#!/usr/bin/env python3
"""
Customer management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, EmailStr
import uuid
from datetime import datetime

from app.core.database import get_db
from app.core.dependencies import get_current_user, check_permission
from app.models.crm import Customer, CustomerStatus, BusinessSector, BusinessSize
from app.models.tenant import User

router = APIRouter()


# Pydantic schemas
class CustomerCreate(BaseModel):
    company_name: str
    website: str | None = None
    main_email: EmailStr | None = None
    main_phone: str | None = None
    business_sector: BusinessSector | None = None
    business_size: BusinessSize | None = None
    description: str | None = None
    billing_address: str | None = None
    billing_postcode: str | None = None


class CustomerResponse(BaseModel):
    id: str
    company_name: str
    status: str
    website: str | None
    main_email: str | None
    business_sector: str | None
    business_size: str | None
    created_at: datetime
    
    class Config:
        from_attributes = True


class CustomerUpdate(BaseModel):
    company_name: str | None = None
    status: CustomerStatus | None = None
    website: str | None = None
    main_email: EmailStr | None = None
    main_phone: str | None = None
    business_sector: BusinessSector | None = None
    business_size: BusinessSize | None = None
    description: str | None = None
    billing_address: str | None = None
    billing_postcode: str | None = None


@router.get("/", response_model=List[CustomerResponse])
async def list_customers(
    skip: int = 0,
    limit: int = 20,
    status: Optional[CustomerStatus] = None,
    sector: Optional[BusinessSector] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List customers for current tenant"""
    query = db.query(Customer).filter_by(
        tenant_id=current_user.tenant_id,
        is_deleted=False
    )
    
    # Apply filters
    if status:
        query = query.filter_by(status=status)
    if sector:
        query = query.filter_by(business_sector=sector)
    if search:
        query = query.filter(Customer.company_name.ilike(f"%{search}%"))
    
    customers = query.offset(skip).limit(limit).all()
    return customers


@router.post("/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer_data: CustomerCreate,
    current_user: User = Depends(check_permission("customer:create")),
    db: Session = Depends(get_db)
):
    """Create new customer"""
    
    # Check for duplicates
    existing = db.query(Customer).filter_by(
        tenant_id=current_user.tenant_id,
        company_name=customer_data.company_name,
        is_deleted=False
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer with this name already exists"
        )
    
    try:
        customer = Customer(
            id=str(uuid.uuid4()),
            tenant_id=current_user.tenant_id,
            company_name=customer_data.company_name,
            website=customer_data.website,
            main_email=customer_data.main_email,
            main_phone=customer_data.main_phone,
            business_sector=customer_data.business_sector,
            business_size=customer_data.business_size,
            description=customer_data.description,
            billing_address=customer_data.billing_address,
            billing_postcode=customer_data.billing_postcode,
            status=CustomerStatus.LEAD
        )
        
        db.add(customer)
        db.commit()
        db.refresh(customer)
        
        return customer
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating customer: {str(e)}"
        )


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get customer by ID"""
    customer = db.query(Customer).filter_by(
        id=customer_id,
        tenant_id=current_user.tenant_id,
        is_deleted=False
    ).first()
    
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    return customer


@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: str,
    customer_update: CustomerUpdate,
    current_user: User = Depends(check_permission("customer:update")),
    db: Session = Depends(get_db)
):
    """Update customer"""
    customer = db.query(Customer).filter_by(
        id=customer_id,
        tenant_id=current_user.tenant_id,
        is_deleted=False
    ).first()
    
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Update fields
    if customer_update.company_name is not None:
        customer.company_name = customer_update.company_name
    if customer_update.status is not None:
        customer.status = customer_update.status
    if customer_update.website is not None:
        customer.website = customer_update.website
    if customer_update.main_email is not None:
        customer.main_email = customer_update.main_email
    if customer_update.main_phone is not None:
        customer.main_phone = customer_update.main_phone
    if customer_update.business_sector is not None:
        customer.business_sector = customer_update.business_sector
    if customer_update.business_size is not None:
        customer.business_size = customer_update.business_size
    if customer_update.description is not None:
        customer.description = customer_update.description
    if customer_update.billing_address is not None:
        customer.billing_address = customer_update.billing_address
    if customer_update.billing_postcode is not None:
        customer.billing_postcode = customer_update.billing_postcode
    
    db.commit()
    db.refresh(customer)
    
    return customer


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(
    customer_id: str,
    current_user: User = Depends(check_permission("customer:delete")),
    db: Session = Depends(get_db)
):
    """Soft delete customer"""
    customer = db.query(Customer).filter_by(
        id=customer_id,
        tenant_id=current_user.tenant_id,
        is_deleted=False
    ).first()
    
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Soft delete
    customer.is_deleted = True
    customer.deleted_at = datetime.utcnow()
    db.commit()
    
    return None
