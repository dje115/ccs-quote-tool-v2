#!/usr/bin/env python3
"""
Two-Factor Authentication Service

SECURITY: Handles TOTP (Time-based One-Time Password) generation and verification.
"""

import pyotp
import qrcode
import io
import base64
import secrets
import hashlib
from typing import Tuple, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.user_2fa import User2FA
from app.models.tenant import User


class TwoFactorService:
    """Service for managing 2FA operations"""
    
    @staticmethod
    def generate_secret() -> str:
        """Generate a new TOTP secret"""
        return pyotp.random_base32()
    
    @staticmethod
    def get_totp_uri(secret: str, email: str, issuer: str = "CCS Quote Tool") -> str:
        """
        Generate TOTP URI for QR code generation
        
        Args:
            secret: TOTP secret (base32)
            email: User's email address
            issuer: Application name
            
        Returns:
            TOTP URI string
        """
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(
            name=email,
            issuer_name=issuer
        )
    
    @staticmethod
    def generate_qr_code(uri: str) -> str:
        """
        Generate QR code as base64 data URL
        
        Args:
            uri: TOTP URI
            
        Returns:
            Base64-encoded data URL for QR code image
        """
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        img_base64 = base64.b64encode(buffer.read()).decode()
        return f"data:image/png;base64,{img_base64}"
    
    @staticmethod
    def verify_code(secret: str, code: str, window: int = 1) -> bool:
        """
        Verify a TOTP code
        
        Args:
            secret: TOTP secret (base32)
            code: 6-digit code from authenticator app
            window: Time window for verification (default: 1 = 30 seconds)
            
        Returns:
            True if code is valid, False otherwise
        """
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=window)
    
    @staticmethod
    def generate_backup_codes(count: int = 10) -> List[str]:
        """
        Generate backup codes for 2FA
        
        Args:
            count: Number of backup codes to generate
            
        Returns:
            List of backup codes (8-digit codes)
        """
        codes = []
        for _ in range(count):
            # Generate 8-digit code
            code = ''.join([str(secrets.randbelow(10)) for _ in range(8)])
            codes.append(code)
        return codes
    
    @staticmethod
    def hash_backup_code(code: str) -> str:
        """
        Hash a backup code for storage
        
        Args:
            code: Plain backup code
            
        Returns:
            SHA-256 hash of the code
        """
        return hashlib.sha256(code.encode()).hexdigest()
    
    @staticmethod
    def verify_backup_code(hashed_codes: str, code: str) -> bool:
        """
        Verify a backup code against hashed codes
        
        Args:
            hashed_codes: JSON string of hashed backup codes
            code: Plain backup code to verify
            
        Returns:
            True if code matches, False otherwise
        """
        import json
        
        if not hashed_codes:
            return False
        
        try:
            codes_list = json.loads(hashed_codes)
            code_hash = TwoFactorService.hash_backup_code(code)
            return code_hash in codes_list
        except (json.JSONDecodeError, TypeError):
            return False
    
    @staticmethod
    def get_user_2fa(db: Session, user_id: str) -> Optional[User2FA]:
        """Get user's 2FA configuration"""
        stmt = select(User2FA).where(User2FA.user_id == user_id)
        result = db.execute(stmt)
        return result.scalars().first()
    
    @staticmethod
    def is_2fa_enabled(db: Session, user_id: str) -> bool:
        """Check if 2FA is enabled for a user"""
        user_2fa = TwoFactorService.get_user_2fa(db, user_id)
        return user_2fa is not None and user_2fa.is_enabled

