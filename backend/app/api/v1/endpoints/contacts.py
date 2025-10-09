#!/usr/bin/env python3
"""
Contact management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel, EmailStr
import uuid
from datetime import datetime

from app.core.database import get_db
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
    email: EmailStr | None = None
    phone: str | None = None
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
    is_primary: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


@router.get("/customer/{customer_id}", response_model=List[ContactResponse])
async def list_customer_contacts(
    customer_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all contacts for a customer"""
    contacts = db.query(Contact).filter_by(
        customer_id=customer_id,
        tenant_id=current_user.tenant_id,
        is_deleted=False
    ).all()
    
    return contacts


@router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(
    contact_data: ContactCreate,
    current_user: User = Depends(check_permission("contact:create")),
    db: Session = Depends(get_db)
):
    """Create new contact"""
    
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
            notes=contact_data.notes,
            is_primary=contact_data.is_primary
        )
        
        db.add(contact)
        db.commit()
        db.refresh(contact)
        
        return contact
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating contact: {str(e)}"
        )


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: str,
    current_user: User = Depends(check_permission("contact:delete")),
    db: Session = Depends(get_db)
):
    """Soft delete contact"""
    contact = db.query(Contact).filter_by(
        id=contact_id,
        tenant_id=current_user.tenant_id,
        is_deleted=False
    ).first()
    
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    contact.is_deleted = True
    contact.deleted_at = datetime.utcnow()
    db.commit()
    
    return None
