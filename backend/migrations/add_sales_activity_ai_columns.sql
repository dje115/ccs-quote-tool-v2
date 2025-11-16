-- Migration: Add AI-related columns to sales_activities table
-- Date: 2025-11-16
-- Description: Adds missing AI-related columns that are referenced in the SalesActivity model

-- ============================================================================
-- ADD MISSING COLUMNS TO SALES_ACTIVITIES TABLE
-- ============================================================================

-- Add notes_cleaned column (AI-cleaned/enhanced version of notes)
ALTER TABLE sales_activities 
ADD COLUMN IF NOT EXISTS notes_cleaned TEXT;

-- Add ai_suggested_action column (AI-suggested next action)
ALTER TABLE sales_activities 
ADD COLUMN IF NOT EXISTS ai_suggested_action TEXT;

-- Add ai_processing_date column (When AI processed this activity)
ALTER TABLE sales_activities 
ADD COLUMN IF NOT EXISTS ai_processing_date TIMESTAMP WITH TIME ZONE;

-- Add comments
COMMENT ON COLUMN sales_activities.notes_cleaned IS 'AI-cleaned/enhanced version of the original notes';
COMMENT ON COLUMN sales_activities.ai_suggested_action IS 'AI-suggested next action based on this activity';
COMMENT ON COLUMN sales_activities.ai_processing_date IS 'When AI processed this activity for enhancement';

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- Verify columns exist
SELECT 
    'AI columns added' AS status,
    COUNT(*) AS count
FROM information_schema.columns
WHERE table_name = 'sales_activities'
AND column_name IN ('notes_cleaned', 'ai_suggested_action', 'ai_processing_date');

