-- Seed AI Providers
-- This script populates the ai_providers table with initial provider configurations

INSERT INTO ai_providers (id, name, slug, provider_type, base_url, supported_models, default_settings, is_active, created_at, updated_at)
VALUES
    (gen_random_uuid(), 'OpenAI', 'openai', 'openai_compatible', 'https://api.openai.com/v1', 
     '["gpt-4","gpt-4-turbo","gpt-4o","gpt-4o-mini","gpt-5","gpt-5-mini","o1","o1-mini"]'::jsonb,
     '{"temperature":0.7,"max_tokens":8000,"top_p":1.0}'::jsonb, TRUE, NOW(), NOW())
ON CONFLICT (slug) DO NOTHING;

INSERT INTO ai_providers (id, name, slug, provider_type, base_url, supported_models, default_settings, is_active, created_at, updated_at)
VALUES
    (gen_random_uuid(), 'Google', 'google', 'google', NULL, 
     '["gemini-pro","gemini-pro-vision","gemini-1.5-pro","gemini-1.5-flash","gemini-2.0-flash-exp"]'::jsonb,
     '{"temperature":0.7,"max_tokens":8000,"top_p":0.95,"top_k":40}'::jsonb, TRUE, NOW(), NOW())
ON CONFLICT (slug) DO NOTHING;

INSERT INTO ai_providers (id, name, slug, provider_type, base_url, supported_models, default_settings, is_active, created_at, updated_at)
VALUES
    (gen_random_uuid(), 'Anthropic', 'anthropic', 'anthropic', NULL, 
     '["claude-3-opus","claude-3-sonnet","claude-3-haiku","claude-3-5-sonnet","claude-3-5-haiku"]'::jsonb,
     '{"temperature":0.7,"max_tokens":8000,"top_p":0.9,"top_k":5}'::jsonb, TRUE, NOW(), NOW())
ON CONFLICT (slug) DO NOTHING;

INSERT INTO ai_providers (id, name, slug, provider_type, base_url, supported_models, default_settings, is_active, created_at, updated_at)
VALUES
    (gen_random_uuid(), 'Cohere', 'cohere', 'cohere', NULL, 
     '["command","command-light","command-r","command-r-plus"]'::jsonb,
     '{"temperature":0.7,"max_tokens":8000,"top_p":0.9,"top_k":0}'::jsonb, TRUE, NOW(), NOW())
ON CONFLICT (slug) DO NOTHING;

INSERT INTO ai_providers (id, name, slug, provider_type, base_url, supported_models, default_settings, is_active, created_at, updated_at)
VALUES
    (gen_random_uuid(), 'Mistral', 'mistral', 'mistral', NULL, 
     '["mistral-tiny","mistral-small","mistral-medium","mistral-large","pixtral-12b"]'::jsonb,
     '{"temperature":0.7,"max_tokens":8000,"top_p":1.0}'::jsonb, TRUE, NOW(), NOW())
ON CONFLICT (slug) DO NOTHING;

INSERT INTO ai_providers (id, name, slug, provider_type, base_url, supported_models, default_settings, is_active, created_at, updated_at)
VALUES
    (gen_random_uuid(), 'DeepSeek', 'deepseek', 'deepseek', NULL, 
     '["deepseek-chat","deepseek-coder"]'::jsonb,
     '{"temperature":0.7,"max_tokens":8000,"top_p":1.0}'::jsonb, TRUE, NOW(), NOW())
ON CONFLICT (slug) DO NOTHING;

INSERT INTO ai_providers (id, name, slug, provider_type, base_url, supported_models, default_settings, is_active, created_at, updated_at)
VALUES
    (gen_random_uuid(), 'Grok', 'grok', 'grok', NULL, 
     '["grok-beta","grok-2"]'::jsonb,
     '{"temperature":0.7,"max_tokens":8000,"top_p":1.0}'::jsonb, TRUE, NOW(), NOW())
ON CONFLICT (slug) DO NOTHING;

INSERT INTO ai_providers (id, name, slug, provider_type, base_url, supported_models, default_settings, is_active, created_at, updated_at)
VALUES
    (gen_random_uuid(), 'Ollama', 'ollama', 'ollama', 'http://localhost:11434', 
     '["llama2","llama3","mistral","codellama","phi","neural-chat","starling-lm","qwen","llava"]'::jsonb,
     '{"temperature":0.7,"num_predict":8000,"top_p":0.9,"top_k":40}'::jsonb, TRUE, NOW(), NOW())
ON CONFLICT (slug) DO NOTHING;

INSERT INTO ai_providers (id, name, slug, provider_type, base_url, supported_models, default_settings, is_active, created_at, updated_at)
VALUES
    (gen_random_uuid(), 'OpenAI Compatible', 'openai_compatible', 'openai_compatible', 'http://localhost:8000/v1', 
     '["custom-model-1","custom-model-2"]'::jsonb,
     '{"temperature":0.7,"max_tokens":8000,"top_p":1.0}'::jsonb, TRUE, NOW(), NOW())
ON CONFLICT (slug) DO NOTHING;

