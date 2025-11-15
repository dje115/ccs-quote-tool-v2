# AI Prompts Principle - Database-Driven Only

## Core Principle

**ALL AI prompts MUST be stored in the database, NOT hardcoded in the code.**

This is a fundamental architectural principle for this application.

## Why Database-Driven Prompts?

1. **No Code Changes Required**: Update prompts without deploying new code
2. **Tenant Customization**: Each tenant can have their own prompts
3. **Version Control**: Track all changes with rollback capability
4. **A/B Testing**: Test different prompt versions
5. **Centralized Management**: Manage all prompts through admin UI
6. **Multi-Tenant Isolation**: Different tenants can have different AI behaviors

## Implementation Pattern

### ✅ CORRECT Pattern (Use This)

```python
# Get prompt from database
prompt_service = AIPromptService(self.db, tenant_id=self.tenant_id)
prompt_obj = await prompt_service.get_prompt(
    category=PromptCategory.QUOTE_ANALYSIS.value,
    tenant_id=self.tenant_id,
    quote_type=quote_type  # Optional for quote_analysis category
)

if not prompt_obj:
    # Log error and return gracefully - DO NOT use fallback hardcoded prompts
    logger.error(f"No prompt found for category {category}")
    return {"success": False, "error": "AI prompt not configured"}

# Render prompt with variables
rendered = prompt_service.render_prompt(prompt_obj, {
    "variable1": value1,
    "variable2": value2
})

user_prompt = rendered['user_prompt']
system_prompt = rendered['system_prompt']
model = rendered['model']
max_tokens = rendered['max_tokens']
temperature = rendered.get('temperature', 0.7)
```

### ❌ WRONG Pattern (Never Do This)

```python
# DO NOT hardcode prompts
system_prompt = "You are a helpful assistant..."
user_prompt = f"Analyze this: {data}"

# DO NOT use fallback hardcoded prompts
if not prompt_obj:
    user_prompt = "Hardcoded fallback prompt..."  # ❌ WRONG
```

## When Adding New AI Features

1. **Create the prompt in the database first** (via seed script or admin UI)
2. **Use AIPromptService to retrieve it** - never hardcode
3. **If prompt doesn't exist, fail gracefully** - don't use fallback prompts
4. **Add prompt category to PromptCategory enum** if it's a new category

## Current Status

### ✅ Already Migrated to Database
- Customer Analysis (`customer_analysis`)
- Activity Enhancement (`activity_enhancement`)
- Action Suggestions (`action_suggestions`)
- Competitor Analysis (`competitor_analysis`)
- Financial Analysis (`financial_analysis`)
- Translation (`translation`)
- Quote Analysis (`quote_analysis`) - with quote_type support
- Product Search (`product_search`)
- Building Analysis (`building_analysis`)

### ⚠️ Still Has Hardcoded Fallbacks (Need Migration)
- `quote_analysis_service.py` - Has fallback prompt
- `ai_analysis_service.py` - Has multiple fallback prompts
- `activity_service.py` - Has fallback prompts
- `translation_service.py` - Has fallback prompt
- `pricing_import_service.py` - Has hardcoded prompts
- `lead_generation_service.py` - Has hardcoded prompts

## Migration Checklist

When migrating hardcoded prompts:

1. ✅ Add prompt to seed script (`backend/scripts/seed_ai_prompts.py`)
2. ✅ Remove hardcoded prompt from service code
3. ✅ Remove fallback prompt logic
4. ✅ Update service to fail gracefully if prompt not found
5. ✅ Test that prompt is retrieved from database
6. ✅ Verify tenant-specific prompts work if applicable

## Admin UI

All prompts can be managed via:
- **Route**: `/prompts`
- **Access**: Admin/Tenant Admin roles only
- **Features**: Create, edit, version history, rollback

## Remember

**If you're writing code that uses AI, always:**
1. Check if a prompt category exists in the database
2. Use `AIPromptService.get_prompt()` to retrieve it
3. Never hardcode prompts as fallbacks
4. Fail gracefully if prompt doesn't exist (log error, return error response)

