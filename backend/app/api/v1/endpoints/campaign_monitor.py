"""
Campaign Monitor API Endpoints

API endpoints for monitoring and managing campaign health.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List
from app.models.tenant import User
from app.core.dependencies import get_current_user
from app.services.campaign_monitor_service import get_campaign_monitor
from app.core.celery_app import celery_app

router = APIRouter()


@router.get("/health")
def get_campaign_health(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get overall campaign health statistics"""
    try:
        monitor = get_campaign_monitor(celery_app)
        
        if not monitor:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Campaign monitor service not available"
            )
        
        health_stats = monitor.get_campaign_health_stats()
        return {
            "success": True,
            "data": health_stats
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get campaign health: {str(e)}"
        )


@router.get("/stuck")
def get_stuck_campaigns(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get list of stuck campaigns"""
    try:
        monitor = get_campaign_monitor(celery_app)
        
        if not monitor:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Campaign monitor service not available"
            )
        
        stuck_campaigns = monitor.detect_stuck_campaigns()
        return {
            "success": True,
            "data": stuck_campaigns
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to detect stuck campaigns: {str(e)}"
        )


@router.post("/cleanup")
def cleanup_stuck_campaigns(
    max_duration_hours: int = 30,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Manually clean up stuck campaigns"""
    try:
        monitor = get_campaign_monitor(celery_app)
        
        if not monitor:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Campaign monitor service not available"
            )
        
        cleanup_results = monitor.cleanup_stuck_campaigns_on_startup()
        return {
            "success": True,
            "data": cleanup_results
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup campaigns: {str(e)}"
        )


@router.post("/force-cleanup")
def force_cleanup_stuck_campaigns(
    max_duration_hours: int = 4,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Force fail campaigns that have been running too long"""
    try:
        monitor = get_campaign_monitor(celery_app)
        
        if not monitor:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Campaign monitor service not available"
            )
        
        cleanup_results = monitor.force_fail_stuck_campaigns(max_duration_hours)
        return {
            "success": True,
            "data": cleanup_results
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to force cleanup campaigns: {str(e)}"
        )


@router.get("/report")
def get_health_report(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get comprehensive campaign health report"""
    try:
        monitor = get_campaign_monitor(celery_app)
        
        if not monitor:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Campaign monitor service not available"
            )
        
        # Get health stats
        health_stats = monitor.get_campaign_health_stats()
        
        # Get stuck campaigns
        stuck_campaigns = monitor.detect_stuck_campaigns()
        
        # Generate recommendations
        recommendations = []
        health_score = health_stats.get('health_score', 0)
        stuck_count = health_stats.get('stuck_campaigns', 0)
        failed_count = health_stats.get('failed_campaigns', 0)
        
        if health_score < 70:
            recommendations.append("Campaign health score is low - investigate failed campaigns")
        
        if stuck_count > 0:
            recommendations.append(f"{stuck_count} campaigns are stuck - consider force cleanup")
        
        if failed_count > 5:
            recommendations.append("High number of failed campaigns - check API keys and external services")
        
        if stuck_count == 0 and health_score > 90:
            recommendations.append("Campaign system is healthy - no action needed")
        
        report = {
            "health_stats": health_stats,
            "stuck_campaigns": stuck_campaigns,
            "recommendations": recommendations
        }
        
        return {
            "success": True,
            "data": report
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate health report: {str(e)}"
        )


@router.post("/monitor")
def trigger_manual_monitoring(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Manually trigger campaign monitoring and cleanup"""
    try:
        monitor = get_campaign_monitor(celery_app)
        
        if not monitor:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Campaign monitor service not available"
            )
        
        # Run comprehensive monitoring
        results = monitor.monitor_and_cleanup()
        
        return {
            "success": True,
            "data": results
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run monitoring: {str(e)}"
        )
