-- Migration: Add quote_prompt_history table
-- Created: 2025-11-20
-- Description: Stores history of prompts used for quote generation and their results

-- Create quote_prompt_history table
CREATE TABLE IF NOT EXISTS quote_prompt_history (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    quote_id VARCHAR(36) NOT NULL REFERENCES quotes(id) ON DELETE CASCADE,
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- Prompt information
    prompt_text TEXT NOT NULL,
    prompt_variables JSONB NOT NULL DEFAULT '{}'::jsonb,
    
    -- AI generation metadata
    ai_model VARCHAR(100),
    ai_provider VARCHAR(100),
    temperature DECIMAL(3, 2),
    max_tokens INTEGER,
    
    -- Results
    generation_successful BOOLEAN NOT NULL DEFAULT FALSE,
    generation_error TEXT,
    generated_quote_data JSONB,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
    
    -- Soft delete
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL
);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_quote_prompt_history_quote_id ON quote_prompt_history(quote_id);
CREATE INDEX IF NOT EXISTS idx_quote_prompt_history_tenant_id ON quote_prompt_history(tenant_id);
CREATE INDEX IF NOT EXISTS idx_quote_prompt_history_created_at ON quote_prompt_history(created_at DESC);

-- Add RLS policies for multi-tenant isolation
ALTER TABLE quote_prompt_history ENABLE ROW LEVEL SECURITY;

CREATE POLICY quote_prompt_history_tenant_isolation ON quote_prompt_history
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE));

-- Add prompt_text column to quotes table to store the last used prompt
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'quotes' AND column_name = 'last_prompt_text'
    ) THEN
        ALTER TABLE quotes ADD COLUMN last_prompt_text TEXT;
        COMMENT ON COLUMN quotes.last_prompt_text IS 'The last prompt text used to generate this quote';
    END IF;
END $$;

