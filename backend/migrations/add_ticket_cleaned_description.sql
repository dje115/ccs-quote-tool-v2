-- Migration: Add cleaned_description field for AI-cleaned customer-facing description
-- Created: 2025-12-02
-- Description: Adds cleaned_description field and AI cleanup tracking for ticket descriptions

DO $$
BEGIN
    -- Add cleaned_description field (separate from improved_description for clarity)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'tickets' AND column_name = 'cleaned_description'
    ) THEN
        ALTER TABLE tickets ADD COLUMN cleaned_description TEXT;
    END IF;

    -- Add AI cleanup status for description
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'tickets' AND column_name = 'description_ai_cleanup_status'
    ) THEN
        ALTER TABLE tickets ADD COLUMN description_ai_cleanup_status VARCHAR(50) DEFAULT 'pending';
        -- Values: 'pending', 'processing', 'completed', 'failed', 'skipped'
    END IF;

    -- Add AI cleanup task ID for description
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'tickets' AND column_name = 'description_ai_cleanup_task_id'
    ) THEN
        ALTER TABLE tickets ADD COLUMN description_ai_cleanup_task_id VARCHAR(100);
    END IF;
END $$;

-- Migrate existing improved_description to cleaned_description if cleaned_description is null
UPDATE tickets 
SET cleaned_description = improved_description
WHERE cleaned_description IS NULL AND improved_description IS NOT NULL;

-- Set cleanup status for existing tickets
UPDATE tickets 
SET description_ai_cleanup_status = 'completed'
WHERE cleaned_description IS NOT NULL AND description_ai_cleanup_status = 'pending';

-- Add comments
COMMENT ON COLUMN tickets.cleaned_description IS 'AI-cleaned professional version of description for customer-facing communication';
COMMENT ON COLUMN tickets.description_ai_cleanup_status IS 'Status of AI cleanup process for description: pending, processing, completed, failed, skipped';
COMMENT ON COLUMN tickets.description_ai_cleanup_task_id IS 'Celery task ID for tracking description AI cleanup job';

