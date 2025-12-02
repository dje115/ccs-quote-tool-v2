-- Migration: Add own products support to suppliers
-- Created: 2025-11-24
-- Description: Ensures is_own_products field exists and adds index

-- Add is_own_products column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'suppliers' AND column_name = 'is_own_products'
    ) THEN
        ALTER TABLE suppliers ADD COLUMN is_own_products BOOLEAN DEFAULT FALSE NOT NULL;
        CREATE INDEX IF NOT EXISTS idx_suppliers_own_products ON suppliers(tenant_id, is_own_products);
        COMMENT ON COLUMN suppliers.is_own_products IS 'True for tenant''s own products/services (hire rates, hosting, etc.)';
    END IF;
END $$;

