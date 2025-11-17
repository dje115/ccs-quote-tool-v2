-- Migration: Add Helpdesk Tables
-- Purpose: Create tables for ticket management, knowledge base, and SLA tracking
-- Date: 2025-01-XX

-- Create tickets table
CREATE TABLE IF NOT EXISTS tickets (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    ticket_number VARCHAR(50) UNIQUE NOT NULL,
    customer_id VARCHAR(36),
    contact_id VARCHAR(36),
    created_by_user_id VARCHAR(36),
    subject VARCHAR(500) NOT NULL,
    description TEXT NOT NULL,
    ticket_type VARCHAR(50) NOT NULL DEFAULT 'support',
    status VARCHAR(50) NOT NULL DEFAULT 'open',
    priority VARCHAR(50) NOT NULL DEFAULT 'medium',
    assigned_to_id VARCHAR(36),
    assigned_at TIMESTAMP WITH TIME ZONE,
    sla_target_hours INTEGER,
    first_response_at TIMESTAMP WITH TIME ZONE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    closed_at TIMESTAMP WITH TIME ZONE,
    related_quote_id VARCHAR(36),
    related_contract_id VARCHAR(36),
    tags JSONB,
    custom_fields JSONB,
    internal_notes TEXT,
    customer_satisfaction_rating INTEGER,
    customer_feedback TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL,
    FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by_user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (assigned_to_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (related_quote_id) REFERENCES quotes(id) ON DELETE SET NULL,
    FOREIGN KEY (related_contract_id) REFERENCES support_contracts(id) ON DELETE SET NULL
);

-- Create ticket_comments table
CREATE TABLE IF NOT EXISTS ticket_comments (
    id VARCHAR(36) PRIMARY KEY,
    ticket_id VARCHAR(36) NOT NULL,
    comment TEXT NOT NULL,
    is_internal BOOLEAN DEFAULT false NOT NULL,
    is_system BOOLEAN DEFAULT false NOT NULL,
    author_id VARCHAR(36),
    author_name VARCHAR(200),
    author_email VARCHAR(200),
    status_change VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE,
    FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Create ticket_attachments table
CREATE TABLE IF NOT EXISTS ticket_attachments (
    id VARCHAR(36) PRIMARY KEY,
    ticket_id VARCHAR(36) NOT NULL,
    comment_id VARCHAR(36),
    filename VARCHAR(500) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER NOT NULL,
    content_type VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE,
    FOREIGN KEY (comment_id) REFERENCES ticket_comments(id) ON DELETE CASCADE
);

-- Create ticket_history table
CREATE TABLE IF NOT EXISTS ticket_history (
    id VARCHAR(36) PRIMARY KEY,
    ticket_id VARCHAR(36) NOT NULL,
    field_name VARCHAR(100) NOT NULL,
    old_value TEXT,
    new_value TEXT NOT NULL,
    changed_by_id VARCHAR(36),
    changed_by_name VARCHAR(200),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE,
    FOREIGN KEY (changed_by_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Create knowledge_base_articles table
CREATE TABLE IF NOT EXISTS knowledge_base_articles (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    summary TEXT,
    category VARCHAR(100),
    tags JSONB,
    is_published BOOLEAN DEFAULT false NOT NULL,
    is_featured BOOLEAN DEFAULT false NOT NULL,
    author_id VARCHAR(36),
    view_count INTEGER DEFAULT 0 NOT NULL,
    helpful_count INTEGER DEFAULT 0 NOT NULL,
    not_helpful_count INTEGER DEFAULT 0 NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
    FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Create sla_policies table
CREATE TABLE IF NOT EXISTS sla_policies (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    first_response_hours INTEGER,
    resolution_hours INTEGER,
    priority VARCHAR(50),
    ticket_type VARCHAR(50),
    customer_ids JSONB,
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_tickets_tenant_id ON tickets(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tickets_ticket_number ON tickets(ticket_number);
CREATE INDEX IF NOT EXISTS idx_tickets_customer_id ON tickets(customer_id);
CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);
CREATE INDEX IF NOT EXISTS idx_tickets_priority ON tickets(priority);
CREATE INDEX IF NOT EXISTS idx_tickets_assigned_to_id ON tickets(assigned_to_id);
CREATE INDEX IF NOT EXISTS idx_tickets_tenant_status ON tickets(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_tickets_tenant_priority ON tickets(tenant_id, priority);
CREATE INDEX IF NOT EXISTS idx_tickets_assigned ON tickets(tenant_id, assigned_to_id, status);
CREATE INDEX IF NOT EXISTS idx_tickets_customer ON tickets(tenant_id, customer_id, status);

CREATE INDEX IF NOT EXISTS idx_ticket_comments_ticket_id ON ticket_comments(ticket_id);
CREATE INDEX IF NOT EXISTS idx_ticket_comments_author_id ON ticket_comments(author_id);

CREATE INDEX IF NOT EXISTS idx_ticket_attachments_ticket_id ON ticket_attachments(ticket_id);
CREATE INDEX IF NOT EXISTS idx_ticket_attachments_comment_id ON ticket_attachments(comment_id);

CREATE INDEX IF NOT EXISTS idx_ticket_history_ticket_id ON ticket_history(ticket_id);
CREATE INDEX IF NOT EXISTS idx_ticket_history_changed_by_id ON ticket_history(changed_by_id);

CREATE INDEX IF NOT EXISTS idx_kb_articles_tenant_id ON knowledge_base_articles(tenant_id);
CREATE INDEX IF NOT EXISTS idx_kb_articles_category ON knowledge_base_articles(category);
CREATE INDEX IF NOT EXISTS idx_kb_articles_is_published ON knowledge_base_articles(is_published);
CREATE INDEX IF NOT EXISTS idx_kb_articles_tenant_published ON knowledge_base_articles(tenant_id, is_published);
CREATE INDEX IF NOT EXISTS idx_kb_articles_category_published ON knowledge_base_articles(tenant_id, category, is_published);

CREATE INDEX IF NOT EXISTS idx_sla_policies_tenant_id ON sla_policies(tenant_id);
CREATE INDEX IF NOT EXISTS idx_sla_policies_is_active ON sla_policies(is_active);

-- Add comments
COMMENT ON TABLE tickets IS 'Helpdesk support tickets';
COMMENT ON TABLE ticket_comments IS 'Comments and updates on tickets';
COMMENT ON TABLE ticket_attachments IS 'File attachments for tickets and comments';
COMMENT ON TABLE ticket_history IS 'Audit log of ticket changes';
COMMENT ON TABLE knowledge_base_articles IS 'Knowledge base articles for self-service support';
COMMENT ON TABLE sla_policies IS 'SLA policies for ticket response and resolution times';

