-- Add task_id column to lead_generation_campaigns table
-- This column will store the Celery task ID for tracking campaign execution

ALTER TABLE lead_generation_campaigns 
ADD COLUMN task_id VARCHAR(255) NULL;

-- Add comment to explain the column purpose
COMMENT ON COLUMN lead_generation_campaigns.task_id IS 'Celery task ID for tracking campaign execution status';


