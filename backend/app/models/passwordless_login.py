#!/usr/bin/env python3
"""
Passwordless Login Token Model

SECURITY: Stores temporary tokens for passwordless email link authentication.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from .base import Base, TimestampMixin


class PasswordlessLoginToken(Base, TimestampMixin):
    """
    Model to store temporary tokens for passwordless email link authentication.
    Tokens expire after a set time period (default: 15 minutes).
    """
    __tablename__ = "passwordless_login_tokens"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    token = Column(String(255), nullable=False, unique=True, index=True)
    email = Column(String(255), nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    used_at = Column(DateTime(timezone=True), nullable=True)
    is_used = Column(Boolean, nullable=False, default=False, index=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 max length
    
    # Relationships
    user = relationship("User", back_populates="passwordless_tokens")
    
    def __repr__(self):
        return f"<PasswordlessLoginToken user_id={self.user_id} email={self.email} expires_at={self.expires_at}>"

