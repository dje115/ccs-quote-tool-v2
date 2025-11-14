# Company Size Filter Feature Guide

## Overview
The company size filter allows users to target specific company sizes when creating lead generation campaigns. This helps reduce large corporate results and focus on SMEs or specific market segments.

## Company Size Categories

| Size | Employee Range | Use Case |
|------|----------------|----------|
| **Micro** | 0-9 employees | Solo entrepreneurs, very small teams, startups |
| **Small** | 10-49 employees | Growing businesses, local SMEs |
| **Medium** | 50-249 employees | Established businesses, regional players |
| **Large** | 250+ employees | Corporations, national chains |

## Frontend Implementation

### Dynamic Business Search Form
**Location:** `/campaigns/new`

The company size selector is displayed in the "Basic Information" section:
```tsx
{/* Company Size Category */}
<Grid size={{ xs: 12, md: 6 }}>
  <FormControl fullWidth>
    <InputLabel>Company Size (Optional)</InputLabel>
    <Select
      value={campaignData.company_size_category || ''}
      onChange={(e) => handleInputChange('company_size_category', e.target.value || undefined)}
    >
      <MenuItem value="">Any Size</MenuItem>
      <MenuItem value="Micro">Micro (0-9 employees)</MenuItem>
      <MenuItem value="Small">Small (10-49 employees)</MenuItem>
      <MenuItem value="Medium">Medium (50-249 employees)</MenuItem>
      <MenuItem value="Large">Large (250+ employees)</MenuItem>
    </Select>
  </FormControl>
</Grid>
```

**Field Properties:**
- Optional field (users can leave blank for "Any Size")
- Located after the Distance field
- Included in form reset functionality
- Passed to API during campaign creation

### Campaign Detail Page
**Location:** `/campaigns/{campaignId}`

The selected company size is displayed in the "Campaign Details" section:
```tsx
{campaign.company_size_category && (
  <Grid size={{ xs: 12, sm: 6, md: 4 }}>
    <Box sx={{ p: 2, backgroundColor: 'white', borderRadius: 2, border: '1px solid #e0e0e0' }}>
      <Typography variant="body2" color="text.secondary" gutterBottom>
        Company Size
      </Typography>
      <Typography variant="body1" fontWeight="600" sx={{ color: '#9c27b0' }}>
        👥 {campaign.company_size_category}
      </Typography>
    </Box>
  </Grid>
)}
```

## Backend Implementation

### Database
**Table:** `lead_generation_campaigns`
**Column:** `company_size_category` (VARCHAR(50), NULLABLE)

Migration:
```sql
ALTER TABLE lead_generation_campaigns 
ADD COLUMN IF NOT EXISTS company_size_category VARCHAR(50) NULL;
```

### API Schema
**File:** `app/schemas/campaign.py`

```python
class CampaignCreate(BaseModel):
    # ... other fields ...
    company_size_category: Optional[str] = Field(
        None, 
        description="Company size filter: Micro, Small, Medium, Large"
    )

class CampaignResponse(BaseModel):
    # ... other fields ...
    company_size_category: Optional[str]
```

### Campaign Creation Endpoint
**File:** `app/api/v1/endpoints/campaigns.py`

The company_size_category is stored when creating a campaign:
```python
campaign = LeadGenerationCampaign(
    # ... other fields ...
    company_size_category=campaign_data.company_size_category,
    # ... rest of fields ...
)
```

### Lead Generation Service
**File:** `app/services/lead_generation_service.py`

#### 1. Prompt Context
The company size is added to the AI prompt context:
```python
Target Company Size: {campaign_data.get('company_size_category', 'Any Size')}
```

#### 2. Search Approach
Instruction for AI to filter by size:
```
5. Filter by company size: Prioritize {size} companies ({employee_range})
```

#### 3. Quality Rules
The AI is told to prioritize the specified size:
```
- Filter by company size: Prioritize {size} companies ({employee_range})
- If no size specified: Prioritize SMEs and small-to-medium enterprises over large corporations
```

#### 4. Helper Method
```python
def _get_company_size_description(self, size_category: str) -> str:
    """Get employee count description for company size category"""
    size_descriptions = {
        'Micro': '0-9 employees',
        'Small': '10-49 employees',
        'Medium': '50-249 employees',
        'Large': '250+ employees'
    }
    return size_descriptions.get(size_category, 'Any size')
```

## Data Flow

```
User selects size
    ↓
Form submission
    ↓
API receives CampaignCreate with company_size_category
    ↓
Campaign stored in DB with size filter
    ↓
Campaign starts (Celery task)
    ↓
Campaign data passed to LeadGenerationService.generate_leads()
    ↓
AI prompt built with size context
    ↓
AI searches for companies matching the specified size
    ↓
Results filtered and returned
    ↓
Campaign Detail page displays search parameters including size
```

## Usage Tips

### Best Practices
1. **For local SME targeting:** Select "Micro" or "Small"
2. **For established businesses:** Select "Medium"
3. **For enterprise sales:** Select "Large"
4. **For broad searches:** Leave blank (Any Size)

### AI Behavior
- **With size selected:** AI prioritizes companies matching that size range
- **Without size selected:** AI defaults to SMEs and small-to-medium enterprises
- **Size is a guide:** AI may still return some companies outside the range if they're highly relevant

### Combining with Other Filters
Company size works alongside:
- **Postcode + Distance:** Location-based filtering
- **Sector:** Industry targeting
- **Max Results:** Quantity control

## Testing the Feature

### Manual Testing Steps
1. Go to `/campaigns/create` → "Dynamic Business Search"
2. Fill in required fields (sector, postcode, distance, max results)
3. Select a company size (e.g., "Small")
4. Create campaign
5. View campaign detail page
6. Verify company size is displayed

### Database Verification
```sql
SELECT id, name, company_size_category FROM lead_generation_campaigns 
WHERE company_size_category IS NOT NULL;
```

## Troubleshooting

### Issue: Column not found error
**Solution:** Run the migration:
```sql
ALTER TABLE lead_generation_campaigns 
ADD COLUMN IF NOT EXISTS company_size_category VARCHAR(50) NULL;
```

### Issue: Company size not showing on detail page
**Solution:** Ensure `company.company_size_category` is in the CampaignResponse schema

### Issue: AI ignoring company size
**Solution:** Check that campaign_data contains `company_size_category` before calling `generate_leads()`

## Future Enhancements
- [ ] Employee count range input (custom ranges)
- [ ] Revenue-based filtering
- [ ] Industry-specific size recommendations
- [ ] Historical performance by company size
- [ ] A/B testing results by size category

