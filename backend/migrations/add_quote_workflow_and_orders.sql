-- Migration: Enhance quote workflow, manual builder, and order tables
-- Created: 2025-11-20
-- Description: Adds workflow tracking, extended quote item fields, customer orders, and supplier purchase orders

BEGIN;

-- ============================
-- Quote versioning / workflow fields
-- ============================
ALTER TABLE quotes
    ADD COLUMN IF NOT EXISTS version_number INTEGER NOT NULL DEFAULT 1,
    ADD COLUMN IF NOT EXISTS parent_quote_id VARCHAR(36) REFERENCES quotes(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS approval_state VARCHAR(20) NOT NULL DEFAULT 'not_required',
    ADD COLUMN IF NOT EXISTS manual_mode BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS sent_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS accepted_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS rejected_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS cancelled_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS cancel_reason TEXT;

CREATE INDEX IF NOT EXISTS idx_quotes_parent_quote_id ON quotes(parent_quote_id);
CREATE INDEX IF NOT EXISTS idx_quotes_version_number ON quotes(version_number);

-- ============================
-- Quote workflow log table
-- ============================
CREATE TABLE IF NOT EXISTS quote_workflow_log (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    quote_id VARCHAR(36) NOT NULL REFERENCES quotes(id) ON DELETE CASCADE,
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    from_status VARCHAR(20),
    to_status VARCHAR(20),
    action VARCHAR(50),
    comment TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_by VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_quote_workflow_log_quote_id ON quote_workflow_log(quote_id);
CREATE INDEX IF NOT EXISTS idx_quote_workflow_log_tenant_id ON quote_workflow_log(tenant_id);

-- ============================
-- Extend quote_items for manual builder
-- ============================
ALTER TABLE quote_items
    ADD COLUMN IF NOT EXISTS item_type VARCHAR(50) NOT NULL DEFAULT 'standard',
    ADD COLUMN IF NOT EXISTS unit_type VARCHAR(50) NOT NULL DEFAULT 'each',
    ADD COLUMN IF NOT EXISTS unit_cost NUMERIC(10, 2) DEFAULT 0,
    ADD COLUMN IF NOT EXISTS margin_percent FLOAT DEFAULT 0,
    ADD COLUMN IF NOT EXISTS tax_rate FLOAT DEFAULT 0,
    ADD COLUMN IF NOT EXISTS supplier_id VARCHAR(36) REFERENCES suppliers(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS is_optional BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS is_alternate BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS alternate_group VARCHAR(36),
    ADD COLUMN IF NOT EXISTS section_name VARCHAR(255),
    ADD COLUMN IF NOT EXISTS bundle_parent_id VARCHAR(36),
    ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'::jsonb;

CREATE INDEX IF NOT EXISTS idx_quote_items_section_name ON quote_items(section_name);
CREATE INDEX IF NOT EXISTS idx_quote_items_supplier_id ON quote_items(supplier_id);

-- ============================
-- Customer orders table
-- ============================
CREATE TABLE IF NOT EXISTS customer_orders (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    quote_id VARCHAR(36) NOT NULL UNIQUE REFERENCES quotes(id) ON DELETE CASCADE,
    status VARCHAR(30) NOT NULL DEFAULT 'draft',
    customer_po_number VARCHAR(100),
    internal_order_number VARCHAR(100),
    billing_address TEXT,
    shipping_address TEXT,
    payment_terms TEXT,
    deposit_required NUMERIC(10, 2),
    total_amount NUMERIC(12, 2),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_by VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_customer_orders_tenant_id ON customer_orders(tenant_id);
CREATE INDEX IF NOT EXISTS idx_customer_orders_status ON customer_orders(status);

-- ============================
-- Supplier purchase orders table
-- ============================
CREATE TABLE IF NOT EXISTS supplier_purchase_orders (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    customer_order_id VARCHAR(36) REFERENCES customer_orders(id) ON DELETE CASCADE,
    supplier_id VARCHAR(36) NOT NULL REFERENCES suppliers(id) ON DELETE CASCADE,
    status VARCHAR(30) NOT NULL DEFAULT 'draft',
    po_number VARCHAR(100),
    expected_date TIMESTAMPTZ,
    total_cost NUMERIC(12, 2),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_by VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_supplier_purchase_orders_tenant_id ON supplier_purchase_orders(tenant_id);
CREATE INDEX IF NOT EXISTS idx_supplier_purchase_orders_supplier_id ON supplier_purchase_orders(supplier_id);

COMMIT;

