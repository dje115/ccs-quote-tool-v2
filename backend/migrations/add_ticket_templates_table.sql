-- Migration: Add ticket_templates table
-- Description: Creates table for ticket templates to improve agent efficiency

CREATE TABLE IF NOT EXISTS ticket_templates (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    subject_template TEXT,
    description_template TEXT,
    npa_template TEXT,
    tags JSON,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_by_id VARCHAR(36),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_ticket_template_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
    CONSTRAINT fk_ticket_template_created_by FOREIGN KEY (created_by_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_template_tenant_active ON ticket_templates(tenant_id, is_active);
CREATE INDEX IF NOT EXISTS idx_template_category ON ticket_templates(category);
CREATE INDEX IF NOT EXISTS idx_template_tenant ON ticket_templates(tenant_id);

