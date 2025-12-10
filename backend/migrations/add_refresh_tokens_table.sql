-- Migration: Add refresh_tokens table for database-backed token storage
-- Purpose: Enable token revocation, rotation tracking, and security auditing

CREATE TABLE IF NOT EXISTS refresh_tokens (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    
    -- Token details
    token_hash VARCHAR(255) NOT NULL UNIQUE,
        token_family VARCHAR(255) NOT NULL,
    parent_token_id VARCHAR(36),
    
    -- Status
    is_revoked BOOLEAN NOT NULL DEFAULT FALSE,
    revoked_at TIMESTAMP WITH TIME ZONE,
    revoked_reason VARCHAR(255),
    
    -- Expiration
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    last_used_at TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_refresh_token_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
    CONSTRAINT fk_refresh_token_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_refresh_token_parent FOREIGN KEY (parent_token_id) REFERENCES refresh_tokens(id) ON DELETE SET NULL
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_refresh_token_tenant ON refresh_tokens(tenant_id);
CREATE INDEX IF NOT EXISTS idx_refresh_token_user ON refresh_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_refresh_token_token_hash ON refresh_tokens(token_hash);
CREATE INDEX IF NOT EXISTS idx_refresh_token_token_family ON refresh_tokens(token_family);
CREATE INDEX IF NOT EXISTS idx_refresh_token_user_family ON refresh_tokens(user_id, token_family);
CREATE INDEX IF NOT EXISTS idx_refresh_token_tenant_user ON refresh_tokens(tenant_id, user_id);
CREATE INDEX IF NOT EXISTS idx_refresh_token_expires ON refresh_tokens(expires_at);
CREATE INDEX IF NOT EXISTS idx_refresh_token_revoked ON refresh_tokens(is_revoked);

COMMENT ON TABLE refresh_tokens IS 'Stores refresh tokens for database-backed token management and revocation';
COMMENT ON COLUMN refresh_tokens.token_hash IS 'SHA-256 hash of the actual token (never store plain tokens)';
COMMENT ON COLUMN refresh_tokens.token_family IS 'Token family ID for rotation tracking - all tokens from same login share family';
COMMENT ON COLUMN refresh_tokens.parent_token_id IS 'Previous token in rotation chain - used to detect token reuse attacks';

