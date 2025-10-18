-- Migration: Fix sales_methodology field length
-- Date: 2025-10-12
-- Issue: sales_methodology limited to 100 chars but AI returns longer text
-- Solution: Change to TEXT type to allow unlimited length

ALTER TABLE tenants 
ALTER COLUMN sales_methodology TYPE TEXT;

-- Add comment explaining the field
COMMENT ON COLUMN tenants.sales_methodology IS 'Sales approach methodology (e.g., consultative, solution-based, value-based) - can include detailed description';





