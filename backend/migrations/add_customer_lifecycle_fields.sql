-- Migration: Add lifecycle management fields to customers table
-- This migration adds fields for automated customer lifecycle transitions

-- Add lifecycle_auto_managed column (allows disabling automation per customer)
ALTER TABLE customers 
ADD COLUMN IF NOT EXISTS lifecycle_auto_managed BOOLEAN NOT NULL DEFAULT TRUE;

-- Add last_contact_date column (tracks last interaction for dormancy checks)
ALTER TABLE customers 
ADD COLUMN IF NOT EXISTS last_contact_date TIMESTAMP WITH TIME ZONE;

-- Add conversion_probability column (0-100 percentage for lead/prospect conversion)
ALTER TABLE customers 
ADD COLUMN IF NOT EXISTS conversion_probability INTEGER;

-- Create index on last_contact_date for efficient dormancy queries
CREATE INDEX IF NOT EXISTS idx_customers_last_contact_date ON customers(last_contact_date) WHERE last_contact_date IS NOT NULL;

-- Create index on lifecycle_auto_managed for filtering
CREATE INDEX IF NOT EXISTS idx_customers_lifecycle_auto_managed ON customers(lifecycle_auto_managed);

-- Update existing customers to have lifecycle_auto_managed = TRUE (default)
UPDATE customers SET lifecycle_auto_managed = TRUE WHERE lifecycle_auto_managed IS NULL;

-- MIGRATION COMPLETE



