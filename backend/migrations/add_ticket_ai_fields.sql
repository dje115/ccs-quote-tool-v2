-- Add AI-powered ticket analysis fields
ALTER TABLE tickets 
ADD COLUMN IF NOT EXISTS original_description TEXT,
ADD COLUMN IF NOT EXISTS improved_description TEXT,
ADD COLUMN IF NOT EXISTS ai_suggestions JSONB,
ADD COLUMN IF NOT EXISTS ai_analysis_date TIMESTAMP WITH TIME ZONE;

-- Add comments
COMMENT ON COLUMN tickets.original_description IS 'Original description typed by agent (preserved for reference)';
COMMENT ON COLUMN tickets.improved_description IS 'AI-improved description shown in customer portal';
COMMENT ON COLUMN tickets.description IS 'Current description (improved version if AI analysis was performed)';
COMMENT ON COLUMN tickets.ai_suggestions IS 'AI-generated suggestions: {"next_actions": [], "questions": [], "solutions": []}';
COMMENT ON COLUMN tickets.ai_analysis_date IS 'Timestamp when AI analysis was performed';

