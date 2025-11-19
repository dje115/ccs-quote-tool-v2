# Startup Initialization

This module handles automatic database initialization and seeding during application startup.

## Overview

When the application starts, it automatically runs all database seed scripts to ensure the database is properly initialized with default data.

## Seed Scripts

The following seed scripts are run automatically on startup (in order):

1. **AI Providers** (`scripts/seed_ai_providers.py`)
   - Seeds initial AI provider configurations (OpenAI, Google, Anthropic, etc.)
   - Must run first as other scripts may depend on providers

2. **AI Prompts** (`scripts/seed_ai_prompts.py`)
   - Seeds all system AI prompts for various features
   - Includes dashboard analytics, customer analysis, quote analysis, etc.
   - Includes all 8 new Smart Quoting Module prompts

3. **Quote Type Prompts** (`scripts/seed_quote_type_prompts.py`)
   - Seeds quote type-specific prompts (cabling, network_build, server_build, etc.)

## Idempotent Design

All seed scripts are **idempotent** - they can be run multiple times safely:
- Scripts check if data already exists before creating
- Existing data is skipped (not overwritten)
- New data is added as needed

## Error Handling

- If a seed script fails, the error is logged but startup continues
- This ensures the application can start even if seed scripts have issues
- Seed scripts can be run manually later if needed

## Manual Execution

Seed scripts can also be run manually:

```bash
# Run all seed scripts
python -m app.startup.seed_data

# Or run individual scripts
python scripts/seed_ai_providers.py
python scripts/seed_ai_prompts.py
python scripts/seed_quote_type_prompts.py
```

## Adding New Seed Scripts

To add a new seed script to the startup process:

1. Create your seed script in `backend/scripts/`
2. Add a function to `backend/app/startup/seed_data.py`:
   ```python
   async def seed_your_feature(db: Session):
       try:
           import sys
           scripts_path = _get_scripts_path()
           if scripts_path not in sys.path:
               sys.path.insert(0, scripts_path)
           
           from your_seed_script import seed_function
           logger.info("Seeding your feature...")
           await seed_function(db)  # or seed_function(db) if sync
           logger.info("✅ Your feature seeded")
       except Exception as e:
           logger.warning(f"⚠️  Error seeding your feature: {e}")
   ```

3. Call it in `run_seed_scripts()` function

## Logging

All seed operations are logged:
- Success: `✅ Feature seeded`
- Skipped: `⏭️  Feature already exists`
- Error: `⚠️  Error seeding feature: {error}`

