-- Migration: Add quote_documents and quote_document_versions tables
-- Created: 2025-11-19
-- Description: Adds support for multi-part quote documents with versioning

-- Create quote_documents table
CREATE TABLE IF NOT EXISTS quote_documents (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    quote_id VARCHAR(36) NOT NULL REFERENCES quotes(id) ON DELETE CASCADE,
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- Document type: 'parts_list', 'technical', 'overview', 'build'
    document_type VARCHAR(50) NOT NULL,
    
    -- Rich content structure (JSONB for flexibility)
    content JSONB NOT NULL DEFAULT '{}'::jsonb,
    
    -- Version tracking
    version INTEGER NOT NULL DEFAULT 1,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
    
    -- Soft delete
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    -- Ensure one document per type per quote
    CONSTRAINT unique_quote_document_type UNIQUE (quote_id, document_type, version)
);

-- Create quote_document_versions table for version history
CREATE TABLE IF NOT EXISTS quote_document_versions (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    document_id VARCHAR(36) NOT NULL REFERENCES quote_documents(id) ON DELETE CASCADE,
    
    -- Version information
    version INTEGER NOT NULL,
    
    -- Content snapshot
    content JSONB NOT NULL,
    
    -- Change tracking
    changes_summary TEXT,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL
);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_quote_documents_quote_id ON quote_documents(quote_id);
CREATE INDEX IF NOT EXISTS idx_quote_documents_tenant_id ON quote_documents(tenant_id);
CREATE INDEX IF NOT EXISTS idx_quote_documents_type ON quote_documents(document_type);
CREATE INDEX IF NOT EXISTS idx_quote_document_versions_document_id ON quote_document_versions(document_id);
CREATE INDEX IF NOT EXISTS idx_quote_document_versions_version ON quote_document_versions(document_id, version);

-- Add tier_type column to quotes table if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'quotes' AND column_name = 'tier_type'
    ) THEN
        ALTER TABLE quotes ADD COLUMN tier_type VARCHAR(20) DEFAULT 'single';
        -- Values: 'single', 'three_tier'
        COMMENT ON COLUMN quotes.tier_type IS 'Quote tier type: single (one quote) or three_tier (Basic/Standard/Premium)';
    END IF;
END $$;

-- Add ai_generation_data JSON column to quotes if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'quotes' AND column_name = 'ai_generation_data'
    ) THEN
        ALTER TABLE quotes ADD COLUMN ai_generation_data JSONB;
        COMMENT ON COLUMN quotes.ai_generation_data IS 'Stores AI generation metadata: industry detected, prompt used, generation settings, etc.';
    END IF;
END $$;

-- Add RLS policies for multi-tenant isolation
ALTER TABLE quote_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE quote_document_versions ENABLE ROW LEVEL SECURITY;

-- RLS policy for quote_documents
CREATE POLICY quote_documents_tenant_isolation ON quote_documents
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE));

-- RLS policy for quote_document_versions (via document_id join)
CREATE POLICY quote_document_versions_tenant_isolation ON quote_document_versions
    FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM quote_documents qd
            WHERE qd.id = quote_document_versions.document_id
            AND qd.tenant_id = current_setting('app.current_tenant_id', TRUE)
        )
    );

