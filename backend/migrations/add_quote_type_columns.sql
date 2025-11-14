-- Add quote_type columns to quotes and ai_prompts tables
ALTER TABLE quotes ADD COLUMN IF NOT EXISTS quote_type VARCHAR(100);
CREATE INDEX IF NOT EXISTS idx_quotes_quote_type ON quotes(quote_type);

ALTER TABLE ai_prompts ADD COLUMN IF NOT EXISTS quote_type VARCHAR(100);
CREATE INDEX IF NOT EXISTS idx_ai_prompts_quote_type ON ai_prompts(quote_type);

