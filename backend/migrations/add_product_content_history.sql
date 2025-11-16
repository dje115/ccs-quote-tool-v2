-- Migration: Enhance Product Content History Table for Price Intelligence Pipeline
-- Purpose: Add fields to existing product_content_history table for price intelligence
-- Date: 2025-01-XX

-- Add new columns to existing product_content_history table (if not exists)
DO $$
BEGIN
    -- Add tenant_id if not exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'product_content_history' AND column_name = 'tenant_id'
    ) THEN
        ALTER TABLE product_content_history ADD COLUMN tenant_id VARCHAR(36);
        ALTER TABLE product_content_history ADD CONSTRAINT fk_product_content_history_tenant 
            FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;
        CREATE INDEX IF NOT EXISTS idx_product_content_history_tenant_id ON product_content_history(tenant_id);
    END IF;
    
    -- Add supplier_product_url if not exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'product_content_history' AND column_name = 'supplier_product_url'
    ) THEN
        ALTER TABLE product_content_history ADD COLUMN supplier_product_url TEXT;
    END IF;
    
    -- Add scraped_content if not exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'product_content_history' AND column_name = 'scraped_content'
    ) THEN
        ALTER TABLE product_content_history ADD COLUMN scraped_content TEXT;
    END IF;
    
    -- Make price nullable if not already
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'product_content_history' 
        AND column_name = 'price' 
        AND is_nullable = 'NO'
    ) THEN
        ALTER TABLE product_content_history ALTER COLUMN price DROP NOT NULL;
    END IF;
    
    -- Add scraping_timestamp if not exists (use recorded_at as fallback)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'product_content_history' AND column_name = 'scraping_timestamp'
    ) THEN
        ALTER TABLE product_content_history ADD COLUMN scraping_timestamp TIMESTAMP WITH TIME ZONE;
        -- Copy from recorded_at if it exists
        UPDATE product_content_history SET scraping_timestamp = recorded_at WHERE scraping_timestamp IS NULL;
        ALTER TABLE product_content_history ALTER COLUMN scraping_timestamp SET DEFAULT NOW();
        ALTER TABLE product_content_history ALTER COLUMN scraping_timestamp SET NOT NULL;
        CREATE INDEX IF NOT EXISTS idx_product_content_history_scraping_timestamp ON product_content_history(scraping_timestamp);
    END IF;
    
    -- Add verification fields if not exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'product_content_history' AND column_name = 'is_verified'
    ) THEN
        ALTER TABLE product_content_history ADD COLUMN is_verified BOOLEAN DEFAULT false NOT NULL;
        ALTER TABLE product_content_history ADD COLUMN verified_by VARCHAR(36);
        ALTER TABLE product_content_history ADD COLUMN verified_at TIMESTAMP WITH TIME ZONE;
        ALTER TABLE product_content_history ADD COLUMN verification_notes TEXT;
        
        ALTER TABLE product_content_history ADD CONSTRAINT fk_product_content_history_verified_by 
            FOREIGN KEY (verified_by) REFERENCES users(id) ON DELETE SET NULL;
        CREATE INDEX IF NOT EXISTS idx_product_content_history_is_verified ON product_content_history(is_verified);
    END IF;
    
    -- Add is_active if not exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'product_content_history' AND column_name = 'is_active'
    ) THEN
        ALTER TABLE product_content_history ADD COLUMN is_active BOOLEAN DEFAULT true NOT NULL;
        CREATE INDEX IF NOT EXISTS idx_product_content_history_is_active ON product_content_history(is_active);
    END IF;
    
    -- Update product_name length if needed
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'product_content_history' 
        AND column_name = 'product_name' 
        AND character_maximum_length < 500
    ) THEN
        ALTER TABLE product_content_history ALTER COLUMN product_name TYPE VARCHAR(500);
    END IF;
    
    -- Make supplier_id nullable if not already
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'product_content_history' 
        AND column_name = 'supplier_id' 
        AND is_nullable = 'NO'
    ) THEN
        ALTER TABLE product_content_history ALTER COLUMN supplier_id DROP NOT NULL;
    END IF;
    
    -- Update default confidence_score if needed
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'product_content_history' 
        AND column_name = 'confidence_score' 
        AND column_default != '0.5'
    ) THEN
        -- Update existing records with high confidence to 0.5 if they're 1.0
        UPDATE product_content_history SET confidence_score = 0.5 WHERE confidence_score = 1.0 AND is_verified = false;
    END IF;
END $$;

-- Create composite indexes for price intelligence queries
CREATE INDEX IF NOT EXISTS idx_product_content_history_price_intelligence 
    ON product_content_history(tenant_id, product_name, scraping_timestamp DESC, is_verified, is_active);

-- Add comments
COMMENT ON TABLE product_content_history IS 'Historical pricing data from web scraping for price intelligence';
COMMENT ON COLUMN product_content_history.scraped_content IS 'Full HTML/text content from supplier page at time of scraping';
COMMENT ON COLUMN product_content_history.scraping_timestamp IS 'Timestamp when scraping occurred';
COMMENT ON COLUMN product_content_history.is_verified IS 'Whether this price has been manually verified by a user';

