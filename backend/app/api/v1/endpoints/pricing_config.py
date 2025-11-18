"""
Pricing Configuration API endpoints
Manage tenant-specific pricing: day rates, bundles, managed services
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal
import asyncio

from app.core.database import get_async_db, SessionLocal
from app.core.dependencies import get_current_user
from app.models.tenant import User, UserRole
from app.models.pricing_config import TenantPricingConfig, PricingBundleItem, PricingConfigType
from app.services.pricing_config_service import PricingConfigService

router = APIRouter()


class DayRateCreate(BaseModel):
    """Request model for creating day rate"""
    name: str
    base_rate: Decimal
    engineers: int = Field(default=2, ge=1, le=10)
    hours_per_day: int = Field(default=8, ge=1, le=24)
    includes_travel: bool = False
    description: Optional[str] = None
    code: Optional[str] = None
    priority: int = Field(default=0, ge=0)
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None


class BundleItemCreate(BaseModel):
    """Request model for bundle item"""
    type: str  # "product", "service", "day_rate", "custom"
    item_id: Optional[str] = None
    name: str
    code: Optional[str] = None
    quantity: Decimal = Field(default=1, gt=0)
    unit_price: Optional[Decimal] = None
    bundle_price: Optional[Decimal] = None
    data: Optional[dict] = None


class BundleCreate(BaseModel):
    """Request model for creating bundle"""
    name: str
    bundle_price: Decimal
    items: List[BundleItemCreate]
    description: Optional[str] = None
    code: Optional[str] = None
    discount_percentage: Optional[float] = Field(default=None, ge=0, le=100)
    priority: int = Field(default=0, ge=0)
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None


class PricingConfigResponse(BaseModel):
    """Response model for pricing configuration"""
    id: str
    config_type: str
    name: str
    description: Optional[str]
    code: Optional[str]
    base_rate: Optional[float]
    unit: Optional[str]
    config_data: Optional[dict]
    is_active: bool
    priority: int
    valid_from: Optional[datetime]
    valid_until: Optional[datetime]
    version: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class BundleItemResponse(BaseModel):
    """Response model for bundle item"""
    id: str
    item_type: str
    item_id: Optional[str]
    item_name: str
    item_code: Optional[str]
    quantity: float
    unit_price: Optional[float]
    bundle_price: Optional[float]
    display_order: int
    
    class Config:
        from_attributes = True


@router.post("/day-rates", response_model=PricingConfigResponse)
async def create_day_rate(
    data: DayRateCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Create a day rate configuration
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    Note: Wraps sync service calls in executor.
    """
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.TENANT_ADMIN]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    def _create_day_rate():
        sync_db = SessionLocal()
        try:
            service = PricingConfigService(sync_db, current_user.tenant_id)
            return service.create_day_rate(
                name=data.name,
                base_rate=data.base_rate,
                engineers=data.engineers,
                hours_per_day=data.hours_per_day,
                includes_travel=data.includes_travel,
                description=data.description,
                code=data.code,
                priority=data.priority,
                valid_from=data.valid_from,
                valid_until=data.valid_until
            )
        finally:
            sync_db.close()
    
    loop = asyncio.get_event_loop()
    config = await loop.run_in_executor(None, _create_day_rate)
    return config


@router.post("/bundles", response_model=PricingConfigResponse)
async def create_bundle(
    data: BundleCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Create a bundle configuration
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    Note: Wraps sync service calls in executor.
    """
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.TENANT_ADMIN]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Convert bundle items
    items = []
    for item in data.items:
        items.append({
            "type": item.type,
            "item_id": item.item_id,
            "name": item.name,
            "code": item.code,
            "quantity": float(item.quantity),
            "unit_price": float(item.unit_price) if item.unit_price else None,
            "bundle_price": float(item.bundle_price) if item.bundle_price else None,
            "data": item.data
        })
    
    def _create_bundle():
        sync_db = SessionLocal()
        try:
            service = PricingConfigService(sync_db, current_user.tenant_id)
            return service.create_bundle(
                name=data.name,
                bundle_price=data.bundle_price,
                items=items,
                description=data.description,
                code=data.code,
                discount_percentage=data.discount_percentage,
                priority=data.priority,
                valid_from=data.valid_from,
                valid_until=data.valid_until
            )
        finally:
            sync_db.close()
    
    loop = asyncio.get_event_loop()
    config = await loop.run_in_executor(None, _create_bundle)
    return config


@router.get("/", response_model=List[PricingConfigResponse])
async def list_configs(
    config_type: Optional[str] = Query(None, description="Filter by config type"),
    include_inactive: bool = Query(False, description="Include inactive configs"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    List pricing configurations
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    Note: Wraps sync service calls in executor.
    """
    def _list_configs():
        sync_db = SessionLocal()
        try:
            service = PricingConfigService(sync_db, current_user.tenant_id)
            return service.list_configs(config_type=config_type, include_inactive=include_inactive)
        finally:
            sync_db.close()
    
    loop = asyncio.get_event_loop()
    configs = await loop.run_in_executor(None, _list_configs)
    return configs


@router.get("/day-rates/active", response_model=PricingConfigResponse)
async def get_active_day_rate(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get the active day rate configuration
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    Note: Wraps sync service calls in executor.
    """
    def _get_active_day_rate():
        sync_db = SessionLocal()
        try:
            service = PricingConfigService(sync_db, current_user.tenant_id)
            return service.get_active_day_rate()
        finally:
            sync_db.close()
    
    loop = asyncio.get_event_loop()
    config = await loop.run_in_executor(None, _get_active_day_rate)
    
    if not config:
        raise HTTPException(status_code=404, detail="No active day rate configuration found")
    
    return config


@router.get("/{config_id}", response_model=PricingConfigResponse)
async def get_config(
    config_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get a specific pricing configuration
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    Note: Wraps sync service calls in executor.
    """
    def _get_config():
        sync_db = SessionLocal()
        try:
            service = PricingConfigService(sync_db, current_user.tenant_id)
            return service.get_config(config_id)
        finally:
            sync_db.close()
    
    loop = asyncio.get_event_loop()
    config = await loop.run_in_executor(None, _get_config)
    
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    
    return config


@router.get("/bundles/{bundle_id}/items", response_model=List[BundleItemResponse])
async def get_bundle_items(
    bundle_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get items for a bundle configuration
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    Note: Wraps sync service calls in executor.
    """
    def _get_bundle_items():
        sync_db = SessionLocal()
        try:
            service = PricingConfigService(sync_db, current_user.tenant_id)
            # Verify bundle exists and belongs to tenant
            config = service.get_config(bundle_id)
            if not config:
                raise HTTPException(status_code=404, detail="Bundle not found")
            
            if config.config_type != PricingConfigType.BUNDLE.value:
                raise HTTPException(status_code=400, detail="Configuration is not a bundle")
            
            return service.get_bundle_items(bundle_id)
        finally:
            sync_db.close()
    
    loop = asyncio.get_event_loop()
    items = await loop.run_in_executor(None, _get_bundle_items)
    return items


@router.put("/{config_id}", response_model=PricingConfigResponse)
async def update_config(
    config_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    base_rate: Optional[Decimal] = None,
    is_active: Optional[bool] = None,
    priority: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Update a pricing configuration
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    Note: Wraps sync service calls in executor.
    """
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.TENANT_ADMIN]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    def _update_config():
        sync_db = SessionLocal()
        try:
            service = PricingConfigService(sync_db, current_user.tenant_id)
            return service.update_config(
                config_id=config_id,
                name=name,
                description=description,
                base_rate=base_rate,
                is_active=is_active,
                priority=priority
            )
        finally:
            sync_db.close()
    
    loop = asyncio.get_event_loop()
    config = await loop.run_in_executor(None, _update_config)
    
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    
    return config


@router.delete("/{config_id}")
async def delete_config(
    config_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Delete a pricing configuration
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    Note: Wraps sync service calls in executor.
    """
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.TENANT_ADMIN]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    def _delete_config():
        sync_db = SessionLocal()
        try:
            service = PricingConfigService(sync_db, current_user.tenant_id)
            return service.delete_config(config_id)
        finally:
            sync_db.close()
    
    loop = asyncio.get_event_loop()
    success = await loop.run_in_executor(None, _delete_config)
    
    if not success:
        raise HTTPException(status_code=404, detail="Configuration not found")
    
    return {"success": True, "message": "Configuration deleted"}



