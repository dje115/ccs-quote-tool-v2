#!/usr/bin/env python3
"""
Metrics API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime

from app.core.dependencies import get_current_user, get_current_tenant
from app.core.database import get_async_db, SessionLocal
from app.models.tenant import User, Tenant

router = APIRouter(prefix="/metrics", tags=["Metrics"])


@router.get("/sla")
async def get_sla_metrics(
    start_date: Optional[str] = Query(None),  # ISO date string
    end_date: Optional[str] = Query(None),  # ISO date string
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get SLA adherence metrics
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        from app.services.metrics_service import MetricsService
        from datetime import datetime as dt
        
        # Parse dates
        start = None
        end = None
        if start_date:
            try:
                start = dt.fromisoformat(start_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_date format. Use ISO format.")
        
        if end_date:
            try:
                end = dt.fromisoformat(end_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_date format. Use ISO format.")
        
        # Use sync session for metrics service
        sync_db = SessionLocal()
        try:
            metrics_service = MetricsService(sync_db, current_user.tenant_id)
            metrics = await metrics_service.get_sla_metrics(
                start_date=start,
                end_date=end
            )
        finally:
            sync_db.close()
        
        return metrics
    
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting SLA metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting SLA metrics: {str(e)}"
        )


@router.get("/ai-usage")
async def get_ai_usage_metrics(
    start_date: Optional[str] = Query(None),  # ISO date string
    end_date: Optional[str] = Query(None),  # ISO date string
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get AI usage and acceptance metrics
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        from app.services.metrics_service import MetricsService
        from datetime import datetime as dt
        
        # Parse dates
        start = None
        end = None
        if start_date:
            try:
                start = dt.fromisoformat(start_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_date format. Use ISO format.")
        
        if end_date:
            try:
                end = dt.fromisoformat(end_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_date format. Use ISO format.")
        
        # Use sync session for metrics service
        sync_db = SessionLocal()
        try:
            metrics_service = MetricsService(sync_db, current_user.tenant_id)
            metrics = await metrics_service.get_ai_usage_metrics(
                start_date=start,
                end_date=end
            )
        finally:
            sync_db.close()
        
        return metrics
    
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting AI usage metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting AI usage metrics: {str(e)}"
        )


@router.get("/lead-velocity")
async def get_lead_velocity_metrics(
    start_date: Optional[str] = Query(None),  # ISO date string
    end_date: Optional[str] = Query(None),  # ISO date string
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get lead velocity metrics
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        from app.services.metrics_service import MetricsService
        from datetime import datetime as dt
        
        # Parse dates
        start = None
        end = None
        if start_date:
            try:
                start = dt.fromisoformat(start_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_date format. Use ISO format.")
        
        if end_date:
            try:
                end = dt.fromisoformat(end_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_date format. Use ISO format.")
        
        # Use sync session for metrics service
        sync_db = SessionLocal()
        try:
            metrics_service = MetricsService(sync_db, current_user.tenant_id)
            metrics = await metrics_service.get_lead_velocity_metrics(
                start_date=start,
                end_date=end
            )
        finally:
            sync_db.close()
        
        return metrics
    
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting lead velocity metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting lead velocity metrics: {str(e)}"
        )


@router.get("/quote-cycle-time")
async def get_quote_cycle_time_metrics(
    start_date: Optional[str] = Query(None),  # ISO date string
    end_date: Optional[str] = Query(None),  # ISO date string
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get quote cycle time metrics
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        from app.services.metrics_service import MetricsService
        from datetime import datetime as dt
        
        # Parse dates
        start = None
        end = None
        if start_date:
            try:
                start = dt.fromisoformat(start_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_date format. Use ISO format.")
        
        if end_date:
            try:
                end = dt.fromisoformat(end_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_date format. Use ISO format.")
        
        # Use sync session for metrics service
        sync_db = SessionLocal()
        try:
            metrics_service = MetricsService(sync_db, current_user.tenant_id)
            metrics = await metrics_service.get_quote_cycle_time_metrics(
                start_date=start,
                end_date=end
            )
        finally:
            sync_db.close()
        
        return metrics
    
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting quote cycle time metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting quote cycle time metrics: {str(e)}"
        )


@router.get("/csat")
async def get_csat_metrics(
    start_date: Optional[str] = Query(None),  # ISO date string
    end_date: Optional[str] = Query(None),  # ISO date string
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get Customer Satisfaction (CSAT) metrics
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        from app.services.metrics_service import MetricsService
        from datetime import datetime as dt
        
        # Parse dates
        start = None
        end = None
        if start_date:
            try:
                start = dt.fromisoformat(start_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_date format. Use ISO format.")
        
        if end_date:
            try:
                end = dt.fromisoformat(end_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_date format. Use ISO format.")
        
        # Use sync session for metrics service
        sync_db = SessionLocal()
        try:
            metrics_service = MetricsService(sync_db, current_user.tenant_id)
            metrics = await metrics_service.get_csat_metrics(
                start_date=start,
                end_date=end
            )
        finally:
            sync_db.close()
        
        return metrics
    
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting CSAT metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting CSAT metrics: {str(e)}"
        )


@router.get("/dashboard")
async def get_dashboard_metrics(
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get comprehensive dashboard metrics (all metrics)
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        from app.services.metrics_service import MetricsService
        
        # Use sync session for metrics service
        sync_db = SessionLocal()
        try:
            metrics_service = MetricsService(sync_db, current_user.tenant_id)
            metrics = await metrics_service.get_dashboard_metrics()
        finally:
            sync_db.close()
        
        return metrics
    
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting dashboard metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting dashboard metrics: {str(e)}"
        )

