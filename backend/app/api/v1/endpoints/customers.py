#!/usr/bin/env python3
"""
Customer management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, case
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr
import uuid
import asyncio
from datetime import datetime

from app.core.database import get_async_db
from app.core.dependencies import get_current_user, get_current_tenant, check_permission
from app.core.api_keys import get_api_keys
from app.models.crm import Customer, CustomerStatus, BusinessSector, BusinessSize
from app.models.tenant import User, Tenant
from app.services.ai_analysis_service import AIAnalysisService
from app.services.storage_service import get_storage_service
from fastapi.responses import Response, StreamingResponse

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
    last_contact_date: datetime | None = None
    conversion_probability: int | None = None
    next_scheduled_contact: datetime | None = None  # Next Point of Action (NPA)
    sla_breach_status: str | None = None  # 'none', 'warning', 'critical' - SLA breach status for customer's tickets
    
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
    lifecycle_auto_managed: bool | None = None


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


@router.get("/leads", response_model=List[CustomerResponse])
async def list_leads(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    _: None = Depends(lambda: check_permission("customers:read"))
):
    """
    Get all CRM leads (customers with status=LEAD)
    Includes lead-specific metrics like lead_score, last_contact_date, conversion_probability
    Also includes next_scheduled_contact (NPA) from activities
    """
    from app.models.sales import SalesActivity
    from datetime import datetime, timezone
    
    stmt = select(Customer).where(
        and_(
            Customer.tenant_id == current_tenant.id,
            Customer.status == CustomerStatus.LEAD,
            Customer.is_deleted == False
        )
    ).order_by(Customer.created_at.desc())
    
    result = await db.execute(stmt)
    customers = result.scalars().all()
    
    # Get next scheduled contact (NPA) for each customer
    customer_ids = [str(c.id) for c in customers]
    next_contacts = {}
    sla_breach_statuses = {}
    
    if customer_ids:
        # Query for the earliest future follow-up date for each customer
        npa_stmt = select(
            SalesActivity.customer_id,
            func.min(SalesActivity.follow_up_date).label('next_contact')
        ).where(
            and_(
                SalesActivity.customer_id.in_(customer_ids),
                SalesActivity.tenant_id == current_tenant.id,
                SalesActivity.follow_up_date.isnot(None),
                SalesActivity.follow_up_date > datetime.now(timezone.utc)
            )
        ).group_by(SalesActivity.customer_id)
        
        npa_result = await db.execute(npa_stmt)
        for row in npa_result:
            next_contacts[str(row.customer_id)] = row.next_contact
        
        # Get SLA breach status for each customer's tickets
        from app.models.helpdesk import Ticket
        from app.models.sla_compliance import SLABreachAlert
        
        breach_stmt = select(
            Ticket.customer_id,
            func.max(
                case(
                    (SLABreachAlert.alert_level == 'critical', 3),
                    (SLABreachAlert.alert_level == 'warning', 2),
                    else_=1
                )
            ).label('max_severity')
        ).join(
            SLABreachAlert, Ticket.id == SLABreachAlert.ticket_id, isouter=True
        ).where(
            and_(
                Ticket.customer_id.in_(customer_ids),
                Ticket.tenant_id == current_tenant.id,
                SLABreachAlert.acknowledged == False
            )
        ).group_by(Ticket.customer_id)
        
        breach_result = await db.execute(breach_stmt)
        for row in breach_result:
            if row.max_severity == 3:
                sla_breach_statuses[str(row.customer_id)] = 'critical'
            elif row.max_severity == 2:
                sla_breach_statuses[str(row.customer_id)] = 'warning'
            else:
                sla_breach_statuses[str(row.customer_id)] = 'none'
    
    # Build response with next scheduled contact
    response = []
    for customer in customers:
        customer_dict = CustomerResponse.model_validate(customer).model_dump()
        customer_dict['next_scheduled_contact'] = next_contacts.get(str(customer.id))
        customer_dict['sla_breach_status'] = sla_breach_statuses.get(str(customer.id), 'none')
        response.append(CustomerResponse(**customer_dict))
    
    return response


@router.get("/", response_model=List[CustomerResponse])
async def list_customers(
    skip: int = 0,
    limit: int = 20,
    status: Optional[CustomerStatus] = None,
    sector: Optional[BusinessSector] = None,
    search: Optional[str] = None,
    is_competitor: Optional[bool] = None,
    exclude_leads: bool = True,  # By default, exclude leads from customers list
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    List customers for current tenant
    
    By default, excludes customers with status=LEAD (these are shown in the separate Leads view).
    Set exclude_leads=False to include leads in the customers list.
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    Database queries are executed asynchronously, allowing concurrent request handling.
    """
    from sqlalchemy import select
    
    # Build query using SQLAlchemy 2.0 syntax
    stmt = select(Customer).where(
        Customer.tenant_id == current_user.tenant_id,
        Customer.is_deleted == False
    )
    
    # By default, exclude leads (status=LEAD) from customers list
    # Leads should be viewed in the separate /leads-crm route
    if exclude_leads:
        stmt = stmt.where(Customer.status != CustomerStatus.LEAD)
    
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
    result = await db.execute(stmt)
    customers = result.scalars().all()
    
    # Get next scheduled contact (NPA) for each customer
    customer_ids = [str(c.id) for c in customers]
    next_contacts = {}
    sla_breach_statuses = {}
    
    if customer_ids:
        from app.models.sales import SalesActivity
        from datetime import datetime, timezone
        from sqlalchemy import func
        npa_stmt = select(
            SalesActivity.customer_id,
            func.min(SalesActivity.follow_up_date).label('next_contact')
        ).where(
            and_(
                SalesActivity.customer_id.in_(customer_ids),
                SalesActivity.tenant_id == current_user.tenant_id,
                SalesActivity.follow_up_date.isnot(None),
                SalesActivity.follow_up_date > datetime.now(timezone.utc)
            )
        ).group_by(SalesActivity.customer_id)
        
        npa_result = await db.execute(npa_stmt)
        for row in npa_result:
            next_contacts[str(row.customer_id)] = row.next_contact
        
        # Get SLA breach status for each customer's tickets
        from app.models.helpdesk import Ticket
        from app.models.sla_compliance import SLABreachAlert
        
        breach_stmt = select(
            Ticket.customer_id,
            func.max(
                case(
                    (SLABreachAlert.alert_level == 'critical', 3),
                    (SLABreachAlert.alert_level == 'warning', 2),
                    else_=1
                )
            ).label('max_severity')
        ).join(
            SLABreachAlert, Ticket.id == SLABreachAlert.ticket_id, isouter=True
        ).where(
            and_(
                Ticket.customer_id.in_(customer_ids),
                Ticket.tenant_id == current_user.tenant_id,
                SLABreachAlert.acknowledged == False
            )
        ).group_by(Ticket.customer_id)
        
        breach_result = await db.execute(breach_stmt)
        for row in breach_result:
            if row.max_severity == 3:
                sla_breach_statuses[str(row.customer_id)] = 'critical'
            elif row.max_severity == 2:
                sla_breach_statuses[str(row.customer_id)] = 'warning'
            else:
                sla_breach_statuses[str(row.customer_id)] = 'none'
    
    # Fix ai_analysis_raw field that might be a string instead of dict
    # Build response with next scheduled contact
    response = []
    for customer in customers:
        if hasattr(customer, 'ai_analysis_raw'):
            customer.ai_analysis_raw = _safe_parse_json_field(customer.ai_analysis_raw)
        
        customer_dict = CustomerResponse.model_validate(customer).model_dump()
        customer_dict['next_scheduled_contact'] = next_contacts.get(str(customer.id))
        customer_dict['sla_breach_status'] = sla_breach_statuses.get(str(customer.id), 'none')
        response.append(CustomerResponse(**customer_dict))
    
    return response


@router.get("/competitors", response_model=List[CustomerResponse])
async def list_competitors(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    List competitors for current tenant
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
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
    result = await db.execute(stmt)
    competitors = result.scalars().all()
    return competitors


@router.post("/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer_data: CustomerCreate,
    current_user: User = Depends(check_permission("customer:create")),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Create new customer
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"[CREATE CUSTOMER] Received data: {customer_data}")
    logger.info(f"[CREATE CUSTOMER] Company name: {customer_data.company_name}")
    
    # Check for duplicates
    from sqlalchemy import select
    
    stmt = select(Customer).where(
        Customer.tenant_id == current_user.tenant_id,
        Customer.company_name == customer_data.company_name,
        Customer.is_deleted == False
    )
    result = await db.execute(stmt)
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
        await db.commit()
        await db.refresh(customer)
        
        # Publish customer.created event (async, non-blocking)
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
        # Fire and forget - don't await to avoid blocking response
        asyncio.create_task(event_publisher.publish_customer_created(
            tenant_id=current_user.tenant_id,
            customer_id=customer.id,
            customer_data=customer_dict
        ))
        
        return customer
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating customer: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating customer: {str(e)}"
        )


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get customer by ID
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    from sqlalchemy import select
    
    stmt = select(Customer).where(
        Customer.id == customer_id,
        Customer.tenant_id == current_user.tenant_id,
        Customer.is_deleted == False
    )
    result = await db.execute(stmt)
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
    db: AsyncSession = Depends(get_async_db)
):
    """
    Update customer
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    from sqlalchemy import select
    
    stmt = select(Customer).where(
        Customer.id == customer_id,
        Customer.tenant_id == current_user.tenant_id,
        Customer.is_deleted == False
    )
    result = await db.execute(stmt)
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
    if customer_update.lifecycle_auto_managed is not None:
        customer.lifecycle_auto_managed = customer_update.lifecycle_auto_managed
    
    await db.commit()
    await db.refresh(customer)
    
    # Publish customer.updated event (async, non-blocking)
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
    # Fire and forget - don't await to avoid blocking response
    asyncio.create_task(event_publisher.publish_customer_updated(
        tenant_id=current_user.tenant_id,
        customer_id=customer.id,
        customer_data=customer_dict
    ))
    
    return customer


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(
    customer_id: str,
    current_user: User = Depends(check_permission("customer:delete")),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Soft delete customer
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    from sqlalchemy import select
    
    stmt = select(Customer).where(
        Customer.id == customer_id,
        Customer.tenant_id == current_user.tenant_id,
        Customer.is_deleted == False
    )
    result = await db.execute(stmt)
    customer = result.scalars().first()
    
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Soft delete
    customer.is_deleted = True
    customer.deleted_at = datetime.utcnow()
    await db.commit()
    
    # Publish customer.deleted event (async, non-blocking)
    from app.core.events import get_event_publisher
    event_publisher = get_event_publisher()
    # Fire and forget - don't await to avoid blocking response
    asyncio.create_task(event_publisher.publish_customer_deleted(
        tenant_id=current_user.tenant_id,
        customer_id=customer_id
    ))
    
    return None


@router.post("/{customer_id}/confirm-registration")
async def confirm_registration(
    customer_id: str,
    confirmed: bool,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Toggle company registration confirmation status
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    from sqlalchemy import select
    
    stmt = select(Customer).where(
        Customer.id == customer_id,
        Customer.tenant_id == current_user.tenant_id,
        Customer.is_deleted == False
    )
    result = await db.execute(stmt)
    customer = result.scalars().first()
    
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    customer.registration_confirmed = confirmed
    await db.commit()
    await db.refresh(customer)
    
    return {"success": True, "registration_confirmed": confirmed}


class AIAnalysisOptions(BaseModel):
    """Options for AI analysis"""
    update_financial_data: bool = True  # Default to True for backward compatibility
    update_addresses: bool = True  # Default to True for backward compatibility


@router.post("/{customer_id}/ai-analysis")
async def run_ai_analysis(
    customer_id: str,
    options: AIAnalysisOptions = AIAnalysisOptions(),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Queue AI analysis for customer to run in background
    
    Analysis runs asynchronously using Celery and includes:
    - Website discovery (using web search like campaigns)
    - Companies House data retrieval (if update_financial_data=True)
    - Google Maps location data (if update_addresses=True)
    - Website scraping and LinkedIn data
    - Comprehensive AI business intelligence
    
    Args:
        options: Analysis options controlling which data sources to update
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    from sqlalchemy import select
    from app.core.celery_app import celery_app
    
    # Get customer
    stmt = select(Customer).where(
        Customer.id == customer_id,
        Customer.tenant_id == current_user.tenant_id,
        Customer.is_deleted == False
    )
    result = await db.execute(stmt)
    customer = result.scalars().first()
    
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    print(f"\n{'='*80}")
    print(f"🔄 QUEUEING AI ANALYSIS TO CELERY")
    print(f"Customer: {customer.company_name} ({customer_id})")
    print(f"Tenant: {current_tenant.name} ({current_tenant.id})")
    print(f"Options: update_financial_data={options.update_financial_data}, update_addresses={options.update_addresses}")
    print(f"{'='*80}\n")
    
    try:
        # Queue the AI analysis task to Celery with options
        task = celery_app.send_task(
            'run_ai_analysis',
            args=[customer_id, str(current_tenant.id)],
            kwargs={
                'update_financial_data': options.update_financial_data,
                'update_addresses': options.update_addresses
            }
        )
        
        print(f"✓ Task queued: {task.id}")
        
        # Update customer with task tracking info (like campaigns)
        from datetime import datetime, timezone
        customer.ai_analysis_status = 'queued'
        customer.ai_analysis_task_id = task.id
        customer.ai_analysis_started_at = datetime.now(timezone.utc)
        customer.ai_analysis_completed_at = None
        await db.commit()
        
        return {
            'success': True,
            'message': 'AI analysis queued in background. The page will refresh automatically when complete.',
            'task_id': task.id,
            'status': 'queued',
            'customer_name': customer.company_name
        }
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error running AI analysis: {e}", exc_info=True)
        
        # Check if it's a Redis/Celery connection error
        error_msg = str(e)
        if 'Connection refused' in error_msg or 'Redis' in error_msg or 'kombu' in error_msg:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI analysis service is temporarily unavailable. Please check that Redis and Celery workers are running."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error running AI analysis: {str(e)}"
            )



@router.post("/{customer_id}/addresses/exclude")
async def exclude_address(
    customer_id: str,
    request: dict,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Exclude an address from display (mark as 'Not this business')
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    from sqlalchemy import select
    
    try:
        stmt = select(Customer).where(
            and_(
                Customer.id == customer_id,
                Customer.tenant_id == current_user.tenant_id
            )
        )
        result = await db.execute(stmt)
        customer = result.scalars().first()
        
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
            
            await db.commit()
            await db.refresh(customer)
        
        return {
            'success': True,
            'message': 'Address excluded successfully',
            'excluded_addresses': customer.excluded_addresses
        }
    
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error excluding address: {str(e)}"
        )


@router.post("/{customer_id}/addresses/include")
async def include_address(
    customer_id: str,
    request: dict,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Include an address back in display (restore from excluded)
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    from sqlalchemy import select
    
    try:
        stmt = select(Customer).where(
            and_(
                Customer.id == customer_id,
                Customer.tenant_id == current_user.tenant_id
            )
        )
        result = await db.execute(stmt)
        customer = result.scalars().first()
        
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
            
            await db.commit()
            await db.refresh(customer)
        
        return {
            'success': True,
            'message': 'Address included successfully',
            'excluded_addresses': excluded_addresses
        }
    
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error including address: {str(e)}"
        )


@router.get("/{customer_id}/accounts-documents")
async def list_accounts_documents(
    customer_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all accounts documents stored in MinIO for a customer
    
    SECURITY: Tenant isolation enforced via:
    1. Database query filters by customer.tenant_id == current_user.tenant_id
    2. Only documents belonging to the authenticated tenant are returned
    3. MinIO paths include tenant_id: accounts/{tenant_id}/{customer_id}/...
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        from sqlalchemy import select
        
        # SECURITY: Database query enforces tenant isolation
        stmt = select(Customer).where(
            and_(
                Customer.id == customer_id,
                Customer.tenant_id == current_user.tenant_id
            )
        )
        result = await db.execute(stmt)
        customer = result.scalars().first()
        
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )
        
        # Get accounts documents from companies_house_data
        accounts_documents = []
        if customer.companies_house_data and isinstance(customer.companies_house_data, dict):
            accounts_documents = customer.companies_house_data.get('accounts_documents', [])
        
        # SECURITY: Filter out any documents that don't match tenant_id (defense in depth)
        tenant_id = current_user.tenant_id
        filtered_documents = []
        for doc in accounts_documents:
            minio_path = doc.get('minio_path', '')
            if minio_path.startswith(f"accounts/{tenant_id}/"):
                filtered_documents.append(doc)
            else:
                # Log potential security issue (document path doesn't match tenant)
                print(f"[SECURITY WARNING] Document path {minio_path} doesn't match tenant {tenant_id}")
        
        return {
            'customer_id': customer_id,
            'customer_name': customer.company_name,
            'accounts_documents': filtered_documents,
            'count': len(filtered_documents)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving accounts documents: {str(e)}"
        )


@router.get("/{customer_id}/accounts-documents/{transaction_id}/view")
async def view_accounts_document(
    customer_id: str,
    transaction_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    View/download a specific accounts document from MinIO
    
    SECURITY: Tenant isolation enforced via:
    1. Database query filters by customer.tenant_id == current_user.tenant_id
    2. MinIO path validation ensures path starts with accounts/{tenant_id}/
    3. Only documents belonging to the authenticated tenant can be accessed
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        from sqlalchemy import select
        from fastapi.responses import Response
        
        stmt = select(Customer).where(
            and_(
                Customer.id == customer_id,
                Customer.tenant_id == current_user.tenant_id
            )
        )
        result = await db.execute(stmt)
        customer = result.scalars().first()
        
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )
        
        # Find the document in companies_house_data
        accounts_documents = []
        if customer.companies_house_data and isinstance(customer.companies_house_data, dict):
            accounts_documents = customer.companies_house_data.get('accounts_documents', [])
        
        # Find the document by transaction_id
        document_info = None
        for doc in accounts_documents:
            if doc.get('transaction_id') == transaction_id:
                document_info = doc
                break
        
        if not document_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Accounts document with transaction_id {transaction_id} not found"
            )
        
        # Get the document from MinIO
        storage_service = get_storage_service()
        minio_path = document_info.get('minio_path')
        
        if not minio_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="MinIO path not found for this document"
            )
        
        # SECURITY: Verify tenant isolation - ensure path starts with tenant_id
        expected_tenant_prefix = f"accounts/{current_user.tenant_id}/"
        if not minio_path.startswith(expected_tenant_prefix):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Tenant isolation violation"
            )
        
        try:
            file_data = await storage_service.download_file(minio_path)
            content_type = document_info.get('content_type', 'application/xhtml+xml')
            
            # Return the file as a response
            return Response(
                content=file_data,
                media_type=content_type,
                headers={
                    'Content-Disposition': f'inline; filename="{transaction_id}.xhtml"',
                    'X-Content-Type-Options': 'nosniff'
                }
            )
        except Exception as storage_error:
            raise HTTPException(
                status_code=500,
                detail=f"Error retrieving document from MinIO: {str(storage_error)}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error viewing accounts document: {str(e)}"
        )


@router.get("/{customer_id}/accounts-documents/{transaction_id}/download-url")
async def get_accounts_document_url(
    customer_id: str,
    transaction_id: str,
    expires_hours: int = Query(default=24, ge=1, le=168),  # 1 hour to 7 days
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a presigned URL to download/view an accounts document (for external sharing)
    
    SECURITY: Tenant isolation enforced via:
    1. Database query filters by customer.tenant_id == current_user.tenant_id
    2. MinIO path validation ensures path starts with accounts/{tenant_id}/
    3. Presigned URLs are time-limited (1-168 hours)
    4. Only documents belonging to the authenticated tenant can be accessed
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        from datetime import timedelta
        from sqlalchemy import select
        
        stmt = select(Customer).where(
            and_(
                Customer.id == customer_id,
                Customer.tenant_id == current_user.tenant_id
            )
        )
        result = await db.execute(stmt)
        customer = result.scalars().first()
        
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )
        
        # Find the document in companies_house_data
        accounts_documents = []
        if customer.companies_house_data and isinstance(customer.companies_house_data, dict):
            accounts_documents = customer.companies_house_data.get('accounts_documents', [])
        
        # Find the document by transaction_id
        document_info = None
        for doc in accounts_documents:
            if doc.get('transaction_id') == transaction_id:
                document_info = doc
                break
        
        if not document_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Accounts document with transaction_id {transaction_id} not found"
            )
        
        # Generate presigned URL
        storage_service = get_storage_service()
        minio_path = document_info.get('minio_path')
        
        if not minio_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="MinIO path not found for this document"
            )
        
        # SECURITY: Verify tenant isolation - ensure path starts with tenant_id
        expected_tenant_prefix = f"accounts/{current_user.tenant_id}/"
        if not minio_path.startswith(expected_tenant_prefix):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Tenant isolation violation"
            )
        
        try:
            presigned_url = storage_service.get_presigned_url(
                object_name=minio_path,
                expires=timedelta(hours=expires_hours)
            )
            
            return {
                'customer_id': customer_id,
                'customer_name': customer.company_name,
                'transaction_id': transaction_id,
                'document_info': document_info,
                'presigned_url': presigned_url,
                'expires_hours': expires_hours
            }
        except Exception as storage_error:
            raise HTTPException(
                status_code=500,
                detail=f"Error generating presigned URL: {str(storage_error)}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting document URL: {str(e)}"
        )


# ============================================================================
# Customer Health Endpoints
# ============================================================================

@router.get("/{customer_id}/health")
async def get_customer_health(
    customer_id: str,
    days_back: int = Query(90, ge=7, le=365),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get customer health analysis
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        from app.services.customer_health_service import CustomerHealthService
        from app.core.database import SessionLocal
        
        # Verify customer exists and belongs to tenant
        stmt = select(Customer).where(
            and_(
                Customer.id == customer_id,
                Customer.tenant_id == current_user.tenant_id
            )
        )
        result = await db.execute(stmt)
        customer = result.scalar_one_or_none()
        
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Use sync session for health service
        # Skip AI digest generation for faster response (can be requested separately if needed)
        sync_db = SessionLocal()
        try:
            health_service = CustomerHealthService(sync_db, current_user.tenant_id)
            health_data = await health_service.analyze_customer_health(
                customer_id,
                days_back=days_back,
                include_digest=False  # Skip slow AI digest generation
            )
        finally:
            sync_db.close()
        
        return health_data
    
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting customer health: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting customer health: {str(e)}"
        )


@router.get("/{customer_id}/timeline")
async def get_customer_timeline(
    customer_id: str,
    limit: int = Query(50, ge=1, le=200),
    activity_types: Optional[List[str]] = Query(None),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get unified activity timeline for customer
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        from app.services.activity_timeline_service import ActivityTimelineService
        from app.core.database import SessionLocal
        
        # Verify customer exists
        stmt = select(Customer).where(
            and_(
                Customer.id == customer_id,
                Customer.tenant_id == current_user.tenant_id
            )
        )
        result = await db.execute(stmt)
        customer = result.scalar_one_or_none()
        
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Use sync session for timeline service
        sync_db = SessionLocal()
        try:
            timeline_service = ActivityTimelineService(sync_db, current_user.tenant_id)
            timeline = await timeline_service.get_customer_timeline(
                customer_id,
                limit=limit,
                activity_types=activity_types
            )
        finally:
            sync_db.close()
        
        return {
            "customer_id": customer_id,
            "customer_name": customer.company_name,
            "timeline": timeline,
            "count": len(timeline)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting customer timeline: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting customer timeline: {str(e)}"
        )


@router.get("/{customer_id}/timeline/daily-summary")
async def get_daily_summary(
    customer_id: str,
    date: Optional[str] = Query(None),  # ISO date string
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get daily AI summary of customer activities
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        from app.services.activity_timeline_service import ActivityTimelineService
        from app.core.database import SessionLocal
        from datetime import datetime as dt
        
        # Verify customer exists
        stmt = select(Customer).where(
            and_(
                Customer.id == customer_id,
                Customer.tenant_id == current_user.tenant_id
            )
        )
        result = await db.execute(stmt)
        customer = result.scalar_one_or_none()
        
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Parse date
        summary_date = None
        if date:
            try:
                summary_date = dt.fromisoformat(date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use ISO format.")
        
        # Use sync session for timeline service
        sync_db = SessionLocal()
        try:
            timeline_service = ActivityTimelineService(sync_db, current_user.tenant_id)
            summary = await timeline_service.generate_daily_summary(
                customer_id,
                date=summary_date
            )
        finally:
            sync_db.close()
        
        return summary
    
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting daily summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting daily summary: {str(e)}"
        )
