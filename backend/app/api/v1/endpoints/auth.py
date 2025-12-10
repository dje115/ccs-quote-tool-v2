#!/usr/bin/env python3
"""
Authentication endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from datetime import timedelta, datetime
from typing import Optional
from pydantic import BaseModel, EmailStr

from app.core.database import get_async_db
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token
from app.core.config import settings
from app.core.dependencies import get_current_user
from app.models.tenant import User, Tenant

router = APIRouter()


@router.get("/csrf-token")
async def get_csrf_token(response: Response):
    """
    Get CSRF token for state-changing operations
    
    SECURITY: Returns a CSRF token that must be included in X-CSRF-Token header
    for all POST, PUT, DELETE, and PATCH requests.
    
    The token is also set as a cookie for automatic inclusion.
    """
    from app.core.csrf import CSRFProtection
    
    csrf_token = CSRFProtection.generate_token()
    
    # Set token in cookie
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=False,  # JavaScript needs to read this
        secure=settings.ENVIRONMENT == "production",
        samesite="strict",
        max_age=3600,  # 1 hour
        path="/"
    )
    
    return {"csrf_token": csrf_token}


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
    db: AsyncSession = Depends(get_async_db)
):
    """
    Login endpoint - sets HttpOnly cookies and returns user info
    
    SECURITY: Tokens are stored in HttpOnly cookies to prevent XSS attacks.
    The frontend should not store tokens in localStorage.
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    # Find user by email or username
    stmt = select(User).where(
        or_(
            User.email == form_data.username,
            User.username == form_data.username
        )
    )
    result = await db.execute(stmt)
    user = result.scalars().first()
    
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
    
    # Create database-backed refresh token
    from app.core.database import SessionLocal
    from app.services.refresh_token_service import create_refresh_token as create_db_refresh_token
    sync_db = SessionLocal()
    try:
        plain_refresh_token, db_refresh_token = create_db_refresh_token(
            db=sync_db,
            user_id=user.id,
            tenant_id=user.tenant_id
        )
        refresh_token = plain_refresh_token
    finally:
        sync_db.close()
    
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
    """Request model for refresh token endpoint
    
    SECURITY: refresh_token is optional to support HttpOnly cookie-only clients.
    If not provided in body, the endpoint will use the cookie value.
    """
    refresh_token: Optional[str] = None


@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: Optional[RefreshTokenRequest] = None,
    response: Response = None,
    refresh_token_cookie: Optional[str] = Cookie(None, alias="refresh_token"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Refresh access token using refresh token with rotation.
    
    SECURITY: Implements refresh token rotation - when a refresh token is used,
    it is invalidated and a new one is issued. This prevents token reuse if
    a refresh token is stolen.
    
    Supports both HttpOnly cookies (preferred) and request body (backward compatibility).
    If refresh_token is provided in both cookie and body, cookie takes precedence.
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    from app.core.security import decode_token
    
    # Try to get refresh token from cookie first (more secure), then from body
    refresh_token_value = refresh_token_cookie or (request.refresh_token if request else None)
    
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
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalars().first()
    
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
    
    # Validate refresh token against database
    from app.core.database import SessionLocal
    from app.services.refresh_token_service import (
        validate_refresh_token,
        create_refresh_token as create_db_refresh_token,
        revoke_refresh_token,
        revoke_token_family
    )
    
    sync_db = SessionLocal()
    try:
        # Validate the refresh token
        db_token = validate_refresh_token(
            db=sync_db,
            token=refresh_token_value,
            user_id=user_id
        )
        
        if not db_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or revoked refresh token"
            )
        
        # Check for token reuse (if parent token is being reused, it's an attack)
        if db_token.parent_token_id:
            # This token was created from a parent - check if parent is still valid
            parent = sync_db.query(RefreshToken).filter(
                RefreshToken.id == db_token.parent_token_id
            ).first()
            
            if parent and not parent.is_revoked:
                # Parent token still exists and is valid - this is token reuse attack!
                # Revoke entire token family
                revoke_token_family(
                    db=sync_db,
                    user_id=user_id,
                    token_family=db_token.token_family,
                    reason="Token reuse attack detected"
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token reuse detected - all tokens revoked"
                )
        
        # Revoke old token (rotation)
        revoke_refresh_token(
            db=sync_db,
            token=refresh_token_value,
            reason="Token rotated"
        )
        
        # Create new tokens
        access_token = create_access_token(data={"sub": user.id, "tenant_id": user.tenant_id})
        plain_new_refresh_token, new_db_token = create_db_refresh_token(
            db=sync_db,
            user_id=user.id,
            tenant_id=user.tenant_id,
            parent_token_id=db_token.id
        )
        new_refresh_token = plain_new_refresh_token
        
    finally:
        sync_db.close()
    
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

