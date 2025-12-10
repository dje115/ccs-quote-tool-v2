#!/usr/bin/env python3
"""
API endpoints for AI provider key management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel
import asyncio

from app.core.database import get_async_db, SessionLocal
from app.core.dependencies import get_current_user, get_current_tenant
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
    api_key: Optional[str] = None  # Optional for test endpoint, required for save
    test_on_save: bool = True  # Test the key when saving


class ProviderKeyTestResponse(BaseModel):
    """Response from testing provider key"""
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    model: Optional[str] = None


class ProviderSettingsUpdate(BaseModel):
    """Request to update provider settings"""
    base_url: Optional[str] = None
    supported_models: Optional[List[str]] = None
    default_settings: Optional[dict] = None
    is_active: Optional[bool] = None


@router.get("/providers", response_model=List[ProviderResponse])
async def list_providers(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    List all available AI providers
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        stmt = select(AIProvider).where(
            AIProvider.is_active == True
        ).order_by(AIProvider.name)
        result = await db.execute(stmt)
        providers = result.scalars().all()
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
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get API key status for all providers (tenant and system level)
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        providers_stmt = select(AIProvider).where(
            AIProvider.is_active == True
        )
        providers_result = await db.execute(providers_stmt)
        providers = providers_result.scalars().all()
        
        results = []
        
        for provider in providers:
            # Check tenant key
            tenant_key_stmt = select(ProviderAPIKey).where(
                and_(
                    ProviderAPIKey.provider_id == provider.id,
                    ProviderAPIKey.tenant_id == current_tenant.id
                )
            )
            tenant_key_result = await db.execute(tenant_key_stmt)
            tenant_key = tenant_key_result.scalars().first()
            
            # Check system key
            system_key_stmt = select(ProviderAPIKey).where(
                and_(
                    ProviderAPIKey.provider_id == provider.id,
                    ProviderAPIKey.tenant_id.is_(None)
                )
            )
            system_key_result = await db.execute(system_key_stmt)
            system_key = system_key_result.scalars().first()
            
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


@router.post("/{provider_id}/test", response_model=ProviderKeyTestResponse)
async def test_provider_key(
    provider_id: str,
    request: Optional[ProviderKeyRequest] = None,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db),
    is_system: bool = False
):
    """
    Test a provider API key
    
    If api_key is provided in request, tests that key.
    Otherwise, tests the existing saved key for the tenant/system.
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    Note: Wraps sync service calls in executor.
    """
    try:
        # Get provider
        provider_stmt = select(AIProvider).where(
            and_(
                AIProvider.id == provider_id,
                AIProvider.is_active == True
            )
        )
        provider_result = await db.execute(provider_stmt)
        provider = provider_result.scalars().first()
        
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
            key_stmt = select(ProviderAPIKey).where(
                and_(
                    ProviderAPIKey.provider_id == provider_id,
                    ProviderAPIKey.tenant_id == tenant_id
                )
            )
            key_result = await db.execute(key_stmt)
            key_record = key_result.scalars().first()
            
            if not key_record:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No API key found to test"
                )
            
            # Decrypt key if encrypted
            from app.core.encryption import decrypt_api_key, is_encrypted
            api_key = key_record.api_key
            if api_key and is_encrypted(api_key):
                api_key = decrypt_api_key(api_key)
        
        # Test the key (service uses sync db)
        sync_db = SessionLocal()
        try:
            provider_service = AIProviderService(sync_db, tenant_id=tenant_id)
            test_result = await provider_service.test_provider(provider_id, api_key)
        finally:
            sync_db.close()
        
        # Update key record if it exists
        if not request or not request.api_key:
            key_stmt = select(ProviderAPIKey).where(
                and_(
                    ProviderAPIKey.provider_id == provider_id,
                    ProviderAPIKey.tenant_id == tenant_id
                )
            )
            key_result = await db.execute(key_stmt)
            key_record = key_result.scalars().first()
            
            if key_record:
                key_record.is_valid = test_result.get("success", False)
                key_record.test_result = test_result.get("message")
                key_record.test_error = test_result.get("error")
                key_record.last_tested = datetime.now(timezone.utc)
                await db.commit()
        
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


@router.post("/{provider_id}", status_code=status.HTTP_200_OK)
@router.put("/{provider_id}", status_code=status.HTTP_200_OK)
async def save_provider_key(
    provider_id: str,
    request: ProviderKeyRequest,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db),
    is_system: bool = False  # Query param: true for system-level key
):
    """
    Save or update provider API key
    
    - Tenant-level keys: Any authenticated user can save for their tenant
    - System-level keys: Only SUPER_ADMIN can save
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    Note: Wraps sync service calls in executor.
    """
    try:
        # Check permissions for system-level keys
        if is_system and current_user.role != UserRole.SUPER_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="System-level API keys can only be managed by super admins"
            )
        
        # Get provider
        provider_stmt = select(AIProvider).where(
            and_(
                AIProvider.id == provider_id,
                AIProvider.is_active == True
            )
        )
        provider_result = await db.execute(provider_stmt)
        provider = provider_result.scalars().first()
        
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Provider not found"
            )
        
        # Determine tenant_id (None for system-level)
        tenant_id = None if is_system else current_tenant.id
        
        # Validate that api_key is provided for save operation
        if not request.api_key or not request.api_key.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="API key is required"
            )
        
        # Check if key already exists
        existing_key_stmt = select(ProviderAPIKey).where(
            and_(
                ProviderAPIKey.provider_id == provider_id,
                ProviderAPIKey.tenant_id == tenant_id
            )
        )
        existing_key_result = await db.execute(existing_key_stmt)
        existing_key = existing_key_result.scalars().first()
        
        # Test the key if requested
        test_result = None
        test_error = None
        is_valid = False
        
        if request.test_on_save:
            sync_db = SessionLocal()
            try:
                provider_service = AIProviderService(sync_db, tenant_id=tenant_id)
                test_result_dict = await provider_service.test_provider(provider_id, request.api_key.strip())
                
                is_valid = test_result_dict.get("success", False)
                test_result = test_result_dict.get("message")
                test_error = test_result_dict.get("error")
            finally:
                sync_db.close()
        
        # Encrypt API key before storing
        from app.core.encryption import encrypt_api_key
        
        encrypted_key = encrypt_api_key(request.api_key.strip()) if request.api_key else None
        
        # Update or create key
        if existing_key:
            existing_key.api_key = encrypted_key  # Store encrypted key
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
                api_key=encrypted_key,  # Store encrypted key
                is_valid=is_valid,
                test_result=test_result,
                test_error=test_error,
                last_tested=datetime.now(timezone.utc) if request.test_on_save else None
            )
            db.add(new_key)
        
        await db.commit()
        
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
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving provider key: {str(e)}"
        )


@router.put("/providers/{provider_id}/settings", response_model=ProviderResponse)
async def update_provider_settings(
    provider_id: str,
    settings: ProviderSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Update provider settings (base_url, supported_models, default_settings) - Admin only
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        provider_stmt = select(AIProvider).where(AIProvider.id == provider_id)
        provider_result = await db.execute(provider_stmt)
        provider = provider_result.scalars().first()
        
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Provider not found"
            )
        
        # Update fields if provided
        if settings.base_url is not None:
            provider.base_url = settings.base_url
        if settings.supported_models is not None:
            provider.supported_models = settings.supported_models
        if settings.default_settings is not None:
            provider.default_settings = settings.default_settings
        if settings.is_active is not None:
            provider.is_active = settings.is_active
        
        provider.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(provider)
        
        return ProviderResponse(
            id=provider.id,
            name=provider.name,
            slug=provider.slug,
            provider_type=provider.provider_type,
            base_url=provider.base_url,
            supported_models=provider.supported_models,
            default_settings=provider.default_settings,
            is_active=provider.is_active
        )
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating provider settings: {str(e)}"
        )


@router.delete("/{provider_id}", status_code=status.HTTP_200_OK)
async def delete_provider_key(
    provider_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db),
    is_system: bool = False
):
    """
    Delete provider API key
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        # Check permissions for system-level keys
        if is_system and current_user.role != UserRole.SUPER_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="System-level API keys can only be managed by super admins"
            )
        
        tenant_id = None if is_system else current_tenant.id
        
        key_stmt = select(ProviderAPIKey).where(
            and_(
                ProviderAPIKey.provider_id == provider_id,
                ProviderAPIKey.tenant_id == tenant_id
            )
        )
        key_result = await db.execute(key_stmt)
        key_record = key_result.scalars().first()
        
        if not key_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
        
        await db.delete(key_record)
        await db.commit()
        
        return {"success": True, "message": "API key deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting provider key: {str(e)}"
        )

