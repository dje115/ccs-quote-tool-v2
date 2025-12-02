-- Migration: Update knowledge_base_articles to use status column
-- Created: 2025-11-24
-- Description: Adds status column to knowledge_base_articles if it doesn't exist, and migrates is_published to status

-- Add status column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'knowledge_base_articles' AND column_name = 'status'
    ) THEN
        ALTER TABLE knowledge_base_articles ADD COLUMN status VARCHAR(20) DEFAULT 'published' NOT NULL;
        
        -- Migrate is_published to status
        UPDATE knowledge_base_articles 
        SET status = CASE 
            WHEN is_published = true THEN 'published'
            ELSE 'draft'
        END;
        
        -- Add index
        CREATE INDEX IF NOT EXISTS idx_kb_articles_status ON knowledge_base_articles(status);
        CREATE INDEX IF NOT EXISTS idx_kb_articles_tenant_status ON knowledge_base_articles(tenant_id, status);
        
        COMMENT ON COLUMN knowledge_base_articles.status IS 'Article status: draft, published, or archived';
    END IF;
END $$;

