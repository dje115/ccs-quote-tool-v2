-- Migration: Enhance pricing scraping with verification workflow and price history
-- Date: 2025-11-16
-- Description: Adds confidence scoring, verification status, and price history tracking

-- Add verification and confidence fields to supplier_pricing
ALTER TABLE supplier_pricing ADD COLUMN IF NOT EXISTS confidence_score NUMERIC(3, 2) DEFAULT 1.0 CHECK (confidence_score >= 0 AND confidence_score <= 1);
ALTER TABLE supplier_pricing ADD COLUMN IF NOT EXISTS verification_status VARCHAR(20) DEFAULT 'pending' CHECK (verification_status IN ('pending', 'verified', 'rejected', 'needs_review'));
ALTER TABLE supplier_pricing ADD COLUMN IF NOT EXISTS verified_by VARCHAR(36);
ALTER TABLE supplier_pricing ADD COLUMN IF NOT EXISTS verified_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE supplier_pricing ADD COLUMN IF NOT EXISTS source_url VARCHAR(500);
ALTER TABLE supplier_pricing ADD COLUMN IF NOT EXISTS scraping_method VARCHAR(50); -- 'direct_url', 'search', 'known_pricing', 'api'
ALTER TABLE supplier_pricing ADD COLUMN IF NOT EXISTS scraping_metadata JSONB; -- Store selector used, retry count, etc.
ALTER TABLE supplier_pricing ADD COLUMN IF NOT EXISTS needs_manual_review BOOLEAN DEFAULT FALSE;
ALTER TABLE supplier_pricing ADD COLUMN IF NOT EXISTS review_reason TEXT; -- Why it needs review

-- Add foreign key for verified_by
ALTER TABLE supplier_pricing ADD CONSTRAINT fk_supplier_pricing_verified_by 
    FOREIGN KEY (verified_by) REFERENCES users(id) ON DELETE SET NULL;

-- Create price history table for tracking price changes
CREATE TABLE IF NOT EXISTS product_content_history (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
    supplier_id VARCHAR(36) NOT NULL,
    product_name VARCHAR(200) NOT NULL,
    product_code VARCHAR(100),
    price NUMERIC(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'GBP' NOT NULL,
    confidence_score NUMERIC(3, 2) DEFAULT 1.0 CHECK (confidence_score >= 0 AND confidence_score <= 1),
    source_url VARCHAR(500),
    scraping_method VARCHAR(50),
    scraping_metadata JSONB,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_product_content_history_supplier_product ON product_content_history(supplier_id, product_name);
CREATE INDEX IF NOT EXISTS idx_product_content_history_recorded_at ON product_content_history(recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_product_content_history_product_code ON product_content_history(product_code) WHERE product_code IS NOT NULL;

-- Create verification queue table for low-confidence prices
CREATE TABLE IF NOT EXISTS pricing_verification_queue (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
    supplier_pricing_id VARCHAR(36) NOT NULL,
    tenant_id VARCHAR(36) NOT NULL,
    priority INTEGER DEFAULT 0, -- Higher = more urgent
    reason TEXT NOT NULL, -- Why it needs verification
    assigned_to VARCHAR(36), -- User assigned to verify
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'verified', 'rejected', 'ignored')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    verified_at TIMESTAMP WITH TIME ZONE,
    FOREIGN KEY (supplier_pricing_id) REFERENCES supplier_pricing(id) ON DELETE CASCADE,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_to) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_pricing_verification_queue_status ON pricing_verification_queue(status, tenant_id);
CREATE INDEX IF NOT EXISTS idx_pricing_verification_queue_assigned ON pricing_verification_queue(assigned_to) WHERE assigned_to IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_pricing_verification_queue_priority ON pricing_verification_queue(priority DESC, created_at);

-- Add index for low-confidence prices
CREATE INDEX IF NOT EXISTS idx_supplier_pricing_low_confidence ON supplier_pricing(confidence_score, verification_status) 
    WHERE confidence_score < 0.7 OR verification_status = 'needs_review';

-- Comments
COMMENT ON COLUMN supplier_pricing.confidence_score IS 'Confidence score 0.0-1.0 based on scraping method and success';
COMMENT ON COLUMN supplier_pricing.verification_status IS 'Verification status: pending, verified, rejected, needs_review';
COMMENT ON COLUMN supplier_pricing.scraping_method IS 'Method used: direct_url, search, known_pricing, api';
COMMENT ON COLUMN product_content_history.scraping_metadata IS 'Metadata about scraping: selectors used, retry count, etc.';
COMMENT ON TABLE pricing_verification_queue IS 'Queue for manual verification of low-confidence or flagged prices';


