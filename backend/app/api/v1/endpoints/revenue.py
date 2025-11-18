#!/usr/bin/env python3
"""
Revenue Tracking API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime
import asyncio

from app.core.database import get_async_db, SessionLocal
from app.core.dependencies import get_current_user, get_current_tenant
from app.models.tenant import User, Tenant
from app.services.revenue_tracking_service import RevenueTrackingService

router = APIRouter(prefix="/revenue", tags=["Revenue"])


@router.get("/recurring")
async def get_recurring_revenue(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get recurring revenue from support contracts
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    Note: Wraps sync service calls in executor.
    """
    try:
        def _get_revenue():
            sync_db = SessionLocal()
            try:
                service = RevenueTrackingService(sync_db, current_user.tenant_id)
                return service.get_recurring_revenue(start_date, end_date)
            finally:
                sync_db.close()
        
        loop = asyncio.get_event_loop()
        revenue = await loop.run_in_executor(None, _get_revenue)
        return revenue
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting recurring revenue: {str(e)}"
        )


@router.get("/forecast")
async def get_revenue_forecast(
    months_ahead: int = Query(12, ge=1, le=24),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get revenue forecast for the next N months
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    Note: Wraps sync service calls in executor.
    """
    try:
        def _get_forecast():
            sync_db = SessionLocal()
            try:
                service = RevenueTrackingService(sync_db, current_user.tenant_id)
                return service.get_revenue_forecast(months_ahead)
            finally:
                sync_db.close()
        
        loop = asyncio.get_event_loop()
        forecast = await loop.run_in_executor(None, _get_forecast)
        return forecast
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating revenue forecast: {str(e)}"
        )


@router.get("/renewals")
async def get_contract_renewal_revenue(
    months_ahead: int = Query(12, ge=1, le=24),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get revenue from contracts renewing in the next N months
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    Note: Wraps sync service calls in executor.
    """
    try:
        def _get_renewals():
            sync_db = SessionLocal()
            try:
                service = RevenueTrackingService(sync_db, current_user.tenant_id)
                return service.get_contract_renewal_revenue(months_ahead)
            finally:
                sync_db.close()
        
        loop = asyncio.get_event_loop()
        renewals = await loop.run_in_executor(None, _get_renewals)
        return renewals
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting renewal revenue: {str(e)}"
        )


@router.get("/customers/{customer_id}")
async def get_customer_revenue_summary(
    customer_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get revenue summary for a specific customer
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    Note: Wraps sync service calls in executor.
    """
    try:
        def _get_summary():
            sync_db = SessionLocal()
            try:
                service = RevenueTrackingService(sync_db, current_user.tenant_id)
                return service.get_customer_revenue_summary(customer_id)
            finally:
                sync_db.close()
        
        loop = asyncio.get_event_loop()
        summary = await loop.run_in_executor(None, _get_summary)
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting customer revenue summary: {str(e)}"
        )

