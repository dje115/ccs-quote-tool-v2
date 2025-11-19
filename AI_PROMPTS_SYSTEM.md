# AI Prompts System - Database-Driven Prompt Management

## Overview

The AI Prompts System allows all AI prompts to be stored in the database rather than hardcoded in the application code. This enables:

- **Easy prompt updates** without code changes
- **Version control** for prompts with rollback capability
- **Tenant-specific customization** of prompts
- **A/B testing** of different prompt versions
- **Centralized management** through admin portal

## Architecture

### Database Schema

**`ai_prompts` table:**
- Stores prompt definitions with system/user prompts
- Supports versioning (version field)
- Tenant-specific or system-wide prompts
- Template variables support

**`ai_prompt_versions` table:**
- Version history for all prompts
- Enables rollback to previous versions
- Tracks who made changes and when

### Service Layer

**`AIPromptService`:**
- Fetches prompts from database with caching (Redis)
- Renders prompts with variable substitution
- Manages prompt CRUD operations
- Handles versioning and rollback

### API Endpoints

All endpoints under `/api/v1/prompts/`:
- `GET /` - List prompts (with filters)
- `GET /{id}` - Get specific prompt
- `POST /` - Create new prompt
- `PUT /{id}` - Update prompt (creates version)
- `DELETE /{id}` - Delete prompt
- `POST /{id}/test` - Test prompt with sample data
- `GET /{id}/versions` - Get version history
- `POST /{id}/rollback/{version}` - Rollback to version

## Prompt Categories

Current categories:
- `customer_analysis` - Comprehensive company analysis
- `activity_enhancement` - Sales activity note cleanup
- `action_suggestions` - Next action recommendations
- `competitor_analysis` - Competitor discovery
- `financial_analysis` - Financial health analysis
- `translation` - Text translation
- `lead_generation` - Lead generation campaigns (various types)
- `planning_analysis` - Planning application analysis
- `quote_analysis` - Quote requirements analysis

## Usage in Services

### Example: Using Database Prompt

```python
from app.services.ai_prompt_service import AIPromptService
from app.models.ai_prompt import PromptCategory

# Initialize service
prompt_service = AIPromptService(db, tenant_id=tenant_id)

# Get prompt
prompt_obj = await prompt_service.get_prompt(
    category=PromptCategory.CUSTOMER_ANALYSIS.value,
    tenant_id=tenant_id
)

# Render with variables
if prompt_obj:
    rendered = prompt_service.render_prompt(prompt_obj, {
        "tenant_context": tenant_context,
        "company_info": company_info
    })
    system_prompt = rendered['system_prompt']
    user_prompt = rendered['user_prompt']
    model = rendered['model']
    max_tokens = rendered['max_tokens']
else:
    # Fallback to hardcoded prompt
    ...
```

## Template Variables

Prompts support template variables using `{variable_name}` syntax:

```python
variables = {
    "tenant_context": "Tenant company information",
    "company_info": "Company data from various sources",
    "activity_type": "Type of activity",
    "notes": "Original notes"
}
```

Variables are replaced during rendering.

## Caching

Prompts are cached in Redis with:
- **TTL**: 1 hour
- **Key format**: `ai_prompt:{category}:{tenant_id}`
- **Automatic invalidation** on updates

## Migration

### Seeding Initial Prompts

Run the seed script to populate initial prompts:

```bash
python backend/scripts/seed_ai_prompts.py
```

This extracts prompts from existing code and creates database entries.

### Running Database Migration

```bash
# Apply migration
psql -U postgres -d ccs_quote_tool -f backend/migrations/add_ai_prompts_tables.sql
```

## Fallback Behavior

All services include fallback to hardcoded prompts if:
- Database prompt not found
- Database connection fails
- Prompt is inactive

This ensures the system continues working even if prompts aren't seeded yet.

## Admin Portal

The admin portal provides:
- List all prompts with filters
- Edit prompts with syntax highlighting
- Test prompts with sample data
- View version history
- Rollback to previous versions

## Best Practices

1. **Always provide fallback prompts** in code
2. **Document template variables** in prompt description
3. **Use versioning** for significant changes
4. **Test prompts** before deploying
5. **Monitor prompt performance** and adjust as needed

## Future Enhancements

- Prompt A/B testing framework
- Prompt performance analytics
- Automatic prompt optimization
- Multi-language prompt support
- Prompt templates library





