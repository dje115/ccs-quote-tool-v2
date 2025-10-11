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
from app.services.ai_analysis_service import AIAnalysisService

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
    ai_analysis_raw: str | None = None
    lead_score: int | None = None


class CustomerResponse(BaseModel):
    id: str
    company_name: str
    status: str
    website: str | None = None
    main_email: str | None = None
    business_sector: str | None = None
    business_size: str | None = None
    created_at: datetime
    updated_at: datetime
    lead_score: int | None = None
    ai_analysis_raw: dict | None = None
    companies_house_data: dict | None = None
    google_maps_data: dict | None = None
    company_registration: str | None = None
    registration_confirmed: bool | None = None
    main_phone: str | None = None
    known_facts: str | None = None
    billing_address: str | None = None
    billing_postcode: str | None = None
    excluded_addresses: list | None = None
    manual_addresses: list | None = None
    shipping_address: str | None = None
    shipping_postcode: str | None = None
    description: str | None = None
    linkedin_url: str | None = None
    linkedin_data: dict | None = None
    website_data: dict | None = None
    
    class Config:
        from_attributes = True


class CustomerUpdate(BaseModel):
    company_name: str | None = None
    company_registration: str | None = None
    status: CustomerStatus | None = None
    website: str | None = None
    main_email: EmailStr | None = None
    main_phone: str | None = None
    business_sector: BusinessSector | None = None
    business_size: BusinessSize | None = None
    description: str | None = None
    billing_address: str | None = None
    billing_postcode: str | None = None
    known_facts: str | None = None


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
    from sqlalchemy import select
    
    # Build query using SQLAlchemy 2.0 syntax
    stmt = select(Customer).where(
        Customer.tenant_id == current_user.tenant_id,
        Customer.is_deleted == False
    )
    
    # Apply filters
    if status:
        stmt = stmt.where(Customer.status == status)
    if sector:
        stmt = stmt.where(Customer.business_sector == sector)
    if search:
        stmt = stmt.where(Customer.company_name.ilike(f"%{search}%"))
    
    stmt = stmt.offset(skip).limit(limit)
    result = db.execute(stmt)
    customers = result.scalars().all()
    return customers


@router.post("/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer_data: CustomerCreate,
    current_user: User = Depends(check_permission("customer:create")),
    db: Session = Depends(get_db)
):
    """Create new customer"""
    print(f"[CREATE CUSTOMER] Received data: {customer_data}")
    print(f"[CREATE CUSTOMER] Company name: {customer_data.company_name}")
    
    # Check for duplicates
    from sqlalchemy import select
    
    stmt = select(Customer).where(
        Customer.tenant_id == current_user.tenant_id,
        Customer.company_name == customer_data.company_name,
        Customer.is_deleted == False
    )
    result = db.execute(stmt)
    existing = result.scalars().first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer with this name already exists"
        )
    
    try:
        import json
        
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
        
        # Store AI analysis if provided
        if customer_data.ai_analysis_raw:
            try:
                customer.ai_analysis_raw = json.loads(customer_data.ai_analysis_raw)
            except:
                customer.ai_analysis_raw = {"raw": customer_data.ai_analysis_raw}
        
        # Store lead score if provided
        if customer_data.lead_score is not None:
            customer.lead_score = customer_data.lead_score
        
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
    from sqlalchemy import select
    
    stmt = select(Customer).where(
        Customer.id == customer_id,
        Customer.tenant_id == current_user.tenant_id,
        Customer.is_deleted == False
    )
    result = db.execute(stmt)
    customer = result.scalars().first()
    
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
    from sqlalchemy import select
    
    stmt = select(Customer).where(
        Customer.id == customer_id,
        Customer.tenant_id == current_user.tenant_id,
        Customer.is_deleted == False
    )
    result = db.execute(stmt)
    customer = result.scalars().first()
    
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Update fields
    if customer_update.company_name is not None:
        customer.company_name = customer_update.company_name
    if customer_update.company_registration is not None:
        customer.company_registration = customer_update.company_registration
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
    if customer_update.known_facts is not None:
        # Allow empty string to clear known facts
        customer.known_facts = customer_update.known_facts if customer_update.known_facts.strip() else None
    
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
    from sqlalchemy import select
    
    stmt = select(Customer).where(
        Customer.id == customer_id,
        Customer.tenant_id == current_user.tenant_id,
        Customer.is_deleted == False
    )
    result = db.execute(stmt)
    customer = result.scalars().first()
    
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Soft delete
    customer.is_deleted = True
    customer.deleted_at = datetime.utcnow()
    db.commit()
    
    return None


@router.post("/{customer_id}/confirm-registration")
async def confirm_registration(
    customer_id: str,
    confirmed: bool,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Toggle company registration confirmation status"""
    from sqlalchemy import select
    
    stmt = select(Customer).where(
        Customer.id == customer_id,
        Customer.tenant_id == current_user.tenant_id,
        Customer.is_deleted == False
    )
    result = db.execute(stmt)
    customer = result.scalars().first()
    
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    customer.registration_confirmed = confirmed
    db.commit()
    db.refresh(customer)
    
    return {"success": True, "registration_confirmed": confirmed}


@router.post("/{customer_id}/ai-analysis")
async def run_ai_analysis(
    customer_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Run AI analysis on customer using Companies House, Google Maps, and OpenAI"""
    from sqlalchemy import select
    
    # Get customer
    stmt = select(Customer).where(
        Customer.id == customer_id,
        Customer.tenant_id == current_user.tenant_id,
        Customer.is_deleted == False
    )
    result = db.execute(stmt)
    customer = result.scalars().first()
    
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    try:
        # Get API keys from tenant settings
        from sqlalchemy import select as sql_select
        from app.models.tenant import Tenant
        
        tenant_stmt = sql_select(Tenant).where(Tenant.id == current_user.tenant_id)
        tenant_result = db.execute(tenant_stmt)
        tenant = tenant_result.scalars().first()
        
        # Initialize AI analysis service with tenant's API keys
        ai_service = AIAnalysisService(
            openai_api_key=tenant.openai_api_key if tenant and tenant.openai_api_key else None,
            companies_house_api_key=tenant.companies_house_api_key if tenant and tenant.companies_house_api_key else None,
            google_maps_api_key=tenant.google_maps_api_key if tenant and tenant.google_maps_api_key else None
        )
        
        print(f"[AI ANALYSIS] Starting analysis for customer: {customer.company_name}")
        
        # Run the AI analysis
        analysis_result = await ai_service.analyze_company(
            company_name=customer.company_name,
            company_number=customer.company_registration,
            website=customer.website,
            known_facts=customer.known_facts
        )
        
        if analysis_result.get('success'):
            # Store the results in customer record
            customer.ai_analysis_raw = analysis_result.get('analysis')
            customer.lead_score = analysis_result.get('analysis', {}).get('lead_score')
            customer.companies_house_data = analysis_result.get('source_data', {}).get('companies_house')
            customer.google_maps_data = analysis_result.get('source_data', {}).get('google_maps')
            
            # Store web scraping data (website and LinkedIn)
            web_scraping_data = analysis_result.get('source_data', {}).get('web_scraping', {})
            if web_scraping_data:
                # Store LinkedIn data
                linkedin_data = web_scraping_data.get('linkedin', {})
                if linkedin_data.get('linkedin_url'):
                    customer.linkedin_url = linkedin_data.get('linkedin_url')
                customer.linkedin_data = linkedin_data if linkedin_data else None
                
                # Store website analysis data
                website_data = web_scraping_data.get('website', {})
                customer.website_data = website_data if website_data else None
            
            # Update company registration if found and not already set
            if not customer.company_registration:
                ch_data = analysis_result.get('source_data', {}).get('companies_house', {})
                if ch_data.get('company_number'):
                    customer.company_registration = ch_data.get('company_number')
            
            db.commit()
            db.refresh(customer)
            
            print(f"[AI ANALYSIS] Successfully completed for {customer.company_name}")
            
            return {
                'success': True,
                'message': 'AI analysis completed successfully',
                'analysis': analysis_result.get('analysis'),
                'source_data': analysis_result.get('source_data')
            }
        else:
            print(f"[AI ANALYSIS] Failed: {analysis_result.get('error')}")
            return {
                'success': False,
                'error': analysis_result.get('error', 'AI analysis failed')
            }
    
    except Exception as e:
        print(f"[AI ANALYSIS] Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error running AI analysis: {str(e)}"
        )


@router.post("/{customer_id}/addresses/exclude")
def exclude_address(
    customer_id: str,
    request: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Exclude an address from display (mark as 'Not this business')"""
    from sqlalchemy.orm.attributes import flag_modified
    
    try:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        location_id = request.get('location_id')
        if not location_id:
            raise HTTPException(status_code=400, detail="location_id is required")
        
        # Get current excluded addresses or initialize empty list
        excluded_addresses = customer.excluded_addresses or []
        
        # Add location_id if not already excluded
        if location_id not in excluded_addresses:
            excluded_addresses.append(location_id)
            customer.excluded_addresses = excluded_addresses
            
            # CRITICAL: Tell SQLAlchemy the JSON field changed
            flag_modified(customer, 'excluded_addresses')
            
            db.add(customer)
            db.commit()
            db.refresh(customer)
        
        return {
            'success': True,
            'message': 'Address excluded successfully',
            'excluded_addresses': customer.excluded_addresses
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error excluding address: {str(e)}"
        )


@router.post("/{customer_id}/addresses/include")
def include_address(
    customer_id: str,
    request: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Include an address back in display (restore from excluded)"""
    from sqlalchemy.orm.attributes import flag_modified
    
    try:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        location_id = request.get('location_id')
        if not location_id:
            raise HTTPException(status_code=400, detail="location_id is required")
        
        # Get current excluded addresses
        excluded_addresses = customer.excluded_addresses or []
        
        # Remove location_id if it exists
        if location_id in excluded_addresses:
            excluded_addresses.remove(location_id)
            customer.excluded_addresses = excluded_addresses
            
            # CRITICAL: Tell SQLAlchemy the JSON field changed
            flag_modified(customer, 'excluded_addresses')
            
            db.add(customer)
            db.commit()
            db.refresh(customer)
        
        return {
            'success': True,
            'message': 'Address included successfully',
            'excluded_addresses': excluded_addresses
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error including address: {str(e)}"
        )
