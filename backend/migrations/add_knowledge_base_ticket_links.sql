-- Migration: Add knowledge_base_ticket_links table
-- Created: 2025-11-24
-- Description: Links knowledge base articles to helpdesk tickets for suggestions and resolution tracking

-- Create knowledge_base_ticket_links table
CREATE TABLE IF NOT EXISTS knowledge_base_ticket_links (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    ticket_id VARCHAR(36) NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    article_id VARCHAR(36) NOT NULL REFERENCES knowledge_base_articles(id) ON DELETE CASCADE,
    
    -- Link metadata
    link_type VARCHAR(20) DEFAULT 'suggested' NOT NULL, -- 'suggested', 'linked', 'resolved'
    relevance_score INTEGER, -- 0-100
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure unique link per ticket-article pair
    CONSTRAINT unique_ticket_article_link UNIQUE (ticket_id, article_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_kb_ticket_links_tenant_id ON knowledge_base_ticket_links(tenant_id);
CREATE INDEX IF NOT EXISTS idx_kb_ticket_links_ticket_id ON knowledge_base_ticket_links(ticket_id);
CREATE INDEX IF NOT EXISTS idx_kb_ticket_links_article_id ON knowledge_base_ticket_links(article_id);
CREATE INDEX IF NOT EXISTS idx_kb_ticket_links_link_type ON knowledge_base_ticket_links(link_type);
CREATE INDEX IF NOT EXISTS idx_kb_link_ticket_article ON knowledge_base_ticket_links(ticket_id, article_id);

-- Add RLS policies for multi-tenant isolation
ALTER TABLE knowledge_base_ticket_links ENABLE ROW LEVEL SECURITY;

-- RLS policy for knowledge_base_ticket_links
CREATE POLICY kb_ticket_links_tenant_isolation ON knowledge_base_ticket_links
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE));

-- Add comment
COMMENT ON TABLE knowledge_base_ticket_links IS 'Links between helpdesk tickets and knowledge base articles for suggestions and resolution tracking';

