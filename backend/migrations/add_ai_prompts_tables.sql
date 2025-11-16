-- Migration: Add AI Prompts tables
-- Created: 2025-01-XX
-- Description: Creates tables for database-driven AI prompt management

-- Create ai_prompts table
CREATE TABLE IF NOT EXISTS ai_prompts (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    category VARCHAR(50) NOT NULL,
    description TEXT,
    system_prompt TEXT NOT NULL,
    user_prompt_template TEXT NOT NULL,
    model VARCHAR(50) DEFAULT 'gpt-5-mini' NOT NULL,
    temperature FLOAT DEFAULT 0.7 NOT NULL,
    max_tokens INTEGER DEFAULT 8000 NOT NULL,
    version INTEGER DEFAULT 1 NOT NULL,
    is_active BOOLEAN DEFAULT true NOT NULL,
    is_system BOOLEAN DEFAULT false NOT NULL,
    tenant_id VARCHAR(36),
    created_by VARCHAR(36),
    variables JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

-- Create ai_prompt_versions table
CREATE TABLE IF NOT EXISTS ai_prompt_versions (
    id VARCHAR(36) PRIMARY KEY,
    prompt_id VARCHAR(36) NOT NULL,
    version INTEGER NOT NULL,
    note VARCHAR(255),
    system_prompt TEXT NOT NULL,
    user_prompt_template TEXT NOT NULL,
    variables JSONB,
    model VARCHAR(50) NOT NULL,
    temperature FLOAT NOT NULL,
    max_tokens INTEGER NOT NULL,
    created_by VARCHAR(36),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    FOREIGN KEY (prompt_id) REFERENCES ai_prompts(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_ai_prompts_category ON ai_prompts(category);
CREATE INDEX IF NOT EXISTS idx_ai_prompts_tenant_id ON ai_prompts(tenant_id);
CREATE INDEX IF NOT EXISTS idx_ai_prompts_is_active ON ai_prompts(is_active);
CREATE INDEX IF NOT EXISTS idx_ai_prompts_category_tenant_active ON ai_prompts(category, tenant_id, is_active);
CREATE INDEX IF NOT EXISTS idx_ai_prompt_versions_prompt_id ON ai_prompt_versions(prompt_id);
CREATE INDEX IF NOT EXISTS idx_ai_prompt_versions_prompt_version ON ai_prompt_versions(prompt_id, version);

-- Add RLS policies (if RLS is enabled)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'ai_prompts') THEN
        -- RLS already configured
        RAISE NOTICE 'RLS policies already exist for ai_prompts';
    ELSE
        -- Enable RLS
        ALTER TABLE ai_prompts ENABLE ROW LEVEL SECURITY;
        ALTER TABLE ai_prompt_versions ENABLE ROW LEVEL SECURITY;
        
        -- Create policies (if RLS is being used)
        -- Note: These will be created by the application's RLS setup if needed
    END IF;
END $$;



