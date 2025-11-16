# AI Prompts Fallback Review - Code Review Findings

**Date**: 2025-01-XX  
**Status**: Review Complete  
**Purpose**: Document all hardcoded fallback prompts that need to be removed per `AI_PROMPTS_PRINCIPLE.md`

---

## Summary

The AI Prompts System is **90% complete**. Most services have been migrated to use database-driven prompts, but several services still contain hardcoded fallback prompts that violate the core principle: **ALL AI prompts MUST be stored in the database, NOT hardcoded in the code.**

---

## Services with Hardcoded Fallbacks

### 1. `ai_analysis_service.py` ⚠️

**Location**: `backend/app/services/ai_analysis_service.py`

#### Fallback 1: Competitor Analysis (Lines 379-416)
- **Category**: `competitor_analysis`
- **Lines**: 379-416
- **Status**: Has database prompt support, but fallback exists
- **Fallback Code**:
  ```python
  if not prompt_obj:
      print("[COMPETITORS] Using fallback prompt - database prompt not found")
      competitor_prompt = f"""Find REAL, VERIFIED UK competitors for: {company_name}..."""
      system_prompt = "You are an expert at finding real, verified business competitors..."
  ```
- **Action Required**: Remove fallback code (lines 379-416). Return error if prompt not found.

#### Fallback 2: Customer Analysis (Lines 715-833)
- **Category**: `customer_analysis`
- **Lines**: 715-833
- **Status**: Has database prompt support, but fallback exists
- **Fallback Code**: Large hardcoded prompt (lines 718-830)
- **Action Required**: Remove fallback code (lines 715-833). Return error if prompt not found.

---

### 2. `activity_service.py` ⚠️

**Location**: `backend/app/services/activity_service.py`

#### Fallback 1: Activity Enhancement (Lines 157-192)
- **Category**: `activity_enhancement`
- **Lines**: 157-192
- **Status**: Has database prompt support, but fallback exists
- **Fallback Code**:
  ```python
  if not prompt_obj:
      print("[ActivityService] Using fallback prompt - database prompt not found")
      user_prompt = f"""You are a sales assistant AI helping to process activity notes..."""
  ```
- **Action Required**: Remove fallback code (lines 157-192). Return error if prompt not found.

#### Fallback 2: Action Suggestions (Lines 457-490)
- **Category**: `action_suggestions`
- **Lines**: 457-490
- **Status**: Has database prompt support, but fallback exists
- **Fallback Code**:
  ```python
  if not prompt_obj:
      print("[ActivityService] Using fallback prompt for action suggestions - database prompt not found")
      user_prompt = f"""You are a sales advisor AI helping prioritize customer engagement actions..."""
  ```
- **Action Required**: Remove fallback code (lines 457-490). Return error if prompt not found.

---

### 3. `translation_service.py` ⚠️

**Location**: `backend/app/services/translation_service.py`

#### Fallback: Translation (Lines 47-60)
- **Category**: `translation`
- **Lines**: 47-60
- **Status**: Has database prompt support, but fallback exists
- **Fallback Code**:
  ```python
  else:
      # Fallback: use generate_with_rendered_prompts
      system_prompt = "You are a professional translator. Translate accurately and naturally."
      user_prompt = f"""Translate the following text from {source_language} to {target_language}..."""
  ```
- **Action Required**: Remove fallback code (lines 47-60). Return error if prompt not found.

---

## Services with Hardcoded Prompts (No Database Support)

### 4. `pricing_import_service.py` ⚠️

**Location**: `backend/app/services/pricing_import_service.py`

#### Hardcoded Prompt: Pricing Import (Lines 181-222)
- **Category**: `pricing_import` (NEW - needs to be added to PromptCategory enum)
- **Lines**: 181-222
- **Status**: No database prompt support - completely hardcoded
- **Hardcoded Code**:
  ```python
  prompt = f"""Analyze this pricing data from a file named "{filename}" and extract product information..."""
  system_prompt = "You are an expert at extracting and standardizing product pricing data from various file formats. Always return valid JSON arrays."
  ```
- **Action Required**:
  1. Add `PRICING_IMPORT = "pricing_import"` to `PromptCategory` enum
  2. Add prompt to seed script
  3. Update service to use `AIPromptService`
  4. Remove hardcoded prompt

---

### 5. `lead_generation_service.py` ⚠️

**Location**: `backend/app/services/lead_generation_service.py`

#### Status: ✅ Already Using Database Prompts
- **Category**: `lead_generation`
- **Status**: Service already uses `AIPromptService` and database prompts
- **Note**: Some hardcoded prompts exist in fallback methods (lines 570-695), but these are for error recovery, not primary prompts
- **Action Required**: Review fallback methods to ensure they're only used for error recovery, not as primary prompts

---

## Services Already Compliant ✅

The following services are already compliant with the database-driven prompts principle:

1. ✅ `quote_analysis_service.py` - Uses database prompts, no fallback
2. ✅ `building_analysis_service.py` - Uses database prompts
3. ✅ `product_search_service.py` - Uses database prompts
4. ✅ `lead_generation_service.py` - Uses database prompts (primary prompts)

---

## Migration Plan

### Phase 1: Remove Fallbacks from Services with Database Support

1. **`ai_analysis_service.py`**
   - Remove competitor analysis fallback (lines 379-416)
   - Remove customer analysis fallback (lines 715-833)
   - Return error if prompt not found: `{"success": False, "error": "AI prompt not configured"}`
   - Update error handling to log missing prompts

2. **`activity_service.py`**
   - Remove activity enhancement fallback (lines 157-192)
   - Remove action suggestions fallback (lines 457-490)
   - Return error if prompt not found

3. **`translation_service.py`**
   - Remove translation fallback (lines 47-60)
   - Return error if prompt not found

### Phase 2: Migrate Hardcoded Prompts to Database

1. **`pricing_import_service.py`**
   - Add `PRICING_IMPORT = "pricing_import"` to `PromptCategory` enum
   - Add prompt to seed script (`backend/scripts/seed_ai_prompts.py`)
   - Update service to use `AIPromptService`
   - Remove hardcoded prompt

### Phase 3: Verify Database State

1. Check if `ai_prompts` table exists in database
2. Check if prompts have been seeded
3. Verify all required prompt categories exist:
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

## Implementation Checklist

### Backend Changes

- [ ] Remove fallback from `ai_analysis_service.py` (2 locations)
- [ ] Remove fallback from `activity_service.py` (2 locations)
- [ ] Remove fallback from `translation_service.py` (1 location)
- [ ] Add `PRICING_IMPORT` to `PromptCategory` enum
- [ ] Add pricing import prompt to seed script
- [ ] Update `pricing_import_service.py` to use `AIPromptService`
- [ ] Remove hardcoded prompt from `pricing_import_service.py`

### Database Verification

- [ ] Verify `ai_prompts` table exists
- [ ] Verify prompts are seeded
- [ ] Verify all categories exist in database
- [ ] Test that services fail gracefully when prompts not found

### Testing

- [ ] Test `ai_analysis_service.py` without fallback
- [ ] Test `activity_service.py` without fallback
- [ ] Test `translation_service.py` without fallback
- [ ] Test `pricing_import_service.py` with database prompt
- [ ] Verify error messages are clear when prompts missing

---

## Error Handling Pattern

When removing fallbacks, use this pattern:

```python
if not prompt_obj:
    logger.error(f"No prompt found for category {category}, tenant_id={tenant_id}")
    return {
        "success": False,
        "error": f"AI prompt not configured for {category}. Please configure prompts in the admin section."
    }
```

**DO NOT** use hardcoded fallback prompts. The system should fail gracefully with a clear error message.

---

## Files to Modify

1. `backend/app/models/ai_prompt.py` - Add `PRICING_IMPORT` to enum
2. `backend/app/services/ai_analysis_service.py` - Remove 2 fallbacks
3. `backend/app/services/activity_service.py` - Remove 2 fallbacks
4. `backend/app/services/translation_service.py` - Remove 1 fallback
5. `backend/app/services/pricing_import_service.py` - Migrate to database
6. `backend/scripts/seed_ai_prompts.py` - Add pricing import prompt

---

## Success Criteria

- ✅ All hardcoded fallbacks removed
- ✅ All services use database prompts only
- ✅ Clear error messages when prompts not found
- ✅ All prompt categories exist in database
- ✅ Seed script includes all prompts
- ✅ No hardcoded prompts in service code

---

**Review Status**: ✅ Complete  
**Next Steps**: Implement migration plan to remove all hardcoded fallbacks

