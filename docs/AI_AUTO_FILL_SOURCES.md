# AI Auto-Fill Sources & Data Collection

## Overview
The AI Auto-Fill feature for tenant company profiles now scrapes and analyzes multiple sources to provide comprehensive business intelligence.

## Data Sources

### 1. **Primary Website** (Required)
- **Method**: HTTP GET request with BeautifulSoup scraping
- **Data Collected**: 
  - Full page text (up to 5000 characters)
  - Meta tags, page structure, content
- **Status**: ✓ Scraped & Analyzed (if successful)
- **Usage**: Primary source for company description, products/services

### 2. **LinkedIn Company Profile** (Auto-discovered)
- **Method**: Multiple URL pattern attempts with web scraping
- **Patterns Tried**:
  - `https://www.linkedin.com/company/{company-name}`
  - `https://www.linkedin.com/company/{companyname}` (no spaces/punctuation)
- **Data Collected**:
  - Profile text (first 1000 characters)
  - Company URL (actual LinkedIn URL)
- **Status**: 
  - ✓ Profile Found & Scraped (if accessible)
  - ⚠ Profile Suggested (if not accessible but URL constructed)
  - ✗ Not found
- **Usage**: Additional context for company culture, size, industry

### 3. **Companies House API** (If API key configured)
- **Method**: Official Companies House API search
- **Data Collected**:
  - Company number
  - Company status (Active, Dissolved, etc.)
  - Company type (Ltd, PLC, etc.)
  - Registered address snippet
- **Status**: ✓ Company Data Retrieved (if found)
- **Usage**: Validates company legitimacy, provides official data

### 4. **AI Inference** (GPT-5-Mini)
- **Method**: OpenAI Chat Completions API
- **Model**: `gpt-5-mini`
- **Tokens**: 20,000 max completion tokens
- **Timeout**: 240 seconds
- **Input Data**: All scraped sources + company name + websites
- **Output**: Structured JSON with:
  - Company description
  - Products & services (5-10 items)
  - Unique selling points (3-7 items)
  - Target markets (3-7 items)
  - Sales methodology (consultative/transactional/etc.)
  - Elevator pitch
  - Contact information (phones, emails, address)
  - **SEO/Marketing Keywords** (automatically extracted)
  - Confidence score (0-100%)

## Data Processing Pipeline

```
User Input (Company Name + Website(s))
         ↓
1. Scrape Primary Website
   - Extract text content
   - Parse structure
         ↓
2. Find & Scrape LinkedIn
   - Try multiple URL patterns
   - Extract profile text
         ↓
3. Search Companies House (if API key available)
   - Validate company existence
   - Get official data
         ↓
4. AI Analysis (GPT-5-Mini)
   - Analyze all collected data
   - Generate insights
   - Extract keywords
   - Calculate confidence score
         ↓
5. Present Results to User
   - Show all sources used
   - Display keywords as chips
   - Allow review before saving
```

## Frontend Display

The auto-fill results are shown in an expanded alert box with:

### Confidence Score
- Percentage (0-100%) indicating data reliability
- Based on source availability and AI analysis

### Data Sources Section
- ✓ / ✗ indicators for each source
- Count of additional sources analyzed
- Clear status for each data collection method

### SEO/Marketing Keywords Section
- Visual chip-based display
- Count of total keywords extracted
- Color-coded for easy scanning
- Keywords can be used for:
  - Website SEO optimization
  - Marketing campaign targeting
  - Content creation
  - Industry positioning

### LinkedIn URL
- Clickable link to company LinkedIn profile
- Opens in new tab
- LinkedIn brand color (#0077b5)

## API Endpoint

**POST** `/api/v1/settings/company-profile/auto-fill`

### Request Body
```json
{
  "company_name": "Required from tenant settings",
  "websites": ["Required: at least one website from profile"]
}
```

### Response
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
    "company_email_addresses": [{"email": "...", "is_default": true}],
    "company_address": "...",
    "keywords": ["keyword1", "keyword2", ...],
    "linkedin_url": "https://linkedin.com/company/..."
  },
  "confidence_score": 85,
  "sources": {
    "website_scraped": true,
    "linkedin_found": true,
    "linkedin_suggested": false,
    "companies_house": true,
    "additional_sources_count": 1,
    "ai_inference": true
  }
}
```

## Error Handling

Each data source is scraped independently with try/catch blocks:
- If website scraping fails → Continue with AI inference only
- If LinkedIn not found → Use suggested URL pattern
- If Companies House unavailable → Skip this source
- If AI analysis fails → Return error to user with details

## Best Practices

1. **Always provide at least one website** - This is the minimum requirement
2. **Set company name in Settings → Profile** before using auto-fill
3. **Configure Companies House API key** for enhanced data (optional)
4. **Review auto-filled data** before saving - AI suggestions should be validated
5. **Use extracted keywords** for marketing campaigns and SEO optimization

## Future Enhancements

- [ ] Crunchbase integration
- [ ] Google Business Profile scraping
- [ ] Social media profile discovery (Twitter, Facebook)
- [ ] Industry news and press release scraping
- [ ] Competitor analysis
- [ ] Market positioning insights
- [ ] Historical data tracking (track changes over time)

## Technical Notes

### Web Scraping
- User-Agent: `Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36`
- Timeout: 5 seconds per source
- Follow redirects: Yes
- HTML Parser: BeautifulSoup with default parser

### API Keys Required
- **OpenAI**: Required for AI analysis
- **Companies House**: Optional but recommended

### Rate Limiting
- No explicit rate limiting currently implemented
- Timeouts prevent hanging requests
- Consider implementing rate limiting for production use

## Version History
- **v2.1.0** (2025-10-12): Enhanced multi-source scraping, keyword extraction, detailed source display
- **v2.0.0** (2025-10-10): Initial AI Auto-Fill implementation


