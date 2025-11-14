#!/usr/bin/env python3
"""
AI Prompts API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from app.core.dependencies import get_db, get_current_user, get_current_tenant
from app.models.tenant import User, Tenant
from app.models.ai_prompt import AIPrompt, AIPromptVersion, PromptCategory
from app.services.ai_prompt_service import AIPromptService

router = APIRouter(prefix="/prompts", tags=["AI Prompts"])


# Request/Response models
class PromptCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    category: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None
    system_prompt: str = Field(..., min_length=1)
    user_prompt_template: str = Field(..., min_length=1)
    model: str = Field(default="gpt-5-mini", max_length=50)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=8000, ge=1, le=100000)
    is_system: bool = Field(default=False)
    variables: Optional[Dict[str, Any]] = None


class PromptUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    system_prompt: Optional[str] = Field(None, min_length=1)
    user_prompt_template: Optional[str] = Field(None, min_length=1)
    model: Optional[str] = Field(None, max_length=50)
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=1, le=100000)
    variables: Optional[Dict[str, Any]] = None
    note: Optional[str] = Field(None, max_length=255)


class PromptResponse(BaseModel):
    id: str
    name: str
    category: str
    description: Optional[str]
    system_prompt: str
    user_prompt_template: str
    model: str
    temperature: float
    max_tokens: int
    version: int
    is_active: bool
    is_system: bool
    tenant_id: Optional[str]
    created_by: Optional[str]
    variables: Optional[Dict[str, Any]]
    created_at: str
    updated_at: str
    
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
    created_at: str
    
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


@router.get("/", response_model=List[PromptResponse])
async def list_prompts(
    category: Optional[str] = Query(None, description="Filter by category"),
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_system: Optional[bool] = Query(None, description="Filter by system prompts"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all prompts with optional filters"""
    try:
        service = AIPromptService(db, tenant_id=current_user.tenant_id)
        prompts = service.list_prompts(
            category=category,
            tenant_id=tenant_id,
            is_active=is_active,
            is_system=is_system
        )
        
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
    db: Session = Depends(get_db)
):
    """Get a specific prompt by ID"""
    try:
        prompt = db.query(AIPrompt).filter(AIPrompt.id == prompt_id).first()
        
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
    db: Session = Depends(get_db)
):
    """Create a new prompt"""
    try:
        # Check permissions (only admins can create system prompts)
        if prompt_data.is_system and current_user.role.value not in ["super_admin", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can create system prompts"
            )
        
        service = AIPromptService(db, tenant_id=current_user.tenant_id)
        
        prompt = service.create_prompt(
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
            description=prompt_data.description
        )
        
        return prompt
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating prompt: {str(e)}"
        )


@router.put("/{prompt_id}", response_model=PromptResponse)
async def update_prompt(
    prompt_id: str,
    prompt_data: PromptUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a prompt (creates new version)"""
    try:
        prompt = db.query(AIPrompt).filter(AIPrompt.id == prompt_id).first()
        
        if not prompt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prompt {prompt_id} not found"
            )
        
        # Check permissions
        if prompt.is_system and current_user.role.value not in ["super_admin", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can update system prompts"
            )
        
        if not prompt.is_system and prompt.tenant_id != current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this prompt"
            )
        
        service = AIPromptService(db, tenant_id=current_user.tenant_id)
        
        updated_prompt = service.update_prompt(
            prompt_id=prompt_id,
            system_prompt=prompt_data.system_prompt,
            user_prompt_template=prompt_data.user_prompt_template,
            model=prompt_data.model,
            temperature=prompt_data.temperature,
            max_tokens=prompt_data.max_tokens,
            variables=prompt_data.variables,
            description=prompt_data.description,
            note=prompt_data.note,
            updated_by=current_user.id
        )
        
        return updated_prompt
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating prompt: {str(e)}"
        )


@router.delete("/{prompt_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prompt(
    prompt_id: str,
    soft_delete: bool = Query(True, description="Soft delete (deactivate) or hard delete"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a prompt"""
    try:
        prompt = db.query(AIPrompt).filter(AIPrompt.id == prompt_id).first()
        
        if not prompt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prompt {prompt_id} not found"
            )
        
        # Check permissions
        if prompt.is_system and current_user.role.value not in ["super_admin", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can delete system prompts"
            )
        
        if not prompt.is_system and prompt.tenant_id != current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this prompt"
            )
        
        service = AIPromptService(db, tenant_id=current_user.tenant_id)
        service.delete_prompt(prompt_id, soft_delete=soft_delete)
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting prompt: {str(e)}"
        )


@router.post("/{prompt_id}/test", response_model=PromptTestResponse)
async def test_prompt(
    prompt_id: str,
    test_data: PromptTestRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Test a prompt with sample variables"""
    try:
        prompt = db.query(AIPrompt).filter(AIPrompt.id == prompt_id).first()
        
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
        
        service = AIPromptService(db, tenant_id=current_user.tenant_id)
        rendered = service.render_prompt(prompt, test_data.variables)
        
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
    db: Session = Depends(get_db)
):
    """Get version history for a prompt"""
    try:
        prompt = db.query(AIPrompt).filter(AIPrompt.id == prompt_id).first()
        
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
        
        service = AIPromptService(db, tenant_id=current_user.tenant_id)
        versions = service.get_prompt_versions(prompt_id)
        
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
    db: Session = Depends(get_db)
):
    """Rollback a prompt to a specific version"""
    try:
        prompt = db.query(AIPrompt).filter(AIPrompt.id == prompt_id).first()
        
        if not prompt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prompt {prompt_id} not found"
            )
        
        # Check permissions
        if prompt.is_system and current_user.role.value not in ["super_admin", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can rollback system prompts"
            )
        
        if not prompt.is_system and prompt.tenant_id != current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this prompt"
            )
        
        service = AIPromptService(db, tenant_id=current_user.tenant_id)
        rolled_back_prompt = service.rollback_to_version(
            prompt_id=prompt_id,
            version=version,
            rolled_back_by=current_user.id
        )
        
        return rolled_back_prompt
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error rolling back prompt: {str(e)}"
        )

