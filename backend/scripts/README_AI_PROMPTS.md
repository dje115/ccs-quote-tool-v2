# AI Prompts Seeding Guide

## Overview
The AI prompts system uses database-driven prompts that can be customized per tenant. All prompts are seeded from `backend/scripts/seed_ai_prompts.py`.

## Current Status
- **Total Prompts**: 34 prompts are currently seeded in the database
- **Seed Script**: `backend/scripts/seed_ai_prompts.py`
- **Categories**: Customer Analysis, Quote Analysis, Contract Generation, Knowledge Base, Customer Service, etc.

## Seeding Prompts

### Manual Seeding
To seed prompts after a database rebuild or when adding new prompts:

```bash
# From the backend directory
cd backend
python scripts/seed_ai_prompts.py
```

### Automated Seeding (Recommended)
The seed script is idempotent - it checks if prompts exist before creating them, so it's safe to run multiple times.

### Integration with Database Setup
To automatically seed prompts on database initialization, you can:

1. **Add to migration scripts**: Include prompt seeding in your database initialization
2. **Add to Docker entrypoint**: Run the seed script in your container startup
3. **Add to CI/CD**: Run seeding as part of deployment

## Prompt Management

### Viewing Prompts
- **Admin Portal**: Navigate to "AI Prompts" section in the admin interface
- **Database**: Query `ai_prompts` table directly

### Customizing Prompts
1. Prompts can be customized per tenant through the admin interface
2. System prompts serve as defaults when tenant-specific prompts don't exist
3. Prompt versions are tracked in `ai_prompt_versions` table

## Categories
The following prompt categories are available:
- `CUSTOMER_ANALYSIS` - Company analysis and lead generation
- `QUOTE_ANALYSIS` - Quote requirements analysis
- `CONTRACT_GENERATION` - Contract template generation
- `KNOWLEDGE_BASE_SEARCH` - KB article search and ranking
- `CUSTOMER_SERVICE` - Helpdesk ticket analysis
- And more...

## Notes
- Prompts are tenant-aware (tenant-specific → system fallback)
- Prompt versions are tracked for audit purposes
- All prompts support variable substitution using `{variable_name}` syntax

