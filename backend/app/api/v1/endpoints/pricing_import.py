#!/usr/bin/env python3
"""
Pricing Import API Endpoints
Import pricing from Excel/CSV files with AI extraction
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from pydantic import BaseModel
import asyncio

from app.core.database import get_async_db, SessionLocal
from app.core.dependencies import get_current_user, get_current_tenant
from app.core.api_keys import get_api_keys
from app.models.tenant import User, Tenant
from app.services.pricing_import_service import PricingImportService

router = APIRouter()


class ImportResponse(BaseModel):
    success: bool
    imported_count: int = 0
    skipped_count: int = 0
    errors: list = []
    products: list = []
    error: Optional[str] = None


@router.post("/import", response_model=ImportResponse)
async def import_pricing(
    file: UploadFile = File(...),
    use_ai_extraction: bool = Query(True, description="Use AI to extract from any format"),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Import pricing from Excel or CSV file
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    Note: Wraps sync service calls in executor.
    """
    try:
        # Validate file type
        file_ext = file.filename.lower().split('.')[-1] if file.filename else ''
        if file_ext not in ['xlsx', 'xls', 'csv']:
            raise HTTPException(
                status_code=400,
                detail="File must be Excel (.xlsx, .xls) or CSV (.csv) format"
            )
        
        # Read file content
        file_content = await file.read()
        
        # Get API keys (need sync session for this)
        def _get_api_keys():
            sync_db = SessionLocal()
            try:
                return get_api_keys(sync_db, current_tenant)
            finally:
                sync_db.close()
        
        loop = asyncio.get_event_loop()
        api_keys = await loop.run_in_executor(None, _get_api_keys)
        
        # Import pricing (service uses sync session)
        def _import_pricing():
            sync_db = SessionLocal()
            try:
                import_service = PricingImportService(
                    db=sync_db,
                    tenant_id=current_tenant.id,
                    openai_api_key=api_keys.openai if use_ai_extraction else None
                )
                # Note: import_service.import_pricing_from_file is async, but service uses sync db
                # We'll need to handle this carefully
                import asyncio
                return asyncio.run(import_service.import_pricing_from_file(
                    file_content=file_content,
                    filename=file.filename or 'import',
                    use_ai_extraction=use_ai_extraction
                ))
            finally:
                sync_db.close()
        
        result = await loop.run_in_executor(None, _import_pricing)
        
        if not result.get('success'):
            raise HTTPException(
                status_code=500,
                detail=result.get('error', 'Import failed')
            )
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error importing pricing: {str(e)}"
        )


@router.get("/import/template")
async def get_import_template(
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get pricing import template structure
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    Note: Wraps sync service calls in executor.
    """
    try:
        def _get_template():
            sync_db = SessionLocal()
            try:
                import_service = PricingImportService(sync_db, current_tenant.id)
                return import_service.get_import_template()
            finally:
                sync_db.close()
        
        loop = asyncio.get_event_loop()
        template = await loop.run_in_executor(None, _get_template)
        return template
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting template: {str(e)}"
        )


