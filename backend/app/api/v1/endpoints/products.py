#!/usr/bin/env python3
"""
Product catalog API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.core.dependencies import get_db, get_current_user
from app.models.tenant import User
from app.models.product import Product
from app.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["Products"])


class ProductCreate(BaseModel):
    name: str
    base_price: float
    category: Optional[str] = None
    subcategory: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    unit: str = "each"
    cost_price: Optional[float] = None
    supplier: Optional[str] = None
    part_number: Optional[str] = None
    is_service: bool = False


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    base_price: Optional[float] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    unit: Optional[str] = None
    cost_price: Optional[float] = None
    supplier: Optional[str] = None
    part_number: Optional[str] = None
    is_active: Optional[bool] = None
    is_service: Optional[bool] = None


class ProductResponse(BaseModel):
    id: str
    code: Optional[str]
    name: str
    description: Optional[str]
    category: Optional[str]
    subcategory: Optional[str]
    unit: str
    base_price: float
    cost_price: Optional[float]
    supplier: Optional[str]
    part_number: Optional[str]
    is_active: bool
    is_service: bool
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


@router.get("/", response_model=List[ProductResponse])
async def list_products(
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    is_service: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List products with filters"""
    try:
        service = ProductService(db, tenant_id=current_user.tenant_id)
        products = service.list_products(
            category=category,
            search=search,
            is_active=is_active,
            is_service=is_service,
            skip=skip,
            limit=limit
        )
        return products
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing products: {str(e)}"
        )


@router.get("/categories", response_model=List[str])
async def get_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all product categories"""
    try:
        service = ProductService(db, tenant_id=current_user.tenant_id)
        categories = service.get_categories()
        return categories
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting categories: {str(e)}"
        )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific product"""
    try:
        service = ProductService(db, tenant_id=current_user.tenant_id)
        product = service.get_product(product_id)
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {product_id} not found"
            )
        
        return product
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting product: {str(e)}"
        )


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new product"""
    try:
        service = ProductService(db, tenant_id=current_user.tenant_id)
        product = service.create_product(
            name=product_data.name,
            base_price=product_data.base_price,
            category=product_data.category,
            subcategory=product_data.subcategory,
            code=product_data.code,
            description=product_data.description,
            unit=product_data.unit,
            cost_price=product_data.cost_price,
            supplier=product_data.supplier,
            part_number=product_data.part_number,
            is_service=product_data.is_service
        )
        
        db.commit()
        db.refresh(product)
        
        return product
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating product: {str(e)}"
        )


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str,
    product_data: ProductUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a product"""
    try:
        service = ProductService(db, tenant_id=current_user.tenant_id)
        
        update_kwargs = {}
        if product_data.name is not None:
            update_kwargs['name'] = product_data.name
        if product_data.base_price is not None:
            update_kwargs['base_price'] = product_data.base_price
        if product_data.category is not None:
            update_kwargs['category'] = product_data.category
        if product_data.subcategory is not None:
            update_kwargs['subcategory'] = product_data.subcategory
        if product_data.code is not None:
            update_kwargs['code'] = product_data.code
        if product_data.description is not None:
            update_kwargs['description'] = product_data.description
        if product_data.unit is not None:
            update_kwargs['unit'] = product_data.unit
        if product_data.cost_price is not None:
            update_kwargs['cost_price'] = product_data.cost_price
        if product_data.supplier is not None:
            update_kwargs['supplier'] = product_data.supplier
        if product_data.part_number is not None:
            update_kwargs['part_number'] = product_data.part_number
        if product_data.is_active is not None:
            update_kwargs['is_active'] = product_data.is_active
        if product_data.is_service is not None:
            update_kwargs['is_service'] = product_data.is_service
        
        product = service.update_product(product_id, **update_kwargs)
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {product_id} not found"
            )
        
        return product
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating product: {str(e)}"
        )


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: str,
    soft_delete: bool = Query(True, description="Soft delete (deactivate) or hard delete"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a product"""
    try:
        service = ProductService(db, tenant_id=current_user.tenant_id)
        success = service.delete_product(product_id, soft_delete=soft_delete)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {product_id} not found"
            )
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting product: {str(e)}"
        )


@router.post("/import-csv")
async def import_products_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Import products from CSV file"""
    try:
        import tempfile
        import os
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        try:
            service = ProductService(db, tenant_id=current_user.tenant_id)
            result = service.import_from_csv(tmp_path)
            
            return result
        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error importing products: {str(e)}"
        )

