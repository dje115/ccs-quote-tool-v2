#!/usr/bin/env python3
"""
Tenant management endpoints - Super Admin Only
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from pydantic import BaseModel, EmailStr
import uuid
from datetime import datetime

from app.core.database import get_async_db
from app.core.dependencies import get_current_super_admin
from app.core.security import get_password_hash
from app.models.tenant import Tenant, User, TenantStatus, UserRole

router = APIRouter()


# Pydantic schemas
class TenantCreate(BaseModel):
    name: str
    slug: str
    domain: str | None = None
    primary_color: str = "#1976d2"
    secondary_color: str = "#dc004e"
    plan: str = "trial"
    admin_email: EmailStr
    admin_password: str
    admin_first_name: str
    admin_last_name: str


class TenantResponse(BaseModel):
    id: str
    name: str
    slug: str
    domain: str | None
    status: str
    plan: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class TenantUpdate(BaseModel):
    name: str | None = None
    status: TenantStatus | None = None
    plan: str | None = None
    primary_color: str | None = None
    secondary_color: str | None = None
    openai_api_key: str | None = None
    companies_house_api_key: str | None = None
    google_maps_api_key: str | None = None


@router.get("/", response_model=List[TenantResponse])
async def list_tenants(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_async_db)
):
    """
    List all tenants (super admin only)
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    stmt = select(Tenant).offset(skip).limit(limit)
    result = await db.execute(stmt)
    tenants = result.scalars().all()
    return tenants


@router.post("/", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    tenant_data: TenantCreate,
    current_user: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Create new tenant with admin user (super admin only)
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    # Check if slug already exists
    stmt = select(Tenant).where(Tenant.slug == tenant_data.slug)
    result = await db.execute(stmt)
    existing_tenant = result.scalars().first()
    if existing_tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant with this slug already exists"
        )
    
    try:
        # Create tenant
        tenant = Tenant(
            id=str(uuid.uuid4()),
            name=tenant_data.name,
            slug=tenant_data.slug,
            domain=tenant_data.domain,
            status=TenantStatus.TRIAL,
            primary_color=tenant_data.primary_color,
            secondary_color=tenant_data.secondary_color,
            plan=tenant_data.plan,
            settings={
                "timezone": "Europe/London",
                "currency": "GBP",
                "date_format": "DD/MM/YYYY",
                "features": {
                    "ai_analysis": True,
                    "lead_generation": True,
                    "quoting": True
                }
            }
        )
        
        db.add(tenant)
        await db.flush()
        
        # Create tenant admin user
        hashed_password = get_password_hash(tenant_data.admin_password)
        
        admin_user = User(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            email=tenant_data.admin_email,
            username=f"{tenant_data.slug}_admin",
            first_name=tenant_data.admin_first_name,
            last_name=tenant_data.admin_last_name,
            hashed_password=hashed_password,
            is_active=True,
            is_verified=True,
            role=UserRole.TENANT_ADMIN,
            permissions=[
                "customer:create", "customer:read", "customer:update", "customer:delete",
                "lead:create", "lead:read", "lead:update", "lead:delete",
                "quote:create", "quote:read", "quote:update", "quote:delete",
                "user:create", "user:read", "user:update", "user:delete",
                "tenant:read", "tenant:update"
            ]
        )
        
        db.add(admin_user)
        await db.commit()
        
        print(f"[OK] Created tenant '{tenant.name}' with admin user {admin_user.email}")
        
        return tenant
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating tenant: {str(e)}"
        )


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: str,
    current_user: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get tenant by ID (super admin only)
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    stmt = select(Tenant).where(Tenant.id == tenant_id)
    result = await db.execute(stmt)
    tenant = result.scalars().first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant


@router.put("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: str,
    tenant_update: TenantUpdate,
    current_user: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Update tenant (super admin only)
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    stmt = select(Tenant).where(Tenant.id == tenant_id)
    result = await db.execute(stmt)
    tenant = result.scalars().first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Update fields
    if tenant_update.name:
        tenant.name = tenant_update.name
    if tenant_update.status:
        tenant.status = tenant_update.status
    if tenant_update.plan:
        tenant.plan = tenant_update.plan
    if tenant_update.primary_color:
        tenant.primary_color = tenant_update.primary_color
    if tenant_update.secondary_color:
        tenant.secondary_color = tenant_update.secondary_color
    if tenant_update.openai_api_key:
        tenant.openai_api_key = tenant_update.openai_api_key
    if tenant_update.companies_house_api_key:
        tenant.companies_house_api_key = tenant_update.companies_house_api_key
    if tenant_update.google_maps_api_key:
        tenant.google_maps_api_key = tenant_update.google_maps_api_key
    
    await db.commit()
    
    # Invalidate API key cache for this tenant
    from app.core.api_keys import invalidate_api_key_cache
    invalidate_api_key_cache(tenant_id)
    
    await db.refresh(tenant)
    
    return tenant


@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant(
    tenant_id: str,
    current_user: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Soft delete tenant (super admin only)
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    stmt = select(Tenant).where(Tenant.id == tenant_id)
    result = await db.execute(stmt)
    tenant = result.scalars().first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Soft delete by setting status to suspended
    tenant.status = TenantStatus.SUSPENDED
    await db.commit()
    
    return None


# Public tenant signup endpoint (no authentication required)
@router.post("/signup", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def signup_tenant(
    tenant_data: TenantCreate,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Public endpoint for new tenant signup
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    # Check if slug already exists
    stmt = select(Tenant).where(Tenant.slug == tenant_data.slug)
    result = await db.execute(stmt)
    existing_tenant = result.scalars().first()
    if existing_tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Company name already taken. Please choose a different one."
        )
    
    # Check if email already exists
    user_stmt = select(User).where(User.email == tenant_data.admin_email)
    user_result = await db.execute(user_stmt)
    existing_user = user_result.scalars().first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    try:
        # Create tenant with trial status
        tenant = Tenant(
            id=str(uuid.uuid4()),
            name=tenant_data.name,
            slug=tenant_data.slug,
            domain=tenant_data.domain,
            status=TenantStatus.TRIAL,
            primary_color=tenant_data.primary_color,
            secondary_color=tenant_data.secondary_color,
            plan="trial",
            settings={
                "timezone": "Europe/London",
                "currency": "GBP",
                "date_format": "DD/MM/YYYY",
                "trial_ends_at": (datetime.utcnow().isoformat()),
                "features": {
                    "ai_analysis": True,
                    "lead_generation": True,
                    "quoting": True,
                    "companies_house": False,  # Requires API key
                    "google_maps": False,  # Requires API key
                    "multilingual": True
                }
            },
            api_limit_monthly=1000  # Trial limit
        )
        
        db.add(tenant)
        await db.flush()
        
        # Create tenant admin user
        hashed_password = get_password_hash(tenant_data.admin_password)
        
        admin_user = User(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            email=tenant_data.admin_email,
            username=f"{tenant_data.slug}_admin",
            first_name=tenant_data.admin_first_name,
            last_name=tenant_data.admin_last_name,
            hashed_password=hashed_password,
            is_active=True,
            is_verified=False,  # Require email verification
            role=UserRole.TENANT_ADMIN,
            permissions=[
                "customer:create", "customer:read", "customer:update", "customer:delete",
                "lead:create", "lead:read", "lead:update", "lead:delete",
                "quote:create", "quote:read", "quote:update", "quote:delete",
                "user:create", "user:read", "user:update",
                "contact:create", "contact:read", "contact:update", "contact:delete",
                "tenant:read", "tenant:update"
            ],
            preferences={
                "theme": "light",
                "language": "en",
                "notifications": True,
                "email_notifications": True
            }
        )
        
        db.add(admin_user)
        await db.commit()
        
        print(f"[OK] New tenant signed up: {tenant.name} ({tenant.slug})")
        print(f"[OK] Admin user: {admin_user.email}")
        
        return tenant
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating tenant: {str(e)}"
        )
