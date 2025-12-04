-- Migration: Add ticket_agent_chat table for persistent agent chat history
-- Created: 2025-01-XX

-- Create ticket_agent_chat table
CREATE TABLE IF NOT EXISTS ticket_agent_chat (
    id VARCHAR(36) PRIMARY KEY,
    ticket_id VARCHAR(36) NOT NULL,
    tenant_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    
    -- Message details
    role VARCHAR(20) NOT NULL,  -- 'user' or 'assistant'
    content TEXT NOT NULL,
    
    -- AI task tracking
    ai_task_id VARCHAR(100),
    ai_status VARCHAR(50) DEFAULT 'pending',
    ai_model VARCHAR(100),
    ai_usage JSONB,
    
    -- Attachments and logs
    attachments JSONB,
    log_files JSONB,
    
    -- NPA and solution tracking
    linked_to_npa_id VARCHAR(36),
    is_solution BOOLEAN DEFAULT FALSE NOT NULL,
    solution_notes TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Foreign keys
    CONSTRAINT fk_ticket_agent_chat_ticket FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE,
    CONSTRAINT fk_ticket_agent_chat_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
    CONSTRAINT fk_ticket_agent_chat_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_ticket_agent_chat_npa FOREIGN KEY (linked_to_npa_id) REFERENCES npa_history(id) ON DELETE SET NULL
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_ticket_agent_chat_ticket ON ticket_agent_chat(ticket_id);
CREATE INDEX IF NOT EXISTS idx_ticket_agent_chat_tenant ON ticket_agent_chat(tenant_id);
CREATE INDEX IF NOT EXISTS idx_ticket_agent_chat_user ON ticket_agent_chat(user_id);
CREATE INDEX IF NOT EXISTS idx_ticket_agent_chat_created ON ticket_agent_chat(ticket_id, created_at);
CREATE INDEX IF NOT EXISTS idx_ticket_agent_chat_user_created ON ticket_agent_chat(user_id, created_at);

-- Add comment
COMMENT ON TABLE ticket_agent_chat IS 'Persistent chat history for agent conversations about tickets';
COMMENT ON COLUMN ticket_agent_chat.role IS 'Message role: user or assistant';
COMMENT ON COLUMN ticket_agent_chat.ai_status IS 'AI processing status: pending, processing, completed, failed';
COMMENT ON COLUMN ticket_agent_chat.linked_to_npa_id IS 'If this chat was saved to an NPA';
COMMENT ON COLUMN ticket_agent_chat.is_solution IS 'If this message was marked as the solution';

