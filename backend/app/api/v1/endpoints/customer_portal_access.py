#!/usr/bin/env python3
"""
Customer Portal Access Management API Endpoints
For managing customer portal access rights from tenant dashboard
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
import secrets
from datetime import datetime, timezone

from app.core.dependencies import get_db, get_current_user, check_permission
from app.models.crm import Customer
from app.models.tenant import User

router = APIRouter(prefix="/customers", tags=["Customer Portal Access"])


class PortalAccessUpdate(BaseModel):
    portal_access_enabled: Optional[bool] = None
    portal_permissions: Optional[dict] = None


class PortalAccessResponse(BaseModel):
    portal_access_enabled: bool
    portal_access_token: Optional[str] = None
    portal_access_token_generated_at: Optional[str] = None
    portal_permissions: Optional[dict] = None
    portal_login_url: Optional[str] = None


@router.post("/{customer_id}/portal-access/generate-token", response_model=PortalAccessResponse)
async def generate_portal_token(
    customer_id: str,
    current_user: User = Depends(check_permission("customer:update")),
    db: Session = Depends(get_db)
):
    """Generate a new portal access token for a customer"""
    customer = db.query(Customer).filter(
        Customer.id == customer_id,
        Customer.tenant_id == current_user.tenant_id,
        Customer.is_deleted == False
    ).first()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    # Generate secure token
    token = secrets.token_urlsafe(32)
    customer.portal_access_token = token
    customer.portal_access_token_generated_at = datetime.now(timezone.utc)
    customer.portal_access_enabled = True
    
    # Set default permissions if not set
    if not customer.portal_permissions:
        customer.portal_permissions = {
            "tickets": True,
            "quotes": True,
            "orders": True,
            "reporting": True
        }
    
    db.commit()
    db.refresh(customer)
    
    # Build portal login URL (will be configured based on deployment)
    portal_base_url = "http://localhost:3001"  # TODO: Get from config
    portal_login_url = f"{portal_base_url}/login?token={token}"
    
    return {
        "portal_access_enabled": customer.portal_access_enabled,
        "portal_access_token": customer.portal_access_token,
        "portal_access_token_generated_at": customer.portal_access_token_generated_at.isoformat() if customer.portal_access_token_generated_at else None,
        "portal_permissions": customer.portal_permissions,
        "portal_login_url": portal_login_url
    }


@router.get("/{customer_id}/portal-access", response_model=PortalAccessResponse)
async def get_portal_access(
    customer_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get customer portal access information"""
    customer = db.query(Customer).filter(
        Customer.id == customer_id,
        Customer.tenant_id == current_user.tenant_id,
        Customer.is_deleted == False
    ).first()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    portal_login_url = None
    if customer.portal_access_token:
        portal_base_url = "http://localhost:3001"  # TODO: Get from config
        portal_login_url = f"{portal_base_url}/login?token={customer.portal_access_token}"
    
    return {
        "portal_access_enabled": customer.portal_access_enabled,
        "portal_access_token": customer.portal_access_token if current_user.is_admin else None,  # Only admins see token
        "portal_access_token_generated_at": customer.portal_access_token_generated_at.isoformat() if customer.portal_access_token_generated_at else None,
        "portal_permissions": customer.portal_permissions,
        "portal_login_url": portal_login_url
    }


@router.put("/{customer_id}/portal-access", response_model=PortalAccessResponse)
async def update_portal_access(
    customer_id: str,
    access_update: PortalAccessUpdate,
    current_user: User = Depends(check_permission("customer:update")),
    db: Session = Depends(get_db)
):
    """Update customer portal access settings"""
    customer = db.query(Customer).filter(
        Customer.id == customer_id,
        Customer.tenant_id == current_user.tenant_id,
        Customer.is_deleted == False
    ).first()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    if access_update.portal_access_enabled is not None:
        customer.portal_access_enabled = access_update.portal_access_enabled
        
        # If disabling, clear token
        if not access_update.portal_access_enabled:
            customer.portal_access_token = None
            customer.portal_access_token_generated_at = None
    
    if access_update.portal_permissions is not None:
        customer.portal_permissions = access_update.portal_permissions
    
    db.commit()
    db.refresh(customer)
    
    portal_login_url = None
    if customer.portal_access_token:
        portal_base_url = "http://localhost:3001"  # TODO: Get from config
        portal_login_url = f"{portal_base_url}/login?token={customer.portal_access_token}"
    
    return {
        "portal_access_enabled": customer.portal_access_enabled,
        "portal_access_token": customer.portal_access_token,
        "portal_access_token_generated_at": customer.portal_access_token_generated_at.isoformat() if customer.portal_access_token_generated_at else None,
        "portal_permissions": customer.portal_permissions,
        "portal_login_url": portal_login_url
    }


@router.post("/{customer_id}/portal-access/revoke-token")
async def revoke_portal_token(
    customer_id: str,
    current_user: User = Depends(check_permission("customer:update")),
    db: Session = Depends(get_db)
):
    """Revoke customer portal access token"""
    customer = db.query(Customer).filter(
        Customer.id == customer_id,
        Customer.tenant_id == current_user.tenant_id,
        Customer.is_deleted == False
    ).first()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    customer.portal_access_token = None
    customer.portal_access_token_generated_at = None
    customer.portal_access_enabled = False
    
    db.commit()
    
    return {"message": "Portal access token revoked successfully"}

