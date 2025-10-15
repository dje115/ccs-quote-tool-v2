-- Migration: Add DISCOVERY status to customer workflow
-- Date: 2025-10-12
-- Purpose: Add DISCOVERY stage for campaign-generated leads that haven't been contacted yet
-- This represents companies identified through campaigns but not yet moved into active CRM workflow

-- Add DISCOVERY to the customerstatus enum type
ALTER TYPE customerstatus ADD VALUE IF NOT EXISTS 'DISCOVERY';

-- Update comment explaining the complete workflow
COMMENT ON TYPE customerstatus IS 'Customer lifecycle stages: DISCOVERY (identified via campaigns) → LEAD (first contact) → PROSPECT (qualified) → OPPORTUNITY (active deal) → CUSTOMER (won). Also includes: COLD_LEAD, INACTIVE, LOST';

-- Note: DISCOVERY represents the earliest stage - companies we've identified but not yet reached out to
-- When a company is contacted or imported to CRM, they move from DISCOVERY to LEAD


