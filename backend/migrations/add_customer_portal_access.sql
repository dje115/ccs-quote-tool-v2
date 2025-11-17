-- Add customer portal access fields to customers table
ALTER TABLE customers 
ADD COLUMN IF NOT EXISTS portal_access_enabled BOOLEAN NOT NULL DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS portal_access_token VARCHAR(255) UNIQUE,
ADD COLUMN IF NOT EXISTS portal_access_token_generated_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS portal_permissions JSONB;

-- Create index on portal_access_token for faster lookups
CREATE INDEX IF NOT EXISTS idx_customers_portal_token ON customers(portal_access_token) WHERE portal_access_token IS NOT NULL;

-- Add comment to explain the fields
COMMENT ON COLUMN customers.portal_access_enabled IS 'Enable customer portal access for this customer';
COMMENT ON COLUMN customers.portal_access_token IS 'Unique token for customer portal authentication';
COMMENT ON COLUMN customers.portal_access_token_generated_at IS 'Timestamp when portal access token was generated';
COMMENT ON COLUMN customers.portal_permissions IS 'JSON object with granular permissions: {"tickets": true, "quotes": true, "orders": true, "reporting": true}';

