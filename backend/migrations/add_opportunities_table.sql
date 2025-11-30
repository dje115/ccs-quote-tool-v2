-- Migration: Add opportunities table for CRM pipeline management
-- This migration creates the opportunities table to track deals through sales pipeline stages

-- Create OpportunityStage enum type
DO $$ BEGIN
    CREATE TYPE opportunitystage AS ENUM (
        'qualified',
        'scoping',
        'proposal_sent',
        'negotiation',
        'verbal_yes',
        'closed_won',
        'closed_lost'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create opportunities table
CREATE TABLE IF NOT EXISTS opportunities (
    id VARCHAR(36) PRIMARY KEY,
    customer_id VARCHAR(36) NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- Basic information
    title VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Pipeline stage
    stage opportunitystage NOT NULL DEFAULT 'qualified',
    
    -- Deal metrics
    conversion_probability INTEGER NOT NULL DEFAULT 20,  -- 0-100 percentage
    potential_deal_date TIMESTAMP WITH TIME ZONE,
    estimated_value NUMERIC(10, 2),
    
    -- Related entities (stored as JSON arrays of IDs)
    quote_ids JSONB,
    support_contract_ids JSONB,
    
    -- Attachments and notes
    attachments JSONB,  -- Array of file references
    notes TEXT,
    
    -- Recurring quote schedule (for subscription/recurring deals)
    recurring_quote_schedule JSONB,
    
    -- User tracking
    created_by VARCHAR(36),
    updated_by VARCHAR(36),
    
    -- Timestamps (from BaseModel)
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Constraints
    CONSTRAINT chk_conversion_probability CHECK (conversion_probability >= 0 AND conversion_probability <= 100)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_opportunities_customer_id ON opportunities(customer_id);
CREATE INDEX IF NOT EXISTS idx_opportunities_tenant_id ON opportunities(tenant_id);
CREATE INDEX IF NOT EXISTS idx_opportunities_stage ON opportunities(stage);
CREATE INDEX IF NOT EXISTS idx_opportunities_created_at ON opportunities(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_opportunities_is_deleted ON opportunities(is_deleted) WHERE is_deleted = FALSE;

-- Create index on quote_ids for efficient lookups (using GIN index for JSONB)
CREATE INDEX IF NOT EXISTS idx_opportunities_quote_ids ON opportunities USING GIN (quote_ids) WHERE quote_ids IS NOT NULL;

-- Add comment to table
COMMENT ON TABLE opportunities IS 'Sales opportunities tracking deals through pipeline stages from qualification to close';
COMMENT ON COLUMN opportunities.stage IS 'Current pipeline stage: qualified, scoping, proposal_sent, negotiation, verbal_yes, closed_won, closed_lost';
COMMENT ON COLUMN opportunities.conversion_probability IS 'Probability of closing this deal (0-100 percentage)';
COMMENT ON COLUMN opportunities.quote_ids IS 'Array of quote IDs linked to this opportunity (JSONB)';
COMMENT ON COLUMN opportunities.support_contract_ids IS 'Array of support contract IDs linked to this opportunity (JSONB)';
COMMENT ON COLUMN opportunities.attachments IS 'Array of file attachments: [{"name": "...", "url": "...", "uploaded_at": "..."}]';
COMMENT ON COLUMN opportunities.recurring_quote_schedule IS 'Schedule for recurring quotes: {"frequency": "monthly|quarterly|annually", "start_date": "...", "end_date": "..."}';

-- MIGRATION COMPLETE

