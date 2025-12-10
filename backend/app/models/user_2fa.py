#!/usr/bin/env python3
"""
User 2FA Model

SECURITY: Stores TOTP secrets for two-factor authentication.
"""

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from .base import Base, TimestampMixin


class User2FA(Base, TimestampMixin):
    """
    Model to store 2FA configuration for users.
    Uses TOTP (Time-based One-Time Password) standard.
    """
    __tablename__ = "user_2fa"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, unique=True, index=True)
    secret = Column(String(255), nullable=False)  # TOTP secret (encrypted in production)
    is_enabled = Column(Boolean, nullable=False, default=False, index=True)
    backup_codes = Column(String(1000), nullable=True)  # JSON array of backup codes (hashed)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="two_factor_auth")
    
    def __repr__(self):
        return f"<User2FA user_id={self.user_id} is_enabled={self.is_enabled}>"

