-- Migration: Add security_events table
-- Purpose: Store security-related events for monitoring and auditing

CREATE TABLE IF NOT EXISTS security_events (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36),
    user_id VARCHAR(36),
    event_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL DEFAULT 'medium',
    description TEXT NOT NULL,
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    metadata TEXT,
    resolved VARCHAR(36),
    resolved_at TIMESTAMP WITH TIME ZONE,
    occurred_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_security_event_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE SET NULL,
    CONSTRAINT fk_security_event_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_security_events_tenant ON security_events(tenant_id);
CREATE INDEX IF NOT EXISTS idx_security_events_user ON security_events(user_id);
CREATE INDEX IF NOT EXISTS idx_security_events_type ON security_events(event_type);
CREATE INDEX IF NOT EXISTS idx_security_events_severity ON security_events(severity);
CREATE INDEX IF NOT EXISTS idx_security_events_occurred_at ON security_events(occurred_at);
CREATE INDEX IF NOT EXISTS idx_security_events_ip ON security_events(ip_address);

COMMENT ON TABLE security_events IS 'Stores security-related events for monitoring and auditing';
COMMENT ON COLUMN security_events.event_type IS 'Type of security event (failed_login, account_locked, etc.)';
COMMENT ON COLUMN security_events.severity IS 'Severity level (low, medium, high, critical)';
COMMENT ON COLUMN security_events.metadata IS 'JSON string for additional event data';
COMMENT ON COLUMN security_events.resolved IS 'User ID who resolved the event (if applicable)';

