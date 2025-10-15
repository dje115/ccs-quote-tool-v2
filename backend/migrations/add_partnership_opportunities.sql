-- Add partnership_opportunities field to tenants table
-- This field stores how the tenant can work WITH businesses in similar/complementary sectors (B2B partnerships)

ALTER TABLE tenants ADD COLUMN IF NOT EXISTS partnership_opportunities TEXT;


