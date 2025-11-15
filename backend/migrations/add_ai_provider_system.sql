-- Add AI Provider System tables and columns
-- This migration adds support for multiple AI providers (OpenAI, Google, Anthropic, etc.)

-- Create ai_providers table
CREATE TABLE IF NOT EXISTS ai_providers (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    slug VARCHAR(50) NOT NULL UNIQUE,
    provider_type VARCHAR(20) NOT NULL,
    base_url VARCHAR(500),
    supported_models JSONB,
    default_settings JSONB,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_provider_slug_active ON ai_providers(slug, is_active);

-- Create provider_api_keys table
CREATE TABLE IF NOT EXISTS provider_api_keys (
    id VARCHAR(36) PRIMARY KEY,
    provider_id VARCHAR(36) NOT NULL REFERENCES ai_providers(id) ON DELETE CASCADE,
    tenant_id VARCHAR(36) REFERENCES tenants(id) ON DELETE CASCADE,
    api_key TEXT NOT NULL,
    last_tested TIMESTAMP WITH TIME ZONE,
    is_valid BOOLEAN NOT NULL DEFAULT FALSE,
    test_result TEXT,
    test_error TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_provider_tenant ON provider_api_keys(provider_id, tenant_id);
CREATE INDEX IF NOT EXISTS idx_provider_valid ON provider_api_keys(provider_id, is_valid);
CREATE INDEX IF NOT EXISTS idx_provider_api_keys_provider_id ON provider_api_keys(provider_id);
CREATE INDEX IF NOT EXISTS idx_provider_api_keys_tenant_id ON provider_api_keys(tenant_id);

-- Add provider columns to ai_prompts table
ALTER TABLE ai_prompts ADD COLUMN IF NOT EXISTS provider_id VARCHAR(36) REFERENCES ai_providers(id) ON DELETE SET NULL;
ALTER TABLE ai_prompts ADD COLUMN IF NOT EXISTS provider_model VARCHAR(100);
ALTER TABLE ai_prompts ADD COLUMN IF NOT EXISTS provider_settings JSONB;
ALTER TABLE ai_prompts ADD COLUMN IF NOT EXISTS use_system_default BOOLEAN NOT NULL DEFAULT TRUE;

CREATE INDEX IF NOT EXISTS idx_ai_prompts_provider_id ON ai_prompts(provider_id);

-- Add provider columns to ai_prompt_versions table (for version history)
ALTER TABLE ai_prompt_versions ADD COLUMN IF NOT EXISTS provider_id VARCHAR(36);
ALTER TABLE ai_prompt_versions ADD COLUMN IF NOT EXISTS provider_model VARCHAR(100);
ALTER TABLE ai_prompt_versions ADD COLUMN IF NOT EXISTS provider_settings JSONB;
ALTER TABLE ai_prompt_versions ADD COLUMN IF NOT EXISTS use_system_default BOOLEAN NOT NULL DEFAULT TRUE;

-- Add comment for documentation
COMMENT ON TABLE ai_providers IS 'Stores AI provider configurations (OpenAI, Google, Anthropic, etc.)';
COMMENT ON TABLE provider_api_keys IS 'Stores API keys per provider per tenant/system with fallback support';
COMMENT ON COLUMN ai_prompts.provider_id IS 'Foreign key to ai_providers - null means use system default';
COMMENT ON COLUMN ai_prompts.use_system_default IS 'If true, uses system default provider; if false, uses prompt-specific provider';

