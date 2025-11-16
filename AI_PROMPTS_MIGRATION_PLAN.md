# AI Prompts Migration Plan - Remove Hardcoded Fallbacks

**Date**: 2025-01-XX  
**Status**: Ready for Implementation  
**Priority**: High  
**Estimated Time**: 0.5 days

---

## Overview

This document provides a step-by-step plan to complete the AI Prompts System migration by removing all hardcoded fallback prompts and migrating remaining hardcoded prompts to the database.

**Current Status**: 90% Complete  
**Remaining Work**: Remove 5 fallback locations, migrate 1 hardcoded prompt

---

## Phase 1: Remove Fallbacks from Services with Database Support

### 1.1 `ai_analysis_service.py` - Competitor Analysis

**File**: `backend/app/services/ai_analysis_service.py`  
**Lines**: 379-416  
**Category**: `competitor_analysis`

**Current Code**:
```python
if not prompt_obj:
    print("[COMPETITORS] Using fallback prompt - database prompt not found")
    competitor_prompt = f"""Find REAL, VERIFIED UK competitors..."""
    # ... hardcoded prompt ...
```

**Action**:
1. Remove lines 379-416 (entire fallback block)
2. Replace with error handling:
   ```python
   if not prompt_obj:
       logger.error(f"No prompt found for competitor_analysis, tenant_id={self.tenant_id}")
       return []
   ```
3. Ensure prompt is always retrieved before this point

**Testing**:
- Verify competitor analysis fails gracefully when prompt not found
- Verify competitor analysis works when prompt exists

---

### 1.2 `ai_analysis_service.py` - Customer Analysis

**File**: `backend/app/services/ai_analysis_service.py`  
**Lines**: 715-833  
**Category**: `customer_analysis`

**Current Code**:
```python
if not prompt_obj:
    print("[AI ANALYSIS] Using fallback prompt - database prompt not found")
    user_prompt = f"""Analyze this company and provide comprehensive..."""
    # ... large hardcoded prompt (118 lines) ...
```

**Action**:
1. Remove lines 715-833 (entire fallback block)
2. Replace with error handling:
   ```python
   if not prompt_obj:
       logger.error(f"No prompt found for customer_analysis, tenant_id={self.tenant_id}")
       raise Exception("AI prompt not configured for customer analysis. Please configure prompts in the admin section.")
   ```
3. Update calling code to handle exception gracefully

**Testing**:
- Verify customer analysis fails gracefully when prompt not found
- Verify customer analysis works when prompt exists

---

### 1.3 `activity_service.py` - Activity Enhancement

**File**: `backend/app/services/activity_service.py`  
**Lines**: 157-192  
**Category**: `activity_enhancement`

**Current Code**:
```python
if not prompt_obj:
    print("[ActivityService] Using fallback prompt - database prompt not found")
    user_prompt = f"""You are a sales assistant AI helping to process activity notes..."""
    # ... hardcoded prompt ...
```

**Action**:
1. Remove lines 157-192 (entire fallback block)
2. Replace with error handling:
   ```python
   if not prompt_obj:
       logger.error(f"No prompt found for activity_enhancement, tenant_id={self.tenant_id}")
       # Don't enhance activity if prompt not found - return early
       return
   ```
3. Ensure prompt is always retrieved before this point

**Testing**:
- Verify activity enhancement is skipped when prompt not found
- Verify activity enhancement works when prompt exists

---

### 1.4 `activity_service.py` - Action Suggestions

**File**: `backend/app/services/activity_service.py`  
**Lines**: 457-490  
**Category**: `action_suggestions`

**Current Code**:
```python
if not prompt_obj:
    print("[ActivityService] Using fallback prompt for action suggestions - database prompt not found")
    user_prompt = f"""You are a sales advisor AI helping prioritize customer engagement actions..."""
    # ... hardcoded prompt ...
```

**Action**:
1. Remove lines 457-490 (entire fallback block)
2. Replace with error handling:
   ```python
   if not prompt_obj:
       logger.error(f"No prompt found for action_suggestions, tenant_id={self.tenant_id}")
       return []  # Return empty list if prompt not found
   ```
3. Ensure prompt is always retrieved before this point

**Testing**:
- Verify action suggestions returns empty list when prompt not found
- Verify action suggestions works when prompt exists

---

### 1.5 `translation_service.py` - Translation

**File**: `backend/app/services/translation_service.py`  
**Lines**: 47-60  
**Category**: `translation`

**Current Code**:
```python
else:
    # Fallback: use generate_with_rendered_prompts
    system_prompt = "You are a professional translator. Translate accurately and naturally."
    user_prompt = f"""Translate the following text from {source_language} to {target_language}..."""
```

**Action**:
1. Remove lines 47-60 (entire fallback block)
2. Replace with error handling:
   ```python
   if not prompt_obj:
       logger.error(f"No prompt found for translation, tenant_id={self.tenant_id}")
       return {
           'success': False,
           'error': 'AI prompt not configured for translation. Please configure prompts in the admin section.'
       }
   ```
3. Ensure prompt is always retrieved before this point

**Testing**:
- Verify translation fails gracefully when prompt not found
- Verify translation works when prompt exists

---

## Phase 2: Migrate Hardcoded Prompt to Database

### 2.1 `pricing_import_service.py` - Pricing Import

**File**: `backend/app/services/pricing_import_service.py`  
**Lines**: 181-222  
**Category**: `pricing_import` (NEW)

**Current Code**:
```python
prompt = f"""Analyze this pricing data from a file named "{filename}" and extract product information..."""
system_prompt = "You are an expert at extracting and standardizing product pricing data from various file formats. Always return valid JSON arrays."
```

**Action**:

1. **Add to PromptCategory enum** (`backend/app/models/ai_prompt.py`):
   ```python
   PRICING_IMPORT = "pricing_import"
   ```

2. **Add prompt to seed script** (`backend/scripts/seed_ai_prompts.py`):
   ```python
   # Pricing Import Prompt
   pricing_import_prompt = """
   Analyze this pricing data from a file named "{filename}" and extract product information.

   The data is in JSON format with these columns: {columns}

   Extract the following information for each product:
   - name: Product name
   - code: Product code/SKU/part number (if available)
   - price: Unit price (in GBP)
   - cost_price: Cost price (if available)
   - category: Product category
   - subcategory: Subcategory (if available)
   - supplier: Supplier/vendor name (if available)
   - part_number: Manufacturer part number (if available)
   - unit: Unit of measure (each, meter, box, etc.)
   - is_service: Boolean indicating if this is a service (default: false)

   Data:
   {df_json}

   Return a JSON array of products. For each product, only include fields that have actual values.
   Standardize product names and categorize appropriately.
   If price information is missing or unclear, set price to 0.
   If category is unclear, use "General" as default.
   """
   
   system_prompt = "You are an expert at extracting and standardizing product pricing data from various file formats. Always return valid JSON arrays."
   ```

3. **Update service to use AIPromptService**:
   ```python
   from app.services.ai_prompt_service import AIPromptService
   from app.models.ai_prompt import PromptCategory
   
   # In _extract_with_ai method:
   prompt_service = AIPromptService(self.db, tenant_id=self.tenant_id)
   prompt_obj = await prompt_service.get_prompt(
       category=PromptCategory.PRICING_IMPORT.value,
       tenant_id=self.tenant_id
   )
   
   if not prompt_obj:
       logger.error(f"No prompt found for pricing_import, tenant_id={self.tenant_id}")
       return []
   
   # Render prompt with variables
   rendered = prompt_service.render_prompt(prompt_obj, {
       "filename": filename,
       "columns": list(df.columns),
       "df_json": df_json
   })
   
   user_prompt = rendered['user_prompt']
   system_prompt = rendered['system_prompt']
   model = rendered['model']
   max_tokens = rendered['max_tokens']
   ```

4. **Remove hardcoded prompt** (lines 181-222)

**Testing**:
- Verify pricing import works with database prompt
- Verify pricing import fails gracefully when prompt not found
- Test with various file formats (Excel, CSV)

---

## Phase 3: Database Verification

### 3.1 Verify Migration Applied

**Check**:
```sql
-- Check if table exists
SELECT EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_name = 'ai_prompts'
);

-- Check table structure
\d ai_prompts
```

**Expected**: Table should exist with all required columns

---

### 3.2 Verify Prompts Seeded

**Check**:
```sql
-- Count prompts by category
SELECT category, COUNT(*) as count
FROM ai_prompts
WHERE is_active = true
GROUP BY category
ORDER BY category;

-- List all prompt categories
SELECT DISTINCT category FROM ai_prompts;
```

**Expected Categories**:
- `customer_analysis` ✅
- `competitor_analysis` ✅
- `activity_enhancement` ✅
- `action_suggestions` ✅
- `translation` ✅
- `quote_analysis` ✅
- `product_search` ✅
- `building_analysis` ✅
- `lead_generation` ✅
- `pricing_import` ⚠️ (needs to be added)

---

### 3.3 Run Seed Script (if needed)

**Command**:
```bash
cd backend
python scripts/seed_ai_prompts.py
```

**Expected**: All prompts should be seeded successfully

---

## Implementation Order

1. ✅ **Phase 1.1**: Remove competitor analysis fallback
2. ✅ **Phase 1.2**: Remove customer analysis fallback
3. ✅ **Phase 1.3**: Remove activity enhancement fallback
4. ✅ **Phase 1.4**: Remove action suggestions fallback
5. ✅ **Phase 1.5**: Remove translation fallback
6. ✅ **Phase 2.1**: Migrate pricing import prompt
7. ✅ **Phase 3**: Verify database state

---

## Testing Checklist

### Unit Tests
- [ ] Test `ai_analysis_service.py` without fallbacks
- [ ] Test `activity_service.py` without fallbacks
- [ ] Test `translation_service.py` without fallback
- [ ] Test `pricing_import_service.py` with database prompt

### Integration Tests
- [ ] Verify all services fail gracefully when prompts not found
- [ ] Verify all services work when prompts exist
- [ ] Verify error messages are clear and actionable

### Manual Testing
- [ ] Run AI analysis on a customer (should work)
- [ ] Run activity enhancement (should work)
- [ ] Run translation (should work)
- [ ] Run pricing import (should work)
- [ ] Test with prompts disabled (should fail gracefully)

---

## Rollback Plan

If issues arise:

1. **Immediate Rollback**: Revert git commits
2. **Partial Rollback**: Re-enable fallbacks for specific services
3. **Database Rollback**: Prompts remain in database, services can be reverted

---

## Success Criteria

- ✅ All hardcoded fallbacks removed
- ✅ All services use database prompts only
- ✅ Clear error messages when prompts not found
- ✅ All prompt categories exist in database
- ✅ Seed script includes all prompts
- ✅ No hardcoded prompts in service code
- ✅ All tests pass

---

## Files to Modify

1. `backend/app/models/ai_prompt.py` - Add `PRICING_IMPORT` enum
2. `backend/app/services/ai_analysis_service.py` - Remove 2 fallbacks
3. `backend/app/services/activity_service.py` - Remove 2 fallbacks
4. `backend/app/services/translation_service.py` - Remove 1 fallback
5. `backend/app/services/pricing_import_service.py` - Migrate to database
6. `backend/scripts/seed_ai_prompts.py` - Add pricing import prompt

---

## Documentation Updates

- [ ] Update `AI_PROMPTS_PRINCIPLE.md` to remove services from "Still Has Hardcoded Fallbacks" list
- [ ] Update `AI_PROMPTS_SYSTEM.md` if needed
- [ ] Update `TODO.md` to mark migration complete

---

**Status**: Ready for Implementation  
**Next Steps**: Begin Phase 1.1 - Remove competitor analysis fallback

