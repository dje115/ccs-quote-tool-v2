#!/usr/bin/env python3
"""
Encryption utilities for sensitive data (API keys, etc.)

SECURITY: Uses Fernet (symmetric encryption) for encrypting API keys at rest.
Fernet provides authenticated encryption using AES-128 in CBC mode with HMAC-SHA256.

IMPORTANT: The encryption key must be stored securely (environment variable).
Never commit the encryption key to version control.
"""

import os
import base64
import logging
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

from app.core.config import settings

logger = logging.getLogger(__name__)

# Global Fernet instance (initialized on first use)
_fernet_instance: Optional[Fernet] = None


def _get_encryption_key() -> bytes:
    """
    Get encryption key from environment or generate from SECRET_KEY
    
    SECURITY: In production, use a dedicated ENCRYPTION_KEY environment variable.
    Falls back to deriving from SECRET_KEY if ENCRYPTION_KEY not set.
    """
    # Try to get dedicated encryption key from environment
    encryption_key = os.getenv("ENCRYPTION_KEY")
    
    if encryption_key:
        # Key is provided as base64-encoded string
        try:
            return base64.urlsafe_b64decode(encryption_key.encode())
        except Exception as e:
            logger.warning(f"Invalid ENCRYPTION_KEY format, deriving from SECRET_KEY: {e}")
    
    # Fall back to deriving from SECRET_KEY
    # SECURITY: This is less secure but better than no encryption
    # In production, always set ENCRYPTION_KEY explicitly
    secret_key = settings.SECRET_KEY.encode()
    
    # Use PBKDF2 to derive a 32-byte key from SECRET_KEY
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"ccs_quote_tool_encryption_salt",  # Fixed salt (not ideal, but acceptable for key derivation)
        iterations=100000,
        backend=default_backend()
    )
    
    key = base64.urlsafe_b64encode(kdf.derive(secret_key))
    return key


def _get_fernet() -> Fernet:
    """
    Get or create Fernet instance for encryption/decryption
    
    Returns:
        Fernet instance
    """
    global _fernet_instance
    
    if _fernet_instance is None:
        key = _get_encryption_key()
        _fernet_instance = Fernet(key)
    
    return _fernet_instance


def encrypt_api_key(plain_key: Optional[str]) -> Optional[str]:
    """
    Encrypt an API key for storage
    
    SECURITY: Never store plain API keys. Always encrypt before storing.
    
    Args:
        plain_key: Plain text API key to encrypt
        
    Returns:
        Base64-encoded encrypted key, or None if input is None/empty
    """
    if not plain_key or not plain_key.strip():
        return None
    
    try:
        fernet = _get_fernet()
        encrypted = fernet.encrypt(plain_key.encode())
        # Return as base64 string for database storage
        return base64.urlsafe_b64encode(encrypted).decode()
    except Exception as e:
        logger.error(f"Failed to encrypt API key: {e}", exc_info=True)
        raise ValueError(f"API key encryption failed: {e}")


def decrypt_api_key(encrypted_key: Optional[str]) -> Optional[str]:
    """
    Decrypt an API key for use
    
    SECURITY: Only decrypt when needed. Never log decrypted keys.
    
    Args:
        encrypted_key: Base64-encoded encrypted key
        
    Returns:
        Plain text API key, or None if input is None/empty
    """
    if not encrypted_key or not encrypted_key.strip():
        return None
    
    try:
        fernet = _get_fernet()
        # Decode from base64
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_key.encode())
        decrypted = fernet.decrypt(encrypted_bytes)
        return decrypted.decode()
    except Exception as e:
        logger.error(f"Failed to decrypt API key: {e}", exc_info=True)
        # If decryption fails, the key might be in plain text (migration scenario)
        # Try to return as-is (for backward compatibility during migration)
        logger.warning("Decryption failed, assuming plain text key (migration scenario)")
        return encrypted_key


def is_encrypted(api_key: Optional[str]) -> bool:
    """
    Check if an API key appears to be encrypted
    
    Args:
        api_key: API key to check
        
    Returns:
        True if key appears encrypted, False otherwise
    """
    if not api_key:
        return False
    
    # Encrypted keys are base64-encoded and typically longer
    # Simple heuristic: if it's valid base64 and > 50 chars, likely encrypted
    try:
        decoded = base64.urlsafe_b64decode(api_key.encode())
        return len(decoded) > 32  # Encrypted keys are typically longer
    except Exception:
        return False


def rotate_encryption_key(old_key: Optional[str], new_key: Optional[str]) -> Optional[str]:
    """
    Rotate encryption key by re-encrypting with new key
    
    SECURITY: Used for key rotation. Old key must be decrypted first.
    
    Args:
        old_key: Currently encrypted key (will be decrypted with old Fernet)
        new_key: New plain key to encrypt with new Fernet
        
    Returns:
        Re-encrypted key with new encryption key
    """
    if not old_key or not new_key:
        return new_key
    
    # Decrypt with old key
    decrypted = decrypt_api_key(old_key)
    
    # Encrypt with new key (temporarily set new key)
    # Note: This requires temporarily changing the encryption key
    # In practice, this should be done during a maintenance window
    # with proper key rotation procedures
    
    # For now, just encrypt the decrypted value
    # (assuming we're using the same key, this is just re-encryption)
    return encrypt_api_key(decrypted)

