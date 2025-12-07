-- Migration: Add ticket_macros table
-- Description: Creates table for ticket macros to automate common workflows

CREATE TABLE IF NOT EXISTS ticket_macros (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    actions JSON NOT NULL, -- Array of action objects
    is_shared BOOLEAN DEFAULT FALSE NOT NULL,
    created_by_id VARCHAR(36),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_ticket_macro_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
    CONSTRAINT fk_ticket_macro_created_by FOREIGN KEY (created_by_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_macro_tenant_shared ON ticket_macros(tenant_id, is_shared);
CREATE INDEX IF NOT EXISTS idx_macro_tenant ON ticket_macros(tenant_id);

