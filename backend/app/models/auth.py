#!/usr/bin/env python3
"""
Authentication models for token management
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from .base import Base, TimestampMixin


class RefreshToken(Base, TimestampMixin):
    """
    Refresh token model for database-backed token storage
    
    SECURITY: Stores refresh tokens in database to enable:
    - Token revocation
    - Token family detection (prevent token reuse attacks)
    - Token rotation tracking
    - Audit logging
    """
    __tablename__ = "refresh_tokens"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    
    # Token details
    token_hash = Column(String(255), nullable=False, unique=True, index=True)  # Hashed token for storage
    token_family = Column(String(36), nullable=False, index=True)  # Token family ID for rotation tracking
    parent_token_id = Column(String(36), ForeignKey("refresh_tokens.id"), nullable=True)  # Previous token in rotation chain
    
    # Status
    is_revoked = Column(Boolean, default=False, nullable=False, index=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revoked_reason = Column(String(255), nullable=True)
    
    # Expiration
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    tenant = relationship("Tenant")
    user = relationship("User", foreign_keys="RefreshToken.user_id")
    parent_token = relationship("RefreshToken", remote_side="RefreshToken.id", backref="child_tokens")
    
    def __repr__(self):
        return f"<RefreshToken {self.id} for user {self.user_id}>"
    
    __table_args__ = (
        Index('idx_refresh_token_user_family', 'user_id', 'token_family'),
        Index('idx_refresh_token_tenant_user', 'tenant_id', 'user_id'),
        Index('idx_refresh_token_expires', 'expires_at'),
    )

