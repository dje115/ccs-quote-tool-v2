#!/usr/bin/env python3
"""
Migration script to encrypt existing API keys in the database

SECURITY: This script encrypts all existing plain-text API keys using Fernet encryption.
Keys are encrypted in-place, maintaining backward compatibility.

Usage:
    python backend/scripts/encrypt_existing_api_keys.py

IMPORTANT: 
- Backup database before running
- Run during maintenance window
- Test in development first
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.encryption import encrypt_api_key, is_encrypted, decrypt_api_key
from app.models.tenant import Tenant
from app.models.ai_provider import ProviderAPIKey
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def encrypt_tenant_api_keys(db: Session):
    """
    Encrypt API keys in tenants table
    """
    logger.info("Encrypting API keys in tenants table...")
    
    tenants = db.query(Tenant).all()
    encrypted_count = 0
    
    for tenant in tenants:
        updated = False
        
        # Encrypt OpenAI key
        if tenant.openai_api_key and not is_encrypted(tenant.openai_api_key):
            try:
                tenant.openai_api_key = encrypt_api_key(tenant.openai_api_key)
                updated = True
                encrypted_count += 1
                logger.info(f"Encrypted OpenAI key for tenant {tenant.name}")
            except Exception as e:
                logger.error(f"Failed to encrypt OpenAI key for tenant {tenant.name}: {e}")
        
        # Encrypt Companies House key
        if tenant.companies_house_api_key and not is_encrypted(tenant.companies_house_api_key):
            try:
                tenant.companies_house_api_key = encrypt_api_key(tenant.companies_house_api_key)
                updated = True
                encrypted_count += 1
                logger.info(f"Encrypted Companies House key for tenant {tenant.name}")
            except Exception as e:
                logger.error(f"Failed to encrypt Companies House key for tenant {tenant.name}: {e}")
        
        # Encrypt Google Maps key
        if tenant.google_maps_api_key and not is_encrypted(tenant.google_maps_api_key):
            try:
                tenant.google_maps_api_key = encrypt_api_key(tenant.google_maps_api_key)
                updated = True
                encrypted_count += 1
                logger.info(f"Encrypted Google Maps key for tenant {tenant.name}")
            except Exception as e:
                logger.error(f"Failed to encrypt Google Maps key for tenant {tenant.name}: {e}")
        
        if updated:
            db.add(tenant)
    
    db.commit()
    logger.info(f"Encrypted {encrypted_count} API keys in tenants table")


def encrypt_provider_api_keys(db: Session):
    """
    Encrypt API keys in provider_api_keys table
    """
    logger.info("Encrypting API keys in provider_api_keys table...")
    
    provider_keys = db.query(ProviderAPIKey).all()
    encrypted_count = 0
    
    for key in provider_keys:
        if key.api_key and not is_encrypted(key.api_key):
            try:
                key.api_key = encrypt_api_key(key.api_key)
                db.add(key)
                encrypted_count += 1
                logger.info(f"Encrypted API key for provider {key.provider_id}")
            except Exception as e:
                logger.error(f"Failed to encrypt API key for provider {key.provider_id}: {e}")
    
    db.commit()
    logger.info(f"Encrypted {encrypted_count} API keys in provider_api_keys table")


def main():
    """
    Main migration function
    """
    logger.info("Starting API key encryption migration...")
    logger.info("=" * 60)
    
    # Create database connection
    engine = create_engine(settings.DATABASE_URL)
    
    with Session(engine) as db:
        try:
            # Encrypt tenant API keys
            encrypt_tenant_api_keys(db)
            
            # Encrypt provider API keys
            encrypt_provider_api_keys(db)
            
            logger.info("=" * 60)
            logger.info("✅ Migration completed successfully!")
            logger.info("All API keys have been encrypted.")
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}", exc_info=True)
            db.rollback()
            sys.exit(1)


if __name__ == "__main__":
    main()

