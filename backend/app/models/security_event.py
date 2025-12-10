#!/usr/bin/env python3
"""
Security Event Model

SECURITY: Stores security-related events for monitoring and auditing.
"""

from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from .base import Base, TimestampMixin


class SecurityEventType(enum.Enum):
    """Types of security events"""
    FAILED_LOGIN = "failed_login"
    SUCCESSFUL_LOGIN = "successful_login"
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_UNLOCKED = "account_unlocked"
    PASSWORD_CHANGED = "password_changed"
    PASSWORD_RESET_REQUESTED = "password_reset_requested"
    PASSWORD_RESET_COMPLETED = "password_reset_completed"
    TWO_FACTOR_ENABLED = "two_factor_enabled"
    TWO_FACTOR_DISABLED = "two_factor_disabled"
    TWO_FACTOR_FAILED = "two_factor_failed"
    PASSWORDLESS_LOGIN_REQUESTED = "passwordless_login_requested"
    PASSWORDLESS_LOGIN_USED = "passwordless_login_used"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    CSRF_TOKEN_INVALID = "csrf_token_invalid"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    API_KEY_ACCESSED = "api_key_accessed"
    API_KEY_ROTATED = "api_key_rotated"
    PERMISSION_DENIED = "permission_denied"
    DATA_EXPORT = "data_export"
    DATA_DELETED = "data_deleted"
    CONFIGURATION_CHANGED = "configuration_changed"


class SecurityEventSeverity(enum.Enum):
    """Severity levels for security events"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SecurityEvent(Base, TimestampMixin):
    """
    Model to store security-related events for monitoring and auditing.
    """
    __tablename__ = "security_events"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    
    event_type = Column(SQLEnum(SecurityEventType), nullable=False, index=True)
    severity = Column(SQLEnum(SecurityEventSeverity), nullable=False, default=SecurityEventSeverity.MEDIUM, index=True)
    
    description = Column(Text, nullable=False)
    ip_address = Column(String(45), nullable=True, index=True)
    user_agent = Column(String(500), nullable=True)
    
    metadata = Column(Text, nullable=True)  # JSON string for additional event data
    resolved = Column(String(36), nullable=True)  # User ID who resolved the event (if applicable)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    occurred_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), index=True)
    
    # Relationships
    tenant = relationship("Tenant", backref="security_events")
    user = relationship("User", backref="security_events")
    
    def __repr__(self):
        return f"<SecurityEvent id={self.id} type={self.event_type.value} severity={self.severity.value} occurred_at={self.occurred_at}>"

