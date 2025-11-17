#!/usr/bin/env python3
"""
FastAPI dependencies for authentication and database access
"""

from fastapi import Depends, HTTPException, status, Request, Cookie
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from jose import jwt

from app.core.config import settings
from app.core.database import get_db
from app.models.tenant import User, Tenant

# Security - HTTPBearer for Authorization header (backward compatibility)
security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    access_token_cookie: Optional[str] = Cookie(None, alias="access_token"),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token
    
    SECURITY: Supports both HttpOnly cookies (preferred) and Authorization header (backward compatibility).
    HttpOnly cookies prevent XSS attacks by making tokens inaccessible to JavaScript.
    """
    # Try to get token from cookie first (more secure)
    token = access_token_cookie
    
    # Fallback to Authorization header for backward compatibility
    if not token and credentials:
        token = credentials.credentials
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials - no token provided",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # Decode JWT token
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
        
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    
    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return user


async def get_current_tenant(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Tenant:
    """
    Get current tenant from authenticated user's JWT token.
    
    SECURITY: This enforces tenant isolation by:
    1. Deriving tenant from JWT token (current_user.tenant_id) - cannot be spoofed
    2. Validating any provided header/subdomain matches the JWT tenant
    3. Rejecting requests where header/subdomain doesn't match JWT tenant
    
    This prevents tenant impersonation attacks.
    """
    # Get tenant from JWT token (source of truth)
    jwt_tenant_id = current_user.tenant_id
    
    # Check if any tenant was provided in header/subdomain (from middleware)
    provided_tenant_id = getattr(request.state, 'tenant_id', None)
    
    # If tenant was provided via header/subdomain, it MUST match JWT tenant
    if provided_tenant_id and provided_tenant_id != jwt_tenant_id:
        # Log security violation
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(
            f"Tenant mismatch detected: JWT tenant={jwt_tenant_id}, "
            f"provided tenant={provided_tenant_id}, user={current_user.id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant mismatch: provided tenant does not match authenticated user's tenant"
        )
    
    # Get tenant from database
    tenant = db.query(Tenant).filter(Tenant.id == jwt_tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    # Set tenant in request state for RLS (if using row-level security)
    request.state.tenant_id = jwt_tenant_id
    request.state.db_tenant_id = jwt_tenant_id
    
    return tenant


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current admin user"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


async def get_current_super_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current super admin user"""
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required"
        )
    return current_user


def check_permission(permission: str):
    """
    Dependency factory to check if user has specific permission
    """
    async def permission_checker(current_user: User = Depends(get_current_user)):
        if permission not in current_user.permissions and not current_user.is_super_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
        return current_user
    
    return permission_checker

