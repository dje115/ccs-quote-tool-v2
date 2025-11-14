#!/usr/bin/env python3
"""
Pricing Import API Endpoints
Import pricing from Excel/CSV files with AI extraction
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from app.core.database import get_db
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
    db: Session = Depends(get_db)
):
    """Import pricing from Excel or CSV file"""
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
        
        # Get API keys
        api_keys = get_api_keys(db, current_tenant)
        
        # Import pricing
        import_service = PricingImportService(
            db=db,
            tenant_id=current_tenant.id,
            openai_api_key=api_keys.openai if use_ai_extraction else None
        )
        
        result = await import_service.import_pricing_from_file(
            file_content=file_content,
            filename=file.filename or 'import',
            use_ai_extraction=use_ai_extraction
        )
        
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
    db: Session = Depends(get_db)
):
    """Get pricing import template structure"""
    try:
        import_service = PricingImportService(db, current_tenant.id)
        template = import_service.get_import_template()
        return template
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting template: {str(e)}"
        )


