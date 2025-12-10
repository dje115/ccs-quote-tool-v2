#!/usr/bin/env python3
"""
Password security service for account lockout and password history

SECURITY: Implements account lockout after failed attempts and password history tracking.
"""

import logging
import uuid
from typing import Optional, List
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from app.models.tenant import User
from app.models.account_lockout import AccountLockout
from app.models.password_history import PasswordHistory
from app.core.security import verify_password, get_password_hash
from app.core.password_policy import validate_password, default_policy

logger = logging.getLogger(__name__)

# Configuration
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15
PASSWORD_HISTORY_COUNT = 5  # Prevent reuse of last 5 passwords


class PasswordSecurityService:
    """
    Service for password security features:
    - Account lockout after failed login attempts
    - Password history tracking to prevent reuse
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def check_account_locked(self, user_id: str) -> tuple[bool, Optional[str]]:
        """
        Check if account is locked
        
        Args:
            user_id: User ID to check
            
        Returns:
            Tuple of (is_locked: bool, reason: Optional[str])
        """
        lockout = self.db.query(AccountLockout).filter(
            AccountLockout.user_id == user_id
        ).first()
        
        if not lockout:
            return False, None
        
        # Check if lockout has expired
        if lockout.locked_until and lockout.locked_until > datetime.now(timezone.utc):
            remaining_minutes = int((lockout.locked_until - datetime.now(timezone.utc)).total_seconds() / 60)
            return True, f"Account locked due to {lockout.failed_attempts} failed login attempts. Try again in {remaining_minutes} minutes."
        
        # Lockout expired, clear it
        if lockout.locked_until:
            lockout.locked_until = None
            lockout.failed_attempts = 0
            lockout.lockout_reason = None
            self.db.commit()
        
        return False, None
    
    def record_failed_attempt(self, user_id: str, ip_address: Optional[str] = None, user_agent: Optional[str] = None):
        """
        Record a failed login attempt
        
        Args:
            user_id: User ID that failed login
            ip_address: Optional IP address
            user_agent: Optional user agent string
        """
        lockout = self.db.query(AccountLockout).filter(
            AccountLockout.user_id == user_id
        ).first()
        
        if not lockout:
            lockout = AccountLockout(
                id=str(uuid.uuid4()),
                user_id=user_id,
                failed_attempts=1,
                last_failed_attempt=datetime.now(timezone.utc)
            )
            self.db.add(lockout)
        else:
            lockout.failed_attempts += 1
            lockout.last_failed_attempt = datetime.now(timezone.utc)
            
            # Lock account if threshold reached
            if lockout.failed_attempts >= MAX_FAILED_ATTEMPTS:
                lockout.locked_until = datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
                lockout.lockout_reason = f"Account locked after {lockout.failed_attempts} failed login attempts"
                logger.warning(f"Account {user_id} locked after {lockout.failed_attempts} failed attempts")
                
                # Log security event for account lockout
                try:
                    from app.services.security_event_service import SecurityEventService
                    from app.models.security_event import SecurityEventType, SecurityEventSeverity
                    from app.models.tenant import User
                    
                    user = self.db.query(User).filter(User.id == user_id).first()
                    if user:
                        event_service = SecurityEventService(self.db)
                        event_service.log_event(
                            event_type=SecurityEventType.ACCOUNT_LOCKED,
                            description=f"Account locked after {lockout.failed_attempts} failed login attempts",
                            severity=SecurityEventSeverity.HIGH,
                            tenant_id=user.tenant_id,
                            user_id=user_id,
                            ip_address=ip_address,
                            user_agent=user_agent,
                            metadata={"failed_attempts": lockout.failed_attempts, "lockout_reason": lockout.lockout_reason}
                        )
                except Exception as e:
                    logger.error(f"Failed to log security event: {e}")
        
        # Log failed login attempt
        try:
            from app.services.security_event_service import SecurityEventService
            from app.models.security_event import SecurityEventType, SecurityEventSeverity
            from app.models.tenant import User
            
            user = self.db.query(User).filter(User.id == user_id).first()
            if user:
                event_service = SecurityEventService(self.db)
                event_service.log_event(
                    event_type=SecurityEventType.FAILED_LOGIN,
                    description="Failed login attempt",
                    severity=SecurityEventSeverity.MEDIUM,
                    tenant_id=user.tenant_id,
                    user_id=user_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    metadata={"failed_attempts": lockout.failed_attempts if lockout else 1}
                )
        except Exception as e:
            logger.error(f"Failed to log security event: {e}")
        
        self.db.commit()
    
    def clear_failed_attempts(self, user_id: str):
        """
        Clear failed attempts after successful login
        
        Args:
            user_id: User ID that successfully logged in
        """
        lockout = self.db.query(AccountLockout).filter(
            AccountLockout.user_id == user_id
        ).first()
        
        if lockout:
            lockout.failed_attempts = 0
            lockout.locked_until = None
            lockout.lockout_reason = None
            self.db.commit()
    
    def check_password_history(self, user_id: str, new_password: str) -> tuple[bool, Optional[str]]:
        """
        Check if password was used recently (prevent reuse)
        
        Args:
            user_id: User ID
            new_password: New password to check
            
        Returns:
            Tuple of (is_recent: bool, error_message: Optional[str])
        """
        # Get last N passwords
        stmt = select(PasswordHistory).where(
            PasswordHistory.user_id == user_id
        ).order_by(desc(PasswordHistory.set_at)).limit(PASSWORD_HISTORY_COUNT)
        
        result = self.db.execute(stmt)
        recent_passwords = result.scalars().all()
        
        # Check if new password matches any recent password
        for history_entry in recent_passwords:
            if verify_password(new_password, history_entry.password_hash):
                return True, f"Password cannot be reused. You must use a password that hasn't been used in your last {PASSWORD_HISTORY_COUNT} passwords."
        
        return False, None
    
    def save_password_to_history(self, user_id: str, password_hash: str):
        """
        Save password hash to history
        
        Args:
            user_id: User ID
            password_hash: Hashed password to save
        """
        import uuid
        
        history_entry = PasswordHistory(
            id=str(uuid.uuid4()),
            user_id=user_id,
            password_hash=password_hash,
            set_at=datetime.now(timezone.utc)
        )
        
        self.db.add(history_entry)
        
        # Keep only last N passwords (delete older ones)
        # Get all passwords for this user, ordered by set_at descending
        stmt = select(PasswordHistory).where(
            PasswordHistory.user_id == user_id
        ).order_by(desc(PasswordHistory.set_at))
        
        result = self.db.execute(stmt)
        all_entries = result.scalars().all()
        
        # Delete entries beyond the history limit
        if len(all_entries) > PASSWORD_HISTORY_COUNT:
            for entry in all_entries[PASSWORD_HISTORY_COUNT:]:
                self.db.delete(entry)
        
        self.db.commit()
    
    def validate_new_password(
        self,
        user: User,
        new_password: str,
        check_history: bool = True
    ) -> tuple[bool, List[str]]:
        """
        Validate new password against policy and history
        
        Args:
            user: User object
            new_password: New password to validate
            check_history: Whether to check password history
            
        Returns:
            Tuple of (is_valid: bool, errors: List[str])
        """
        errors = []
        
        # Check password policy
        is_valid, policy_errors = validate_password(
            new_password,
            username=user.username,
            email=user.email
        )
        
        if not is_valid:
            errors.extend(policy_errors)
        
        # Check password history
        if check_history:
            is_recent, history_error = self.check_password_history(user.id, new_password)
            if is_recent:
                errors.append(history_error)
        
        return len(errors) == 0, errors

