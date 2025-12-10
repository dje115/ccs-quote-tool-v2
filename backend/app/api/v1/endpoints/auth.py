#!/usr/bin/env python3
"""
Authentication endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie, Request
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from datetime import timedelta, datetime
from typing import Optional
from pydantic import BaseModel, EmailStr
import uuid

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


class Login2FARequiredResponse(BaseModel):
    requires_2fa: bool = True
    temp_token: str  # Temporary token to use for 2FA verification
    message: str = "Two-factor authentication required"


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
    
    # Check account lockout before password verification
    if user:
        from app.core.database import SessionLocal
        from app.services.password_security_service import PasswordSecurityService
        
        sync_db = SessionLocal()
        try:
            password_service = PasswordSecurityService(sync_db)
            is_locked, lockout_reason = password_service.check_account_locked(user.id)
            
            if is_locked:
                raise HTTPException(
                    status_code=status.HTTP_423_LOCKED,
                    detail=lockout_reason or "Account is locked due to multiple failed login attempts"
                )
        finally:
            sync_db.close()
    
    # Verify password
    if not user or not verify_password(form_data.password, user.hashed_password):
        # Record failed attempt if user exists
        if user:
            from app.core.database import SessionLocal
            from app.services.password_security_service import PasswordSecurityService
            
            sync_db = SessionLocal()
            try:
                password_service = PasswordSecurityService(sync_db)
                password_service.record_failed_attempt(user.id)
            finally:
                sync_db.close()
        
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
    
    # Clear failed attempts on successful login
    from app.core.database import SessionLocal
    from app.services.password_security_service import PasswordSecurityService
    
    sync_db = SessionLocal()
    try:
        password_service = PasswordSecurityService(sync_db)
        password_service.clear_failed_attempts(user.id)
    finally:
        sync_db.close()
    
    # Check if 2FA is enabled
    from app.core.database import SessionLocal
    from app.services.two_factor_service import TwoFactorService
    
    sync_db = SessionLocal()
    try:
        if TwoFactorService.is_2fa_enabled(sync_db, user.id):
            # Generate temporary token for 2FA verification (stored in Redis, expires in 5 minutes)
            import secrets
            from app.core.redis import get_redis
            from fastapi.responses import JSONResponse
            
            temp_token = secrets.token_urlsafe(32)
            redis_client = await get_redis()
            await redis_client.setex(
                f"2fa_temp_token:{temp_token}",
                300,  # 5 minutes
                f"{user.id}:{user.tenant_id}"
            )
            
            # Return 2FA required response
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "requires_2fa": True,
                    "temp_token": temp_token,
                    "message": "Two-factor authentication required"
                }
            )
    finally:
        sync_db.close()
    
    # Create tokens (2FA not required or already verified)
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


# Passwordless login models
class PasswordlessLoginRequest(BaseModel):
    email: EmailStr


class PasswordlessLoginVerify(BaseModel):
    token: str


@router.post("/passwordless/request")
async def request_passwordless_login(
    request_data: PasswordlessLoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Request passwordless login - sends email with magic link
    
    SECURITY: Generates a secure token and sends it via email.
    Token expires in 15 minutes and can only be used once.
    """
    import secrets
    from datetime import timedelta
    from app.models.passwordless_login import PasswordlessLoginToken
    from app.services.email_service import get_email_service
    
    # Find user by email
    stmt = select(User).where(User.email == request_data.email)
    result = await db.execute(stmt)
    user = result.scalars().first()
    
    # Don't reveal if user exists (security best practice)
    if not user or not user.is_active:
        # Return success even if user doesn't exist (prevents email enumeration)
        return {"message": "If an account exists with this email, a login link has been sent."}
    
    # Generate secure token
    token = secrets.token_urlsafe(32)
    
    # Create token record (expires in 15 minutes)
    expires_at = datetime.utcnow() + timedelta(minutes=15)
    login_token = PasswordlessLoginToken(
        id=str(uuid.uuid4()),
        user_id=user.id,
        token=token,
        email=user.email,
        expires_at=expires_at,
        ip_address=request.client.host if request.client else None
    )
    
    db.add(login_token)
    await db.commit()
    
    # Send email with magic link
    email_service = get_email_service()
    login_url = f"{settings.CORS_ORIGINS[0] if settings.CORS_ORIGINS else 'http://localhost:3000'}/login/passwordless?token={token}"
    
    email_body = f"""
    <html>
    <body>
        <h2>Passwordless Login</h2>
        <p>Hello {user.first_name},</p>
        <p>Click the link below to log in to your account:</p>
        <p><a href="{login_url}" style="background-color: #1976d2; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Login</a></p>
        <p>Or copy and paste this link into your browser:</p>
        <p>{login_url}</p>
        <p><strong>This link will expire in 15 minutes.</strong></p>
        <p>If you didn't request this login link, please ignore this email.</p>
    </body>
    </html>
    """
    
    await email_service.send_email(
        to=user.email,
        subject="Your Login Link - CCS Quote Tool",
        body=email_body,
        body_html=email_body
    )
    
    return {"message": "If an account exists with this email, a login link has been sent."}


@router.post("/passwordless/verify", response_model=LoginResponse)
async def verify_passwordless_login(
    verify_data: PasswordlessLoginVerify,
    response: Response,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Verify passwordless login token and log user in
    
    SECURITY: Validates token, checks expiration, and prevents reuse.
    """
    from app.models.passwordless_login import PasswordlessLoginToken
    from datetime import timezone
    
    # Find token
    stmt = select(PasswordlessLoginToken).where(
        PasswordlessLoginToken.token == verify_data.token
    )
    result = await db.execute(stmt)
    login_token = result.scalars().first()
    
    if not login_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired login link"
        )
    
    # Check if already used
    if login_token.is_used:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This login link has already been used"
        )
    
    # Check expiration
    if login_token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This login link has expired"
        )
    
    # Get user
    user_stmt = select(User).where(User.id == login_token.user_id)
    user_result = await db.execute(user_stmt)
    user = user_result.scalars().first()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive"
        )
    
    # Mark token as used
    login_token.is_used = True
    login_token.used_at = datetime.now(timezone.utc)
    await db.commit()
    
    # Create tokens (same as regular login)
    access_token = create_access_token(data={"sub": user.id, "tenant_id": user.tenant_id})
    refresh_token = create_refresh_token(data={"sub": user.id, "tenant_id": user.tenant_id})
    
    # Store refresh token in database
    from app.core.database import SessionLocal
    from app.models.auth import RefreshToken as DBRefreshToken
    
    sync_db = SessionLocal()
    try:
        db_refresh_token = DBRefreshToken(
            id=str(uuid.uuid4()),
            user_id=user.id,
            tenant_id=user.tenant_id,
            token=refresh_token,
            expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            token_family=str(uuid.uuid4())
        )
        sync_db.add(db_refresh_token)
        sync_db.commit()
    finally:
        sync_db.close()
    
    # Set HttpOnly cookies
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
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
        value=refresh_token,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
        max_age=int(refresh_token_expires.total_seconds()),
        path="/"
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user
    }


class Verify2FARequest(BaseModel):
    temp_token: str
    code: str  # 6-digit TOTP code or backup code


@router.post("/login/verify-2fa", response_model=LoginResponse)
async def verify_2fa_login(
    verify_data: Verify2FARequest,
    response: Response,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Verify 2FA code and complete login
    
    SECURITY: Verifies TOTP code or backup code and completes authentication.
    """
    from app.core.redis import get_redis
    from app.core.database import SessionLocal
    from app.services.two_factor_service import TwoFactorService
    from app.models.user_2fa import User2FA
    
    # Get user info from temporary token
    redis_client = await get_redis()
    token_data = await redis_client.get(f"2fa_temp_token:{verify_data.temp_token}")
    
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired temporary token"
        )
    
    # Parse user_id and tenant_id from token data
    user_id, tenant_id = token_data.decode().split(":")
    
    # Get user
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalars().first()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Get 2FA configuration
    sync_db = SessionLocal()
    try:
        user_2fa = TwoFactorService.get_user_2fa(sync_db, user.id)
        
        if not user_2fa or not user_2fa.is_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA is not enabled for this user"
            )
        
        # Verify code (try TOTP first, then backup codes)
        code_valid = False
        
        # Try TOTP code
        if len(verify_data.code) == 6 and verify_data.code.isdigit():
            code_valid = TwoFactorService.verify_code(user_2fa.secret, verify_data.code)
        
        # Try backup code if TOTP failed
        if not code_valid and user_2fa.backup_codes:
            code_valid = TwoFactorService.verify_backup_code(user_2fa.backup_codes, verify_data.code)
            if code_valid:
                # Remove used backup code
                import json
                codes_list = json.loads(user_2fa.backup_codes)
                code_hash = TwoFactorService.hash_backup_code(verify_data.code)
                codes_list = [c for c in codes_list if c != code_hash]
                user_2fa.backup_codes = json.dumps(codes_list) if codes_list else None
                sync_db.add(user_2fa)
                sync_db.commit()
        
        if not code_valid:
            # Delete temporary token on failed verification
            await redis_client.delete(f"2fa_temp_token:{verify_data.temp_token}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid 2FA code"
            )
        
        # Update last used timestamp
        user_2fa.last_used_at = datetime.utcnow()
        sync_db.add(user_2fa)
        sync_db.commit()
    finally:
        sync_db.close()
    
    # Delete temporary token
    await redis_client.delete(f"2fa_temp_token:{verify_data.temp_token}")
    
    # Create tokens
    access_token = create_access_token(data={"sub": user.id, "tenant_id": user.tenant_id})
    
    # Create database-backed refresh token
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
    
    # Set HttpOnly cookies
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
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
        value=refresh_token,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
        max_age=int(refresh_token_expires.total_seconds()),
        path="/"
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user
    }

