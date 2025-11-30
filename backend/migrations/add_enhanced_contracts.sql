-- Enhanced Contracts System with AI Generation, Versioning, and JSON Placeholders
-- Migration: add_enhanced_contracts.sql

-- Create enhanced_contract_templates table (separate from support_contract contract_templates)
CREATE TABLE IF NOT EXISTS enhanced_contract_templates (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    contract_type VARCHAR(50) NOT NULL,
    ai_generated BOOLEAN DEFAULT FALSE NOT NULL,
    ai_generation_prompt TEXT,
    ai_generated_at TIMESTAMP WITH TIME ZONE,
    ai_generated_by VARCHAR(36) REFERENCES users(id),
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    is_system BOOLEAN DEFAULT FALSE NOT NULL,
    is_public BOOLEAN DEFAULT FALSE NOT NULL,
    category VARCHAR(100),
    tags JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_enhanced_template_tenant_type ON enhanced_contract_templates(tenant_id, contract_type);
CREATE INDEX IF NOT EXISTS idx_enhanced_template_active ON enhanced_contract_templates(tenant_id, is_active);
CREATE INDEX IF NOT EXISTS idx_enhanced_template_name ON enhanced_contract_templates(name);

-- Create contract_template_versions table for versioning
CREATE TABLE IF NOT EXISTS contract_template_versions (
    id VARCHAR(36) PRIMARY KEY,
    template_id VARCHAR(36) NOT NULL REFERENCES enhanced_contract_templates(id) ON DELETE CASCADE,
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    version_name VARCHAR(100),
    is_current BOOLEAN DEFAULT FALSE NOT NULL,
    template_content TEXT NOT NULL,
    placeholder_schema JSONB,
    default_values JSONB,
    description TEXT,
    created_by VARCHAR(36) REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    CONSTRAINT unique_template_version UNIQUE (template_id, version_number)
);

CREATE INDEX IF NOT EXISTS idx_template_version ON contract_template_versions(template_id, version_number);
CREATE INDEX IF NOT EXISTS idx_template_current ON contract_template_versions(template_id, is_current);
CREATE INDEX IF NOT EXISTS idx_template_version_tenant ON contract_template_versions(tenant_id);

-- Create contracts table (enhanced from support_contracts)
CREATE TABLE IF NOT EXISTS contracts (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    customer_id VARCHAR(36) NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    template_id VARCHAR(36) REFERENCES enhanced_contract_templates(id),
    template_version_id VARCHAR(36) REFERENCES contract_template_versions(id),
    contract_number VARCHAR(100) UNIQUE NOT NULL,
    contract_name VARCHAR(255) NOT NULL,
    description TEXT,
    contract_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'draft' NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    renewal_date DATE,
    signed_date DATE,
    monthly_value NUMERIC(12, 2),
    annual_value NUMERIC(12, 2),
    setup_fee NUMERIC(12, 2) DEFAULT 0 NOT NULL,
    currency VARCHAR(3) DEFAULT 'GBP' NOT NULL,
    contract_content TEXT NOT NULL,
    placeholder_values JSONB,
    terms TEXT,
    sla_level VARCHAR(50),
    included_services JSONB,
    excluded_services JSONB,
    opportunity_id VARCHAR(36) REFERENCES opportunities(id),
    quote_id VARCHAR(36) REFERENCES quotes(id),
    requires_signature BOOLEAN DEFAULT TRUE NOT NULL,
    signed_by_customer BOOLEAN DEFAULT FALSE NOT NULL,
    signed_by_company BOOLEAN DEFAULT FALSE NOT NULL,
    customer_signed_at TIMESTAMP WITH TIME ZONE,
    company_signed_at TIMESTAMP WITH TIME ZONE,
    signed_by_user_id VARCHAR(36) REFERENCES users(id),
    notes TEXT,
    metadata JSONB,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_contract_tenant_customer ON contracts(tenant_id, customer_id);
CREATE INDEX IF NOT EXISTS idx_contract_status_type ON contracts(status, contract_type);
CREATE INDEX IF NOT EXISTS idx_contract_opportunity ON contracts(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_contract_template ON contracts(template_id);
CREATE INDEX IF NOT EXISTS idx_contract_number ON contracts(contract_number);
CREATE INDEX IF NOT EXISTS idx_contract_customer ON contracts(customer_id);

-- Add contract_ids to opportunities table
ALTER TABLE opportunities 
ADD COLUMN IF NOT EXISTS contract_ids JSONB;

-- Create function to generate contract numbers
CREATE OR REPLACE FUNCTION generate_contract_number(tenant_prefix TEXT DEFAULT 'CON')
RETURNS TEXT AS $$
DECLARE
    new_number TEXT;
    year_part TEXT;
    seq_num INTEGER;
BEGIN
    year_part := TO_CHAR(NOW(), 'YY');
    
    -- Get next sequence number for this year
    SELECT COALESCE(MAX(CAST(SUBSTRING(contract_number FROM '[0-9]+$') AS INTEGER)), 0) + 1
    INTO seq_num
    FROM contracts
    WHERE contract_number LIKE tenant_prefix || '-' || year_part || '-%';
    
    new_number := tenant_prefix || '-' || year_part || '-' || LPAD(seq_num::TEXT, 6, '0');
    RETURN new_number;
END;
$$ LANGUAGE plpgsql;

