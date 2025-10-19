-- Add company_size_category column to lead_generation_campaigns table
-- This column stores the company size filter (Micro, Small, Medium, Large)

ALTER TABLE lead_generation_campaigns 
ADD COLUMN company_size_category VARCHAR(50) NULL;

-- Add comment to explain the column purpose
COMMENT ON COLUMN lead_generation_campaigns.company_size_category IS 'Company size category filter: Micro (0-9), Small (10-49), Medium (50-249), Large (250+) employees';
