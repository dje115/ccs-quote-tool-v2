#!/usr/bin/env python3
"""
Quote Prompt Management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from app.core.database import get_async_db, SessionLocal
from app.core.dependencies import get_current_user, get_current_tenant
from app.models.quotes import Quote
from app.models.quote_prompt_history import QuotePromptHistory
from app.models.tenant import User, Tenant
from app.services.quote_builder_service import QuoteBuilderService
import uuid

router = APIRouter(prefix="/quotes", tags=["quote-prompts"])


class PromptRegenerateRequest(BaseModel):
    prompt_text: str = Field(..., description="Modified prompt text to use for regeneration")
    customer_request: Optional[str] = Field(None, description="Updated customer request (optional)")


class PromptHistoryResponse(BaseModel):
    id: str
    quote_id: str
    prompt_text: str
    prompt_variables: dict
    ai_model: Optional[str]
    ai_provider: Optional[str]
    temperature: Optional[float]
    max_tokens: Optional[int]
    generation_successful: bool
    generation_error: Optional[str]
    created_at: datetime
    created_by: Optional[str]


@router.get("/{quote_id}/prompt")
async def get_quote_prompt(
    quote_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Get the current prompt text for a quote"""
    try:
        # Verify quote exists
        quote_stmt = select(Quote).where(
            and_(
                Quote.id == quote_id,
                Quote.tenant_id == str(current_tenant.id),
                Quote.is_deleted == False
            )
        )
        result = await db.execute(quote_stmt)
        quote = result.scalar_one_or_none()
        
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")
        
        return {
            "quote_id": quote_id,
            "prompt_text": quote.last_prompt_text or "",
            "has_prompt": bool(quote.last_prompt_text)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting quote prompt: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting quote prompt: {str(e)}"
        )


@router.post("/{quote_id}/prompt/regenerate")
async def regenerate_quote_with_prompt(
    quote_id: str,
    request: PromptRegenerateRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Regenerate a quote using a modified prompt"""
    try:
        # Use sync session for services
        sync_db = SessionLocal()
        builder_service = QuoteBuilderService(sync_db, str(current_tenant.id))
        
        try:
            # Get quote to extract original request details
            quote_stmt = select(Quote).where(
                and_(
                    Quote.id == quote_id,
                    Quote.tenant_id == str(current_tenant.id),
                    Quote.is_deleted == False
                )
            )
            result = await db.execute(quote_stmt)
            quote = result.scalar_one_or_none()
            
            if not quote:
                raise HTTPException(status_code=404, detail="Quote not found")
            
            # Use custom prompt to regenerate
            customer_request = request.customer_request or quote.description or ""
            
            # Call AI generation with custom prompt
            from app.services.quote_ai_generation_service import QuoteAIGenerationService
            ai_service = QuoteAIGenerationService(sync_db, str(current_tenant.id))
            
            ai_result = await ai_service.generate_quote(
                customer_request=customer_request,
                user_id=str(current_user.id),
                custom_prompt_text=request.prompt_text
            )
            
            if not ai_result.get("success"):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=ai_result.get("error", "AI generation failed")
                )
            
            quote_data = ai_result["quote_data"]
            prompt_metadata = quote_data.get("_prompt_metadata", {})
            
            # Save prompt history
            prompt_history = QuotePromptHistory(
                id=str(uuid.uuid4()),
                tenant_id=str(current_tenant.id),
                quote_id=quote_id,
                prompt_text=request.prompt_text,
                prompt_variables=prompt_metadata.get("prompt_variables", {}),
                ai_model=prompt_metadata.get("ai_model"),
                ai_provider=prompt_metadata.get("ai_provider"),
                temperature=prompt_metadata.get("temperature"),
                max_tokens=prompt_metadata.get("max_tokens"),
                generation_successful=prompt_metadata.get("generation_successful", True),
                generated_quote_data=quote_data,
                created_by=str(current_user.id)
            )
            sync_db.add(prompt_history)
            
            # Update quote with new prompt text
            quote.last_prompt_text = request.prompt_text
            sync_db.commit()
            
            return {
                "success": True,
                "message": "Quote regenerated successfully",
                "prompt_history_id": prompt_history.id,
                "quote_data": quote_data
            }
        
        finally:
            sync_db.close()
    
    except HTTPException:
        raise
    except Exception as e:
        import logging
        import uuid
        logger = logging.getLogger(__name__)
        logger.error(f"Error regenerating quote: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error regenerating quote: {str(e)}"
        )


@router.get("/{quote_id}/prompt/history")
async def get_quote_prompt_history(
    quote_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Get prompt history for a quote"""
    try:
        # Verify quote exists
        quote_stmt = select(Quote).where(
            and_(
                Quote.id == quote_id,
                Quote.tenant_id == str(current_tenant.id),
                Quote.is_deleted == False
            )
        )
        result = await db.execute(quote_stmt)
        quote = result.scalar_one_or_none()
        
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")
        
        # Get prompt history
        history_stmt = select(QuotePromptHistory).where(
            and_(
                QuotePromptHistory.quote_id == quote_id,
                QuotePromptHistory.tenant_id == str(current_tenant.id),
                QuotePromptHistory.is_deleted == False
            )
        ).order_by(desc(QuotePromptHistory.created_at))
        
        history_result = await db.execute(history_stmt)
        history_items = history_result.scalars().all()
        
        return {
            "quote_id": quote_id,
            "history": [
                {
                    "id": item.id,
                    "prompt_text": item.prompt_text,
                    "prompt_variables": item.prompt_variables or {},
                    "ai_model": item.ai_model,
                    "ai_provider": item.ai_provider,
                    "temperature": float(item.temperature) if item.temperature else None,
                    "max_tokens": item.max_tokens,
                    "generation_successful": item.generation_successful,
                    "generation_error": item.generation_error,
                    "created_at": item.created_at.isoformat() if item.created_at else None,
                    "created_by": item.created_by
                }
                for item in history_items
            ]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting prompt history: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting prompt history: {str(e)}"
        )

