#!/usr/bin/env python3
"""
Refresh token service for database-backed token management

SECURITY: Implements token rotation, family detection, and revocation
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_

from app.models.auth import RefreshToken
from app.core.config import settings
from app.core.security import create_refresh_token as create_jwt_refresh_token


def hash_token(token: str) -> str:
    """
    Hash a token for storage (SHA-256)
    
    SECURITY: Never store plain tokens - always hash them
    """
    return hashlib.sha256(token.encode()).hexdigest()


def generate_token_family() -> str:
    """
    Generate a unique token family ID
    
    All tokens from the same login session share the same family ID
    """
    return secrets.token_urlsafe(32)


def create_refresh_token(
    db: Session,
    user_id: str,
    tenant_id: str,
    parent_token_id: Optional[str] = None
) -> Tuple[str, RefreshToken]:
    """
    Create a new refresh token and store it in the database
    
    Args:
        db: Database session
        user_id: User ID
        tenant_id: Tenant ID
        parent_token_id: Optional parent token ID for rotation
        
    Returns:
        Tuple of (plain_token, RefreshToken model)
    """
    # Create JWT refresh token
    token_data = {"sub": user_id, "tenant_id": tenant_id}
    plain_token = create_jwt_refresh_token(token_data)
    
    # Hash token for storage
    token_hash = hash_token(plain_token)
    
    # Get or create token family
    if parent_token_id:
        # Get family from parent token
        parent = db.query(RefreshToken).filter(RefreshToken.id == parent_token_id).first()
        token_family = parent.token_family if parent else generate_token_family()
    else:
        # New login - create new family
        token_family = generate_token_family()
    
    # Calculate expiration
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    # Create database record
    refresh_token = RefreshToken(
        tenant_id=tenant_id,
        user_id=user_id,
        token_hash=token_hash,
        token_family=token_family,
        parent_token_id=parent_token_id,
        expires_at=expires_at,
        is_revoked=False
    )
    
    db.add(refresh_token)
    db.commit()
    db.refresh(refresh_token)
    
    return plain_token, refresh_token


def validate_refresh_token(
    db: Session,
    token: str,
    user_id: Optional[str] = None
) -> Optional[RefreshToken]:
    """
    Validate a refresh token against the database
    
    Args:
        db: Database session
        token: Plain refresh token
        user_id: Optional user ID for additional validation
        
    Returns:
        RefreshToken model if valid, None otherwise
    """
    # Hash the token
    token_hash = hash_token(token)
    
    # Find token in database
    stmt = select(RefreshToken).where(
        and_(
            RefreshToken.token_hash == token_hash,
            RefreshToken.is_revoked == False,
            RefreshToken.expires_at > datetime.now(timezone.utc)
        )
    )
    
    if user_id:
        stmt = stmt.where(RefreshToken.user_id == user_id)
    
    result = db.execute(stmt)
    refresh_token = result.scalar_one_or_none()
    
    if refresh_token:
        # Update last used timestamp
        refresh_token.last_used_at = datetime.now(timezone.utc)
        db.commit()
    
    return refresh_token


def revoke_refresh_token(
    db: Session,
    token: str,
    reason: Optional[str] = None
) -> bool:
    """
    Revoke a refresh token
    
    Args:
        db: Database session
        token: Plain refresh token
        reason: Optional revocation reason
        
    Returns:
        True if token was revoked, False if not found
    """
    token_hash = hash_token(token)
    
    refresh_token = db.query(RefreshToken).filter(
        RefreshToken.token_hash == token_hash
    ).first()
    
    if refresh_token and not refresh_token.is_revoked:
        refresh_token.is_revoked = True
        refresh_token.revoked_at = datetime.now(timezone.utc)
        refresh_token.revoked_reason = reason
        db.commit()
        return True
    
    return False


def revoke_token_family(
    db: Session,
    user_id: str,
    token_family: str,
    reason: Optional[str] = None
) -> int:
    """
    Revoke all tokens in a token family (detect token reuse attack)
    
    Args:
        db: Database session
        user_id: User ID
        token_family: Token family ID
        reason: Optional revocation reason
        
    Returns:
        Number of tokens revoked
    """
    tokens = db.query(RefreshToken).filter(
        and_(
            RefreshToken.user_id == user_id,
            RefreshToken.token_family == token_family,
            RefreshToken.is_revoked == False
        )
    ).all()
    
    count = 0
    for token in tokens:
        token.is_revoked = True
        token.revoked_at = datetime.now(timezone.utc)
        token.revoked_reason = reason or "Token family revoked - possible reuse attack"
        count += 1
    
    if count > 0:
        db.commit()
    
    return count


def revoke_all_user_tokens(
    db: Session,
    user_id: str,
    reason: Optional[str] = None
) -> int:
    """
    Revoke all refresh tokens for a user (e.g., on password change)
    
    Args:
        db: Database session
        user_id: User ID
        reason: Optional revocation reason
        
    Returns:
        Number of tokens revoked
    """
    tokens = db.query(RefreshToken).filter(
        and_(
            RefreshToken.user_id == user_id,
            RefreshToken.is_revoked == False
        )
    ).all()
    
    count = 0
    for token in tokens:
        token.is_revoked = True
        token.revoked_at = datetime.now(timezone.utc)
        token.revoked_reason = reason or "All tokens revoked"
        count += 1
    
    if count > 0:
        db.commit()
    
    return count


def cleanup_expired_tokens(db: Session) -> int:
    """
    Clean up expired tokens (maintenance task)
    
    Args:
        db: Database session
        
    Returns:
        Number of tokens deleted
    """
    from datetime import datetime, timezone
    
    expired_tokens = db.query(RefreshToken).filter(
        RefreshToken.expires_at < datetime.now(timezone.utc)
    ).all()
    
    count = len(expired_tokens)
    for token in expired_tokens:
        db.delete(token)
    
    if count > 0:
        db.commit()
    
    return count

