#!/usr/bin/env python3
"""
API endpoints for AI provider key management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel

from app.core.dependencies import get_db, get_current_user, get_current_tenant
from app.models.tenant import User, Tenant, UserRole
from app.models.ai_provider import AIProvider, ProviderAPIKey
from app.services.ai_provider_service import AIProviderService
import uuid


router = APIRouter(prefix="/provider-keys", tags=["provider-keys"])


class ProviderResponse(BaseModel):
    """Provider information response"""
    id: str
    name: str
    slug: str
    provider_type: str
    base_url: Optional[str]
    supported_models: Optional[List[str]]
    default_settings: Optional[dict]
    is_active: bool
    
    class Config:
        from_attributes = True


class ProviderKeyStatusResponse(BaseModel):
    """Provider key status response"""
    provider: ProviderResponse
    has_tenant_key: bool
    has_system_key: bool
    tenant_key_valid: bool
    system_key_valid: bool
    last_tested: Optional[datetime]
    test_result: Optional[str]
    test_error: Optional[str]


class ProviderKeyRequest(BaseModel):
    """Request to save/update provider API key"""
    api_key: str
    test_on_save: bool = True  # Test the key when saving


class ProviderKeyTestResponse(BaseModel):
    """Response from testing provider key"""
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    model: Optional[str] = None


@router.get("/providers", response_model=List[ProviderResponse])
async def list_providers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all available AI providers"""
    try:
        providers = db.query(AIProvider).filter(
            AIProvider.is_active == True
        ).order_by(AIProvider.name).all()
        
        return providers
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing providers: {str(e)}"
        )


@router.get("/status", response_model=List[ProviderKeyStatusResponse])
async def get_provider_key_status(
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Get API key status for all providers (tenant and system level)"""
    try:
        providers = db.query(AIProvider).filter(
            AIProvider.is_active == True
        ).all()
        
        results = []
        
        for provider in providers:
            # Check tenant key
            tenant_key = db.query(ProviderAPIKey).filter(
                ProviderAPIKey.provider_id == provider.id,
                ProviderAPIKey.tenant_id == current_tenant.id
            ).first()
            
            # Check system key
            system_key = db.query(ProviderAPIKey).filter(
                ProviderAPIKey.provider_id == provider.id,
                ProviderAPIKey.tenant_id.is_(None)
            ).first()
            
            results.append(ProviderKeyStatusResponse(
                provider=ProviderResponse(
                    id=provider.id,
                    name=provider.name,
                    slug=provider.slug,
                    provider_type=provider.provider_type,
                    base_url=provider.base_url,
                    supported_models=provider.supported_models,
                    default_settings=provider.default_settings,
                    is_active=provider.is_active
                ),
                has_tenant_key=tenant_key is not None,
                has_system_key=system_key is not None,
                tenant_key_valid=tenant_key.is_valid if tenant_key else False,
                system_key_valid=system_key.is_valid if system_key else False,
                last_tested=tenant_key.last_tested if tenant_key else (system_key.last_tested if system_key else None),
                test_result=tenant_key.test_result if tenant_key else (system_key.test_result if system_key else None),
                test_error=tenant_key.test_error if tenant_key else (system_key.test_error if system_key else None)
            ))
        
        return results
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting provider key status: {str(e)}"
        )


@router.put("/{provider_id}", status_code=status.HTTP_200_OK)
async def save_provider_key(
    provider_id: str,
    request: ProviderKeyRequest,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db),
    is_system: bool = False  # Query param: true for system-level key
):
    """
    Save or update provider API key
    
    - Tenant-level keys: Any authenticated user can save for their tenant
    - System-level keys: Only SUPER_ADMIN can save
    """
    try:
        # Check permissions for system-level keys
        if is_system and current_user.role != UserRole.SUPER_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="System-level API keys can only be managed by super admins"
            )
        
        # Get provider
        provider = db.query(AIProvider).filter(
            AIProvider.id == provider_id,
            AIProvider.is_active == True
        ).first()
        
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Provider not found"
            )
        
        # Determine tenant_id (None for system-level)
        tenant_id = None if is_system else current_tenant.id
        
        # Check if key already exists
        existing_key = db.query(ProviderAPIKey).filter(
            ProviderAPIKey.provider_id == provider_id,
            ProviderAPIKey.tenant_id == tenant_id
        ).first()
        
        # Test the key if requested
        test_result = None
        test_error = None
        is_valid = False
        
        if request.test_on_save:
            provider_service = AIProviderService(db, tenant_id=tenant_id)
            test_result_dict = await provider_service.test_provider(provider_id, request.api_key)
            
            is_valid = test_result_dict.get("success", False)
            test_result = test_result_dict.get("message")
            test_error = test_result_dict.get("error")
        
        # Update or create key
        if existing_key:
            existing_key.api_key = request.api_key.strip()
            existing_key.is_valid = is_valid
            existing_key.test_result = test_result
            existing_key.test_error = test_error
            existing_key.last_tested = datetime.now(timezone.utc) if request.test_on_save else existing_key.last_tested
            existing_key.updated_at = datetime.now(timezone.utc)
        else:
            new_key = ProviderAPIKey(
                id=str(uuid.uuid4()),
                provider_id=provider_id,
                tenant_id=tenant_id,
                api_key=request.api_key.strip(),
                is_valid=is_valid,
                test_result=test_result,
                test_error=test_error,
                last_tested=datetime.now(timezone.utc) if request.test_on_save else None
            )
            db.add(new_key)
        
        db.commit()
        
        return {
            "success": True,
            "message": f"API key saved successfully{' and tested' if request.test_on_save else ''}",
            "is_valid": is_valid,
            "test_result": test_result,
            "test_error": test_error
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving provider key: {str(e)}"
        )


@router.post("/{provider_id}/test", response_model=ProviderKeyTestResponse)
async def test_provider_key(
    provider_id: str,
    request: Optional[ProviderKeyRequest] = None,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db),
    is_system: bool = False
):
    """
    Test a provider API key
    
    If api_key is provided in request, tests that key.
    Otherwise, tests the existing saved key for the tenant/system.
    """
    try:
        # Get provider
        provider = db.query(AIProvider).filter(
            AIProvider.id == provider_id,
            AIProvider.is_active == True
        ).first()
        
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Provider not found"
            )
        
        # Determine tenant_id
        tenant_id = None if is_system else current_tenant.id
        
        # Get API key to test
        api_key = None
        if request and request.api_key:
            api_key = request.api_key.strip()
        else:
            # Get existing key
            key_record = db.query(ProviderAPIKey).filter(
                ProviderAPIKey.provider_id == provider_id,
                ProviderAPIKey.tenant_id == tenant_id
            ).first()
            
            if not key_record:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No API key found to test"
                )
            
            api_key = key_record.api_key
        
        # Test the key
        provider_service = AIProviderService(db, tenant_id=tenant_id)
        test_result = await provider_service.test_provider(provider_id, api_key)
        
        # Update key record if it exists
        if not request or not request.api_key:
            key_record = db.query(ProviderAPIKey).filter(
                ProviderAPIKey.provider_id == provider_id,
                ProviderAPIKey.tenant_id == tenant_id
            ).first()
            
            if key_record:
                key_record.is_valid = test_result.get("success", False)
                key_record.test_result = test_result.get("message")
                key_record.test_error = test_result.get("error")
                key_record.last_tested = datetime.now(timezone.utc)
                db.commit()
        
        return ProviderKeyTestResponse(
            success=test_result.get("success", False),
            message=test_result.get("message"),
            error=test_result.get("error"),
            model=test_result.get("model")
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error testing provider key: {str(e)}"
        )


@router.delete("/{provider_id}", status_code=status.HTTP_200_OK)
async def delete_provider_key(
    provider_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db),
    is_system: bool = False
):
    """Delete provider API key"""
    try:
        # Check permissions for system-level keys
        if is_system and current_user.role != UserRole.SUPER_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="System-level API keys can only be managed by super admins"
            )
        
        tenant_id = None if is_system else current_tenant.id
        
        key_record = db.query(ProviderAPIKey).filter(
            ProviderAPIKey.provider_id == provider_id,
            ProviderAPIKey.tenant_id == tenant_id
        ).first()
        
        if not key_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
        
        db.delete(key_record)
        db.commit()
        
        return {"success": True, "message": "API key deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting provider key: {str(e)}"
        )

