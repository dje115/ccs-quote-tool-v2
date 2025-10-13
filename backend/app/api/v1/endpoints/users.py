#!/usr/bin/env python3
"""
User management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel, EmailStr
import uuid
from datetime import datetime

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_admin_user
from app.core.security import get_password_hash
from app.models.tenant import User, UserRole
from app.core.permissions import get_permissions_by_category, get_default_permissions

router = APIRouter()


# Pydantic schemas
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    first_name: str
    last_name: str
    password: str
    role: UserRole = UserRole.USER
    phone: str | None = None
    permissions: List[str] | None = None  # Optional custom permissions


class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    first_name: str
    last_name: str
    role: str
    permissions: List[str] | None = None
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    language: str | None = None
    timezone: str | None = None
    is_active: bool | None = None


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information"""
    return current_user


@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """List all users in current tenant (admin only)"""
    users = db.query(User).filter_by(
        tenant_id=current_user.tenant_id
    ).offset(skip).limit(limit).all()
    return users


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Create new user in current tenant (admin only)"""
    
    # Check if email already exists
    existing_user = db.query(User).filter_by(email=user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username already exists
    existing_username = db.query(User).filter_by(username=user_data.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    try:
        hashed_password = get_password_hash(user_data.password)
        
        # Use custom permissions if provided, otherwise use role defaults
        permissions = user_data.permissions if user_data.permissions is not None else get_default_permissions(user_data.role.value)
        
        user = User(
            id=str(uuid.uuid4()),
            tenant_id=current_user.tenant_id,
            email=user_data.email,
            username=user_data.username,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            hashed_password=hashed_password,
            is_active=True,
            is_verified=False,
            role=user_data.role,
            phone=user_data.phone,
            permissions=permissions
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating user: {str(e)}"
        )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Update user (admin only)"""
    user = db.query(User).filter_by(
        id=user_id,
        tenant_id=current_user.tenant_id
    ).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update fields
    if user_update.first_name is not None:
        user.first_name = user_update.first_name
    if user_update.last_name is not None:
        user.last_name = user_update.last_name
    if user_update.phone is not None:
        user.phone = user_update.phone
    if user_update.language is not None:
        user.language = user_update.language
    if user_update.timezone is not None:
        user.timezone = user_update.timezone
    if user_update.is_active is not None:
        user.is_active = user_update.is_active
    
    db.commit()
    db.refresh(user)
    
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Deactivate user (admin only)"""
    user = db.query(User).filter_by(
        id=user_id,
        tenant_id=current_user.tenant_id
    ).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Don't allow deleting yourself
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    # Soft delete - just deactivate
    user.is_active = False
    db.commit()
    
    return None


def _get_default_permissions(role: UserRole) -> List[str]:
    """Get default permissions for a role"""
    if role == UserRole.SUPER_ADMIN:
        return ["*"]  # All permissions
    elif role == UserRole.TENANT_ADMIN:
        return [
            "customer:create", "customer:read", "customer:update", "customer:delete",
            "lead:create", "lead:read", "lead:update", "lead:delete",
            "quote:create", "quote:read", "quote:update", "quote:delete",
            "user:create", "user:read", "user:update", "user:delete",
            "contact:create", "contact:read", "contact:update", "contact:delete",
            "tenant:read", "tenant:update"
        ]
    elif role == UserRole.MANAGER:
        return [
            "customer:create", "customer:read", "customer:update",
            "lead:create", "lead:read", "lead:update",
            "quote:create", "quote:read", "quote:update",
            "contact:create", "contact:read", "contact:update",
            "user:read"
        ]
    elif role == UserRole.SALES_REP:
        return [
            "customer:read", "customer:update",
            "lead:read", "lead:update",
            "quote:create", "quote:read", "quote:update",
            "contact:create", "contact:read", "contact:update"
        ]
    else:  # USER
        return [
            "customer:read",
            "lead:read",
            "quote:read",
            "contact:read"
        ]


@router.get("/permissions/available")
async def get_available_permissions(
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get all available permissions organized by category
    Admin only - used when creating/editing users
    """
    return {
        "permissions": get_permissions_by_category(),
        "roles": {
            "super_admin": "Super Admin (All Permissions)",
            "tenant_admin": "Tenant Admin",
            "manager": "Manager",
            "sales_rep": "Sales Representative",
            "user": "User (Read Only)"
        }
    }


@router.get("/permissions/defaults/{role}")
async def get_role_default_permissions(
    role: str,
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get default permissions for a specific role
    Admin only - used to pre-populate permission checkboxes
    """
    return {
        "role": role,
        "permissions": get_default_permissions(role)
    }
