-- Migration: Add next_point_of_action to tickets table
-- Created: 2025-11-24
-- Description: Every ticket should have a next point of action (NPA) or be closed/resolved

-- Add next_point_of_action column
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'tickets' AND column_name = 'next_point_of_action'
    ) THEN
        ALTER TABLE tickets ADD COLUMN next_point_of_action TEXT;
        ALTER TABLE tickets ADD COLUMN next_point_of_action_due_date TIMESTAMP WITH TIME ZONE;
        ALTER TABLE tickets ADD COLUMN next_point_of_action_assigned_to_id VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL;
        ALTER TABLE tickets ADD COLUMN npa_last_updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
        
        -- Add index for querying tickets with NPAs
        CREATE INDEX IF NOT EXISTS idx_tickets_npa_due_date ON tickets(tenant_id, next_point_of_action_due_date) WHERE next_point_of_action IS NOT NULL;
        CREATE INDEX IF NOT EXISTS idx_tickets_npa_assigned ON tickets(tenant_id, next_point_of_action_assigned_to_id) WHERE next_point_of_action IS NOT NULL;
        
        COMMENT ON COLUMN tickets.next_point_of_action IS 'Next point of action required for this ticket. Must be set unless ticket is closed/resolved.';
        COMMENT ON COLUMN tickets.next_point_of_action_due_date IS 'Due date for the next point of action';
        COMMENT ON COLUMN tickets.next_point_of_action_assigned_to_id IS 'User assigned to complete the next point of action';
    END IF;
END $$;

