#!/usr/bin/env python3
"""
Password history model for tracking password changes

SECURITY: Prevents password reuse by tracking last N passwords per user.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from .base import Base, TimestampMixin


class PasswordHistory(Base, TimestampMixin):
    """
    Password history model for tracking password changes
    
    SECURITY: Stores hashed passwords to prevent reuse of last N passwords.
    Passwords are hashed using the same algorithm as User.hashed_password.
    """
    __tablename__ = "password_history"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    
    # Hashed password (same format as User.hashed_password)
    password_hash = Column(String(255), nullable=False)
    
    # When this password was set
    set_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), index=True)
    
    # Relationships
    user = relationship("User", back_populates="password_history")
    
    def __repr__(self):
        return f"<PasswordHistory {self.id} for user {self.user_id}>"
    
    __table_args__ = (
        Index('idx_password_history_user_set_at', 'user_id', 'set_at'),
    )

