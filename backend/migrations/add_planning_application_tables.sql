-- Migration: Add Planning Application tables for UK county-based planning monitoring
-- Date: 2025-01-22
-- Description: Creates tables for planning application campaigns, applications, and keywords

-- ============================================================================
-- 1. CREATE ENUMS
-- ============================================================================

-- Planning application status enum
CREATE TYPE planningapplicationstatus AS ENUM (
    'validated',
    'under_review', 
    'approved',
    'refused',
    'withdrawn',
    'other'
);

-- Planning campaign status enum
CREATE TYPE planningcampaignstatus AS ENUM (
    'draft',
    'active',
    'paused', 
    'completed',
    'failed'
);

-- Application type enum
CREATE TYPE applicationtype AS ENUM (
    'commercial',
    'residential',
    'industrial',
    'mixed_use',
    'change_of_use',
    'minor',
    'other'
);

-- ============================================================================
-- 2. CREATE PLANNING APPLICATION CAMPAIGNS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS planning_application_campaigns (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    tenant_id VARCHAR(36) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    county VARCHAR(100) NOT NULL,
    source_portal VARCHAR(100) NOT NULL,
    
    -- Filtering settings (tenant-specific)
    application_types JSONB DEFAULT NULL,
    include_residential BOOLEAN DEFAULT FALSE NOT NULL,
    include_commercial BOOLEAN DEFAULT TRUE NOT NULL,
    include_industrial BOOLEAN DEFAULT TRUE NOT NULL,
    include_change_of_use BOOLEAN DEFAULT TRUE NOT NULL,
    
    -- Keyword filtering (tenant-specific)
    keyword_filters JSONB DEFAULT NULL,
    exclude_keywords JSONB DEFAULT NULL,
    
    -- Geographic filtering
    center_postcode VARCHAR(20),
    radius_miles INTEGER DEFAULT 50 NOT NULL,
    
    -- Data retention settings
    days_to_monitor INTEGER DEFAULT 14 NOT NULL,
    max_results_per_run INTEGER DEFAULT 300 NOT NULL,
    
    -- Scheduling configuration
    status planningcampaignstatus DEFAULT 'draft' NOT NULL,
    is_scheduled BOOLEAN DEFAULT FALSE NOT NULL,
    schedule_frequency_days INTEGER DEFAULT 14 NOT NULL,
    last_run_at TIMESTAMP WITH TIME ZONE,
    next_run_at TIMESTAMP WITH TIME ZONE,
    
    -- AI Analysis settings
    enable_ai_analysis BOOLEAN DEFAULT TRUE NOT NULL,
    max_ai_analysis_per_run INTEGER DEFAULT 20 NOT NULL,
    
    -- Results tracking
    total_applications_found INTEGER DEFAULT 0,
    new_applications_this_run INTEGER DEFAULT 0,
    ai_analysis_completed INTEGER DEFAULT 0,
    leads_generated INTEGER DEFAULT 0,
    
    -- Error tracking
    last_error TEXT,
    consecutive_failures INTEGER DEFAULT 0,
    
    -- Timestamps and user tracking
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    created_by VARCHAR(36),
    updated_by VARCHAR(36),
    
    -- Soft delete
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_planning_campaigns_tenant_id ON planning_application_campaigns(tenant_id);
CREATE INDEX IF NOT EXISTS idx_planning_campaigns_county ON planning_application_campaigns(county);
CREATE INDEX IF NOT EXISTS idx_planning_campaigns_status ON planning_application_campaigns(status);
CREATE INDEX IF NOT EXISTS idx_planning_campaigns_next_run ON planning_application_campaigns(next_run_at) WHERE is_scheduled = TRUE;

-- ============================================================================
-- 3. CREATE PLANNING APPLICATIONS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS planning_applications (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    tenant_id VARCHAR(36) NOT NULL,
    
    -- External reference from planning portal
    reference VARCHAR(100) NOT NULL,
    external_id VARCHAR(100),
    
    -- Basic application details
    address TEXT NOT NULL,
    proposal TEXT NOT NULL,
    application_type applicationtype,
    status planningapplicationstatus DEFAULT 'validated' NOT NULL,
    
    -- Dates
    date_validated TIMESTAMP WITH TIME ZONE,
    date_decided TIMESTAMP WITH TIME ZONE,
    
    -- Location data
    latitude FLOAT,
    longitude FLOAT,
    postcode VARCHAR(20),
    
    -- Source information
    county VARCHAR(100) NOT NULL,
    source_portal VARCHAR(100) NOT NULL,
    
    -- Classification and scoring (tenant-specific)
    tenant_classification VARCHAR(50),
    relevance_score INTEGER CHECK (relevance_score >= 0 AND relevance_score <= 100),
    
    -- AI Analysis (tenant-specific)
    ai_analysis JSONB DEFAULT NULL,
    ai_summary TEXT,
    why_fit TEXT,
    suggested_sales_approach TEXT,
    
    -- Lead conversion tracking
    converted_to_lead_id VARCHAR(36),
    converted_to_customer_id VARCHAR(36),
    conversion_date TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    
    -- Soft delete
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_planning_applications_tenant_id ON planning_applications(tenant_id);
CREATE INDEX IF NOT EXISTS idx_planning_applications_reference ON planning_applications(reference);
CREATE INDEX IF NOT EXISTS idx_planning_applications_county ON planning_applications(county);
CREATE INDEX IF NOT EXISTS idx_planning_applications_relevance_score ON planning_applications(relevance_score);
CREATE INDEX IF NOT EXISTS idx_planning_applications_date_validated ON planning_applications(date_validated);
CREATE INDEX IF NOT EXISTS idx_planning_applications_application_type ON planning_applications(application_type);

-- ============================================================================
-- 4. CREATE PLANNING APPLICATION KEYWORDS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS planning_application_keywords (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    tenant_id VARCHAR(36) NOT NULL,
    
    -- Keyword details
    keyword VARCHAR(200) NOT NULL,
    keyword_type VARCHAR(50) NOT NULL, -- 'commercial', 'residential', 'exclude', 'include'
    weight INTEGER DEFAULT 10 NOT NULL CHECK (weight >= 1 AND weight <= 100),
    
    -- Category
    category VARCHAR(100),
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    
    -- Soft delete
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_planning_keywords_tenant_id ON planning_application_keywords(tenant_id);
CREATE INDEX IF NOT EXISTS idx_planning_keywords_keyword_type ON planning_application_keywords(keyword_type);
CREATE INDEX IF NOT EXISTS idx_planning_keywords_active ON planning_application_keywords(is_active);

-- ============================================================================
-- 5. ADD COMMENTS
-- ============================================================================

COMMENT ON TABLE planning_application_campaigns IS 'Manages county monitoring campaigns per tenant for planning applications';
COMMENT ON TABLE planning_applications IS 'Stores individual planning applications fetched from UK planning portals';
COMMENT ON TABLE planning_application_keywords IS 'Tenant-specific keywords for planning application classification and scoring';

COMMENT ON COLUMN planning_application_campaigns.county IS 'UK county name (e.g., Leicestershire)';
COMMENT ON COLUMN planning_application_campaigns.source_portal IS 'Planning portal identifier (e.g., leicester_opendatasoft)';
COMMENT ON COLUMN planning_application_campaigns.application_types IS 'Array of ApplicationType enums to filter applications';
COMMENT ON COLUMN planning_application_campaigns.keyword_filters IS 'Keywords to include for relevance scoring';
COMMENT ON COLUMN planning_application_campaigns.exclude_keywords IS 'Keywords to exclude from results';
COMMENT ON COLUMN planning_application_campaigns.is_scheduled IS 'Whether campaign runs automatically on schedule';

COMMENT ON COLUMN planning_applications.reference IS 'External planning application reference number';
COMMENT ON COLUMN planning_applications.proposal IS 'Description of the proposed development';
COMMENT ON COLUMN planning_applications.tenant_classification IS 'How tenant classified this application type';
COMMENT ON COLUMN planning_applications.relevance_score IS '0-100 score based on tenant keywords/interests';
COMMENT ON COLUMN planning_applications.ai_analysis IS 'Tenant-specific AI analysis results';
COMMENT ON COLUMN planning_applications.ai_summary IS 'Short AI-generated summary';
COMMENT ON COLUMN planning_applications.why_fit IS 'Why this project fits tenant services';
COMMENT ON COLUMN planning_applications.suggested_sales_approach IS 'Recommended sales approach';

COMMENT ON COLUMN planning_application_keywords.keyword_type IS 'Type: commercial, residential, exclude, include';
COMMENT ON COLUMN planning_application_keywords.weight IS 'Relevance weight 1-100 for scoring applications';
COMMENT ON COLUMN planning_application_keywords.category IS 'Category like data_centre, warehouse, office_fit_out';

