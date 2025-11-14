-- Migration: Add Supplier Configuration Tables
-- Description: Adds supplier management tables for multi-tenant quote system
-- Date: 2025-01-14

-- Create supplier_categories table
CREATE TABLE IF NOT EXISTS supplier_categories (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_supplier_categories_tenant ON supplier_categories(tenant_id);
CREATE INDEX IF NOT EXISTS idx_supplier_categories_active ON supplier_categories(is_active);

-- Create suppliers table
CREATE TABLE IF NOT EXISTS suppliers (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    category_id VARCHAR(36) NOT NULL,
    name VARCHAR(100) NOT NULL,
    website VARCHAR(200),
    pricing_url VARCHAR(500),
    api_key VARCHAR(200),
    notes TEXT,
    is_preferred BOOLEAN DEFAULT false NOT NULL,
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES supplier_categories(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_suppliers_tenant ON suppliers(tenant_id);
CREATE INDEX IF NOT EXISTS idx_suppliers_category ON suppliers(category_id);
CREATE INDEX IF NOT EXISTS idx_suppliers_active ON suppliers(is_active);
CREATE INDEX IF NOT EXISTS idx_suppliers_preferred ON suppliers(is_preferred);

-- Create supplier_pricing table (cached pricing)
CREATE TABLE IF NOT EXISTS supplier_pricing (
    id VARCHAR(36) PRIMARY KEY,
    supplier_id VARCHAR(36) NOT NULL,
    product_name VARCHAR(200) NOT NULL,
    product_code VARCHAR(100),
    price NUMERIC(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'GBP' NOT NULL,
    is_active BOOLEAN DEFAULT true NOT NULL,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_supplier_pricing_supplier ON supplier_pricing(supplier_id);
CREATE INDEX IF NOT EXISTS idx_supplier_pricing_product ON supplier_pricing(product_name);
CREATE INDEX IF NOT EXISTS idx_supplier_pricing_active ON supplier_pricing(is_active);
CREATE INDEX IF NOT EXISTS idx_supplier_pricing_updated ON supplier_pricing(last_updated);

-- Add supplier_id foreign key to products table (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'products' AND column_name = 'supplier_id'
    ) THEN
        ALTER TABLE products ADD COLUMN supplier_id VARCHAR(36);
        ALTER TABLE products ADD CONSTRAINT fk_products_supplier 
            FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE SET NULL;
        CREATE INDEX IF NOT EXISTS idx_products_supplier ON products(supplier_id);
    END IF;
END $$;

-- Seed default supplier categories for existing tenants
DO $$
DECLARE
    tenant_record RECORD;
BEGIN
    FOR tenant_record IN SELECT id FROM tenants LOOP
        -- WiFi/Networking category
        INSERT INTO supplier_categories (id, tenant_id, name, description, is_active)
        SELECT gen_random_uuid()::text, tenant_record.id, 'WiFi/Networking', 'Wireless access points, routers, switches', true
        WHERE NOT EXISTS (
            SELECT 1 FROM supplier_categories WHERE tenant_id = tenant_record.id AND name = 'WiFi/Networking'
        );
        
        -- Cabling category
        INSERT INTO supplier_categories (id, tenant_id, name, description, is_active)
        SELECT gen_random_uuid()::text, tenant_record.id, 'Cabling', 'Structured cabling, patch panels, connectors', true
        WHERE NOT EXISTS (
            SELECT 1 FROM supplier_categories WHERE tenant_id = tenant_record.id AND name = 'Cabling'
        );
        
        -- CCTV category
        INSERT INTO supplier_categories (id, tenant_id, name, description, is_active)
        SELECT gen_random_uuid()::text, tenant_record.id, 'CCTV', 'Security cameras, NVRs, recording equipment', true
        WHERE NOT EXISTS (
            SELECT 1 FROM supplier_categories WHERE tenant_id = tenant_record.id AND name = 'CCTV'
        );
        
        -- Door Entry category
        INSERT INTO supplier_categories (id, tenant_id, name, description, is_active)
        SELECT gen_random_uuid()::text, tenant_record.id, 'Door Entry', 'Access control, intercoms, door entry systems', true
        WHERE NOT EXISTS (
            SELECT 1 FROM supplier_categories WHERE tenant_id = tenant_record.id AND name = 'Door Entry'
        );
        
        -- Network Equipment category
        INSERT INTO supplier_categories (id, tenant_id, name, description, is_active)
        SELECT gen_random_uuid()::text, tenant_record.id, 'Network Equipment', 'Switches, routers, firewalls, network infrastructure', true
        WHERE NOT EXISTS (
            SELECT 1 FROM supplier_categories WHERE tenant_id = tenant_record.id AND name = 'Network Equipment'
        );
    END LOOP;
END $$;


