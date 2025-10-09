#!/usr/bin/env python3
"""
Quote management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from decimal import Decimal
import uuid
from datetime import datetime

from app.core.database import get_db
from app.core.dependencies import get_current_user, check_permission
from app.models.quotes import Quote, QuoteStatus
from app.models.tenant import User

router = APIRouter()


class QuoteCreate(BaseModel):
    customer_id: str
    title: str
    description: str | None = None
    valid_until: datetime | None = None


class QuoteResponse(BaseModel):
    id: str
    customer_id: str
    quote_number: str
    title: str
    status: str
    total_amount: float
    created_at: datetime
    
    class Config:
        from_attributes = True


class QuoteUpdate(BaseModel):
    status: QuoteStatus | None = None
    title: str | None = None
    description: str | None = None


@router.get("/", response_model=List[QuoteResponse])
async def list_quotes(
    skip: int = 0,
    limit: int = 20,
    status: QuoteStatus | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List quotes for current tenant"""
    query = db.query(Quote).filter_by(
        tenant_id=current_user.tenant_id,
        is_deleted=False
    )
    
    if status:
        query = query.filter_by(status=status)
    
    quotes = query.order_by(Quote.created_at.desc()).offset(skip).limit(limit).all()
    return quotes


@router.post("/", response_model=QuoteResponse, status_code=status.HTTP_201_CREATED)
async def create_quote(
    quote_data: QuoteCreate,
    current_user: User = Depends(check_permission("quote:create")),
    db: Session = Depends(get_db)
):
    """Create new quote"""
    
    try:
        # Generate quote number
        quote_count = db.query(Quote).filter_by(tenant_id=current_user.tenant_id).count()
        quote_number = f"Q-{datetime.now().strftime('%Y%m')}-{quote_count + 1:04d}"
        
        quote = Quote(
            id=str(uuid.uuid4()),
            tenant_id=current_user.tenant_id,
            customer_id=quote_data.customer_id,
            quote_number=quote_number,
            title=quote_data.title,
            description=quote_data.description,
            status=QuoteStatus.DRAFT,
            valid_until=quote_data.valid_until,
            subtotal=Decimal('0.00'),
            tax_rate=0.20,
            tax_amount=Decimal('0.00'),
            total_amount=Decimal('0.00')
        )
        
        db.add(quote)
        db.commit()
        db.refresh(quote)
        
        return quote
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating quote: {str(e)}"
        )


@router.get("/{quote_id}", response_model=QuoteResponse)
async def get_quote(
    quote_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get quote by ID"""
    quote = db.query(Quote).filter_by(
        id=quote_id,
        tenant_id=current_user.tenant_id,
        is_deleted=False
    ).first()
    
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    return quote


@router.put("/{quote_id}", response_model=QuoteResponse)
async def update_quote(
    quote_id: str,
    quote_update: QuoteUpdate,
    current_user: User = Depends(check_permission("quote:update")),
    db: Session = Depends(get_db)
):
    """Update quote"""
    quote = db.query(Quote).filter_by(
        id=quote_id,
        tenant_id=current_user.tenant_id,
        is_deleted=False
    ).first()
    
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    if quote_update.status is not None:
        quote.status = quote_update.status
    if quote_update.title is not None:
        quote.title = quote_update.title
    if quote_update.description is not None:
        quote.description = quote_update.description
    
    db.commit()
    db.refresh(quote)
    
    return quote


@router.delete("/{quote_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_quote(
    quote_id: str,
    current_user: User = Depends(check_permission("quote:delete")),
    db: Session = Depends(get_db)
):
    """Soft delete quote"""
    quote = db.query(Quote).filter_by(
        id=quote_id,
        tenant_id=current_user.tenant_id,
        is_deleted=False
    ).first()
    
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    quote.is_deleted = True
    quote.deleted_at = datetime.utcnow()
    db.commit()
    
    return None
