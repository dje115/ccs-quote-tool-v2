#!/usr/bin/env python3
"""
Reporting & Analytics API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from pydantic import BaseModel

from app.core.dependencies import get_db, get_current_user, get_current_tenant
from app.models.tenant import User, Tenant
from app.services.reporting_service import ReportingService

router = APIRouter(prefix="/reports", tags=["Reporting"])


@router.get("/sales-pipeline")
async def get_sales_pipeline_report(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Get sales pipeline report"""
    try:
        service = ReportingService(db, current_user.tenant_id)
        report = service.get_sales_pipeline_report(start_date, end_date)
        return report
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating sales pipeline report: {str(e)}"
        )


@router.get("/revenue")
async def get_revenue_report(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    group_by: str = Query("month", regex="^(day|week|month|year)$"),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Get revenue report with time series data"""
    try:
        service = ReportingService(db, current_user.tenant_id)
        report = service.get_revenue_report(start_date, end_date, group_by)
        return report
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating revenue report: {str(e)}"
        )


@router.get("/helpdesk")
async def get_helpdesk_report(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Get helpdesk performance report"""
    try:
        service = ReportingService(db, current_user.tenant_id)
        report = service.get_helpdesk_report(start_date, end_date)
        return report
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating helpdesk report: {str(e)}"
        )


@router.get("/activities")
async def get_activity_report(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    user_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Get sales activity report"""
    try:
        service = ReportingService(db, current_user.tenant_id)
        report = service.get_activity_report(start_date, end_date, user_id)
        return report
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating activity report: {str(e)}"
        )


@router.get("/customers/{customer_id}/lifetime-value")
async def get_customer_lifetime_value(
    customer_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Get customer lifetime value metrics"""
    try:
        service = ReportingService(db, current_user.tenant_id)
        clv = service.get_customer_lifetime_value(customer_id)
        return clv
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating customer lifetime value: {str(e)}"
        )

