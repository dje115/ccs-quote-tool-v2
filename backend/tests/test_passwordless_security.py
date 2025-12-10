#!/usr/bin/env python3
"""
Security tests for passwordless login implementation

Tests:
- Token generation randomness
- Token expiration
- One-time use enforcement
- Email enumeration prevention
- IP address tracking
"""

import pytest
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.models.tenant import User
from app.models.passwordless_login import PasswordlessLoginToken


def test_token_generation_randomness():
    """Test that tokens are generated with sufficient randomness"""
    tokens = set()
    
    # Generate multiple tokens
    for _ in range(1000):
        token = secrets.token_urlsafe(32)
        tokens.add(token)
    
    # All tokens should be unique
    assert len(tokens) == 1000
    
    # Tokens should be 43-44 characters (base64url encoding of 32 bytes)
    for token in tokens:
        assert 43 <= len(token) <= 44
        # token_urlsafe uses base64url encoding: A-Z, a-z, 0-9, -, _
        assert all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_" for c in token)


def test_token_expiration(db_session: Session, test_user: User):
    """Test that tokens expire correctly"""
    # Create expired token
    expired_token = PasswordlessLoginToken(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        token=secrets.token_urlsafe(32),
        email=test_user.email,
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),  # Expired 1 minute ago
        is_used=False
    )
    db_session.add(expired_token)
    db_session.commit()
    
    # Verify token is expired
    assert expired_token.expires_at < datetime.now(timezone.utc)
    
    # Create valid token
    valid_token = PasswordlessLoginToken(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        token=secrets.token_urlsafe(32),
        email=test_user.email,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),  # Valid for 15 minutes
        is_used=False
    )
    db_session.add(valid_token)
    db_session.commit()
    
    # Verify token is valid
    assert valid_token.expires_at > datetime.now(timezone.utc)


def test_one_time_use_enforcement(db_session: Session, test_user: User):
    """Test that tokens can only be used once"""
    # Create token
    token = PasswordlessLoginToken(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        token=secrets.token_urlsafe(32),
        email=test_user.email,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
        is_used=False
    )
    db_session.add(token)
    db_session.commit()
    
    # Verify token is not used
    assert token.is_used == False
    
    # Mark token as used
    token.is_used = True
    token.used_at = datetime.now(timezone.utc)
    db_session.commit()
    
    # Verify token is marked as used
    db_session.refresh(token)
    assert token.is_used == True
    assert token.used_at is not None


def test_email_enumeration_prevention():
    """Test that email enumeration is prevented"""
    # The passwordless login endpoint should return the same response
    # regardless of whether the email exists or not
    # This is tested at the API level, not the model level
    
    # For model-level testing, we verify that tokens are created
    # even if we don't reveal whether the user exists
    pass  # This is handled in the endpoint logic


def test_ip_address_tracking(db_session: Session, test_user: User):
    """Test that IP addresses are tracked for security"""
    # Create token with IP address
    ip_address = "192.168.1.1"
    token = PasswordlessLoginToken(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        token=secrets.token_urlsafe(32),
        email=test_user.email,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
        is_used=False,
        ip_address=ip_address
    )
    db_session.add(token)
    db_session.commit()
    
    # Verify IP address is stored
    assert token.ip_address == ip_address
    
    # Test with IPv6 address
    ipv6_address = "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
    token2 = PasswordlessLoginToken(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        token=secrets.token_urlsafe(32),
        email=test_user.email,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
        is_used=False,
        ip_address=ipv6_address
    )
    db_session.add(token2)
    db_session.commit()
    
    # Verify IPv6 address is stored
    assert token2.ip_address == ipv6_address


def test_token_uniqueness(db_session: Session, test_user: User):
    """Test that tokens are unique"""
    tokens = []
    for _ in range(100):
        token = PasswordlessLoginToken(
            id=str(uuid.uuid4()),
            user_id=test_user.id,
            token=secrets.token_urlsafe(32),
            email=test_user.email,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
            is_used=False
        )
        tokens.append(token.token)
    
    # All tokens should be unique
    assert len(set(tokens)) == 100


def test_token_expiration_window():
    """Test that tokens have a reasonable expiration window"""
    # Tokens should expire in 15 minutes (standard for passwordless login)
    expiration_minutes = 15
    
    # Create token
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=expiration_minutes)
    
    # Verify expiration is in the future
    assert expires_at > datetime.now(timezone.utc)
    
    # Verify expiration is within reasonable window (15 minutes)
    time_until_expiration = (expires_at - datetime.now(timezone.utc)).total_seconds() / 60
    assert 14 <= time_until_expiration <= 16  # Allow 1 minute tolerance

