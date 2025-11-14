-- Add is_archived field to planning_applications table
-- This enables archiving applications for deduplication while keeping records

ALTER TABLE planning_applications 
ADD COLUMN is_archived BOOLEAN NOT NULL DEFAULT FALSE;

-- Create index for better query performance when filtering by archived status
CREATE INDEX idx_planning_applications_is_archived ON planning_applications(is_archived);

-- Add composite index for tenant_id and is_archived for efficient filtering
CREATE INDEX idx_planning_applications_tenant_archived ON planning_applications(tenant_id, is_archived);
