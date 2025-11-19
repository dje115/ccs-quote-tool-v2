-- Migration: Add lead_id column to quotes table
-- Created: 2025-11-19
-- Description: Adds lead_id column to support quotes created from leads

-- Add lead_id column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'quotes' AND column_name = 'lead_id'
    ) THEN
        ALTER TABLE quotes ADD COLUMN lead_id VARCHAR(36);
        ALTER TABLE quotes ADD CONSTRAINT fk_quotes_lead_id 
            FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE SET NULL;
        CREATE INDEX IF NOT EXISTS idx_quotes_lead_id ON quotes(lead_id);
    END IF;
END $$;

