-- Migration: Add missing columns to leads table
-- Date: 2025-11-16
-- Description: Adds missing columns that exist in the model but not in the database

-- Company registration fields
ALTER TABLE leads ADD COLUMN IF NOT EXISTS company_registration VARCHAR(50);
ALTER TABLE leads ADD COLUMN IF NOT EXISTS registration_confirmed BOOLEAN DEFAULT FALSE;

-- Address/distance fields
ALTER TABLE leads ADD COLUMN IF NOT EXISTS distance_from_search_center FLOAT;

-- Business details
ALTER TABLE leads ADD COLUMN IF NOT EXISTS annual_revenue VARCHAR(50);

-- AI analysis fields
ALTER TABLE leads ADD COLUMN IF NOT EXISTS ai_confidence_score FLOAT;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS ai_recommendation TEXT;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS ai_notes TEXT;

-- External data sources
ALTER TABLE leads ADD COLUMN IF NOT EXISTS google_maps_data JSONB;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS social_media_links JSONB;

-- Conversion tracking
ALTER TABLE leads ADD COLUMN IF NOT EXISTS conversion_date TIMESTAMP WITH TIME ZONE;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS conversion_value FLOAT;

-- Lead details
ALTER TABLE leads ADD COLUMN IF NOT EXISTS qualification_reason TEXT;

-- Project information
ALTER TABLE leads ADD COLUMN IF NOT EXISTS potential_project_value FLOAT;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS timeline_estimate VARCHAR(100);

-- Follow-up tracking
ALTER TABLE leads ADD COLUMN IF NOT EXISTS notes TEXT;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS last_contact_date TIMESTAMP WITH TIME ZONE;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS next_follow_up_date TIMESTAMP WITH TIME ZONE;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS contact_attempts INTEGER DEFAULT 0;

-- Comments
COMMENT ON COLUMN leads.company_registration IS 'Companies House registration number';
COMMENT ON COLUMN leads.registration_confirmed IS 'Whether the registration number has been verified';
COMMENT ON COLUMN leads.distance_from_search_center IS 'Distance from search center in miles';
COMMENT ON COLUMN leads.ai_confidence_score IS 'AI confidence score (0.0-1.0)';
COMMENT ON COLUMN leads.contact_attempts IS 'Number of contact attempts made';

