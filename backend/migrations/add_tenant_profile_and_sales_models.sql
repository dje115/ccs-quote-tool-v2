-- Migration: Add tenant profile and sales activity models
-- Date: 2025-10-12
-- Description: Adds tenant company profile fields and sales activity tracking tables

-- ============================================================================
-- 1. ADD TENANT PROFILE FIELDS
-- ============================================================================

-- Add company profile fields to tenants table
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS company_description TEXT;
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS products_services JSONB DEFAULT '[]'::jsonb;
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS unique_selling_points JSONB DEFAULT '[]'::jsonb;
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS target_markets JSONB DEFAULT '[]'::jsonb;
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS sales_methodology VARCHAR(100);
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS elevator_pitch TEXT;

-- Add AI analysis fields
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS company_analysis JSONB DEFAULT '{}'::jsonb;
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS company_analysis_date TIMESTAMP WITH TIME ZONE;

COMMENT ON COLUMN tenants.company_description IS 'What does the tenant company do? Used for AI-powered sales guidance.';
COMMENT ON COLUMN tenants.products_services IS 'List of products/services offered. JSON array of strings.';
COMMENT ON COLUMN tenants.unique_selling_points IS 'USPs that differentiate the tenant. JSON array of strings.';
COMMENT ON COLUMN tenants.target_markets IS 'Industries/sectors the tenant targets. JSON array of strings.';
COMMENT ON COLUMN tenants.sales_methodology IS 'Preferred sales approach (e.g., consultative, solution-based)';
COMMENT ON COLUMN tenants.elevator_pitch IS '30-second company pitch';
COMMENT ON COLUMN tenants.company_analysis IS 'AI-generated analysis of tenant business. Used for intelligent sales guidance.';
COMMENT ON COLUMN tenants.company_analysis_date IS 'When AI analysis was last run on tenant company';

-- ============================================================================
-- 2. CREATE SALES ACTIVITY ENUM TYPES
-- ============================================================================

-- Create activity type enum
DO $$ BEGIN
    CREATE TYPE activitytype AS ENUM ('call', 'meeting', 'email', 'note', 'task');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create activity outcome enum
DO $$ BEGIN
    CREATE TYPE activityoutcome AS ENUM (
        'successful',
        'no_answer',
        'voicemail',
        'follow_up_required',
        'not_interested',
        'meeting_scheduled',
        'quote_requested',
        'won',
        'lost'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- ============================================================================
-- 3. CREATE SALES_ACTIVITIES TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS sales_activities (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    customer_id VARCHAR(36) NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    contact_id VARCHAR(36) REFERENCES contacts(id) ON DELETE SET NULL,
    
    -- Activity details
    activity_type activitytype NOT NULL,
    activity_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    duration_minutes INTEGER,
    
    -- Content
    subject VARCHAR(255),
    notes TEXT NOT NULL,
    outcome activityoutcome,
    
    -- AI assistance tracking
    ai_suggestions_used JSONB DEFAULT '[]'::jsonb,
    ai_context JSONB DEFAULT '{}'::jsonb,
    
    -- Follow-up
    follow_up_required BOOLEAN DEFAULT FALSE,
    follow_up_date TIMESTAMP WITH TIME ZONE,
    follow_up_notes TEXT,
    
    -- Additional metadata
    additional_data JSONB DEFAULT '{}'::jsonb,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    CONSTRAINT fk_sales_activities_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id),
    CONSTRAINT fk_sales_activities_customer FOREIGN KEY (customer_id) REFERENCES customers(id),
    CONSTRAINT fk_sales_activities_user FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT fk_sales_activities_contact FOREIGN KEY (contact_id) REFERENCES contacts(id)
);

-- Create indexes for sales_activities
CREATE INDEX IF NOT EXISTS idx_sales_activities_tenant ON sales_activities(tenant_id);
CREATE INDEX IF NOT EXISTS idx_sales_activities_customer ON sales_activities(customer_id);
CREATE INDEX IF NOT EXISTS idx_sales_activities_user ON sales_activities(user_id);
CREATE INDEX IF NOT EXISTS idx_sales_activities_contact ON sales_activities(contact_id);
CREATE INDEX IF NOT EXISTS idx_sales_activities_date ON sales_activities(activity_date DESC);
CREATE INDEX IF NOT EXISTS idx_sales_activities_type ON sales_activities(activity_type);

COMMENT ON TABLE sales_activities IS 'Tracks all sales interactions (calls, meetings, emails) with comprehensive audit trail';
COMMENT ON COLUMN sales_activities.notes IS 'Detailed notes: what was discussed, pain points, objections, next steps';
COMMENT ON COLUMN sales_activities.ai_suggestions_used IS 'Track which AI suggestions were used in this interaction';
COMMENT ON COLUMN sales_activities.ai_context IS 'Store AI context provided for this interaction';

-- ============================================================================
-- 4. CREATE SALES_NOTES TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS sales_notes (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    customer_id VARCHAR(36) NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Note content
    note TEXT NOT NULL,
    is_important BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    CONSTRAINT fk_sales_notes_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id),
    CONSTRAINT fk_sales_notes_customer FOREIGN KEY (customer_id) REFERENCES customers(id),
    CONSTRAINT fk_sales_notes_user FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Create indexes for sales_notes
CREATE INDEX IF NOT EXISTS idx_sales_notes_tenant ON sales_notes(tenant_id);
CREATE INDEX IF NOT EXISTS idx_sales_notes_customer ON sales_notes(customer_id);
CREATE INDEX IF NOT EXISTS idx_sales_notes_user ON sales_notes(user_id);
CREATE INDEX IF NOT EXISTS idx_sales_notes_created ON sales_notes(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_sales_notes_important ON sales_notes(is_important) WHERE is_important = TRUE;

COMMENT ON TABLE sales_notes IS 'Quick sales notes for observations, reminders, and strategic notes';
COMMENT ON COLUMN sales_notes.is_important IS 'Pin important notes to top';

-- ============================================================================
-- 5. CREATE TRIGGERS FOR UPDATED_AT
-- ============================================================================

-- Trigger function for updating updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add triggers
DROP TRIGGER IF EXISTS update_sales_activities_updated_at ON sales_activities;
CREATE TRIGGER update_sales_activities_updated_at
    BEFORE UPDATE ON sales_activities
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_sales_notes_updated_at ON sales_notes;
CREATE TRIGGER update_sales_notes_updated_at
    BEFORE UPDATE ON sales_notes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- Verify tables exist
SELECT 
    'Tenant profile fields added' AS status,
    COUNT(*) AS count
FROM information_schema.columns
WHERE table_name = 'tenants'
AND column_name IN ('company_description', 'products_services', 'company_analysis');

SELECT 
    'Sales tables created' AS status,
    COUNT(*) AS count
FROM information_schema.tables
WHERE table_name IN ('sales_activities', 'sales_notes');

