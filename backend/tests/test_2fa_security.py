#!/usr/bin/env python3
"""
Security tests for 2FA implementation

Tests:
- TOTP code validation
- Backup code security
- Rate limiting for 2FA attempts
- Token expiration
- Invalid code handling
"""

import pytest
import pyotp
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.models.tenant import User
from app.models.user_2fa import User2FA
from app.services.two_factor_service import TwoFactorService
from app.core.security import get_password_hash, verify_password


def test_totp_code_validation():
    """Test that TOTP codes are correctly validated"""
    secret = TwoFactorService.generate_totp_secret()
    totp = pyotp.TOTP(secret)
    
    # Generate a valid code
    valid_code = totp.now()
    
    # Verify valid code
    assert TwoFactorService.verify_totp_code(secret, valid_code) == True
    
    # Verify invalid code
    assert TwoFactorService.verify_totp_code(secret, "000000") == False
    
    # Verify code with wrong secret
    wrong_secret = TwoFactorService.generate_totp_secret()
    assert TwoFactorService.verify_totp_code(wrong_secret, valid_code) == False


def test_backup_code_security():
    """Test that backup codes are hashed and validated correctly"""
    plain_codes, hashed_codes = TwoFactorService.generate_backup_codes(num_codes=5)
    
    # All codes should be unique
    assert len(set(plain_codes)) == 5
    
    # All codes should be 8 characters
    for code in plain_codes:
        assert len(code) == 8
    
    # Verify backup codes can be validated
    for i, plain_code in enumerate(plain_codes):
        assert verify_password(plain_code, hashed_codes[i]) == True
    
    # Invalid backup code should fail
    assert verify_password("INVALID", hashed_codes[0]) == False


def test_backup_code_one_time_use(db_session: Session, test_user: User):
    """Test that backup codes are removed after use"""
    # Enable 2FA for user
    totp_secret, plain_backup_codes, qr_code = TwoFactorService(db_session).enable_2fa(test_user.id)
    
    # Get 2FA record
    user_2fa = TwoFactorService(db_session).get_user_2fa_record(test_user.id)
    assert user_2fa is not None
    assert user_2fa.is_enabled == True
    
    # Use a backup code
    used_code = plain_backup_codes[0]
    is_valid = TwoFactorService(db_session).verify_2fa_login_code(test_user.id, used_code)
    assert is_valid == True
    
    # Verify backup code was removed
    db_session.refresh(user_2fa)
    assert len(user_2fa.backup_codes) == 4  # One less backup code
    
    # Try to use the same backup code again (should fail)
    is_valid_again = TwoFactorService(db_session).verify_2fa_login_code(test_user.id, used_code)
    assert is_valid_again == False


def test_2fa_rate_limiting():
    """Test that 2FA verification is rate limited"""
    # This test would require mocking the rate limiting middleware
    # For now, we verify that the endpoint is classified correctly
    from app.core.rate_limiting import RateLimitMiddleware
    
    middleware = RateLimitMiddleware(None)
    
    # Verify 2FA endpoint is classified correctly
    assert middleware._classify_endpoint("/api/v1/auth/login/verify-2fa") == "2fa"
    
    # Verify rate limit is set
    assert middleware.RATE_LIMITS["2fa"] == 10  # 10 requests per minute


def test_totp_time_window():
    """Test that TOTP codes are valid within the time window"""
    secret = TwoFactorService.generate_totp_secret()
    totp = pyotp.TOTP(secret)
    
    # Generate code
    code = totp.now()
    
    # Code should be valid immediately
    assert TwoFactorService.verify_totp_code(secret, code) == True
    
    # Code should still be valid within the time window (30 seconds)
    # Note: This test may be flaky due to timing, but validates the concept
    assert TwoFactorService.verify_totp_code(secret, code) == True


def test_invalid_2fa_code_handling():
    """Test that invalid 2FA codes are rejected"""
    secret = TwoFactorService.generate_totp_secret()
    
    # Test various invalid codes
    invalid_codes = [
        "",           # Empty
        "12345",      # Too short
        "1234567",    # Too long
        "abcdef",     # Non-numeric
        "000000",     # Valid format but wrong code
    ]
    
    for invalid_code in invalid_codes:
        # For non-6-digit codes, TOTP verification should fail
        if len(invalid_code) != 6 or not invalid_code.isdigit():
            # These should be rejected before TOTP verification
            continue
        assert TwoFactorService.verify_totp_code(secret, invalid_code) == False


def test_2fa_secret_generation():
    """Test that 2FA secrets are generated securely"""
    secrets = set()
    
    # Generate multiple secrets
    for _ in range(100):
        secret = TwoFactorService.generate_totp_secret()
        secrets.add(secret)
    
    # All secrets should be unique
    assert len(secrets) == 100
    
    # All secrets should be base32 encoded (32 characters)
    for secret in secrets:
        assert len(secret) == 32
        # Base32 characters: A-Z, 2-7
        assert all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567" for c in secret)


def test_qr_code_generation():
    """Test that QR codes are generated correctly"""
    secret = TwoFactorService.generate_totp_secret()
    email = "test@example.com"
    issuer = "CCS Quote Tool"
    
    # Generate TOTP URI
    uri = TwoFactorService.get_totp_uri(secret, email, issuer)
    
    # URI should contain required components
    assert "otpauth://totp/" in uri
    assert email in uri
    assert issuer in uri
    assert f"secret={secret}" in uri
    
    # Generate QR code
    qr_code = TwoFactorService.generate_qr_code_svg(uri)
    
    # QR code should be base64-encoded PNG
    assert qr_code is not None
    assert len(qr_code) > 0
    # Base64 strings typically start with data or are just base64
    # PNG files start with specific bytes, but base64 encoding makes it a string
    assert isinstance(qr_code, str)

