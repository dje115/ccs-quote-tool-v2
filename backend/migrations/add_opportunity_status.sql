-- Migration: Add OPPORTUNITY status to customer workflow
-- Date: 2025-10-12
-- Purpose: Add OPPORTUNITY stage between PROSPECT and CUSTOMER for tracking active sales opportunities
-- This represents customers who have moved beyond prospecting and have active opportunities/quotes

-- Add OPPORTUNITY to the customerstatus enum type
ALTER TYPE customerstatus ADD VALUE IF NOT EXISTS 'OPPORTUNITY';

-- Add comment explaining the new status
COMMENT ON TYPE customerstatus IS 'Customer lifecycle stages: LEAD → PROSPECT → OPPORTUNITY → CUSTOMER. Also includes: COLD_LEAD, INACTIVE, LOST';

-- Note: The order in PostgreSQL enum is determined by creation order
-- New values are always added at the end
-- This doesn't affect application logic as we don't rely on enum ordering


