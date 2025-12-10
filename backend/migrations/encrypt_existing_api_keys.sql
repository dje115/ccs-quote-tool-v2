-- Migration: Encrypt existing API keys in database
-- Purpose: Encrypt all existing API keys at rest for security
-- 
-- IMPORTANT: This migration requires the encryption utility to be run via Python script
-- SQL cannot perform encryption, so we'll create a Python migration script instead.
-- 
-- This SQL file is a placeholder. The actual encryption will be done by:
-- backend/scripts/encrypt_existing_api_keys.py

-- Note: After encryption, all API keys will be stored as base64-encoded encrypted strings
-- The encryption utility handles backward compatibility (plain keys are auto-encrypted on first use)

COMMENT ON TABLE tenants IS 'API keys in tenants table will be encrypted by Python migration script';
COMMENT ON TABLE provider_api_keys IS 'API keys in provider_api_keys table will be encrypted by Python migration script';

