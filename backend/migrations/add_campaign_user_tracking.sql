-- Migration: Add user tracking fields to lead_generation_campaigns
-- Date: 2025-10-12
-- Purpose: Add created_by and updated_by fields to track campaign ownership

-- Add created_by column
ALTER TABLE lead_generation_campaigns 
ADD COLUMN IF NOT EXISTS created_by VARCHAR(36);

-- Add updated_by column
ALTER TABLE lead_generation_campaigns 
ADD COLUMN IF NOT EXISTS updated_by VARCHAR(36);

-- Add comments
COMMENT ON COLUMN lead_generation_campaigns.created_by IS 'User ID who created the campaign';
COMMENT ON COLUMN lead_generation_campaigns.updated_by IS 'User ID who last updated the campaign';

-- Note: These are nullable to support existing campaigns and system-generated campaigns



