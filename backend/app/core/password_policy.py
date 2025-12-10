#!/usr/bin/env python3
"""
Password policy validation and enforcement

SECURITY: Implements password complexity requirements and validation.
"""

import re
import logging
from typing import List, Tuple, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class PasswordPolicy:
    """
    Password policy configuration and validation
    
    SECURITY: Enforces strong password requirements to prevent weak passwords.
    """
    
    def __init__(
        self,
        min_length: int = 12,
        require_uppercase: bool = True,
        require_lowercase: bool = True,
        require_digits: bool = True,
        require_special: bool = True,
        max_length: int = 128,
        prevent_common_passwords: bool = True,
        prevent_user_info: bool = True
    ):
        """
        Initialize password policy
        
        Args:
            min_length: Minimum password length (default: 12)
            require_uppercase: Require at least one uppercase letter
            require_lowercase: Require at least one lowercase letter
            require_digits: Require at least one digit
            require_special: Require at least one special character
            max_length: Maximum password length (default: 128)
            prevent_common_passwords: Prevent common weak passwords
            prevent_user_info: Prevent passwords containing username/email
        """
        self.min_length = min_length
        self.require_uppercase = require_uppercase
        self.require_lowercase = require_lowercase
        self.require_digits = require_digits
        self.require_special = require_special
        self.max_length = max_length
        self.prevent_common_passwords = prevent_common_passwords
        self.prevent_user_info = prevent_user_info
        
        # Common weak passwords to prevent
        self.common_passwords = {
            "password", "password123", "12345678", "123456789", "1234567890",
            "qwerty", "abc123", "letmein", "welcome", "admin", "root",
            "password1", "Password1", "Password123", "Admin123"
        }
    
    def validate(
        self,
        password: str,
        username: Optional[str] = None,
        email: Optional[str] = None
    ) -> Tuple[bool, List[str]]:
        """
        Validate password against policy
        
        Args:
            password: Password to validate
            username: Optional username (to check if password contains it)
            email: Optional email (to check if password contains it)
            
        Returns:
            Tuple of (is_valid: bool, errors: List[str])
        """
        errors = []
        
        # Check length
        if len(password) < self.min_length:
            errors.append(f"Password must be at least {self.min_length} characters long")
        
        if len(password) > self.max_length:
            errors.append(f"Password must be no more than {self.max_length} characters long")
        
        # Check character requirements
        if self.require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if self.require_lowercase and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if self.require_digits and not re.search(r'\d', password):
            errors.append("Password must contain at least one digit")
        
        if self.require_special and not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>/?]', password):
            errors.append("Password must contain at least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)")
        
        # Check for common passwords
        if self.prevent_common_passwords and password.lower() in self.common_passwords:
            errors.append("Password is too common. Please choose a more unique password.")
        
        # Check for user information
        if self.prevent_user_info:
            if username and username.lower() in password.lower():
                errors.append("Password cannot contain your username")
            
            if email:
                email_local = email.split('@')[0].lower()
                if email_local and email_local in password.lower():
                    errors.append("Password cannot contain your email address")
        
        # Removed repeated character check (too strict)
        # Removed sequential character check (too strict)
        
        return len(errors) == 0, errors
    
    def get_strength_score(self, password: str) -> int:
        """
        Calculate password strength score (0-100)
        
        Args:
            password: Password to score
            
        Returns:
            Strength score from 0 (weak) to 100 (very strong)
        """
        score = 0
        
        # Length score (max 40 points)
        length_score = min(40, len(password) * 2)
        score += length_score
        
        # Character variety (max 30 points)
        has_upper = bool(re.search(r'[A-Z]', password))
        has_lower = bool(re.search(r'[a-z]', password))
        has_digit = bool(re.search(r'\d', password))
        has_special = bool(re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>/?]', password))
        
        variety_count = sum([has_upper, has_lower, has_digit, has_special])
        score += variety_count * 7.5  # 7.5 points per variety type
        
        # Complexity bonus (max 30 points)
        # Check for mixed case, numbers, special chars in different positions
        if len(password) >= 12 and variety_count >= 3:
            score += 15
        
        if len(password) >= 16 and variety_count == 4:
            score += 15
        
        # Penalties
        if password.lower() in self.common_passwords:
            score -= 50  # Heavy penalty for common passwords
        
        # Ensure score is between 0 and 100
        return max(0, min(100, score))


# Default password policy instance (simplified)
default_policy = PasswordPolicy(
    min_length=8,  # Reduced from 12 to 8
    require_uppercase=True,
    require_lowercase=True,
    require_digits=True,
    require_special=False,  # Made optional - not required
    max_length=128,
    prevent_common_passwords=True,
    prevent_user_info=True
)


def validate_password(
    password: str,
    username: Optional[str] = None,
    email: Optional[str] = None,
    policy: Optional[PasswordPolicy] = None
) -> Tuple[bool, List[str]]:
    """
    Validate password against policy (convenience function)
    
    Args:
        password: Password to validate
        username: Optional username
        email: Optional email
        policy: Optional custom policy (uses default if not provided)
        
    Returns:
        Tuple of (is_valid: bool, errors: List[str])
    """
    if policy is None:
        policy = default_policy
    
    return policy.validate(password, username, email)


def get_password_strength(password: str) -> int:
    """
    Get password strength score (0-100)
    
    Args:
        password: Password to score
        
    Returns:
        Strength score from 0 (weak) to 100 (very strong)
    """
    return default_policy.get_strength_score(password)

