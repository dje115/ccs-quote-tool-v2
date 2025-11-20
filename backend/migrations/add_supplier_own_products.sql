-- Migration: Add Own Products support to suppliers
-- Created: 2025-11-19
-- Description: Adds is_own_products flag and makes category_id nullable for Own Products

-- Make category_id nullable (for Own Products that don't need a category)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'suppliers' AND column_name = 'category_id' AND is_nullable = 'NO'
    ) THEN
        ALTER TABLE suppliers ALTER COLUMN category_id DROP NOT NULL;
        COMMENT ON COLUMN suppliers.category_id IS 'Nullable for Own Products - Own Products may not need a category';
    END IF;
END $$;

-- Add is_own_products flag
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'suppliers' AND column_name = 'is_own_products'
    ) THEN
        ALTER TABLE suppliers ADD COLUMN is_own_products BOOLEAN DEFAULT FALSE NOT NULL;
        CREATE INDEX IF NOT EXISTS idx_suppliers_is_own_products ON suppliers(is_own_products);
        COMMENT ON COLUMN suppliers.is_own_products IS 'True for tenant''s own products/services (hire rates, hosting rates, etc.)';
    END IF;
END $$;

