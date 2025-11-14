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
from app.core.dependencies import get_current_user, get_current_tenant, check_permission
from app.core.api_keys import get_api_keys
from app.models.crm import Customer, CustomerStatus, BusinessSector, BusinessSize
from app.models.tenant import User, Tenant
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
    is_competitor: bool | None = None
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
    ai_analysis_status: str | None = None
    ai_analysis_task_id: str | None = None
    ai_analysis_started_at: datetime | None = None
    ai_analysis_completed_at: datetime | None = None
    
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
    is_competitor: bool | None = None


def _safe_parse_json_field(value):
    """Safely parse JSON field that might be a string or dict"""
    if value is None:
        return None
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            import json
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            # If it's not valid JSON, wrap it in a dict
            return {"raw": value}
    return None


@router.get("/", response_model=List[CustomerResponse])
async def list_customers(
    skip: int = 0,
    limit: int = 20,
    status: Optional[CustomerStatus] = None,
    sector: Optional[BusinessSector] = None,
    search: Optional[str] = None,
    is_competitor: Optional[bool] = None,
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
    if is_competitor is not None:
        stmt = stmt.where(Customer.is_competitor == is_competitor)
    
    stmt = stmt.offset(skip).limit(limit)
    result = db.execute(stmt)
    customers = result.scalars().all()
    
    # Fix ai_analysis_raw field that might be a string instead of dict
    for customer in customers:
        if hasattr(customer, 'ai_analysis_raw'):
            customer.ai_analysis_raw = _safe_parse_json_field(customer.ai_analysis_raw)
    
    return customers


@router.get("/competitors", response_model=List[CustomerResponse])
async def list_competitors(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List competitors for current tenant"""
    from sqlalchemy import select
    
    # Build query to get only competitors
    stmt = select(Customer).where(
        Customer.tenant_id == current_user.tenant_id,
        Customer.is_deleted == False,
        Customer.is_competitor == True
    )
    
    # Apply search filter if provided
    if search:
        stmt = stmt.where(Customer.company_name.ilike(f"%{search}%"))
    
    stmt = stmt.offset(skip).limit(limit)
    result = db.execute(stmt)
    competitors = result.scalars().all()
    return competitors


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
        
        # Publish customer.created event
        from app.core.events import get_event_publisher
        event_publisher = get_event_publisher()
        # Convert customer to dict for event
        customer_dict = {
            "id": customer.id,
            "company_name": customer.company_name,
            "status": customer.status.value if hasattr(customer.status, 'value') else str(customer.status),
            "website": customer.website,
            "main_email": customer.main_email,
            "main_phone": customer.main_phone,
            "business_sector": customer.business_sector.value if customer.business_sector and hasattr(customer.business_sector, 'value') else str(customer.business_sector) if customer.business_sector else None,
            "business_size": customer.business_size.value if customer.business_size and hasattr(customer.business_size, 'value') else str(customer.business_size) if customer.business_size else None,
        }
        event_publisher.publish_customer_created(
            tenant_id=current_user.tenant_id,
            customer_id=customer.id,
            customer_data=customer_dict
        )
        
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
    
    # Fix ai_analysis_raw field that might be a string instead of dict
    if hasattr(customer, 'ai_analysis_raw'):
        customer.ai_analysis_raw = _safe_parse_json_field(customer.ai_analysis_raw)
    
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
    if customer_update.is_competitor is not None:
        customer.is_competitor = customer_update.is_competitor
    
    db.commit()
    db.refresh(customer)
    
    # Publish customer.updated event
    from app.core.events import get_event_publisher
    event_publisher = get_event_publisher()
    # Convert customer to dict for event
    customer_dict = {
        "id": customer.id,
        "company_name": customer.company_name,
        "status": customer.status.value if hasattr(customer.status, 'value') else str(customer.status),
        "website": customer.website,
        "main_email": customer.main_email,
        "main_phone": customer.main_phone,
        "business_sector": customer.business_sector.value if customer.business_sector and hasattr(customer.business_sector, 'value') else str(customer.business_sector) if customer.business_sector else None,
        "business_size": customer.business_size.value if customer.business_size and hasattr(customer.business_size, 'value') else str(customer.business_size) if customer.business_size else None,
        "is_competitor": customer.is_competitor,
    }
    event_publisher.publish_customer_updated(
        tenant_id=current_user.tenant_id,
        customer_id=customer.id,
        customer_data=customer_dict
    )
    
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
    
    # Publish customer.deleted event
    from app.core.events import get_event_publisher
    event_publisher = get_event_publisher()
    event_publisher.publish_customer_deleted(
        tenant_id=current_user.tenant_id,
        customer_id=customer_id
    )
    
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
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Queue AI analysis for customer to run in background
    
    Analysis runs asynchronously using Celery and includes:
    - Website discovery (using web search like campaigns)
    - Companies House data retrieval
    - Google Maps location data
    - Website scraping and LinkedIn data
    - Comprehensive AI business intelligence
    """
    from sqlalchemy import select
    from app.core.celery_app import celery_app
    
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
    
    print(f"\n{'='*80}")
    print(f"🔄 QUEUEING AI ANALYSIS TO CELERY")
    print(f"Customer: {customer.company_name} ({customer_id})")
    print(f"Tenant: {current_tenant.name} ({current_tenant.id})")
    print(f"{'='*80}\n")
    
    # Queue the AI analysis task to Celery
    task = celery_app.send_task(
        'run_ai_analysis',
        args=[customer_id, str(current_tenant.id)]
    )
    
    print(f"✓ Task queued: {task.id}")
    
    # Update customer with task tracking info (like campaigns)
    from datetime import datetime, timezone
    customer.ai_analysis_status = 'queued'
    customer.ai_analysis_task_id = task.id
    customer.ai_analysis_started_at = datetime.now(timezone.utc)
    customer.ai_analysis_completed_at = None
    db.commit()
    
    return {
        'success': True,
        'message': 'AI analysis queued in background. The page will refresh automatically when complete.',
        'task_id': task.id,
        'status': 'queued',
        'customer_name': customer.company_name
    }



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
