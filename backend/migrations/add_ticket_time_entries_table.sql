-- Migration: Add ticket_time_entries table
-- Description: Creates table for tracking time spent on tickets

CREATE TABLE IF NOT EXISTS ticket_time_entries (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    ticket_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    description TEXT,
    hours DECIMAL(10, 2) NOT NULL,
    billable BOOLEAN DEFAULT FALSE NOT NULL,
    activity_type VARCHAR(50), -- 'work', 'research', 'communication', 'meeting', 'other'
    started_at TIMESTAMP WITH TIME ZONE,
    ended_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_time_entry_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
    CONSTRAINT fk_time_entry_ticket FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE,
    CONSTRAINT fk_time_entry_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_time_entry_ticket ON ticket_time_entries(ticket_id);
CREATE INDEX IF NOT EXISTS idx_time_entry_user ON ticket_time_entries(user_id);
CREATE INDEX IF NOT EXISTS idx_time_entry_tenant ON ticket_time_entries(tenant_id);
CREATE INDEX IF NOT EXISTS idx_time_entry_date ON ticket_time_entries(started_at);

