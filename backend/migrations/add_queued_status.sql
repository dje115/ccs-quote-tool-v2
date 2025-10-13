-- Add QUEUED status to leadgenerationstatus enum
-- This allows campaigns to be queued in Celery before execution

DO $$
BEGIN
    -- Check if 'queued' value already exists in the enum
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum
        WHERE enumlabel = 'QUEUED'
        AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'leadgenerationstatus')
    ) THEN
        -- Add 'QUEUED' status after 'DRAFT'
        ALTER TYPE leadgenerationstatus ADD VALUE 'QUEUED' AFTER 'DRAFT';
        RAISE NOTICE 'Added QUEUED status to leadgenerationstatus enum';
    ELSE
        RAISE NOTICE 'QUEUED status already exists in leadgenerationstatus enum';
    END IF;
END$$;

