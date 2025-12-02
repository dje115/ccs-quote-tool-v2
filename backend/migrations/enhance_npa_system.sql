-- Migration: Enhance NPA system with states, AI cleanup, and SLA exclusion
-- Created: 2025-12-02
-- Description: Adds NPA states, original/cleaned text tracking, date override, and SLA exclusion

-- Create NPA state enum
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'npastate') THEN
        CREATE TYPE npastate AS ENUM (
            'investigation',
            'waiting_customer',
            'waiting_vendor',
            'waiting_parts',
            'solution',
            'implementation',
            'testing',
            'documentation',
            'other'
        );
    END IF;
END $$;

-- Add new NPA columns
DO $$
BEGIN
    -- NPA state
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'tickets' AND column_name = 'npa_state'
    ) THEN
        ALTER TABLE tickets ADD COLUMN npa_state npastate DEFAULT 'investigation';
    END IF;

    -- Original and cleaned text for customer-facing NPAs
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'tickets' AND column_name = 'npa_original_text'
    ) THEN
        ALTER TABLE tickets ADD COLUMN npa_original_text TEXT;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'tickets' AND column_name = 'npa_cleaned_text'
    ) THEN
        ALTER TABLE tickets ADD COLUMN npa_cleaned_text TEXT;
    END IF;

    -- Date override flag
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'tickets' AND column_name = 'npa_date_override'
    ) THEN
        ALTER TABLE tickets ADD COLUMN npa_date_override BOOLEAN DEFAULT FALSE;
    END IF;

    -- SLA exclusion flag
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'tickets' AND column_name = 'npa_exclude_from_sla'
    ) THEN
        ALTER TABLE tickets ADD COLUMN npa_exclude_from_sla BOOLEAN DEFAULT FALSE;
    END IF;

    -- AI cleanup status
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'tickets' AND column_name = 'npa_ai_cleanup_status'
    ) THEN
        ALTER TABLE tickets ADD COLUMN npa_ai_cleanup_status VARCHAR(50) DEFAULT 'pending';
        -- Values: 'pending', 'processing', 'completed', 'failed', 'skipped'
    END IF;

    -- AI cleanup task ID for tracking
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'tickets' AND column_name = 'npa_ai_cleanup_task_id'
    ) THEN
        ALTER TABLE tickets ADD COLUMN npa_ai_cleanup_task_id VARCHAR(100);
    END IF;
END $$;

-- Migrate existing next_point_of_action to npa_cleaned_text
UPDATE tickets 
SET npa_cleaned_text = next_point_of_action,
    npa_original_text = next_point_of_action
WHERE next_point_of_action IS NOT NULL 
  AND npa_cleaned_text IS NULL;

-- Set SLA exclusion for waiting states
UPDATE tickets 
SET npa_exclude_from_sla = TRUE
WHERE next_point_of_action IS NOT NULL
  AND (
    LOWER(next_point_of_action) LIKE '%waiting for customer%' OR
    LOWER(next_point_of_action) LIKE '%waiting for vendor%' OR
    LOWER(next_point_of_action) LIKE '%waiting for parts%' OR
    LOWER(next_point_of_action) LIKE '%awaiting customer%' OR
    LOWER(next_point_of_action) LIKE '%awaiting vendor%' OR
    LOWER(next_point_of_action) LIKE '%awaiting parts%'
  );

-- Add comments
COMMENT ON COLUMN tickets.npa_state IS 'State of the next point of action (investigation, waiting_customer, waiting_vendor, waiting_parts, solution, etc.)';
COMMENT ON COLUMN tickets.npa_original_text IS 'Original NPA text as typed by the agent (for reference)';
COMMENT ON COLUMN tickets.npa_cleaned_text IS 'AI-cleaned professional version of NPA text (customer-facing)';
COMMENT ON COLUMN tickets.npa_date_override IS 'Whether the NPA due date was manually overridden';
COMMENT ON COLUMN tickets.npa_exclude_from_sla IS 'Whether this NPA should be excluded from SLA calculations (e.g., waiting for customer/vendor/parts)';
COMMENT ON COLUMN tickets.npa_ai_cleanup_status IS 'Status of AI cleanup process: pending, processing, completed, failed, skipped';
COMMENT ON COLUMN tickets.npa_ai_cleanup_task_id IS 'Celery task ID for tracking AI cleanup job';

-- Add index for SLA exclusion queries
CREATE INDEX IF NOT EXISTS idx_tickets_npa_exclude_sla ON tickets(tenant_id, npa_exclude_from_sla) WHERE npa_exclude_from_sla = TRUE;
CREATE INDEX IF NOT EXISTS idx_tickets_npa_state ON tickets(tenant_id, npa_state) WHERE next_point_of_action IS NOT NULL;

