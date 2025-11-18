#!/usr/bin/env python3
"""
Supplier Management API Endpoints
Multi-tenant aware supplier and pricing management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload, joinedload
from typing import List, Optional
from pydantic import BaseModel
import json

from app.core.database import get_async_db
from app.core.dependencies import get_current_user, get_current_tenant
from app.models.tenant import User, Tenant
from app.models.supplier import Supplier, SupplierCategory, SupplierPricing
from app.services.supplier_pricing_service import SupplierPricingService

router = APIRouter()


# Pydantic models
class SupplierCategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None


class SupplierCategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class SupplierCategoryResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    description: Optional[str]
    is_active: bool
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class SupplierCreate(BaseModel):
    category_id: str
    name: str
    website: Optional[str] = None
    pricing_url: Optional[str] = None
    api_key: Optional[str] = None
    notes: Optional[str] = None
    scraping_config: Optional[dict] = None
    scraping_enabled: bool = True
    scraping_method: str = "generic"
    is_preferred: bool = False


class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    category_id: Optional[str] = None
    website: Optional[str] = None
    pricing_url: Optional[str] = None
    api_key: Optional[str] = None
    notes: Optional[str] = None
    scraping_config: Optional[dict] = None
    scraping_enabled: Optional[bool] = None
    scraping_method: Optional[str] = None
    is_preferred: Optional[bool] = None
    is_active: Optional[bool] = None


class SupplierResponse(BaseModel):
    id: str
    tenant_id: str
    category_id: str
    name: str
    website: Optional[str]
    pricing_url: Optional[str]
    api_key: Optional[str] = None
    notes: Optional[str]
    scraping_config: Optional[dict] = None
    scraping_enabled: bool = True
    scraping_method: str = "generic"
    is_preferred: bool
    is_active: bool
    created_at: str
    updated_at: str
    category: Optional[SupplierCategoryResponse] = None
    pricing_count: Optional[int] = None
    
    class Config:
        from_attributes = True


class PricingRefreshResponse(BaseModel):
    success: bool
    refreshed_count: int
    message: str


# Category endpoints
@router.get("/categories", response_model=List[SupplierCategoryResponse])
async def list_categories(
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    List all supplier categories
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        stmt = select(SupplierCategory).where(
            and_(
                SupplierCategory.tenant_id == current_tenant.id,
                SupplierCategory.is_active == True
            )
        )
        result = await db.execute(stmt)
        categories = result.scalars().all()
        
        # Convert to response format
        return [
            SupplierCategoryResponse(
                id=cat.id,
                tenant_id=cat.tenant_id,
                name=cat.name,
                description=cat.description,
                is_active=cat.is_active,
                created_at=cat.created_at.isoformat() if cat.created_at else "",
                updated_at=cat.updated_at.isoformat() if cat.updated_at else ""
            )
            for cat in categories
        ]
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error fetching categories: {str(e)}")


@router.post("/categories", response_model=SupplierCategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: SupplierCategoryCreate,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Create a new supplier category
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    import uuid
    category = SupplierCategory(
        id=str(uuid.uuid4()),
        tenant_id=current_tenant.id,
        name=category_data.name,
        description=category_data.description
    )
    db.add(category)
    await db.commit()
    await db.refresh(category)
    
    return SupplierCategoryResponse(
        id=category.id,
        tenant_id=category.tenant_id,
        name=category.name,
        description=category.description,
        is_active=category.is_active,
        created_at=category.created_at.isoformat() if category.created_at else "",
        updated_at=category.updated_at.isoformat() if category.updated_at else ""
    )


@router.get("/categories/{category_id}", response_model=SupplierCategoryResponse)
async def get_category(
    category_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get a supplier category
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    stmt = select(SupplierCategory).where(
        and_(
            SupplierCategory.id == category_id,
            SupplierCategory.tenant_id == current_tenant.id
        )
    )
    result = await db.execute(stmt)
    category = result.scalars().first()
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return SupplierCategoryResponse(
        id=category.id,
        tenant_id=category.tenant_id,
        name=category.name,
        description=category.description,
        is_active=category.is_active,
        created_at=category.created_at.isoformat() if category.created_at else "",
        updated_at=category.updated_at.isoformat() if category.updated_at else ""
    )


@router.put("/categories/{category_id}", response_model=SupplierCategoryResponse)
async def update_category(
    category_id: str,
    category_data: SupplierCategoryUpdate,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Update a supplier category
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    stmt = select(SupplierCategory).where(
        and_(
            SupplierCategory.id == category_id,
            SupplierCategory.tenant_id == current_tenant.id
        )
    )
    result = await db.execute(stmt)
    category = result.scalars().first()
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    if category_data.name is not None:
        category.name = category_data.name
    if category_data.description is not None:
        category.description = category_data.description
    if category_data.is_active is not None:
        category.is_active = category_data.is_active
    
    await db.commit()
    await db.refresh(category)
    
    return SupplierCategoryResponse(
        id=category.id,
        tenant_id=category.tenant_id,
        name=category.name,
        description=category.description,
        is_active=category.is_active,
        created_at=category.created_at.isoformat() if category.created_at else "",
        updated_at=category.updated_at.isoformat() if category.updated_at else ""
    )


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Delete a supplier category (soft delete)
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    stmt = select(SupplierCategory).where(
        and_(
            SupplierCategory.id == category_id,
            SupplierCategory.tenant_id == current_tenant.id
        )
    )
    result = await db.execute(stmt)
    category = result.scalars().first()
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Soft delete
    category.is_active = False
    await db.commit()


# Supplier endpoints
@router.get("/", response_model=List[SupplierResponse])
async def list_suppliers(
    category_id: Optional[str] = Query(None),
    is_preferred: Optional[bool] = Query(None),
    is_active: Optional[bool] = Query(True),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    List suppliers with optional filters
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        from sqlalchemy import func as sql_func
        
        # Build query with eager loading of category
        stmt = select(Supplier).options(joinedload(Supplier.category)).where(
            Supplier.tenant_id == current_tenant.id
        )
        
        if category_id:
            stmt = stmt.where(Supplier.category_id == category_id)
        if is_preferred is not None:
            stmt = stmt.where(Supplier.is_preferred == is_preferred)
        if is_active is not None:
            stmt = stmt.where(Supplier.is_active == is_active)
        
        result = await db.execute(stmt)
        suppliers = result.unique().scalars().all()
        
        # Get pricing counts for all suppliers
        supplier_ids = [s.id for s in suppliers]
        pricing_counts = {}
        if supplier_ids:
            from sqlalchemy import func as sql_func
            pricing_stmt = select(
                SupplierPricing.supplier_id,
                sql_func.count(SupplierPricing.id).label('count')
            ).where(
                SupplierPricing.supplier_id.in_(supplier_ids),
                SupplierPricing.is_active == True
            ).group_by(SupplierPricing.supplier_id)
            pricing_result = await db.execute(pricing_stmt)
            pricing_counts = {row.supplier_id: row.count for row in pricing_result.all()}
        
        # Convert to response format
        result_list = []
        for supplier in suppliers:
            category_data = supplier.category if supplier.category else None
            
            # Parse scraping_config if it's a string
            scraping_config = None
            if supplier.scraping_config:
                if isinstance(supplier.scraping_config, str):
                    try:
                        scraping_config = json.loads(supplier.scraping_config)
                    except:
                        scraping_config = {}
                else:
                    scraping_config = supplier.scraping_config
            
            supplier_response = SupplierResponse(
                id=supplier.id,
                tenant_id=supplier.tenant_id,
                category_id=supplier.category_id,
                name=supplier.name,
                website=supplier.website,
                pricing_url=supplier.pricing_url,
                api_key=supplier.api_key,
                notes=supplier.notes,
                scraping_config=scraping_config,
                scraping_enabled=supplier.scraping_enabled if hasattr(supplier, 'scraping_enabled') else True,
                scraping_method=supplier.scraping_method if hasattr(supplier, 'scraping_method') else "generic",
                is_preferred=supplier.is_preferred,
                is_active=supplier.is_active,
                created_at=supplier.created_at.isoformat() if supplier.created_at else "",
                updated_at=supplier.updated_at.isoformat() if supplier.updated_at else "",
                category=SupplierCategoryResponse(
                    id=category_data.id,
                    tenant_id=category_data.tenant_id,
                    name=category_data.name,
                    description=category_data.description,
                    is_active=category_data.is_active,
                    created_at=category_data.created_at.isoformat() if category_data.created_at else "",
                    updated_at=category_data.updated_at.isoformat() if category_data.updated_at else ""
                ) if category_data else None,
                pricing_count=pricing_counts.get(supplier.id, 0)
            )
            result_list.append(supplier_response)
        
        return result_list
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error fetching suppliers: {str(e)}")


@router.post("/", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED)
async def create_supplier(
    supplier_data: SupplierCreate,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Create a new supplier
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        import uuid
        
        # Verify category exists and belongs to tenant
        category_stmt = select(SupplierCategory).where(
            and_(
                SupplierCategory.id == supplier_data.category_id,
                SupplierCategory.tenant_id == current_tenant.id,
                SupplierCategory.is_active == True
            )
        )
        category_result = await db.execute(category_stmt)
        category = category_result.scalars().first()
        
        if not category:
            raise HTTPException(status_code=400, detail="Invalid category or category not found")
        
        # Prepare scraping_config
        scraping_config_value = None
        if supplier_data.scraping_config:
            if isinstance(supplier_data.scraping_config, dict):
                scraping_config_value = supplier_data.scraping_config
            else:
                scraping_config_value = supplier_data.scraping_config
        
        # Create supplier
        supplier = Supplier(
            id=str(uuid.uuid4()),
            tenant_id=current_tenant.id,
            category_id=supplier_data.category_id,
            name=supplier_data.name,
            website=supplier_data.website,
            pricing_url=supplier_data.pricing_url,
            api_key=supplier_data.api_key,
            notes=supplier_data.notes,
            scraping_config=scraping_config_value,
            scraping_enabled=supplier_data.scraping_enabled,
            scraping_method=supplier_data.scraping_method,
            is_preferred=supplier_data.is_preferred
        )
        
        db.add(supplier)
        await db.commit()
        await db.refresh(supplier)
        
        # Reload with category relationship
        supplier_stmt = select(Supplier).options(joinedload(Supplier.category)).where(
            Supplier.id == supplier.id
        )
        supplier_result = await db.execute(supplier_stmt)
        supplier = supplier_result.unique().scalars().first()
        
        category_data = supplier.category if supplier.category else None
        
        # Parse scraping_config
        scraping_config = None
        if supplier.scraping_config:
            if isinstance(supplier.scraping_config, str):
                try:
                    scraping_config = json.loads(supplier.scraping_config)
                except:
                    scraping_config = {}
            else:
                scraping_config = supplier.scraping_config
        
        return SupplierResponse(
            id=supplier.id,
            tenant_id=supplier.tenant_id,
            category_id=supplier.category_id,
            name=supplier.name,
            website=supplier.website,
            pricing_url=supplier.pricing_url,
            api_key=supplier.api_key,
            notes=supplier.notes,
            scraping_config=scraping_config,
            scraping_enabled=supplier.scraping_enabled if hasattr(supplier, 'scraping_enabled') else True,
            scraping_method=supplier.scraping_method if hasattr(supplier, 'scraping_method') else "generic",
            is_preferred=supplier.is_preferred,
            is_active=supplier.is_active,
            created_at=supplier.created_at.isoformat() if supplier.created_at else "",
            updated_at=supplier.updated_at.isoformat() if supplier.updated_at else "",
            category=SupplierCategoryResponse(
                id=category_data.id,
                tenant_id=category_data.tenant_id,
                name=category_data.name,
                description=category_data.description,
                is_active=category_data.is_active,
                created_at=category_data.created_at.isoformat() if category_data.created_at else "",
                updated_at=category_data.updated_at.isoformat() if category_data.updated_at else ""
            ) if category_data else None,
            pricing_count=0
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating supplier: {str(e)}")


@router.get("/{supplier_id}", response_model=SupplierResponse)
async def get_supplier(
    supplier_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get a supplier
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    from sqlalchemy import func as sql_func
    
    stmt = select(Supplier).options(joinedload(Supplier.category)).where(
        and_(
            Supplier.id == supplier_id,
            Supplier.tenant_id == current_tenant.id
        )
    )
    result = await db.execute(stmt)
    supplier = result.unique().scalars().first()
    
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    # Get pricing count
    pricing_count_stmt = select(sql_func.count(SupplierPricing.id)).where(
        and_(
            SupplierPricing.supplier_id == supplier_id,
            SupplierPricing.is_active == True
        )
    )
    pricing_count_result = await db.execute(pricing_count_stmt)
    pricing_count = pricing_count_result.scalar() or 0
    
    # Parse scraping_config if it's a string
    scraping_config = None
    if supplier.scraping_config:
        if isinstance(supplier.scraping_config, str):
            try:
                scraping_config = json.loads(supplier.scraping_config)
            except:
                scraping_config = {}
        else:
            scraping_config = supplier.scraping_config
    
    category_data = supplier.category if supplier.category else None
    
    return SupplierResponse(
        id=supplier.id,
        tenant_id=supplier.tenant_id,
        category_id=supplier.category_id,
        name=supplier.name,
        website=supplier.website,
        pricing_url=supplier.pricing_url,
        api_key=supplier.api_key,
        notes=supplier.notes,
        scraping_config=scraping_config,
        scraping_enabled=supplier.scraping_enabled if hasattr(supplier, 'scraping_enabled') else True,
        scraping_method=supplier.scraping_method if hasattr(supplier, 'scraping_method') else "generic",
        is_preferred=supplier.is_preferred,
        is_active=supplier.is_active,
        created_at=supplier.created_at.isoformat() if supplier.created_at else "",
        updated_at=supplier.updated_at.isoformat() if supplier.updated_at else "",
        category=SupplierCategoryResponse(
            id=category_data.id,
            tenant_id=category_data.tenant_id,
            name=category_data.name,
            description=category_data.description,
            is_active=category_data.is_active,
            created_at=category_data.created_at.isoformat() if category_data.created_at else "",
            updated_at=category_data.updated_at.isoformat() if category_data.updated_at else ""
        ) if category_data else None,
        pricing_count=pricing_count
    )


@router.put("/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(
    supplier_id: str,
    supplier_data: SupplierUpdate,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Update a supplier
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    from sqlalchemy import func as sql_func
    
    stmt = select(Supplier).options(joinedload(Supplier.category)).where(
        and_(
            Supplier.id == supplier_id,
            Supplier.tenant_id == current_tenant.id
        )
    )
    result = await db.execute(stmt)
    supplier = result.unique().scalars().first()
    
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    # Update fields
    if supplier_data.name is not None:
        supplier.name = supplier_data.name
    if supplier_data.category_id is not None:
        # Verify new category exists and belongs to tenant
        category_stmt = select(SupplierCategory).where(
            and_(
                SupplierCategory.id == supplier_data.category_id,
                SupplierCategory.tenant_id == current_tenant.id
            )
        )
        category_result = await db.execute(category_stmt)
        if not category_result.scalars().first():
            raise HTTPException(status_code=400, detail="Invalid category")
        supplier.category_id = supplier_data.category_id
    if supplier_data.website is not None:
        supplier.website = supplier_data.website
    if supplier_data.pricing_url is not None:
        supplier.pricing_url = supplier_data.pricing_url
    if supplier_data.api_key is not None:
        supplier.api_key = supplier_data.api_key
    if supplier_data.notes is not None:
        supplier.notes = supplier_data.notes
    if supplier_data.scraping_config is not None:
        if isinstance(supplier_data.scraping_config, dict):
            supplier.scraping_config = supplier_data.scraping_config
        else:
            supplier.scraping_config = supplier_data.scraping_config
    if supplier_data.scraping_enabled is not None:
        supplier.scraping_enabled = supplier_data.scraping_enabled
    if supplier_data.scraping_method is not None:
        supplier.scraping_method = supplier_data.scraping_method
    if supplier_data.is_preferred is not None:
        supplier.is_preferred = supplier_data.is_preferred
    if supplier_data.is_active is not None:
        supplier.is_active = supplier_data.is_active
    
    await db.commit()
    await db.refresh(supplier)
    
    # Reload with category relationship
    supplier_stmt = select(Supplier).options(joinedload(Supplier.category)).where(
        Supplier.id == supplier.id
    )
    supplier_result = await db.execute(supplier_stmt)
    supplier = supplier_result.unique().scalars().first()
    
    # Get pricing count
    pricing_count_stmt = select(sql_func.count(SupplierPricing.id)).where(
        and_(
            SupplierPricing.supplier_id == supplier_id,
            SupplierPricing.is_active == True
        )
    )
    pricing_count_result = await db.execute(pricing_count_stmt)
    pricing_count = pricing_count_result.scalar() or 0
    
    # Parse scraping_config
    scraping_config = None
    if supplier.scraping_config:
        if isinstance(supplier.scraping_config, str):
            try:
                scraping_config = json.loads(supplier.scraping_config)
            except:
                scraping_config = {}
        else:
            scraping_config = supplier.scraping_config
    
    category_data = supplier.category if supplier.category else None
    
    return SupplierResponse(
        id=supplier.id,
        tenant_id=supplier.tenant_id,
        category_id=supplier.category_id,
        name=supplier.name,
        website=supplier.website,
        pricing_url=supplier.pricing_url,
        api_key=supplier.api_key,
        notes=supplier.notes,
        scraping_config=scraping_config,
        scraping_enabled=supplier.scraping_enabled if hasattr(supplier, 'scraping_enabled') else True,
        scraping_method=supplier.scraping_method if hasattr(supplier, 'scraping_method') else "generic",
        is_preferred=supplier.is_preferred,
        is_active=supplier.is_active,
        created_at=supplier.created_at.isoformat() if supplier.created_at else "",
        updated_at=supplier.updated_at.isoformat() if supplier.updated_at else "",
        category=SupplierCategoryResponse(
            id=category_data.id,
            tenant_id=category_data.tenant_id,
            name=category_data.name,
            description=category_data.description,
            is_active=category_data.is_active,
            created_at=category_data.created_at.isoformat() if category_data.created_at else "",
            updated_at=category_data.updated_at.isoformat() if category_data.updated_at else ""
        ) if category_data else None,
        pricing_count=pricing_count
    )


@router.delete("/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_supplier(
    supplier_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Delete a supplier (soft delete)
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    stmt = select(Supplier).where(
        and_(
            Supplier.id == supplier_id,
            Supplier.tenant_id == current_tenant.id
        )
    )
    result = await db.execute(stmt)
    supplier = result.scalars().first()
    
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    # Soft delete
    supplier.is_active = False
    await db.commit()


# Pricing endpoints
@router.get("/{supplier_id}/pricing/summary")
async def get_supplier_pricing_summary(
    supplier_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get pricing summary for a supplier
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    Note: Wraps sync SupplierPricingService calls in executor.
    """
    import asyncio
    from app.core.database import SessionLocal
    
    # Verify supplier exists
    stmt = select(Supplier).where(
        and_(
            Supplier.id == supplier_id,
            Supplier.tenant_id == current_tenant.id
        )
    )
    result = await db.execute(stmt)
    supplier = result.scalars().first()
    
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    # Wrap sync service call in executor
    def _get_summary():
        sync_db = SessionLocal()
        try:
            pricing_service = SupplierPricingService(sync_db, current_tenant.id)
            return pricing_service.get_supplier_pricing_summary()
        finally:
            sync_db.close()
    
    loop = asyncio.get_event_loop()
    summary = await loop.run_in_executor(None, _get_summary)
    
    # Filter to this supplier
    supplier_summary = [s for s in summary if s['supplier_id'] == supplier_id]
    return supplier_summary[0] if supplier_summary else None


@router.post("/{supplier_id}/pricing/refresh", response_model=PricingRefreshResponse)
async def refresh_supplier_pricing(
    supplier_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Refresh pricing for a supplier
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    # Verify supplier exists
    stmt = select(Supplier).where(
        and_(
            Supplier.id == supplier_id,
            Supplier.tenant_id == current_tenant.id
        )
    )
    result = await db.execute(stmt)
    supplier = result.scalars().first()
    
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    # SupplierPricingService.refresh_all_pricing is async, but service uses sync session
    # We'll need to create a sync session for the service
    from app.core.database import SessionLocal
    sync_db = SessionLocal()
    try:
        pricing_service = SupplierPricingService(sync_db, current_tenant.id)
        result = await pricing_service.refresh_all_pricing()
        return result
    finally:
        sync_db.close()


@router.get("/pricing/summary")
async def get_all_pricing_summary(
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get pricing summary for all suppliers
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    Note: Wraps sync SupplierPricingService calls in executor.
    """
    import asyncio
    from app.core.database import SessionLocal
    
    def _get_summary():
        sync_db = SessionLocal()
        try:
            pricing_service = SupplierPricingService(sync_db, current_tenant.id)
            return pricing_service.get_supplier_pricing_summary()
        finally:
            sync_db.close()
    
    loop = asyncio.get_event_loop()
    summary = await loop.run_in_executor(None, _get_summary)
    return summary


@router.post("/pricing/refresh-all", response_model=PricingRefreshResponse)
async def refresh_all_pricing(
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Refresh pricing for all preferred suppliers
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    from app.core.database import SessionLocal
    
    sync_db = SessionLocal()
    try:
        pricing_service = SupplierPricingService(sync_db, current_tenant.id)
        result = await pricing_service.refresh_all_pricing()
        
        if not result.get('success'):
            raise HTTPException(
                status_code=500,
                detail=result.get('error', 'Failed to refresh pricing')
            )
        
        return result
    finally:
        sync_db.close()


@router.get("/pricing/test/{supplier_name}/{product_name}")
async def test_pricing(
    supplier_name: str,
    product_name: str,
    force_refresh: bool = Query(True),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Test pricing lookup for a specific supplier and product
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        from app.core.database import SessionLocal
        
        sync_db = SessionLocal()
        try:
            pricing_service = SupplierPricingService(sync_db, current_tenant.id)
            result = await pricing_service.get_product_price(
                supplier_name=supplier_name,
                product_name=product_name,
                force_refresh=force_refresh
            )
            
            return {
                'success': True,
                'result': result
            }
        finally:
            sync_db.close()
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error testing pricing: {str(e)}"
        )


@router.get("/{supplier_id}/products")
async def get_supplier_products(
    supplier_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get products from a supplier (from products table and supplier_pricing table)
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        from app.models.product import Product
        
        # Get supplier
        supplier_stmt = select(Supplier).where(
            and_(
                Supplier.id == supplier_id,
                Supplier.tenant_id == current_tenant.id
            )
        )
        supplier_result = await db.execute(supplier_stmt)
        supplier = supplier_result.scalars().first()
        
        if not supplier:
            raise HTTPException(status_code=404, detail="Supplier not found")
        
        # Get products linked to this supplier
        products_stmt = select(Product).where(
            and_(
                Product.supplier_id == supplier_id,
                Product.tenant_id == current_tenant.id,
                Product.is_active == True
            )
        )
        products_result = await db.execute(products_stmt)
        products = products_result.scalars().all()
        
        # Get cached pricing for this supplier
        pricing_stmt = select(SupplierPricing).where(
            and_(
                SupplierPricing.supplier_id == supplier_id,
                SupplierPricing.is_active == True
            )
        )
        pricing_result = await db.execute(pricing_stmt)
        cached_pricing = pricing_result.scalars().all()
        
        # Combine products and pricing
        result = []
        
        # Add products from products table
        for product in products:
            result.append({
                'id': product.id,
                'name': product.name,
                'code': product.code,
                'description': product.description,
                'category': product.category,
                'base_price': float(product.base_price) if product.base_price else None,
                'unit': product.unit,
                'part_number': product.part_number,
                'source': 'products_table'
            })
        
        # Add products from cached pricing (if not already in result)
        existing_names = {p['name'].lower() for p in result}
        for pricing in cached_pricing:
            if pricing.product_name.lower() not in existing_names:
                result.append({
                    'id': pricing.id,
                    'name': pricing.product_name,
                    'code': pricing.product_code,
                    'description': None,
                    'category': None,
                    'base_price': float(pricing.price) if pricing.price else None,
                    'unit': 'each',
                    'part_number': pricing.product_code,
                    'source': 'cached_pricing',
                    'last_updated': pricing.last_updated.isoformat() if pricing.last_updated else None
                })
        
        return {
            'supplier': {
                'id': supplier.id,
                'name': supplier.name,
                'website': supplier.website
            },
            'products': result,
            'count': len(result)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting supplier products: {str(e)}"
        )

