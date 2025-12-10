-- Migration: Add password security tables
-- Purpose: Enable password history tracking and account lockout

-- Password history table
CREATE TABLE IF NOT EXISTS password_history (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    set_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_password_history_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Account lockout table
CREATE TABLE IF NOT EXISTS account_lockouts (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL UNIQUE,
    failed_attempts INTEGER NOT NULL DEFAULT 0,
    locked_until TIMESTAMP WITH TIME ZONE,
    last_failed_attempt TIMESTAMP WITH TIME ZONE,
    lockout_reason VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_account_lockout_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_password_history_user_set_at ON password_history(user_id, set_at);
CREATE INDEX IF NOT EXISTS idx_lockout_user_locked ON account_lockouts(user_id, locked_until);

COMMENT ON TABLE password_history IS 'Stores password history to prevent reuse of last N passwords';
COMMENT ON TABLE account_lockouts IS 'Tracks failed login attempts and account lockouts';
COMMENT ON COLUMN password_history.password_hash IS 'Hashed password (same format as users.hashed_password)';
COMMENT ON COLUMN account_lockouts.locked_until IS 'Account locked until this timestamp (NULL if not locked)';

