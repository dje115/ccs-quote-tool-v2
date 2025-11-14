#!/usr/bin/env python3
"""
Product Search API Endpoints
AI-powered product search
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_tenant
from app.core.api_keys import get_api_keys
from app.models.tenant import User, Tenant
from app.services.product_search_service import ProductSearchService

router = APIRouter()


class ProductSearchRequest(BaseModel):
    query: str
    category: Optional[str] = None


class ProductSearchResponse(BaseModel):
    success: bool
    products: List[dict]
    query: str
    category: Optional[str] = None


@router.post("/search", response_model=ProductSearchResponse)
async def search_products(
    request: ProductSearchRequest,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Search for products using AI"""
    try:
        api_keys = get_api_keys(db, current_tenant)
        if not api_keys.openai:
            raise HTTPException(
                status_code=400,
                detail="OpenAI API key not configured"
            )
        
        search_service = ProductSearchService(
            db=db,
            tenant_id=current_tenant.id,
            openai_api_key=api_keys.openai
        )
        
        products = await search_service.search_products(
            query=request.query,
            category=request.category
        )
        
        return {
            'success': True,
            'products': products,
            'query': request.query,
            'category': request.category
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error searching products: {str(e)}"
        )


@router.get("/search", response_model=ProductSearchResponse)
async def search_products_get(
    query: str = Query(..., description="Search query"),
    category: Optional[str] = Query(None, description="Product category"),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Search for products using AI (GET endpoint)"""
    try:
        api_keys = get_api_keys(db, current_tenant)
        if not api_keys.openai:
            raise HTTPException(
                status_code=400,
                detail="OpenAI API key not configured"
            )
        
        search_service = ProductSearchService(
            db=db,
            tenant_id=current_tenant.id,
            openai_api_key=api_keys.openai
        )
        
        products = await search_service.search_products(
            query=query,
            category=category
        )
        
        return {
            'success': True,
            'products': products,
            'query': query,
            'category': category
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error searching products: {str(e)}"
        )


