#!/usr/bin/env python3
"""
Dynamic Pricing API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from pydantic import BaseModel
from decimal import Decimal
import asyncio

from app.core.database import get_async_db, SessionLocal
from app.core.dependencies import get_current_user, get_current_tenant
from app.models.tenant import User, Tenant
from app.services.dynamic_pricing_service import DynamicPricingService

router = APIRouter(prefix="/dynamic-pricing", tags=["Dynamic Pricing"])


class CalculatePriceRequest(BaseModel):
    base_price: float
    product_name: str
    quantity: int = 1
    customer_id: Optional[str] = None
    currency: str = "GBP"
    apply_rules: bool = True


class SuggestPriceRequest(BaseModel):
    product_name: str
    base_price: float
    competitor_prices: Optional[list] = None


@router.post("/calculate")
async def calculate_dynamic_price(
    request: CalculatePriceRequest,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Calculate dynamic price with all applicable rules (FX, competitor matching, volume discounts, etc.)
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    Note: Wraps sync service calls in executor.
    """
    try:
        def _calculate():
            sync_db = SessionLocal()
            try:
                service = DynamicPricingService(sync_db, current_user.tenant_id)
                return service.calculate_dynamic_price(
                    base_price=Decimal(str(request.base_price)),
                    product_name=request.product_name,
                    quantity=request.quantity,
                    customer_id=request.customer_id,
                    currency=request.currency,
                    apply_rules=request.apply_rules
                )
            finally:
                sync_db.close()
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _calculate)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating dynamic price: {str(e)}"
        )


@router.post("/suggest")
async def suggest_optimal_price(
    request: SuggestPriceRequest,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Use AI to suggest optimal pricing based on market analysis
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    Note: Service method is async, but service uses sync db.
    """
    try:
        sync_db = SessionLocal()
        try:
            service = DynamicPricingService(sync_db, current_user.tenant_id)
            result = await service.suggest_optimal_price(
                product_name=request.product_name,
                base_price=Decimal(str(request.base_price)),
                competitor_prices=request.competitor_prices
            )
        finally:
            sync_db.close()
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating price suggestion: {str(e)}"
        )


@router.get("/competitor-prices/{product_name}")
async def get_competitor_prices(
    product_name: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get competitor prices for a product
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    Note: Wraps sync service calls in executor.
    """
    try:
        def _get_competitors():
            sync_db = SessionLocal()
            try:
                service = DynamicPricingService(sync_db, current_user.tenant_id)
                return service.price_intel.get_competitor_prices(product_name)
            finally:
                sync_db.close()
        
        loop = asyncio.get_event_loop()
        competitors = await loop.run_in_executor(None, _get_competitors)
        return {"competitors": competitors}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting competitor prices: {str(e)}"
        )


@router.get("/price-trends/{product_name}")
async def get_price_trends(
    product_name: str,
    supplier_id: Optional[str] = Query(None),
    days_back: int = Query(90, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get price trends for a product
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    Note: Wraps sync service calls in executor.
    """
    try:
        def _get_trends():
            sync_db = SessionLocal()
            try:
                service = DynamicPricingService(sync_db, current_user.tenant_id)
                return service.price_intel.get_price_trends(
                    product_name=product_name,
                    supplier_id=supplier_id,
                    days_back=days_back
                )
            finally:
                sync_db.close()
        
        loop = asyncio.get_event_loop()
        trends = await loop.run_in_executor(None, _get_trends)
        return trends
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting price trends: {str(e)}"
        )


@router.post("/fx-rates")
async def update_fx_rates(
    rates: dict,
    base_currency: str = "GBP",
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Update FX exchange rates (admin only)
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    Note: Wraps sync service calls in executor.
    """
    try:
        # Check admin permission
        if current_user.role.value not in ['super_admin', 'tenant_admin']:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        def _update_fx():
            sync_db = SessionLocal()
            try:
                service = DynamicPricingService(sync_db, current_user.tenant_id)
                return service.create_fx_rate_config(rates, base_currency)
            finally:
                sync_db.close()
        
        loop = asyncio.get_event_loop()
        config = await loop.run_in_executor(None, _update_fx)
        return {"success": True, "config_id": config.id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating FX rates: {str(e)}"
        )


@router.get("/fx-rates/{from_currency}/{to_currency}")
async def get_fx_rate(
    from_currency: str,
    to_currency: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get FX exchange rate
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    Note: Wraps sync service calls in executor.
    """
    try:
        def _get_fx():
            sync_db = SessionLocal()
            try:
                service = DynamicPricingService(sync_db, current_user.tenant_id)
                return service.get_fx_rate(from_currency, to_currency)
            finally:
                sync_db.close()
        
        loop = asyncio.get_event_loop()
        rate = await loop.run_in_executor(None, _get_fx)
        if rate is None:
            raise HTTPException(status_code=404, detail="FX rate not found")
        return {"from_currency": from_currency, "to_currency": to_currency, "rate": rate}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting FX rate: {str(e)}"
        )

