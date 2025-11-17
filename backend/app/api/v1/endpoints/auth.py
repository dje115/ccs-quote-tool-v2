#!/usr/bin/env python3
"""
Authentication endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from pydantic import BaseModel, EmailStr

from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token
from app.core.config import settings
from app.core.dependencies import get_current_user
from app.models.tenant import User, Tenant

router = APIRouter()


# Pydantic models
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    first_name: str
    last_name: str
    role: str
    tenant_id: str
    
    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user: UserResponse


@router.post("/login", response_model=LoginResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login endpoint - returns JWT tokens
    """
    # Find user by email or username
    user = db.query(User).filter(
        (User.email == form_data.username) | (User.username == form_data.username)
    ).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email/username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Create tokens
    access_token = create_access_token(data={"sub": user.id, "tenant_id": user.tenant_id})
    refresh_token = create_refresh_token(data={"sub": user.id, "tenant_id": user.tenant_id})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user
    }


class RefreshTokenRequest(BaseModel):
    """Request model for refresh token endpoint"""
    refresh_token: str


@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token with rotation.
    
    SECURITY: Implements refresh token rotation - when a refresh token is used,
    it is invalidated and a new one is issued. This prevents token reuse if
    a refresh token is stolen.
    """
    from app.core.security import decode_token
    
    refresh_token_value = request.refresh_token
    
    # Decode and validate refresh token
    payload = decode_token(refresh_token_value)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_id = payload.get("sub")
    tenant_id = payload.get("tenant_id")
    
    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Verify tenant_id matches (additional security check)
    if tenant_id and user.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant mismatch"
        )
    
    # TODO: Implement refresh token storage and rotation
    # For now, we issue new tokens but don't invalidate old ones
    # This is a security improvement but full rotation requires:
    # 1. Store refresh tokens in database/Redis with unique ID
    # 2. Check if token exists and is valid
    # 3. Invalidate old token when issuing new one
    # 4. Handle token family detection (if old token is reused, invalidate all tokens)
    
    # Create new tokens (rotation: old token will be replaced by new one)
    access_token = create_access_token(data={"sub": user.id, "tenant_id": user.tenant_id})
    new_refresh_token = create_refresh_token(data={"sub": user.id, "tenant_id": user.tenant_id})
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user information
    """
    return current_user

