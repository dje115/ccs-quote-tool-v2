#!/usr/bin/env python3
"""
AI Prompt Service for managing database-driven prompts
"""

import json
import uuid
import asyncio
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, timezone

from app.models.ai_prompt import AIPrompt, AIPromptVersion, PromptCategory
from app.core.redis import get_redis
import redis.asyncio as redis


class AIPromptService:
    """Service for managing AI prompts from database"""
    
    def __init__(self, db: Session, tenant_id: Optional[str] = None):
        self.db = db
        self.tenant_id = tenant_id
        self._redis_client: Optional[redis.Redis] = None
    
    async def _get_redis(self) -> Optional[redis.Redis]:
        """Get Redis client for caching"""
        try:
            if self._redis_client is None:
                self._redis_client = await get_redis()
            return self._redis_client
        except Exception as e:
            print(f"[AIPromptService] Redis not available: {e}")
            return None
    
    def _get_cache_key(self, category: str, tenant_id: Optional[str] = None, quote_type: Optional[str] = None) -> str:
        """Generate cache key for prompt"""
        tenant_key = tenant_id or "system"
        quote_type_key = f":{quote_type}" if quote_type else ""
        return f"ai_prompt:{category}:{tenant_key}{quote_type_key}"
    
    async def get_prompt(
        self,
        category: str,
        tenant_id: Optional[str] = None,
        version: Optional[int] = None,
        quote_type: Optional[str] = None
    ) -> Optional[AIPrompt]:
        """
        Get prompt by category with tenant and quote_type fallback
        
        Priority for quote_analysis category:
        1. Tenant-specific prompt with matching quote_type
        2. Tenant-specific prompt with quote_type=None (generic)
        3. System prompt with matching quote_type
        4. System prompt with quote_type=None (generic)
        5. None if not found
        
        For other categories, quote_type is ignored.
        """
        # Try cache first
        cache_key = self._get_cache_key(category, tenant_id or self.tenant_id, quote_type)
        redis_client = await self._get_redis()
        
        if redis_client:
            try:
                cached = await redis_client.get(cache_key)
                if cached:
                    prompt_data = json.loads(cached)
                    # Reconstruct prompt object from cached data
                    prompt = self.db.query(AIPrompt).filter(
                        AIPrompt.id == prompt_data['id']
                    ).first()
                    if prompt and prompt.is_active:
                        return prompt
            except Exception as e:
                print(f"[AIPromptService] Cache read error: {e}")
        
        # Build query
        query = self.db.query(AIPrompt).filter(
            AIPrompt.category == category,
            AIPrompt.is_active == True
        )
        
        # If version specified, filter by version
        if version:
            query = query.filter(AIPrompt.version == version)
        else:
            # Get latest version
            query = query.order_by(AIPrompt.version.desc())
        
        # For quote_analysis category, filter by quote_type if provided
        if category == PromptCategory.QUOTE_ANALYSIS.value and quote_type:
            # Try tenant-specific with matching quote_type first
            if tenant_id or self.tenant_id:
                tenant_id_to_use = tenant_id or self.tenant_id
                prompt = query.filter(
                    AIPrompt.tenant_id == tenant_id_to_use,
                    AIPrompt.quote_type == quote_type
                ).first()
                
                if prompt:
                    await self._cache_prompt(prompt, cache_key)
                    return prompt
                
                # Fallback to tenant-specific generic (quote_type=None)
                prompt = query.filter(
                    AIPrompt.tenant_id == tenant_id_to_use,
                    AIPrompt.quote_type.is_(None)
                ).first()
                
                if prompt:
                    await self._cache_prompt(prompt, cache_key)
                    return prompt
            
            # Try system prompt with matching quote_type
            prompt = query.filter(
                AIPrompt.is_system == True,
                AIPrompt.tenant_id.is_(None),
                AIPrompt.quote_type == quote_type
            ).first()
            
            if prompt:
                await self._cache_prompt(prompt, cache_key)
                return prompt
        
        # Try tenant-specific first (without quote_type filter for non-quote_analysis or fallback)
        if tenant_id or self.tenant_id:
            tenant_id_to_use = tenant_id or self.tenant_id
            prompt = query.filter(
                AIPrompt.tenant_id == tenant_id_to_use
            ).first()
            
            if prompt:
                # Cache it
                await self._cache_prompt(prompt, cache_key)
                return prompt
        
        # Fallback to system prompt
        prompt = query.filter(
            AIPrompt.is_system == True,
            AIPrompt.tenant_id.is_(None)
        ).first()
        
        if prompt:
            # Cache it
            await self._cache_prompt(prompt, cache_key)
            return prompt
        
        return None
    
    async def _cache_prompt(self, prompt: AIPrompt, cache_key: str):
        """Cache prompt in Redis"""
        redis_client = await self._get_redis()
        if redis_client:
            try:
                prompt_data = {
                    'id': prompt.id,
                    'category': prompt.category,
                    'name': prompt.name,
                    'system_prompt': prompt.system_prompt,
                    'user_prompt_template': prompt.user_prompt_template,
                    'model': prompt.model,
                    'temperature': prompt.temperature,
                    'max_tokens': prompt.max_tokens,
                    'variables': prompt.variables
                }
                await redis_client.setex(
                    cache_key,
                    3600,  # 1 hour TTL
                    json.dumps(prompt_data)
                )
            except Exception as e:
                print(f"[AIPromptService] Cache write error: {e}")
    
    def render_prompt(
        self,
        prompt: AIPrompt,
        variables: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Render prompt template with variables
        
        Returns:
            Dict with 'system_prompt' and 'user_prompt' keys
        """
        system_prompt = prompt.system_prompt
        user_prompt = prompt.user_prompt_template
        
        # Replace variables in templates
        for key, value in variables.items():
            placeholder = f"{{{key}}}"
            if isinstance(value, (list, dict)):
                value_str = json.dumps(value, indent=2)
            else:
                value_str = str(value)
            
            system_prompt = system_prompt.replace(placeholder, value_str)
            user_prompt = user_prompt.replace(placeholder, value_str)
        
        return {
            'system_prompt': system_prompt,
            'user_prompt': user_prompt,
            'model': prompt.model,
            'temperature': prompt.temperature,
            'max_tokens': prompt.max_tokens
        }
    
    def create_prompt(
        self,
        name: str,
        category: str,
        system_prompt: str,
        user_prompt_template: str,
        model: str = "gpt-5-mini",
        temperature: float = 0.7,
        max_tokens: int = 8000,
        is_system: bool = False,
        tenant_id: Optional[str] = None,
        created_by: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None
    ) -> AIPrompt:
        """Create a new prompt"""
        prompt = AIPrompt(
            id=str(uuid.uuid4()),
            name=name,
            category=category,
            description=description,
            system_prompt=system_prompt,
            user_prompt_template=user_prompt_template,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            version=1,
            is_active=True,
            is_system=is_system,
            tenant_id=tenant_id or self.tenant_id,
            created_by=created_by,
            variables=variables
        )
        
        self.db.add(prompt)
        self.db.flush()
        
        # Create initial version
        self._create_version(prompt, created_by, "Initial version")
        
        self.db.commit()
        self.db.refresh(prompt)
        
        # Invalidate cache
        asyncio.create_task(self._invalidate_cache(category, tenant_id or self.tenant_id))
        
        return prompt
    
    def update_prompt(
        self,
        prompt_id: str,
        system_prompt: Optional[str] = None,
        user_prompt_template: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        variables: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
        note: Optional[str] = None,
        updated_by: Optional[str] = None
    ) -> AIPrompt:
        """Update prompt (creates new version)"""
        prompt = self.db.query(AIPrompt).filter(AIPrompt.id == prompt_id).first()
        
        if not prompt:
            raise ValueError(f"Prompt {prompt_id} not found")
        
        # Save current version before updating
        self._create_version(
            prompt,
            updated_by,
            note or "Updated prompt"
        )
        
        # Update fields
        if system_prompt is not None:
            prompt.system_prompt = system_prompt
        if user_prompt_template is not None:
            prompt.user_prompt_template = user_prompt_template
        if model is not None:
            prompt.model = model
        if temperature is not None:
            prompt.temperature = temperature
        if max_tokens is not None:
            prompt.max_tokens = max_tokens
        if variables is not None:
            prompt.variables = variables
        if description is not None:
            prompt.description = description
        
        # Increment version
        prompt.version += 1
        prompt.updated_at = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(prompt)
        
        # Invalidate cache
        asyncio.create_task(self._invalidate_cache(prompt.category, prompt.tenant_id))
        
        return prompt
    
    def _create_version(
        self,
        prompt: AIPrompt,
        created_by: Optional[str],
        note: Optional[str]
    ):
        """Create a version snapshot"""
        version = AIPromptVersion(
            id=str(uuid.uuid4()),
            prompt_id=prompt.id,
            version=prompt.version,
            note=note,
            system_prompt=prompt.system_prompt,
            user_prompt_template=prompt.user_prompt_template,
            variables=prompt.variables,
            model=prompt.model,
            temperature=prompt.temperature,
            max_tokens=prompt.max_tokens,
            created_by=created_by
        )
        
        self.db.add(version)
    
    def delete_prompt(self, prompt_id: str, soft_delete: bool = True) -> bool:
        """Delete prompt (soft delete by default)"""
        prompt = self.db.query(AIPrompt).filter(AIPrompt.id == prompt_id).first()
        
        if not prompt:
            return False
        
        if soft_delete:
            prompt.is_active = False
            prompt.updated_at = datetime.now(timezone.utc)
        else:
            self.db.delete(prompt)
        
        self.db.commit()
        
        # Invalidate cache
        asyncio.create_task(self._invalidate_cache(prompt.category, prompt.tenant_id))
        
        return True
    
    def get_prompt_versions(self, prompt_id: str) -> List[AIPromptVersion]:
        """Get all versions of a prompt"""
        return self.db.query(AIPromptVersion).filter(
            AIPromptVersion.prompt_id == prompt_id
        ).order_by(AIPromptVersion.version.desc()).all()
    
    def rollback_to_version(self, prompt_id: str, version: int, rolled_back_by: Optional[str] = None) -> AIPrompt:
        """Rollback prompt to a specific version"""
        prompt = self.db.query(AIPrompt).filter(AIPrompt.id == prompt_id).first()
        
        if not prompt:
            raise ValueError(f"Prompt {prompt_id} not found")
        
        # Find the version to rollback to
        version_record = self.db.query(AIPromptVersion).filter(
            AIPromptVersion.prompt_id == prompt_id,
            AIPromptVersion.version == version
        ).first()
        
        if not version_record:
            raise ValueError(f"Version {version} not found for prompt {prompt_id}")
        
        # Create version snapshot of current state
        self._create_version(prompt, rolled_back_by, f"Rollback to version {version}")
        
        # Restore from version
        prompt.system_prompt = version_record.system_prompt
        prompt.user_prompt_template = version_record.user_prompt_template
        prompt.variables = version_record.variables
        prompt.model = version_record.model
        prompt.temperature = version_record.temperature
        prompt.max_tokens = version_record.max_tokens
        prompt.version += 1
        prompt.updated_at = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(prompt)
        
        # Invalidate cache
        asyncio.create_task(self._invalidate_cache(prompt.category, prompt.tenant_id))
        
        return prompt
    
    def list_prompts(
        self,
        category: Optional[str] = None,
        tenant_id: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_system: Optional[bool] = None
    ) -> List[AIPrompt]:
        """List prompts with filters"""
        query = self.db.query(AIPrompt)
        
        if category:
            query = query.filter(AIPrompt.category == category)
        if tenant_id:
            query = query.filter(AIPrompt.tenant_id == tenant_id)
        if is_active is not None:
            query = query.filter(AIPrompt.is_active == is_active)
        if is_system is not None:
            query = query.filter(AIPrompt.is_system == is_system)
        
        return query.order_by(AIPrompt.category, AIPrompt.version.desc()).all()
    
    async def _invalidate_cache(self, category: str, tenant_id: Optional[str]):
        """Invalidate cache for a prompt category"""
        redis_client = await self._get_redis()
        if redis_client:
            try:
                cache_key = self._get_cache_key(category, tenant_id, None)
                await redis_client.delete(cache_key)
            except Exception as e:
                print(f"[AIPromptService] Cache invalidation error: {e}")

