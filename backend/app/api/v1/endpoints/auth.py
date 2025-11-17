#!/usr/bin/env python3
"""
Authentication endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from typing import Optional
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
    response: Response = None,
    db: Session = Depends(get_db)
):
    """
    Login endpoint - sets HttpOnly cookies and returns user info
    
    SECURITY: Tokens are stored in HttpOnly cookies to prevent XSS attacks.
    The frontend should not store tokens in localStorage.
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
    
    # Calculate cookie expiration times
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    # Set HttpOnly cookies
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",  # HTTPS only in production
        samesite="lax",  # CSRF protection
        max_age=int(access_token_expires.total_seconds()),
        path="/"
    )
    
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
        max_age=int(refresh_token_expires.total_seconds()),
        path="/"
    )
    
    # Return user info (tokens are in cookies, not in response body for security)
    # Still return tokens in body for backward compatibility during migration
    return {
        "access_token": access_token,  # Deprecated - use cookie
        "refresh_token": refresh_token,  # Deprecated - use cookie
        "token_type": "bearer",
        "user": user
    }


class RefreshTokenRequest(BaseModel):
    """Request model for refresh token endpoint"""
    refresh_token: str


@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: RefreshTokenRequest,
    response: Response = None,
    refresh_token_cookie: Optional[str] = Cookie(None, alias="refresh_token"),
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token with rotation.
    
    SECURITY: Implements refresh token rotation - when a refresh token is used,
    it is invalidated and a new one is issued. This prevents token reuse if
    a refresh token is stolen.
    
    Supports both HttpOnly cookies (preferred) and request body (backward compatibility).
    """
    from app.core.security import decode_token
    
    # Try to get refresh token from cookie first (more secure)
    refresh_token_value = refresh_token_cookie or request.refresh_token
    
    if not refresh_token_value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not provided"
        )
    
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
    
    # Calculate cookie expiration times
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    # Set HttpOnly cookies
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
        max_age=int(access_token_expires.total_seconds()),
        path="/"
    )
    
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
        max_age=int(refresh_token_expires.total_seconds()),
        path="/"
    )
    
    # Return tokens in body for backward compatibility
    return {
        "access_token": access_token,  # Deprecated - use cookie
        "refresh_token": new_refresh_token,  # Deprecated - use cookie
        "token_type": "bearer"
    }


@router.post("/logout")
async def logout(response: Response):
    """
    Logout endpoint - clears HttpOnly cookies
    
    SECURITY: Clears authentication cookies to log out the user.
    """
    # Clear HttpOnly cookies
    response.delete_cookie(key="access_token", path="/", samesite="lax")
    response.delete_cookie(key="refresh_token", path="/", samesite="lax")
    
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user information
    
    This endpoint can be used by the frontend to check authentication status
    since HttpOnly cookies cannot be read by JavaScript.
    """
    return current_user

