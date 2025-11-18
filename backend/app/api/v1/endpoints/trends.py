#!/usr/bin/env python3
"""
Trend Detection API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from pydantic import BaseModel

from app.core.dependencies import get_current_user, get_current_tenant
from app.core.database import get_async_db, SessionLocal
from app.models.tenant import User, Tenant

router = APIRouter(prefix="/trends", tags=["Trends"])


@router.get("/recurring-defects")
async def get_recurring_defects(
    days_back: int = Query(30, ge=7, le=365),
    min_occurrences: int = Query(3, ge=2, le=50),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get recurring defects/issues across customers
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        from app.services.trend_detection_service import TrendDetectionService
        
        # Use sync session for trend service
        sync_db = SessionLocal()
        try:
            trend_service = TrendDetectionService(sync_db, current_user.tenant_id)
            defects = await trend_service.detect_recurring_defects(
                days_back=days_back,
                min_occurrences=min_occurrences
            )
        finally:
            sync_db.close()
        
        return {
            "defects": defects,
            "count": len(defects),
            "period_days": days_back
        }
    
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting recurring defects: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting recurring defects: {str(e)}"
        )


@router.get("/quote-hurdles")
async def get_quote_hurdles(
    days_back: int = Query(30, ge=7, le=365),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get quote hurdles (common reasons quotes stall/fail)
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        from app.services.trend_detection_service import TrendDetectionService
        
        # Use sync session for trend service
        sync_db = SessionLocal()
        try:
            trend_service = TrendDetectionService(sync_db, current_user.tenant_id)
            hurdles = await trend_service.detect_quote_hurdles(days_back=days_back)
        finally:
            sync_db.close()
        
        return {
            "hurdles": hurdles,
            "count": len(hurdles),
            "period_days": days_back
        }
    
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting quote hurdles: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting quote hurdles: {str(e)}"
        )


@router.get("/churn-signals")
async def get_churn_signals(
    days_back: int = Query(90, ge=30, le=365),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get emerging churn signals across customers
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        from app.services.trend_detection_service import TrendDetectionService
        
        # Use sync session for trend service
        sync_db = SessionLocal()
        try:
            trend_service = TrendDetectionService(sync_db, current_user.tenant_id)
            signals = await trend_service.detect_churn_signals(days_back=days_back)
        finally:
            sync_db.close()
        
        return {
            "signals": signals,
            "count": len(signals),
            "period_days": days_back
        }
    
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting churn signals: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting churn signals: {str(e)}"
        )


@router.get("/report")
async def get_trend_report(
    days_back: int = Query(30, ge=7, le=365),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get comprehensive trend report
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        from app.services.trend_detection_service import TrendDetectionService
        
        # Use sync session for trend service
        sync_db = SessionLocal()
        try:
            trend_service = TrendDetectionService(sync_db, current_user.tenant_id)
            report = await trend_service.generate_trend_report(days_back=days_back)
        finally:
            sync_db.close()
        
        return report
    
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error generating trend report: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating trend report: {str(e)}"
        )

