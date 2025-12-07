-- Migration: Add merged_into_ticket_id field to tickets table
-- Description: Allows tickets to be merged into other tickets

ALTER TABLE tickets 
ADD COLUMN IF NOT EXISTS merged_into_ticket_id VARCHAR(36);

-- Add foreign key constraint
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'fk_ticket_merged_into'
    ) THEN
        ALTER TABLE tickets
        ADD CONSTRAINT fk_ticket_merged_into
        FOREIGN KEY (merged_into_ticket_id) REFERENCES tickets(id);
    END IF;
END $$;

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_ticket_merged_into ON tickets(merged_into_ticket_id);

