#!/usr/bin/env python3
"""
Account lockout model for tracking failed login attempts

SECURITY: Implements account lockout after N failed login attempts.
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from .base import Base, TimestampMixin


class AccountLockout(Base, TimestampMixin):
    """
    Account lockout model for tracking failed login attempts
    
    SECURITY: Tracks failed login attempts and locks accounts after threshold.
    """
    __tablename__ = "account_lockouts"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, unique=True, index=True)
    
    # Failed attempt tracking
    failed_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime(timezone=True), nullable=True, index=True)
    last_failed_attempt = Column(DateTime(timezone=True), nullable=True)
    
    # Lockout reason (for audit)
    lockout_reason = Column(String(255), nullable=True)
    
    # Relationships
    user = relationship("User", backref="lockout_info", uselist=False)
    
    def __repr__(self):
        return f"<AccountLockout {self.id} for user {self.user_id} (attempts: {self.failed_attempts})>"
    
    __table_args__ = (
        Index('idx_lockout_user_locked', 'user_id', 'locked_until'),
    )

