# AI Suggestion Review & Merge System

## Overview

The AI Auto-Fill feature now includes a comprehensive review and merge system that allows users to see exactly what the AI suggests before applying any changes. This prevents accidental overwrites of manually curated data and gives complete control over which suggestions to accept.

## Key Features

### 1. **No Automatic Updates**
- AI suggestions are **never automatically applied** to the form
- All suggestions are stored in a separate state (`autoFillResults`)
- User must explicitly choose to apply, merge, or discard suggestions

### 2. **Side-by-Side Comparison**
Each field is displayed with a visual comparison:
- **LEFT SIDE (Gray)**: Current/existing data
- **RIGHT SIDE (Colored)**: AI-suggested data

### 3. **Section-by-Section Control**
Users can handle each section independently:

#### **📝 Company Description**
- Visual text comparison (current vs AI)
- Actions: **Use AI Version** | **Keep Current**

#### **📦 Products & Services**
- Chip-based display showing counts: `CURRENT (5)` vs `AI SUGGESTED (8)`
- Actions: **Replace** | **Merge (Add New)** | **Keep Current**

#### **⭐ Unique Selling Points**
- Chip-based display with counts
- Actions: **Replace** | **Merge (Add New)** | **Keep Current**

#### **🎯 Target Markets**
- Chip-based display with counts
- Actions: **Replace** | **Merge (Add New)** | **Keep Current**

#### **💼 Elevator Pitch**
- Visual text comparison
- Actions: **Use AI Version** | **Keep Current**

### 4. **Global Actions**
Quick actions to apply to all sections at once:
- **Replace All** - Replace all fields with AI suggestions
- **Merge All** - Merge AI suggestions with existing data (arrays combined, no duplicates)
- **Discard All** - Ignore all AI suggestions and close the review panel

## Technical Implementation

### Frontend State Management

```typescript
interface AutoFillResults {
  confidence_score: number;
  sources: string[];
  keywords: string[];
  linkedin_url: string | null;
  social_media_links: Record<string, string>;
  ai_data: {
    company_description: string;
    products_services: string[];
    unique_selling_points: string[];
    target_markets: string[];
    sales_methodology: string;
    elevator_pitch: string;
    company_phone_numbers: string[];
    company_email_addresses: Array<{ email: string; is_default: boolean }>;
    company_address: string;
    website_keywords: Record<string, string[]>;
  };
}
```

### Key Functions

#### `applySectionSuggestion(field: string, action: 'replace' | 'merge' | 'discard')`
Applies AI suggestion to a single field:
- **Replace**: Overwrites current value with AI value
- **Merge**: Combines arrays (removing duplicates) or merges objects
- **Discard**: Keeps current value unchanged

#### `applyAllSuggestions(action: 'replace' | 'merge')`
Applies AI suggestions to all fields at once with the specified action.

#### `discardAllSuggestions()`
Clears the `autoFillResults` state and closes the review panel.

### Merge Logic

For **array fields** (products_services, unique_selling_points, target_markets):
```typescript
[...new Set([...currentArray, ...aiArray])]
```
This combines both arrays and removes duplicates using JavaScript Set.

For **object fields** (website_keywords):
```typescript
{ ...currentObject, ...aiObject }
```
This merges objects with AI values taking precedence.

For **string fields** (company_description, elevator_pitch):
- Merge = Replace (since merging text doesn't make sense)

## User Workflow

1. **Navigate to Settings → Company Profile**
2. **Add company website** (required for AI analysis)
3. **Click "AI Auto-Fill Profile"**
4. **AI analyzes:**
   - Company website (scraped & analyzed)
   - LinkedIn profile (if found)
   - Companies House data (if available)
   - Social media links
   - Performs AI inference

5. **Review Results Panel Appears:**
   - Shows confidence score (e.g., 85%)
   - Lists data sources used
   - Displays social media links found
   - Shows extracted keywords

6. **Review Each Section:**
   - See current data vs AI suggestions side-by-side
   - Choose action per section (Replace/Merge/Keep)
   - Or use global actions (Replace All/Merge All/Discard All)

7. **Click "Save Company Profile":**
   - Only after applying desired suggestions
   - Persists changes to database

## Visual Design

### Color Coding
- **Current Data Boxes**: Light gray (`#f5f5f5`)
- **AI Suggested Boxes**: Colored backgrounds
  - Company Description: Light blue (`#e3f2fd`)
  - Products & Services: Light blue (`#e3f2fd`)
  - Unique Selling Points: Light green (`#e8f5e9`)
  - Target Markets: Light purple (`#f3e5f5`)
  - Elevator Pitch: Light red (`#ffebee`)

### Border Colors
Each section has a colored left border:
- 🟠 Company Description: Orange (`warning.main`)
- 🔵 Products & Services: Blue (`info.main`)
- 🟢 Unique Selling Points: Green (`success.main`)
- 🟣 Target Markets: Purple (`secondary.main`)
- 🔴 Elevator Pitch: Red (`error.main`)

## Benefits

1. **Transparency**: Users see exactly what AI suggests before applying
2. **Control**: Granular control over which fields to update
3. **Safety**: No accidental overwrites of manually entered data
4. **Flexibility**: Can mix AI and manual data (merge mode)
5. **Confidence**: Shows AI confidence score and data sources
6. **Reversibility**: Can discard all suggestions without affecting current data

## Backend API Response

The `/company-profile/auto-fill` endpoint returns:

```json
{
  "success": true,
  "message": "Company profile auto-filled successfully",
  "data": {
    "company_description": "...",
    "products_services": [...],
    "unique_selling_points": [...],
    "target_markets": [...],
    "sales_methodology": "...",
    "elevator_pitch": "...",
    "company_phone_numbers": [...],
    "company_email_addresses": [...],
    "company_address": "...",
    "keywords": [...],
    "linkedin_url": "...",
    "website_keywords": {...},
    "social_media_links": {...}
  },
  "confidence_score": 85,
  "sources": [
    "Primary Website: ✓ Scraped & Analyzed",
    "LinkedIn: ⚠ Profile Suggested (not scraped)",
    "Companies House: ✓ Company Data Retrieved",
    "AI Inference: ✓ Enhanced with AI analysis"
  ]
}
```

## Future Enhancements

- [ ] Edit suggestions inline before applying
- [ ] Show diff highlighting (red for removed, green for added)
- [ ] Save/load suggestion presets
- [ ] AI confidence per field (not just overall)
- [ ] Undo/redo functionality
- [ ] Version history of profile changes

