-- Migration: Add passwordless login tokens table
-- Purpose: Enable passwordless email link authentication

CREATE TABLE IF NOT EXISTS passwordless_login_tokens (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    token VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    used_at TIMESTAMP WITH TIME ZONE,
    is_used BOOLEAN NOT NULL DEFAULT false,
    ip_address VARCHAR(45),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_passwordless_token_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_passwordless_token_token ON passwordless_login_tokens(token);
CREATE INDEX IF NOT EXISTS idx_passwordless_token_email ON passwordless_login_tokens(email);
CREATE INDEX IF NOT EXISTS idx_passwordless_token_expires ON passwordless_login_tokens(expires_at);
CREATE INDEX IF NOT EXISTS idx_passwordless_token_user ON passwordless_login_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_passwordless_token_used ON passwordless_login_tokens(is_used);

-- Cleanup expired tokens (can be run periodically)
-- DELETE FROM passwordless_login_tokens WHERE expires_at < NOW() OR (is_used = true AND used_at < NOW() - INTERVAL '1 day');

COMMENT ON TABLE passwordless_login_tokens IS 'Stores temporary tokens for passwordless email link authentication';
COMMENT ON COLUMN passwordless_login_tokens.token IS 'Unique token for passwordless login (URL-safe)';
COMMENT ON COLUMN passwordless_login_tokens.expires_at IS 'Token expiration timestamp (default: 15 minutes)';
COMMENT ON COLUMN passwordless_login_tokens.is_used IS 'Whether the token has been used (prevents reuse)';

