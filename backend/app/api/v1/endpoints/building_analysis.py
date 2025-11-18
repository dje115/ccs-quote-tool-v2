#!/usr/bin/env python3
"""
Building Analysis API Endpoints
AI-powered building analysis with Google Maps integration
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from pydantic import BaseModel
import asyncio

from app.core.database import get_async_db, SessionLocal
from app.core.dependencies import get_current_user, get_current_tenant
from app.core.api_keys import get_api_keys
from app.models.tenant import User, Tenant
from app.services.building_analysis_service import BuildingAnalysisService

router = APIRouter()


class BuildingAnalysisRequest(BaseModel):
    address: str
    building_type: Optional[str] = None
    building_size: Optional[float] = None


class BuildingAnalysisResponse(BaseModel):
    success: bool
    analysis: dict
    address: str


@router.post("/analyze", response_model=BuildingAnalysisResponse)
async def analyze_building(
    request: BuildingAnalysisRequest,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Analyze building for cabling requirements
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    Note: Wraps sync service calls in executor.
    """
    try:
        def _get_api_keys():
            sync_db = SessionLocal()
            try:
                return get_api_keys(sync_db, current_tenant)
            finally:
                sync_db.close()
        
        loop = asyncio.get_event_loop()
        api_keys = await loop.run_in_executor(None, _get_api_keys)
        
        if not api_keys.openai:
            raise HTTPException(
                status_code=400,
                detail="OpenAI API key not configured"
            )
        
        # BuildingAnalysisService.analyze_building is async but service uses sync db
        sync_db = SessionLocal()
        try:
            analysis_service = BuildingAnalysisService(
                db=sync_db,
                tenant_id=current_tenant.id,
                openai_api_key=api_keys.openai
            )
            analysis = await analysis_service.analyze_building(
                address=request.address,
                building_type=request.building_type,
                building_size=request.building_size
            )
        finally:
            sync_db.close()
        
        if 'error' in analysis:
            raise HTTPException(
                status_code=500,
                detail=analysis['error']
            )
        
        return {
            'success': True,
            'analysis': analysis,
            'address': request.address
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing building: {str(e)}"
        )


@router.get("/analyze", response_model=BuildingAnalysisResponse)
async def analyze_building_get(
    address: str = Query(..., description="Building address"),
    building_type: Optional[str] = Query(None, description="Building type"),
    building_size: Optional[float] = Query(None, description="Building size in sqm"),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Analyze building for cabling requirements (GET endpoint)
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    Note: Wraps sync service calls in executor.
    """
    try:
        def _get_api_keys():
            sync_db = SessionLocal()
            try:
                return get_api_keys(sync_db, current_tenant)
            finally:
                sync_db.close()
        
        loop = asyncio.get_event_loop()
        api_keys = await loop.run_in_executor(None, _get_api_keys)
        
        if not api_keys.openai:
            raise HTTPException(
                status_code=400,
                detail="OpenAI API key not configured"
            )
        
        sync_db = SessionLocal()
        try:
            analysis_service = BuildingAnalysisService(
                db=sync_db,
                tenant_id=current_tenant.id,
                openai_api_key=api_keys.openai
            )
            analysis = await analysis_service.analyze_building(
                address=address,
                building_type=building_type,
                building_size=building_size
            )
        finally:
            sync_db.close()
        
        if 'error' in analysis:
            raise HTTPException(
                status_code=500,
                detail=analysis['error']
            )
        
        return {
            'success': True,
            'analysis': analysis,
            'address': address
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing building: {str(e)}"
        )


