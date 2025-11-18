-- Migration: Add Tenant Pricing Configuration Tables
-- Creates tables for centralized tenant-specific pricing: day rates, bundles, managed services

-- Create tenant_pricing_configs table
CREATE TABLE IF NOT EXISTS tenant_pricing_configs (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(36) NOT NULL,
    
    -- Configuration type
    config_type VARCHAR(50) NOT NULL,
    
    -- Basic information
    name VARCHAR(200) NOT NULL,
    description TEXT,
    code VARCHAR(100),
    
    -- Pricing details
    base_rate NUMERIC(10, 2),
    unit VARCHAR(50),
    
    -- Configuration data (JSON)
    config_data JSONB,
    
    -- Validity and conditions
    valid_from TIMESTAMP WITH TIME ZONE,
    valid_until TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- Priority/order
    priority INTEGER NOT NULL DEFAULT 0,
    
    -- Versioning
    version INTEGER NOT NULL DEFAULT 1,
    parent_config_id VARCHAR(36),
    
    -- Soft delete and timestamps
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_config_id) REFERENCES tenant_pricing_configs(id) ON DELETE SET NULL
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_pricing_config_tenant_type_active ON tenant_pricing_configs(tenant_id, config_type, is_active);
CREATE INDEX IF NOT EXISTS idx_pricing_config_code ON tenant_pricing_configs(code);
CREATE INDEX IF NOT EXISTS idx_pricing_config_type ON tenant_pricing_configs(config_type);
CREATE INDEX IF NOT EXISTS idx_pricing_config_active ON tenant_pricing_configs(is_active);

-- Create pricing_bundle_items table
CREATE TABLE IF NOT EXISTS pricing_bundle_items (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(36) NOT NULL,
    bundle_config_id VARCHAR(36) NOT NULL,
    
    -- Item details
    item_type VARCHAR(50) NOT NULL,
    item_id VARCHAR(36),
    item_name VARCHAR(200) NOT NULL,
    item_code VARCHAR(100),
    
    -- Quantity and pricing
    quantity NUMERIC(10, 2) NOT NULL DEFAULT 1,
    unit_price NUMERIC(10, 2),
    bundle_price NUMERIC(10, 2),
    
    -- Order within bundle
    display_order INTEGER NOT NULL DEFAULT 0,
    
    -- Additional data
    item_data JSONB,
    
    -- Soft delete and timestamps
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
    FOREIGN KEY (bundle_config_id) REFERENCES tenant_pricing_configs(id) ON DELETE CASCADE
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_bundle_items_bundle ON pricing_bundle_items(bundle_config_id, display_order);
CREATE INDEX IF NOT EXISTS idx_bundle_items_type ON pricing_bundle_items(item_type);



