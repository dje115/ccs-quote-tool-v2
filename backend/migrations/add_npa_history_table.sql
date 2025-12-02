-- Migration: Add NPA History table to track all NPAs (call history)
-- This ensures we preserve completed NPAs and can use them for AI analysis

-- Create NPA History table
CREATE TABLE IF NOT EXISTS npa_history (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    ticket_id VARCHAR(36) NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- NPA content
    npa_original_text TEXT NOT NULL,
    npa_cleaned_text TEXT,
    npa_state VARCHAR(50) NOT NULL,  -- investigation, waiting_customer, solution, etc.
    
    -- Assignment and dates
    assigned_to_id VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
    due_date TIMESTAMP WITH TIME ZONE,
    date_override BOOLEAN DEFAULT FALSE,
    
    -- SLA exclusion
    exclude_from_sla BOOLEAN DEFAULT FALSE,
    
    -- AI cleanup status
    ai_cleanup_status VARCHAR(50) DEFAULT 'pending',  -- pending, processing, completed, failed, skipped
    ai_cleanup_task_id VARCHAR(100),
    
    -- Answers to questions in this NPA
    answers_to_questions TEXT,  -- Answers provided to questions asked in this NPA
    
    -- Completion tracking
    completed_at TIMESTAMP WITH TIME ZONE,  -- When this NPA was completed/marked as solution
    completed_by_id VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
    completion_notes TEXT,  -- Notes on how/why it was completed
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    CONSTRAINT fk_npa_history_ticket FOREIGN KEY (ticket_id) REFERENCES tickets(id),
    CONSTRAINT fk_npa_history_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id),
    CONSTRAINT fk_npa_history_assigned FOREIGN KEY (assigned_to_id) REFERENCES users(id),
    CONSTRAINT fk_npa_history_completed_by FOREIGN KEY (completed_by_id) REFERENCES users(id)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_npa_history_ticket ON npa_history(ticket_id);
CREATE INDEX IF NOT EXISTS idx_npa_history_tenant ON npa_history(tenant_id);
CREATE INDEX IF NOT EXISTS idx_npa_history_assigned ON npa_history(assigned_to_id);
CREATE INDEX IF NOT EXISTS idx_npa_history_created ON npa_history(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_npa_history_state ON npa_history(npa_state);
CREATE INDEX IF NOT EXISTS idx_npa_history_completed ON npa_history(completed_at) WHERE completed_at IS NOT NULL;

-- Add RLS policies
ALTER TABLE npa_history ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see NPA history for tickets in their tenant
CREATE POLICY npa_history_tenant_isolation ON npa_history
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', true));

COMMENT ON TABLE npa_history IS 'Complete history of all NPAs for tickets - this is the call history';
COMMENT ON COLUMN npa_history.npa_original_text IS 'Original NPA text as typed by agent';
COMMENT ON COLUMN npa_history.npa_cleaned_text IS 'AI-cleaned professional version';
COMMENT ON COLUMN npa_history.answers_to_questions IS 'Answers provided to questions asked in this NPA';
COMMENT ON COLUMN npa_history.completed_at IS 'When this NPA was completed/marked as solution - NULL means it is still active';

