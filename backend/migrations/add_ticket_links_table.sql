-- Migration: Add ticket_links table
-- Description: Creates table for linking related tickets together

CREATE TABLE IF NOT EXISTS ticket_links (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    source_ticket_id VARCHAR(36) NOT NULL,
    target_ticket_id VARCHAR(36) NOT NULL,
    link_type VARCHAR(50) NOT NULL DEFAULT 'related', -- 'related', 'duplicate', 'blocks', 'blocked_by', 'follows', 'followed_by'
    created_by_id VARCHAR(36),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_ticket_link_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
    CONSTRAINT fk_ticket_link_source FOREIGN KEY (source_ticket_id) REFERENCES tickets(id) ON DELETE CASCADE,
    CONSTRAINT fk_ticket_link_target FOREIGN KEY (target_ticket_id) REFERENCES tickets(id) ON DELETE CASCADE,
    CONSTRAINT fk_ticket_link_created_by FOREIGN KEY (created_by_id) REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT uq_ticket_link UNIQUE (source_ticket_id, target_ticket_id, link_type)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_ticket_link_source ON ticket_links(source_ticket_id);
CREATE INDEX IF NOT EXISTS idx_ticket_link_target ON ticket_links(target_ticket_id);
CREATE INDEX IF NOT EXISTS idx_ticket_link_tenant ON ticket_links(tenant_id);
CREATE INDEX IF NOT EXISTS idx_ticket_link_type ON ticket_links(link_type);

