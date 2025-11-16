-- Support Contracts Tables Migration
-- Creates tables for managing support contracts, renewals, and templates

-- Create enum types
DO $$ BEGIN
    CREATE TYPE contracttype AS ENUM (
        'managed_services',
        'maintenance',
        'saas_subscription',
        'support_hours',
        'warranty',
        'consulting'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE contractstatus AS ENUM (
        'draft',
        'active',
        'pending_renewal',
        'expired',
        'cancelled',
        'suspended'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE renewalfrequency AS ENUM (
        'monthly',
        'quarterly',
        'semi_annual',
        'annual',
        'biennial',
        'triennial',
        'one_time'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Support Contracts table
CREATE TABLE IF NOT EXISTS support_contracts (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    customer_id VARCHAR(36) NOT NULL,
    
    -- Contract identification
    contract_number VARCHAR(100) UNIQUE NOT NULL,
    contract_name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Contract type and status
    contract_type contracttype NOT NULL,
    status contractstatus NOT NULL DEFAULT 'draft',
    
    -- Dates
    start_date DATE NOT NULL,
    end_date DATE,
    renewal_date DATE,
    renewal_frequency renewalfrequency,
    auto_renew BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- Financials
    monthly_value NUMERIC(12, 2),
    annual_value NUMERIC(12, 2),
    setup_fee NUMERIC(12, 2) NOT NULL DEFAULT 0,
    currency VARCHAR(3) NOT NULL DEFAULT 'GBP',
    
    -- Contract details
    terms TEXT,
    sla_level VARCHAR(50),
    included_services JSONB,
    excluded_services JSONB,
    support_hours_included INTEGER,
    support_hours_used INTEGER NOT NULL DEFAULT 0,
    
    -- Renewal and cancellation
    renewal_notice_days INTEGER NOT NULL DEFAULT 90,
    cancellation_notice_days INTEGER NOT NULL DEFAULT 30,
    cancellation_reason TEXT,
    cancelled_at TIMESTAMP,
    cancelled_by VARCHAR(36),
    
    -- Related records
    quote_id VARCHAR(36),
    opportunity_id VARCHAR(36),
    
    -- Notes and metadata
    notes TEXT,
    contract_metadata JSONB,
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign keys
    CONSTRAINT fk_support_contracts_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
    CONSTRAINT fk_support_contracts_customer FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
    CONSTRAINT fk_support_contracts_quote FOREIGN KEY (quote_id) REFERENCES quotes(id) ON DELETE SET NULL,
    CONSTRAINT fk_support_contracts_cancelled_by FOREIGN KEY (cancelled_by) REFERENCES users(id) ON DELETE SET NULL
);

-- Indexes for support_contracts
CREATE INDEX IF NOT EXISTS idx_support_contracts_tenant_id ON support_contracts(tenant_id);
CREATE INDEX IF NOT EXISTS idx_support_contracts_customer_id ON support_contracts(customer_id);
CREATE INDEX IF NOT EXISTS idx_support_contracts_contract_number ON support_contracts(contract_number);
CREATE INDEX IF NOT EXISTS idx_support_contracts_start_date ON support_contracts(start_date);
CREATE INDEX IF NOT EXISTS idx_support_contracts_end_date ON support_contracts(end_date);
CREATE INDEX IF NOT EXISTS idx_support_contracts_renewal_date ON support_contracts(renewal_date);
CREATE INDEX IF NOT EXISTS idx_support_contracts_status ON support_contracts(status);
CREATE INDEX IF NOT EXISTS idx_support_contracts_contract_type ON support_contracts(contract_type);
CREATE INDEX IF NOT EXISTS idx_support_contracts_quote_id ON support_contracts(quote_id);
CREATE INDEX IF NOT EXISTS idx_contract_tenant_customer ON support_contracts(tenant_id, customer_id);
CREATE INDEX IF NOT EXISTS idx_contract_renewal_date ON support_contracts(renewal_date);
CREATE INDEX IF NOT EXISTS idx_contract_status_type ON support_contracts(status, contract_type);

-- Contract Renewals table
CREATE TABLE IF NOT EXISTS contract_renewals (
    id VARCHAR(36) PRIMARY KEY,
    contract_id VARCHAR(36) NOT NULL,
    tenant_id VARCHAR(36) NOT NULL,
    
    -- Renewal details
    renewal_date DATE NOT NULL,
    previous_end_date DATE,
    new_end_date DATE,
    
    -- Financial changes
    previous_monthly_value NUMERIC(12, 2),
    new_monthly_value NUMERIC(12, 2),
    previous_annual_value NUMERIC(12, 2),
    new_annual_value NUMERIC(12, 2),
    
    -- Status
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    renewal_type VARCHAR(50),
    
    -- Actions
    reminder_sent_at TIMESTAMP,
    reminder_sent_to VARCHAR(36),
    approved_at TIMESTAMP,
    approved_by VARCHAR(36),
    completed_at TIMESTAMP,
    declined_at TIMESTAMP,
    declined_reason TEXT,
    
    -- Notes
    notes TEXT,
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign keys
    CONSTRAINT fk_contract_renewals_contract FOREIGN KEY (contract_id) REFERENCES support_contracts(id) ON DELETE CASCADE,
    CONSTRAINT fk_contract_renewals_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
    CONSTRAINT fk_contract_renewals_reminder_sent_to FOREIGN KEY (reminder_sent_to) REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT fk_contract_renewals_approved_by FOREIGN KEY (approved_by) REFERENCES users(id) ON DELETE SET NULL
);

-- Indexes for contract_renewals
CREATE INDEX IF NOT EXISTS idx_contract_renewals_contract_id ON contract_renewals(contract_id);
CREATE INDEX IF NOT EXISTS idx_contract_renewals_tenant_id ON contract_renewals(tenant_id);
CREATE INDEX IF NOT EXISTS idx_contract_renewals_renewal_date ON contract_renewals(renewal_date);
CREATE INDEX IF NOT EXISTS idx_contract_renewals_status ON contract_renewals(status);
CREATE INDEX IF NOT EXISTS idx_renewal_contract_date ON contract_renewals(contract_id, renewal_date);
CREATE INDEX IF NOT EXISTS idx_renewal_status ON contract_renewals(status);

-- Contract Templates table
CREATE TABLE IF NOT EXISTS contract_templates (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    
    -- Template details
    name VARCHAR(255) NOT NULL,
    description TEXT,
    contract_type contracttype NOT NULL,
    
    -- Template content
    terms_template TEXT,
    included_services_template JSONB,
    sla_level VARCHAR(50),
    
    -- Default values
    default_renewal_frequency renewalfrequency,
    default_renewal_notice_days INTEGER NOT NULL DEFAULT 90,
    default_cancellation_notice_days INTEGER NOT NULL DEFAULT 30,
    default_monthly_value NUMERIC(12, 2),
    default_annual_value NUMERIC(12, 2),
    
    -- Status
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_system BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign keys
    CONSTRAINT fk_contract_templates_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);

-- Indexes for contract_templates
CREATE INDEX IF NOT EXISTS idx_contract_templates_tenant_id ON contract_templates(tenant_id);
CREATE INDEX IF NOT EXISTS idx_contract_templates_contract_type ON contract_templates(contract_type);
CREATE INDEX IF NOT EXISTS idx_contract_templates_is_active ON contract_templates(is_active);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_support_contracts_updated_at BEFORE UPDATE ON support_contracts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_contract_renewals_updated_at BEFORE UPDATE ON contract_renewals
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_contract_templates_updated_at BEFORE UPDATE ON contract_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to generate contract number
CREATE OR REPLACE FUNCTION generate_contract_number(tenant_slug TEXT)
RETURNS TEXT AS $$
DECLARE
    new_number TEXT;
    counter INTEGER := 1;
BEGIN
    LOOP
        new_number := UPPER(tenant_slug) || '-CON-' || TO_CHAR(CURRENT_DATE, 'YYYY') || '-' || LPAD(counter::TEXT, 5, '0');
        
        IF NOT EXISTS (SELECT 1 FROM support_contracts WHERE contract_number = new_number) THEN
            RETURN new_number;
        END IF;
        
        counter := counter + 1;
        
        IF counter > 99999 THEN
            RAISE EXCEPTION 'Unable to generate unique contract number';
        END IF;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

