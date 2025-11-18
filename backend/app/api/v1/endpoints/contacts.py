#!/usr/bin/env python3
"""
Contact management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from pydantic import BaseModel, EmailStr
import uuid
from datetime import datetime

from app.core.database import get_db, get_async_db
from app.core.dependencies import get_current_user, check_permission
from app.models.crm import Contact, ContactRole
from app.models.tenant import User

router = APIRouter()


class ContactCreate(BaseModel):
    customer_id: str
    first_name: str
    last_name: str
    job_title: str | None = None
    role: ContactRole = ContactRole.OTHER
    email: str | None = None  # Primary email
    phone: str | None = None  # Primary phone
    emails: list | None = None  # Additional emails
    phones: list | None = None  # Additional phones
    notes: str | None = None
    is_primary: bool = False


class ContactResponse(BaseModel):
    id: str
    customer_id: str
    first_name: str
    last_name: str
    job_title: str | None
    role: str
    email: str | None
    phone: str | None
    emails: list | None = None
    phones: list | None = None
    notes: str | None = None
    is_primary: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


@router.get("/customer/{customer_id}", response_model=List[ContactResponse])
async def list_customer_contacts(
    customer_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    List all contacts for a customer
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    from sqlalchemy import select
    
    stmt = select(Contact).where(
        Contact.customer_id == customer_id,
        Contact.tenant_id == current_user.tenant_id,
        Contact.is_deleted == False
    )
    result = await db.execute(stmt)
    contacts = result.scalars().all()
    
    return contacts


@router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(
    contact_data: ContactCreate,
    current_user: User = Depends(check_permission("contact:create")),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Create new contact
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    
    try:
        contact = Contact(
            id=str(uuid.uuid4()),
            tenant_id=current_user.tenant_id,
            customer_id=contact_data.customer_id,
            first_name=contact_data.first_name,
            last_name=contact_data.last_name,
            job_title=contact_data.job_title,
            role=contact_data.role,
            email=contact_data.email,
            phone=contact_data.phone,
            emails=contact_data.emails,
            phones=contact_data.phones,
            notes=contact_data.notes,
            is_primary=contact_data.is_primary
        )
        
        db.add(contact)
        await db.commit()
        await db.refresh(contact)
        
        return contact
        
    except Exception as e:
        await db.rollback()
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error creating contact: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating contact: {str(e)}"
        )


@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: str,
    contact_data: ContactCreate,
    current_user: User = Depends(check_permission("contact:update")),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Update contact
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    from sqlalchemy import select
    
    stmt = select(Contact).where(
        Contact.id == contact_id,
        Contact.tenant_id == current_user.tenant_id,
        Contact.is_deleted == False
    )
    result = await db.execute(stmt)
    contact = result.scalar_one_or_none()
    
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    # Update fields
    contact.first_name = contact_data.first_name
    contact.last_name = contact_data.last_name
    contact.job_title = contact_data.job_title
    contact.role = contact_data.role
    contact.email = contact_data.email
    contact.phone = contact_data.phone
    contact.emails = contact_data.emails
    contact.phones = contact_data.phones
    contact.notes = contact_data.notes
    contact.is_primary = contact_data.is_primary
    
    await db.commit()
    await db.refresh(contact)
    
    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: str,
    current_user: User = Depends(check_permission("contact:delete")),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Soft delete contact
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    from sqlalchemy import select
    
    stmt = select(Contact).where(
        Contact.id == contact_id,
        Contact.tenant_id == current_user.tenant_id,
        Contact.is_deleted == False
    )
    result = await db.execute(stmt)
    contact = result.scalar_one_or_none()
    
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    contact.is_deleted = True
    contact.deleted_at = datetime.utcnow()
    await db.commit()
    
    return None
