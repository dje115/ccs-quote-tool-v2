#!/usr/bin/env python3
"""
Supplier Management API Endpoints
Multi-tenant aware supplier and pricing management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_tenant
from app.models.tenant import User, Tenant
from app.services.supplier_service import SupplierService
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
    is_preferred: bool = False


class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    category_id: Optional[str] = None
    website: Optional[str] = None
    pricing_url: Optional[str] = None
    api_key: Optional[str] = None
    notes: Optional[str] = None
    is_preferred: Optional[bool] = None
    is_active: Optional[bool] = None


class SupplierResponse(BaseModel):
    id: str
    tenant_id: str
    category_id: str
    name: str
    website: Optional[str]
    pricing_url: Optional[str]
    notes: Optional[str]
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
    db: Session = Depends(get_db)
):
    """List all supplier categories"""
    try:
        service = SupplierService(db, current_tenant.id)
        categories = service.list_categories()
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
    db: Session = Depends(get_db)
):
    """Create a new supplier category"""
    service = SupplierService(db, current_tenant.id)
    category = service.create_category(
        name=category_data.name,
        description=category_data.description
    )
    return category


@router.get("/categories/{category_id}", response_model=SupplierCategoryResponse)
async def get_category(
    category_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Get a supplier category"""
    service = SupplierService(db, current_tenant.id)
    category = service.get_category(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@router.put("/categories/{category_id}", response_model=SupplierCategoryResponse)
async def update_category(
    category_id: str,
    category_data: SupplierCategoryUpdate,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Update a supplier category"""
    service = SupplierService(db, current_tenant.id)
    category = service.update_category(
        category_id=category_id,
        name=category_data.name,
        description=category_data.description,
        is_active=category_data.is_active
    )
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Delete a supplier category"""
    service = SupplierService(db, current_tenant.id)
    success = service.delete_category(category_id)
    if not success:
        raise HTTPException(status_code=404, detail="Category not found")


# Supplier endpoints
@router.get("/", response_model=List[SupplierResponse])
async def list_suppliers(
    category_id: Optional[str] = Query(None),
    is_preferred: Optional[bool] = Query(None),
    is_active: Optional[bool] = Query(True),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """List suppliers with optional filters"""
    try:
        service = SupplierService(db, current_tenant.id)
        suppliers = service.list_suppliers(
            category_id=category_id,
            is_preferred=is_preferred,
            is_active=is_active
        )
        
        # Convert to response format
        result = []
        for supplier in suppliers:
            # Eager load category relationship
            if supplier.category:
                category_data = supplier.category
            else:
                category_data = None
            
            supplier_response = SupplierResponse(
                id=supplier.id,
                tenant_id=supplier.tenant_id,
                category_id=supplier.category_id,
                name=supplier.name,
                website=supplier.website,
                pricing_url=supplier.pricing_url,
                notes=supplier.notes,
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
                pricing_count=service.get_supplier_pricing_count(supplier.id) if hasattr(service, 'get_supplier_pricing_count') else 0
            )
            result.append(supplier_response)
        
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error fetching suppliers: {str(e)}")


@router.post("/", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED)
async def create_supplier(
    supplier_data: SupplierCreate,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Create a new supplier"""
    try:
        service = SupplierService(db, current_tenant.id)
        supplier = service.create_supplier(
            category_id=supplier_data.category_id,
            name=supplier_data.name,
            website=supplier_data.website,
            pricing_url=supplier_data.pricing_url,
            api_key=supplier_data.api_key,
            notes=supplier_data.notes,
            is_preferred=supplier_data.is_preferred
        )
        if not supplier:
            raise HTTPException(status_code=400, detail="Invalid category or supplier creation failed")
        
        # Eager load category relationship
        db.refresh(supplier)
        category_data = supplier.category if supplier.category else None
        
        # Convert to response format
        return SupplierResponse(
            id=supplier.id,
            tenant_id=supplier.tenant_id,
            category_id=supplier.category_id,
            name=supplier.name,
            website=supplier.website,
            pricing_url=supplier.pricing_url,
            notes=supplier.notes,
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
        raise HTTPException(status_code=500, detail=f"Error creating supplier: {str(e)}")


@router.get("/{supplier_id}", response_model=SupplierResponse)
async def get_supplier(
    supplier_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Get a supplier"""
    service = SupplierService(db, current_tenant.id)
    supplier = service.get_supplier(supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    supplier_dict = {
        **{c.name: getattr(supplier, c.name) for c in supplier.__table__.columns},
        'category': supplier.category,
        'pricing_count': service.get_supplier_pricing_count(supplier.id)
    }
    return supplier_dict


@router.put("/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(
    supplier_id: str,
    supplier_data: SupplierUpdate,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Update a supplier"""
    service = SupplierService(db, current_tenant.id)
    supplier = service.update_supplier(
        supplier_id=supplier_id,
        name=supplier_data.name,
        category_id=supplier_data.category_id,
        website=supplier_data.website,
        pricing_url=supplier_data.pricing_url,
        api_key=supplier_data.api_key,
        notes=supplier_data.notes,
        is_preferred=supplier_data.is_preferred,
        is_active=supplier_data.is_active
    )
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    supplier_dict = {
        **{c.name: getattr(supplier, c.name) for c in supplier.__table__.columns},
        'category': supplier.category,
        'pricing_count': service.get_supplier_pricing_count(supplier.id)
    }
    return supplier_dict


@router.delete("/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_supplier(
    supplier_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Delete a supplier"""
    service = SupplierService(db, current_tenant.id)
    success = service.delete_supplier(supplier_id)
    if not success:
        raise HTTPException(status_code=404, detail="Supplier not found")


# Pricing endpoints
@router.get("/{supplier_id}/pricing/summary")
async def get_supplier_pricing_summary(
    supplier_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Get pricing summary for a supplier"""
    service = SupplierService(db, current_tenant.id)
    supplier = service.get_supplier(supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    pricing_service = SupplierPricingService(db, current_tenant.id)
    summary = pricing_service.get_supplier_pricing_summary()
    
    # Filter to this supplier
    supplier_summary = [s for s in summary if s['supplier_id'] == supplier_id]
    return supplier_summary[0] if supplier_summary else None


@router.post("/{supplier_id}/pricing/refresh", response_model=PricingRefreshResponse)
async def refresh_supplier_pricing(
    supplier_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Refresh pricing for a supplier"""
    service = SupplierService(db, current_tenant.id)
    supplier = service.get_supplier(supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    pricing_service = SupplierPricingService(db, current_tenant.id)
    result = await pricing_service.refresh_all_pricing()
    
    return result


@router.get("/pricing/summary")
async def get_all_pricing_summary(
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Get pricing summary for all suppliers"""
    pricing_service = SupplierPricingService(db, current_tenant.id)
    summary = pricing_service.get_supplier_pricing_summary()
    return summary


@router.post("/pricing/refresh-all", response_model=PricingRefreshResponse)
async def refresh_all_pricing(
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Refresh pricing for all preferred suppliers"""
    pricing_service = SupplierPricingService(db, current_tenant.id)
    result = await pricing_service.refresh_all_pricing()
    
    if not result.get('success'):
        raise HTTPException(
            status_code=500,
            detail=result.get('error', 'Failed to refresh pricing')
        )
    
    return result


@router.get("/pricing/test/{supplier_name}/{product_name}")
async def test_pricing(
    supplier_name: str,
    product_name: str,
    force_refresh: bool = Query(True),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Test pricing lookup for a specific supplier and product"""
    try:
        pricing_service = SupplierPricingService(db, current_tenant.id)
        result = await pricing_service.get_product_price(
            supplier_name=supplier_name,
            product_name=product_name,
            force_refresh=force_refresh
        )
        
        return {
            'success': True,
            'result': result
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error testing pricing: {str(e)}"
        )

