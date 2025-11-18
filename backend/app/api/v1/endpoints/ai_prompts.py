#!/usr/bin/env python3
"""
AI Prompts API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_, and_, select
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
import asyncio

from app.core.database import get_async_db, SessionLocal
from app.core.dependencies import get_current_user, get_current_tenant
from app.models.tenant import User, Tenant, UserRole
from app.models.ai_prompt import AIPrompt, AIPromptVersion, PromptCategory
from app.models.ai_provider import AIProvider, ProviderAPIKey
from app.services.ai_prompt_service import AIPromptService
from app.services.ai_provider_service import AIProviderService

router = APIRouter(prefix="/prompts", tags=["AI Prompts"])


# Request/Response models
class PromptCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    category: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None
    quote_type: Optional[str] = Field(None, max_length=100, description="For quote_analysis category: quote type like 'cabling', 'network_build', etc.")
    system_prompt: str = Field(..., min_length=1)
    user_prompt_template: str = Field(..., min_length=1)
    model: str = Field(default="gpt-5-mini", max_length=50)  # Legacy - kept for backward compatibility
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=8000, ge=1, le=100000)
    is_system: bool = Field(default=False)
    variables: Optional[Dict[str, Any]] = None
    # Provider configuration (new)
    provider_id: Optional[str] = Field(None, description="AI provider ID - if not set, uses system default")
    provider_model: Optional[str] = Field(None, max_length=100, description="Specific model name for the provider")
    provider_settings: Optional[Dict[str, Any]] = Field(None, description="Provider-specific settings (temperature, max_tokens, etc.)")
    use_system_default: bool = Field(default=True, description="If true, uses system default provider; if false, uses prompt-specific provider")


class PromptUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    quote_type: Optional[str] = Field(None, max_length=100)
    system_prompt: Optional[str] = Field(None, min_length=1)
    user_prompt_template: Optional[str] = Field(None, min_length=1)
    model: Optional[str] = Field(None, max_length=50)  # Legacy
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=1, le=100000)
    variables: Optional[Dict[str, Any]] = None
    note: Optional[str] = Field(None, max_length=255)
    # Provider configuration (new)
    provider_id: Optional[str] = Field(None, description="AI provider ID")
    provider_model: Optional[str] = Field(None, max_length=100)
    provider_settings: Optional[Dict[str, Any]] = None
    use_system_default: Optional[bool] = Field(None, description="If true, uses system default provider")


class PromptResponse(BaseModel):
    id: str
    name: str
    category: str
    description: Optional[str]
    quote_type: Optional[str] = None
    system_prompt: str
    user_prompt_template: str
    model: str  # Legacy
    temperature: float
    max_tokens: int
    version: int
    is_active: bool
    is_system: bool
    tenant_id: Optional[str]
    created_by: Optional[str]
    variables: Optional[Dict[str, Any]]
    # Provider configuration (new)
    provider_id: Optional[str] = None
    provider_model: Optional[str] = None
    provider_settings: Optional[Dict[str, Any]] = None
    use_system_default: bool = True
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PromptVersionResponse(BaseModel):
    id: str
    prompt_id: str
    version: int
    note: Optional[str]
    system_prompt: str
    user_prompt_template: str
    variables: Optional[Dict[str, Any]]
    model: str
    temperature: float
    max_tokens: int
    created_by: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class PromptTestRequest(BaseModel):
    variables: Dict[str, Any] = Field(default_factory=dict)


class PromptTestResponse(BaseModel):
    system_prompt: str
    user_prompt: str
    model: str
    temperature: float
    max_tokens: int


class AvailableProviderResponse(BaseModel):
    """Available provider with key status"""
    id: str
    name: str
    slug: str
    provider_type: str
    supported_models: Optional[List[str]]
    has_valid_key: bool  # True if tenant or system has valid API key


@router.get("/available-providers", response_model=List[AvailableProviderResponse])
async def get_available_providers(
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """Get list of providers that have valid API keys (tenant or system level)"""
    try:
        providers_stmt = select(AIProvider).where(
            AIProvider.is_active == True
        )
        providers_result = await db.execute(providers_stmt)
        providers = providers_result.scalars().all()
        
        results = []
        
        for provider in providers:
            # Check if tenant or system has valid key
            tenant_key_stmt = select(ProviderAPIKey).where(
                and_(
                    ProviderAPIKey.provider_id == provider.id,
                    ProviderAPIKey.tenant_id == current_tenant.id,
                    ProviderAPIKey.is_valid == True
                )
            )
            tenant_key_result = await db.execute(tenant_key_stmt)
            has_tenant_key = tenant_key_result.scalars().first() is not None
            
            system_key_stmt = select(ProviderAPIKey).where(
                and_(
                    ProviderAPIKey.provider_id == provider.id,
                    ProviderAPIKey.tenant_id.is_(None),
                    ProviderAPIKey.is_valid == True
                )
            )
            system_key_result = await db.execute(system_key_stmt)
            has_system_key = system_key_result.scalars().first() is not None
            
            # For OpenAI, also check legacy tenant.openai_api_key
            if provider.slug == "openai":
                if current_tenant.openai_api_key:
                    has_tenant_key = True
                system_tenant_stmt = select(Tenant).where(
                    or_(Tenant.name == "System", Tenant.plan == "system")
                )
                system_tenant_result = await db.execute(system_tenant_stmt)
                system_tenant = system_tenant_result.scalars().first()
                if system_tenant and system_tenant.openai_api_key:
                    has_system_key = True
            
            has_valid_key = has_tenant_key or has_system_key
            
            results.append(AvailableProviderResponse(
                id=provider.id,
                name=provider.name,
                slug=provider.slug,
                provider_type=provider.provider_type,
                supported_models=provider.supported_models,
                has_valid_key=has_valid_key
            ))
        
        return results
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting available providers: {str(e)}"
        )


@router.get("/available-models/{provider_id}", response_model=List[str])
async def get_available_models(
    provider_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Get list of available models for a provider"""
    try:
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
        
        # Return supported models from provider config
        if provider.supported_models:
            return provider.supported_models
        
        # Fallback: try to get from provider instance
        try:
            from app.core.ai_providers import create_provider
            from app.core.api_keys import get_provider_api_key
            
            api_key = get_provider_api_key(db, current_user.tenant, provider.slug)
            if api_key:
                provider_instance = create_provider(provider.slug, api_key, provider.base_url)
                if provider_instance:
                    return provider_instance.get_supported_models()
        except Exception:
            pass
        
        return []
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting available models: {str(e)}"
        )


@router.get("/", response_model=List[PromptResponse])
async def list_prompts(
    category: Optional[str] = Query(None, description="Filter by category"),
    quote_type: Optional[str] = Query(None, description="Filter by quote type (for quote_analysis category)"),
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_system: Optional[bool] = Query(None, description="Filter by system prompts"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """List all prompts with optional filters (Advanced users only)"""
    # Check if user has permission to manage prompts (admin or tenant_admin)
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.TENANT_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Advanced user access required to manage AI prompts"
        )
    try:
        # Build query to get both system prompts and tenant-specific prompts
        stmt = select(AIPrompt)
        
        # Apply filters
        if category:
            stmt = stmt.where(AIPrompt.category == category)
        if is_active is not None:
            stmt = stmt.where(AIPrompt.is_active == is_active)
        if is_system is not None:
            stmt = stmt.where(AIPrompt.is_system == is_system)
        else:
            # If not filtering by is_system, get both system and tenant prompts
            # System prompts: is_system=True AND tenant_id IS NULL
            # Tenant prompts: is_system=False AND tenant_id = current_user.tenant_id
            stmt = stmt.where(
                or_(
                    and_(AIPrompt.is_system == True, AIPrompt.tenant_id.is_(None)),
                    and_(AIPrompt.is_system == False, AIPrompt.tenant_id == current_user.tenant_id)
                )
            )
        
        if tenant_id:
            # If specific tenant_id requested, filter to that tenant's prompts only
            stmt = stmt.where(AIPrompt.tenant_id == tenant_id)
        
        if quote_type:
            stmt = stmt.where(AIPrompt.quote_type == quote_type)
        
        stmt = stmt.order_by(AIPrompt.category, AIPrompt.version.desc())
        prompts_result = await db.execute(stmt)
        prompts = prompts_result.scalars().all()
        
        return prompts
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing prompts: {str(e)}"
        )


@router.get("/{prompt_id}", response_model=PromptResponse)
async def get_prompt(
    prompt_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Get a specific prompt by ID (Advanced users only)"""
    try:
        # Check if user has permission to manage prompts
        if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.TENANT_ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Advanced user access required to manage AI prompts"
            )
        
        prompt_stmt = select(AIPrompt).where(AIPrompt.id == prompt_id)
        prompt_result = await db.execute(prompt_stmt)
        prompt = prompt_result.scalars().first()
        
        if not prompt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prompt {prompt_id} not found"
            )
        
        # Check tenant access (if not system prompt)
        if not prompt.is_system and prompt.tenant_id != current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this prompt"
            )
        
        return prompt
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting prompt: {str(e)}"
        )


@router.post("/", response_model=PromptResponse, status_code=status.HTTP_201_CREATED)
async def create_prompt(
    prompt_data: PromptCreate,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """Create a new prompt (Advanced users only)"""
    try:
        # Check if user has permission to manage prompts
        if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.TENANT_ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Advanced user access required to manage AI prompts"
            )
        
        # Check permissions (only super admins can create system prompts)
        if prompt_data.is_system and current_user.role != UserRole.SUPER_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only super admins can create system prompts"
            )
        
        def _create_prompt():
            sync_db = SessionLocal()
            try:
                service = AIPromptService(sync_db, tenant_id=current_user.tenant_id)
                return service.create_prompt(
                    name=prompt_data.name,
                    category=prompt_data.category,
                    system_prompt=prompt_data.system_prompt,
                    user_prompt_template=prompt_data.user_prompt_template,
                    model=prompt_data.model,
                    temperature=prompt_data.temperature,
                    max_tokens=prompt_data.max_tokens,
                    is_system=prompt_data.is_system,
                    tenant_id=None if prompt_data.is_system else current_user.tenant_id,
                    created_by=current_user.id,
                    variables=prompt_data.variables,
                    description=prompt_data.description,
                    quote_type=prompt_data.quote_type,
                    provider_id=prompt_data.provider_id,
                    provider_model=prompt_data.provider_model,
                    provider_settings=prompt_data.provider_settings,
                    use_system_default=prompt_data.use_system_default
                )
            finally:
                sync_db.close()
        
        loop = asyncio.get_event_loop()
        prompt = await loop.run_in_executor(None, _create_prompt)
        
        return prompt
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating prompt: {str(e)}"
        )


@router.put("/{prompt_id}", response_model=PromptResponse)
async def update_prompt(
    prompt_id: str,
    prompt_data: PromptUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Update a prompt (creates new version) - Advanced users only"""
    try:
        # Check if user has permission to manage prompts
        if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.TENANT_ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Advanced user access required to manage AI prompts"
            )
        
        prompt_stmt = select(AIPrompt).where(AIPrompt.id == prompt_id)
        prompt_result = await db.execute(prompt_stmt)
        prompt = prompt_result.scalars().first()
        
        if not prompt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prompt {prompt_id} not found"
            )
        
        # Check permissions
        if prompt.is_system and current_user.role != UserRole.SUPER_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only super admins can update system prompts"
            )
        
        if not prompt.is_system and prompt.tenant_id != current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this prompt"
            )
        
        def _update_prompt():
            sync_db = SessionLocal()
            try:
                service = AIPromptService(sync_db, tenant_id=current_user.tenant_id)
                return service.update_prompt(
                    prompt_id=prompt_id,
                    system_prompt=prompt_data.system_prompt,
                    user_prompt_template=prompt_data.user_prompt_template,
                    model=prompt_data.model,
                    temperature=prompt_data.temperature,
                    max_tokens=prompt_data.max_tokens,
                    variables=prompt_data.variables,
                    description=prompt_data.description,
                    quote_type=prompt_data.quote_type,
                    note=prompt_data.note,
                    updated_by=current_user.id,
                    provider_id=prompt_data.provider_id,
                    provider_model=prompt_data.provider_model,
                    provider_settings=prompt_data.provider_settings,
                    use_system_default=prompt_data.use_system_default
                )
            finally:
                sync_db.close()
        
        loop = asyncio.get_event_loop()
        updated_prompt = await loop.run_in_executor(None, _update_prompt)
        
        return updated_prompt
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating prompt: {str(e)}"
        )


@router.delete("/{prompt_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prompt(
    prompt_id: str,
    soft_delete: bool = Query(True, description="Soft delete (deactivate) or hard delete"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Delete a prompt (Advanced users only)"""
    try:
        # Check if user has permission to manage prompts
        if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.TENANT_ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Advanced user access required to manage AI prompts"
            )
        
        prompt_stmt = select(AIPrompt).where(AIPrompt.id == prompt_id)
        prompt_result = await db.execute(prompt_stmt)
        prompt = prompt_result.scalars().first()
        
        if not prompt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prompt {prompt_id} not found"
            )
        
        # Check permissions
        if prompt.is_system and current_user.role != UserRole.SUPER_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only super admins can delete system prompts"
            )
        
        if not prompt.is_system and prompt.tenant_id != current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this prompt"
            )
        
        def _delete_prompt():
            sync_db = SessionLocal()
            try:
                service = AIPromptService(sync_db, tenant_id=current_user.tenant_id)
                service.delete_prompt(prompt_id, soft_delete=soft_delete)
            finally:
                sync_db.close()
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _delete_prompt)
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting prompt: {str(e)}"
        )


@router.post("/{prompt_id}/test", response_model=PromptTestResponse)
async def test_prompt(
    prompt_id: str,
    test_data: PromptTestRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Test a prompt with sample variables (Advanced users only)"""
    try:
        # Check if user has permission to manage prompts
        if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.TENANT_ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Advanced user access required to manage AI prompts"
            )
        
        prompt_stmt = select(AIPrompt).where(AIPrompt.id == prompt_id)
        prompt_result = await db.execute(prompt_stmt)
        prompt = prompt_result.scalars().first()
        
        if not prompt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prompt {prompt_id} not found"
            )
        
        # Check access
        if not prompt.is_system and prompt.tenant_id != current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this prompt"
            )
        
        def _render_prompt():
            sync_db = SessionLocal()
            try:
                service = AIPromptService(sync_db, tenant_id=current_user.tenant_id)
                return service.render_prompt(prompt, test_data.variables)
            finally:
                sync_db.close()
        
        loop = asyncio.get_event_loop()
        rendered = await loop.run_in_executor(None, _render_prompt)
        
        return PromptTestResponse(
            system_prompt=rendered['system_prompt'],
            user_prompt=rendered['user_prompt'],
            model=rendered['model'],
            temperature=rendered['temperature'],
            max_tokens=rendered['max_tokens']
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error testing prompt: {str(e)}"
        )


@router.get("/{prompt_id}/versions", response_model=List[PromptVersionResponse])
async def get_prompt_versions(
    prompt_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Get version history for a prompt (Advanced users only)"""
    try:
        # Check if user has permission to manage prompts
        if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.TENANT_ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Advanced user access required to manage AI prompts"
            )
        
        prompt_stmt = select(AIPrompt).where(AIPrompt.id == prompt_id)
        prompt_result = await db.execute(prompt_stmt)
        prompt = prompt_result.scalars().first()
        
        if not prompt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prompt {prompt_id} not found"
            )
        
        # Check access
        if not prompt.is_system and prompt.tenant_id != current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this prompt"
            )
        
        def _get_versions():
            sync_db = SessionLocal()
            try:
                service = AIPromptService(sync_db, tenant_id=current_user.tenant_id)
                return service.get_prompt_versions(prompt_id)
            finally:
                sync_db.close()
        
        loop = asyncio.get_event_loop()
        versions = await loop.run_in_executor(None, _get_versions)
        
        return versions
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting prompt versions: {str(e)}"
        )


@router.post("/{prompt_id}/rollback/{version}", response_model=PromptResponse)
async def rollback_prompt(
    prompt_id: str,
    version: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Rollback a prompt to a specific version (Advanced users only)"""
    try:
        # Check if user has permission to manage prompts
        if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.TENANT_ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Advanced user access required to manage AI prompts"
            )
        
        prompt_stmt = select(AIPrompt).where(AIPrompt.id == prompt_id)
        prompt_result = await db.execute(prompt_stmt)
        prompt = prompt_result.scalars().first()
        
        if not prompt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prompt {prompt_id} not found"
            )
        
        # Check permissions
        if prompt.is_system and current_user.role != UserRole.SUPER_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only super admins can rollback system prompts"
            )
        
        if not prompt.is_system and prompt.tenant_id != current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this prompt"
            )
        
        def _rollback():
            sync_db = SessionLocal()
            try:
                service = AIPromptService(sync_db, tenant_id=current_user.tenant_id)
                return service.rollback_to_version(
                    prompt_id=prompt_id,
                    version=version,
                    rolled_back_by=current_user.id
                )
            finally:
                sync_db.close()
        
        loop = asyncio.get_event_loop()
        rolled_back_prompt = await loop.run_in_executor(None, _rollback)
        
        return rolled_back_prompt
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error rolling back prompt: {str(e)}"
        )

