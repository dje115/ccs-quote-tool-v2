-- Migration: Add AI cleanup fields for NPA answers
-- This allows answers to questions to be cleaned up by AI, same as other agent inputs

-- Add cleanup fields to tickets table for current NPA answers
ALTER TABLE tickets ADD COLUMN IF NOT EXISTS npa_answers_original_text TEXT;
ALTER TABLE tickets ADD COLUMN IF NOT EXISTS npa_answers_cleaned_text TEXT;
ALTER TABLE tickets ADD COLUMN IF NOT EXISTS npa_answers_ai_cleanup_status VARCHAR(50) DEFAULT 'pending';
ALTER TABLE tickets ADD COLUMN IF NOT EXISTS npa_answers_ai_cleanup_task_id VARCHAR(100);

-- Add cleanup fields to npa_history table for historical NPA answers
ALTER TABLE npa_history ADD COLUMN IF NOT EXISTS answers_cleaned_text TEXT;
ALTER TABLE npa_history ADD COLUMN IF NOT EXISTS answers_ai_cleanup_status VARCHAR(50) DEFAULT 'pending';
ALTER TABLE npa_history ADD COLUMN IF NOT EXISTS answers_ai_cleanup_task_id VARCHAR(100);

COMMENT ON COLUMN tickets.npa_answers_original_text IS 'Original answers text as typed by agent';
COMMENT ON COLUMN tickets.npa_answers_cleaned_text IS 'AI-cleaned professional version of answers';
COMMENT ON COLUMN tickets.npa_answers_ai_cleanup_status IS 'AI cleanup status: pending, processing, completed, failed, skipped';
COMMENT ON COLUMN tickets.npa_answers_ai_cleanup_task_id IS 'Celery task ID for answers AI cleanup';
COMMENT ON COLUMN npa_history.answers_cleaned_text IS 'AI-cleaned professional version of answers';
COMMENT ON COLUMN npa_history.answers_ai_cleanup_status IS 'AI cleanup status: pending, processing, completed, failed, skipped';
COMMENT ON COLUMN npa_history.answers_ai_cleanup_task_id IS 'Celery task ID for answers AI cleanup';

