-- Migration: Enhance quotes table with v1 fields
-- Created: 2025-01-XX
-- Description: Adds fields from v1 quote system to support full quote functionality

-- Add project details fields
ALTER TABLE quotes ADD COLUMN IF NOT EXISTS project_title VARCHAR(200);
ALTER TABLE quotes ADD COLUMN IF NOT EXISTS project_description TEXT;
ALTER TABLE quotes ADD COLUMN IF NOT EXISTS site_address TEXT;

-- Add building/project details
ALTER TABLE quotes ADD COLUMN IF NOT EXISTS building_type VARCHAR(100);
ALTER TABLE quotes ADD COLUMN IF NOT EXISTS building_size FLOAT; -- in square meters
ALTER TABLE quotes ADD COLUMN IF NOT EXISTS number_of_floors INTEGER DEFAULT 1;
ALTER TABLE quotes ADD COLUMN IF NOT EXISTS number_of_rooms INTEGER DEFAULT 1;

-- Add requirements fields
ALTER TABLE quotes ADD COLUMN IF NOT EXISTS cabling_type VARCHAR(50); -- cat5e, cat6, fiber
ALTER TABLE quotes ADD COLUMN IF NOT EXISTS wifi_requirements BOOLEAN DEFAULT false;
ALTER TABLE quotes ADD COLUMN IF NOT EXISTS cctv_requirements BOOLEAN DEFAULT false;
ALTER TABLE quotes ADD COLUMN IF NOT EXISTS door_entry_requirements BOOLEAN DEFAULT false;
ALTER TABLE quotes ADD COLUMN IF NOT EXISTS special_requirements TEXT;

-- Add travel cost fields
ALTER TABLE quotes ADD COLUMN IF NOT EXISTS travel_distance_km FLOAT;
ALTER TABLE quotes ADD COLUMN IF NOT EXISTS travel_time_minutes FLOAT;
ALTER TABLE quotes ADD COLUMN IF NOT EXISTS travel_cost NUMERIC(10, 2);

-- Add AI analysis fields (JSON)
ALTER TABLE quotes ADD COLUMN IF NOT EXISTS ai_analysis JSONB;
ALTER TABLE quotes ADD COLUMN IF NOT EXISTS recommended_products JSONB;
ALTER TABLE quotes ADD COLUMN IF NOT EXISTS labour_breakdown JSONB;
ALTER TABLE quotes ADD COLUMN IF NOT EXISTS quotation_details JSONB;

-- Add estimated fields
ALTER TABLE quotes ADD COLUMN IF NOT EXISTS estimated_time INTEGER; -- hours
ALTER TABLE quotes ADD COLUMN IF NOT EXISTS estimated_cost NUMERIC(10, 2);

-- Add created_by relationship (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'quotes' AND column_name = 'created_by'
    ) THEN
        ALTER TABLE quotes ADD COLUMN created_by VARCHAR(36);
        ALTER TABLE quotes ADD CONSTRAINT fk_quotes_created_by 
            FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;
    END IF;
END $$;

-- Create products table (migrate from v1 PricingItem)
CREATE TABLE IF NOT EXISTS products (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    code VARCHAR(100),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    subcategory VARCHAR(100),
    unit VARCHAR(50) DEFAULT 'each' NOT NULL, -- meter, piece, hour, day, etc.
    base_price NUMERIC(10, 2) NOT NULL,
    cost_price NUMERIC(10, 2),
    supplier VARCHAR(100),
    part_number VARCHAR(100),
    is_active BOOLEAN DEFAULT true NOT NULL,
    is_service BOOLEAN DEFAULT false NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);

-- Create pricing_rules table
CREATE TABLE IF NOT EXISTS pricing_rules (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    name VARCHAR(200) NOT NULL,
    rule_type VARCHAR(50) NOT NULL, -- volume_discount, bundle, seasonal
    conditions JSONB NOT NULL,
    discount_percentage NUMERIC(5, 2),
    discount_amount NUMERIC(10, 2),
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);

-- Create quote_versions table for quote versioning
CREATE TABLE IF NOT EXISTS quote_versions (
    id VARCHAR(36) PRIMARY KEY,
    quote_id VARCHAR(36) NOT NULL,
    version INTEGER NOT NULL,
    quote_data JSONB NOT NULL, -- Full quote snapshot
    created_by VARCHAR(36),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    FOREIGN KEY (quote_id) REFERENCES quotes(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_products_tenant_id ON products(tenant_id);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_is_active ON products(is_active);
CREATE INDEX IF NOT EXISTS idx_pricing_rules_tenant_id ON pricing_rules(tenant_id);
CREATE INDEX IF NOT EXISTS idx_quote_versions_quote_id ON quote_versions(quote_id);
CREATE INDEX IF NOT EXISTS idx_quotes_created_by ON quotes(created_by);

-- Add RLS policies (if RLS is enabled)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'quotes') THEN
        -- RLS already configured
        RAISE NOTICE 'RLS policies already exist for quotes';
    ELSE
        -- Enable RLS
        ALTER TABLE products ENABLE ROW LEVEL SECURITY;
        ALTER TABLE pricing_rules ENABLE ROW LEVEL SECURITY;
        ALTER TABLE quote_versions ENABLE ROW LEVEL SECURITY;
    END IF;
END $$;




