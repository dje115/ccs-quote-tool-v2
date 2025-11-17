#!/usr/bin/env python3
"""
Revenue Tracking API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.core.dependencies import get_db, get_current_user, get_current_tenant
from app.models.tenant import User, Tenant
from app.services.revenue_tracking_service import RevenueTrackingService

router = APIRouter(prefix="/revenue", tags=["Revenue"])


@router.get("/recurring")
async def get_recurring_revenue(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Get recurring revenue from support contracts"""
    try:
        service = RevenueTrackingService(db, current_user.tenant_id)
        revenue = service.get_recurring_revenue(start_date, end_date)
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
    db: Session = Depends(get_db)
):
    """Get revenue forecast for the next N months"""
    try:
        service = RevenueTrackingService(db, current_user.tenant_id)
        forecast = service.get_revenue_forecast(months_ahead)
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
    db: Session = Depends(get_db)
):
    """Get revenue from contracts renewing in the next N months"""
    try:
        service = RevenueTrackingService(db, current_user.tenant_id)
        renewals = service.get_contract_renewal_revenue(months_ahead)
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
    db: Session = Depends(get_db)
):
    """Get revenue summary for a specific customer"""
    try:
        service = RevenueTrackingService(db, current_user.tenant_id)
        summary = service.get_customer_revenue_summary(customer_id)
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting customer revenue summary: {str(e)}"
        )

