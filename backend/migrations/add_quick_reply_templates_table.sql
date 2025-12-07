-- Migration: Add quick_reply_templates table
-- Description: Creates table for quick reply templates to speed up agent responses

CREATE TABLE IF NOT EXISTS quick_reply_templates (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    name VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(100),
    is_shared BOOLEAN DEFAULT FALSE NOT NULL,
    created_by_id VARCHAR(36),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_quick_reply_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
    CONSTRAINT fk_quick_reply_created_by FOREIGN KEY (created_by_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_quick_reply_tenant_shared ON quick_reply_templates(tenant_id, is_shared);
CREATE INDEX IF NOT EXISTS idx_quick_reply_category ON quick_reply_templates(category);
CREATE INDEX IF NOT EXISTS idx_quick_reply_tenant ON quick_reply_templates(tenant_id);

