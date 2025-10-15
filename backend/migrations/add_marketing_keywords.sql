-- Add marketing_keywords column to tenants table
-- This stores SEO/Marketing keywords extracted from AI analysis for use in future marketing modules

ALTER TABLE tenants 
ADD COLUMN IF NOT EXISTS marketing_keywords JSON DEFAULT '[]'::json;

-- Add comment to explain the field
COMMENT ON COLUMN tenants.marketing_keywords IS 'SEO/Marketing keywords extracted from AI auto-fill analysis, used for marketing campaigns and content generation';


