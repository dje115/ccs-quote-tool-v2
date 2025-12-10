-- Migration: Rename metadata column to event_metadata in security_events table
-- Purpose: Fix SQLAlchemy reserved name conflict - 'metadata' is reserved in Declarative API

-- Rename the column if it exists
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'security_events' 
        AND column_name = 'metadata'
    ) THEN
        ALTER TABLE security_events RENAME COLUMN metadata TO event_metadata;
    END IF;
END $$;

-- Update the comment
COMMENT ON COLUMN security_events.event_metadata IS 'JSON string for additional event data';

