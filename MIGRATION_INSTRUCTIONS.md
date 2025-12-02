# Database Migration Instructions

## Overview
This document provides instructions for applying the database migrations for the CRM Lifecycle and Opportunity Management features.

## Migrations to Apply

1. **Customer Lifecycle Fields** (`add_customer_lifecycle_fields.sql`)
   - Adds `lifecycle_auto_managed` column
   - Adds `last_contact_date` column
   - Adds `conversion_probability` column
   - Creates indexes for performance

2. **Opportunities Table** (`add_opportunities_table.sql`)
   - Creates `opportunitystage` enum type
   - Creates `opportunities` table with all required fields
   - Creates indexes including GIN index for JSONB fields

## How to Apply Migrations

### Option 1: Using the Python Script (Recommended)

```bash
cd backend
python scripts/apply_lifecycle_migrations.py
```

This script will:
- Apply both migrations in order
- Show success/error messages for each
- Provide a summary at the end

### Option 2: Manual Application via Docker

If you're using Docker, you can apply migrations directly:

```bash
# Apply lifecycle fields migration
docker exec -i ccs-db psql -U postgres -d ccs_quote_tool < backend/migrations/add_customer_lifecycle_fields.sql

# Apply opportunities table migration
docker exec -i ccs-db psql -U postgres -d ccs_quote_tool < backend/migrations/add_opportunities_table.sql
```

### Option 3: Manual Application via psql

If you have direct database access:

```bash
# Connect to your database
psql -U your_user -d your_database

# Then run:
\i backend/migrations/add_customer_lifecycle_fields.sql
\i backend/migrations/add_opportunities_table.sql
```

## Verification

After applying migrations, verify the changes:

```sql
-- Check lifecycle fields exist
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name = 'customers' 
AND column_name IN ('lifecycle_auto_managed', 'last_contact_date', 'conversion_probability');

-- Check opportunities table exists
SELECT table_name 
FROM information_schema.tables 
WHERE table_name = 'opportunities';

-- Check opportunitystage enum exists
SELECT typname FROM pg_type WHERE typname = 'opportunitystage';
```

## Post-Migration Steps

1. **Restart Backend Container** (if using Docker)
   ```bash
   docker-compose restart backend
   ```

2. **Verify Celery Tasks**
   - The lifecycle automation tasks are already configured in `celery_app.py`
   - The `check_dormant_customers` task runs daily
   - No additional configuration needed

3. **Test the Features**
   - Create a test opportunity
   - Link a quote to an opportunity
   - Check the Dashboard for opportunity metrics
   - Verify lifecycle automation is working

## Rollback (if needed)

If you need to rollback the migrations:

```sql
-- Rollback opportunities table
DROP TABLE IF EXISTS opportunities CASCADE;
DROP TYPE IF EXISTS opportunitystage;

-- Rollback lifecycle fields
ALTER TABLE customers DROP COLUMN IF EXISTS lifecycle_auto_managed;
ALTER TABLE customers DROP COLUMN IF EXISTS last_contact_date;
ALTER TABLE customers DROP COLUMN IF EXISTS conversion_probability;
DROP INDEX IF EXISTS idx_customers_last_contact_date;
DROP INDEX IF EXISTS idx_customers_lifecycle_auto_managed;
```

## Troubleshooting

### Error: "relation already exists"
- The migration uses `IF NOT EXISTS` clauses, so this shouldn't happen
- If it does, the table/column already exists and you can skip that migration

### Error: "type already exists"
- The enum type may already exist from a previous migration
- The migration handles this with `IF NOT EXISTS`, so it should be safe

### Error: "permission denied"
- Ensure your database user has CREATE TABLE and ALTER TABLE permissions
- Check that you're connected to the correct database

## Support

If you encounter any issues:
1. Check the migration SQL files for syntax errors
2. Verify database connection and permissions
3. Check Docker logs if using containers
4. Review the error messages for specific guidance



