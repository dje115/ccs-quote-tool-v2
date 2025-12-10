-- Migration: Add user 2FA table
-- Purpose: Enable two-factor authentication using TOTP

CREATE TABLE IF NOT EXISTS user_2fa (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL UNIQUE,
    secret VARCHAR(255) NOT NULL,
    is_enabled BOOLEAN NOT NULL DEFAULT false,
    backup_codes VARCHAR(1000),
    last_used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_user_2fa_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_2fa_user ON user_2fa(user_id);
CREATE INDEX IF NOT EXISTS idx_user_2fa_enabled ON user_2fa(is_enabled);

COMMENT ON TABLE user_2fa IS 'Stores TOTP secrets for two-factor authentication';
COMMENT ON COLUMN user_2fa.secret IS 'TOTP secret key (base32 encoded)';
COMMENT ON COLUMN user_2fa.backup_codes IS 'JSON array of backup codes (hashed)';
COMMENT ON COLUMN user_2fa.is_enabled IS 'Whether 2FA is enabled for this user';

