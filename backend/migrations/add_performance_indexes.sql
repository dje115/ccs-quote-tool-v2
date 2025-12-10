-- Migration: Add performance indexes for frequently queried fields
-- Purpose: Improve query performance for common access patterns

-- Customer indexes
CREATE INDEX IF NOT EXISTS idx_customers_tenant_status_deleted ON customers(tenant_id, status, is_deleted);
CREATE INDEX IF NOT EXISTS idx_customers_tenant_sector ON customers(tenant_id, business_sector) WHERE is_deleted = false;
CREATE INDEX IF NOT EXISTS idx_customers_tenant_competitor ON customers(tenant_id, is_competitor) WHERE is_deleted = false;
CREATE INDEX IF NOT EXISTS idx_customers_company_name_trgm ON customers USING gin(company_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_customers_last_contact_date ON customers(tenant_id, last_contact_date) WHERE last_contact_date IS NOT NULL;

-- Sales Activity indexes
CREATE INDEX IF NOT EXISTS idx_sales_activities_customer_tenant ON sales_activities(customer_id, tenant_id);
CREATE INDEX IF NOT EXISTS idx_sales_activities_follow_up_date ON sales_activities(tenant_id, follow_up_date) WHERE follow_up_date IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_sales_activities_activity_date ON sales_activities(tenant_id, activity_date);

-- Ticket indexes (if not already exist)
CREATE INDEX IF NOT EXISTS idx_tickets_customer_tenant ON tickets(customer_id, tenant_id);
CREATE INDEX IF NOT EXISTS idx_tickets_status_priority ON tickets(tenant_id, status, priority);
CREATE INDEX IF NOT EXISTS idx_tickets_created_at ON tickets(tenant_id, created_at DESC);

-- Contact indexes
CREATE INDEX IF NOT EXISTS idx_contacts_customer_tenant ON contacts(customer_id, tenant_id) WHERE is_deleted = false;

-- Quote indexes
CREATE INDEX IF NOT EXISTS idx_quotes_customer_tenant ON quotes(customer_id, tenant_id);
CREATE INDEX IF NOT EXISTS idx_quotes_status_created ON quotes(tenant_id, status, created_at DESC);

-- Opportunity indexes
CREATE INDEX IF NOT EXISTS idx_opportunities_customer_tenant ON opportunities(customer_id, tenant_id);
CREATE INDEX IF NOT EXISTS idx_opportunities_stage_tenant ON opportunities(tenant_id, stage);

-- Enable pg_trgm extension for fuzzy text search (if not already enabled)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

COMMENT ON INDEX idx_customers_company_name_trgm IS 'GIN index for fast text search on company names';
COMMENT ON INDEX idx_customers_tenant_status_deleted IS 'Composite index for common customer list queries';
COMMENT ON INDEX idx_sales_activities_follow_up_date IS 'Index for NPA (Next Point of Action) queries';

