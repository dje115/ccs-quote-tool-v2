-- Update AI Provider Settings
-- This ensures all providers have correct base_url, supported_models, and default_settings

-- OpenAI
UPDATE ai_providers SET 
  base_url = 'https://api.openai.com/v1',
  supported_models = '["gpt-4","gpt-4-turbo","gpt-4o","gpt-4o-mini","gpt-5","gpt-5-mini","o1","o1-mini"]'::jsonb,
  default_settings = '{"temperature":0.7,"max_tokens":8000,"top_p":1.0}'::jsonb
WHERE slug = 'openai';

-- Google (uses SDK, no base_url needed)
UPDATE ai_providers SET 
  base_url = NULL,
  supported_models = '["gemini-pro","gemini-pro-vision","gemini-1.5-pro","gemini-1.5-flash","gemini-2.0-flash-exp"]'::jsonb,
  default_settings = '{"temperature":0.7,"max_tokens":8000,"top_p":0.95,"top_k":40}'::jsonb
WHERE slug = 'google';

-- Anthropic (uses SDK, no base_url needed)
UPDATE ai_providers SET 
  base_url = NULL,
  supported_models = '["claude-3-opus","claude-3-sonnet","claude-3-haiku","claude-3-5-sonnet","claude-3-5-haiku"]'::jsonb,
  default_settings = '{"temperature":0.7,"max_tokens":8000,"top_p":0.9,"top_k":5}'::jsonb
WHERE slug = 'anthropic';

-- Cohere (uses SDK, no base_url needed)
UPDATE ai_providers SET 
  base_url = NULL,
  supported_models = '["command","command-light","command-r","command-r-plus"]'::jsonb,
  default_settings = '{"temperature":0.7,"max_tokens":8000,"top_p":0.9,"top_k":0}'::jsonb
WHERE slug = 'cohere';

-- Mistral (uses SDK, no base_url needed)
UPDATE ai_providers SET 
  base_url = NULL,
  supported_models = '["mistral-tiny","mistral-small","mistral-medium","mistral-large","pixtral-12b"]'::jsonb,
  default_settings = '{"temperature":0.7,"max_tokens":8000,"top_p":1.0}'::jsonb
WHERE slug = 'mistral';

-- DeepSeek (uses SDK, no base_url needed)
UPDATE ai_providers SET 
  base_url = NULL,
  supported_models = '["deepseek-chat","deepseek-coder"]'::jsonb,
  default_settings = '{"temperature":0.7,"max_tokens":8000,"top_p":1.0}'::jsonb
WHERE slug = 'deepseek';

-- Grok (uses SDK, no base_url needed)
UPDATE ai_providers SET 
  base_url = NULL,
  supported_models = '["grok-beta","grok-2"]'::jsonb,
  default_settings = '{"temperature":0.7,"max_tokens":8000,"top_p":1.0}'::jsonb
WHERE slug = 'grok';

-- Ollama (on-premise, needs base_url)
UPDATE ai_providers SET 
  base_url = 'http://localhost:11434',
  supported_models = '["llama2","llama3","mistral","codellama","phi","neural-chat","starling-lm","qwen","llava"]'::jsonb,
  default_settings = '{"temperature":0.7,"num_predict":8000,"top_p":0.9,"top_k":40}'::jsonb
WHERE slug = 'ollama';

-- OpenAI Compatible (custom endpoint, needs base_url)
UPDATE ai_providers SET 
  base_url = 'http://localhost:8000/v1',
  supported_models = '["custom-model-1","custom-model-2"]'::jsonb,
  default_settings = '{"temperature":0.7,"max_tokens":8000,"top_p":1.0}'::jsonb
WHERE slug = 'openai_compatible';




