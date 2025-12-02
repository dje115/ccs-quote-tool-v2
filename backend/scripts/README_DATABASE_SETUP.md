# Database Setup Scripts

This directory contains scripts for setting up and maintaining the CCS Quote Tool v2 database.

## Scripts Overview

### Migration Scripts

- **`run_all_migrations.sh`** - Applies all SQL migration files in the `backend/migrations/` directory
  - Automatically finds and runs all `.sql` files in alphabetical order
  - Handles errors gracefully (continues if a migration fails or is already applied)
  - Usage: `bash backend/scripts/run_all_migrations.sh`

### Seed Scripts

- **`run_all_seeds.sh`** - Runs all Python seed scripts to populate initial data
  - Seeds AI Providers (must be first)
  - Seeds AI Prompts
  - Seeds Quote Type Prompts
  - All scripts are idempotent (safe to run multiple times)
  - Usage: `bash backend/scripts/run_all_seeds.sh`

### Complete Setup

- **`setup_database.sh`** - Complete database setup (migrations + seeds)
  - Runs all migrations first
  - Then runs all seed scripts
  - Usage: `bash backend/scripts/setup_database.sh`

## Database Migrations

All migration files are located in `backend/migrations/` and include:

### Core Tables
- Customer management
- Quote system
- Contract management
- Helpdesk/ticketing system
- Knowledge base
- SLA system
- Supplier management

### Recent Additions (v3.3.0)
- NPA (Next Point of Action) history table
- NPA answers cleanup fields
- Ticket cleaned description fields
- Knowledge base ticket links
- Enhanced NPA system
- Ticket enums and states

### Migration Files
All migration files use `CREATE TABLE IF NOT EXISTS` and `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` to ensure idempotency.

## Seed Data

Seed scripts populate the database with essential initial data:

1. **AI Providers** (`seed_ai_providers.py`)
   - OpenAI, Anthropic, Google, Microsoft Copilot, etc.
   - Provider configurations and settings

2. **AI Prompts** (`seed_ai_prompts.py`)
   - System-wide AI prompts for various categories
   - Customer service prompts
   - Quote generation prompts
   - Helpdesk-specific prompts (37 total prompts)

3. **Quote Type Prompts** (`seed_quote_type_prompts.py`)
   - Quote type-specific prompts
   - Custom prompts for different quote categories

4. **Sectors** (via `seed_data.py`)
   - Business sectors from CSV file
   - Used for lead generation campaigns

## Automatic Setup

The application automatically runs seed scripts on startup via `backend/app/startup/seed_data.py`. This ensures:
- Fresh databases are properly initialized
- Missing seed data is automatically populated
- All seed scripts are idempotent (safe to run multiple times)

## Manual Setup

For manual database setup or rebuilding:

```bash
# Option 1: Complete setup (recommended)
bash backend/scripts/setup_database.sh

# Option 2: Step by step
bash backend/scripts/run_all_migrations.sh
bash backend/scripts/run_all_seeds.sh
```

## Environment Variables

The scripts use the following environment variables (with defaults):

- `POSTGRES_DB` (default: `ccs_quote_tool`)
- `POSTGRES_USER` (default: `postgres`)
- `POSTGRES_PASSWORD` (default: `postgres_password_2025`)
- `POSTGRES_HOST` (default: `localhost`)
- `POSTGRES_PORT` (default: `5432`)

## Docker Setup

When running in Docker, the database setup is handled automatically:
1. Migrations are applied via SQL files
2. Seed scripts run on application startup
3. All scripts are idempotent and safe to run multiple times

## Troubleshooting

### Migration Errors
- If a migration fails, check the error message
- Most migrations use `IF NOT EXISTS` clauses, so they're safe to re-run
- Check database connection settings

### Seed Script Errors
- Seed scripts log warnings but don't fail startup
- Check application logs for detailed error messages
- Seed scripts can be run manually if needed

### Missing Data
- Run seed scripts manually: `bash backend/scripts/run_all_seeds.sh`
- Check that all required seed scripts exist
- Verify database connection and permissions

## Version Information

- **Current Version**: 3.3.0
- **Last Updated**: December 2024
- **Database Schema**: PostgreSQL 16

