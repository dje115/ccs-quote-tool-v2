# Lead Generation Campaigns - Complete Guide

## 🎯 Overview

The Lead Generation Campaign system is a world-class AI-powered solution for discovering potential customers through comprehensive web search and multi-source data enrichment.

## ✨ Key Features

### 1. **AI-Powered Lead Discovery**
- Uses **GPT-5-mini with Responses API** for web search
- Minimum **20,000 tokens** for comprehensive results
- **240-second timeout** for extensive searches
- Finds REAL, VERIFIED UK businesses only

### 2. **Multi-Source Data Enrichment**
Automatically enriches every lead with data from:
- **Google Maps API**: Multiple locations, ratings, contact info
- **Companies House API**: Registration number, financials, directors, SIC codes
- **LinkedIn**: Company profiles and social presence
- **Website Scraping**: Additional business details

### 3. **Intelligent Deduplication**
- Automatically checks against **existing customers** in CRM
- Checks against **existing leads** across all campaigns
- Case-insensitive company name matching
- Prevents duplicate work and ensures data quality

### 4. **Background Processing**
- Campaigns run in the background (3-10 minutes typical)
- No need to stay on the page
- Real-time status updates
- Automatic completion notifications

### 5. **DISCOVERY Status Integration**
- All campaign-generated leads start at **DISCOVERY** status
- Follows complete workflow: `DISCOVERY → LEAD → PROSPECT → OPPORTUNITY → CUSTOMER`
- Easy conversion to CRM customers

## 📋 Campaign Types

### IT/MSP Campaigns
1. **IT/MSP Expansion** - Find IT companies that could add cabling services
2. **IT/MSP Service Gaps** - Find IT companies with service gaps
3. **Competitor Verification** - Verify and research competitor companies

### Sector-Specific Campaigns
4. **Education** - Schools, colleges, universities
5. **Healthcare** - Hospitals, medical practices, clinics
6. **Manufacturing** - Industrial facilities, production companies
7. **Retail & Office** - Retail stores, office buildings, commercial properties

### Timing-Based Campaigns
8. **New Businesses** - Recently opened businesses needing IT infrastructure
9. **Planning Applications** - Companies with construction/renovation plans

### Custom Campaigns
10. **Similar Business Lookup** - Find businesses similar to a specific company
11. **Location-Based** - Target businesses in specific geographic areas
12. **Custom Prompt** - Create your own targeting criteria

## 🚀 Creating a Campaign

### Step 1: Choose Campaign Type
Select from 10+ pre-configured campaign types, each optimized for specific industries and scenarios.

### Step 2: Configure Search Parameters
```
- Postcode: UK postcode for search center
- Distance: Radius in miles (1-200)
- Max Results: Number of businesses to find (1-500)
```

### Step 3: Advanced Options (Optional)
- Include existing customers: Include companies already in your CRM
- Minimum company size: Filter by employee count
- Business sectors: Specific industries to target

### Step 4: Launch
Campaign automatically starts running in the background.

## 🔄 Campaign Workflow

```
1. Campaign Creation
   ↓
2. AI Web Search (GPT-5-mini with web search)
   ↓
3. Initial Results Parsing
   ↓
4. Data Enrichment (Google Maps, Companies House, LinkedIn)
   ↓
5. Deduplication Check
   ↓
6. Lead Record Creation (DISCOVERY status)
   ↓
7. Campaign Completion
```

## 📊 Lead Data Structure

Each lead includes:

### Basic Information
- Company name
- Website URL
- Company registration number (Companies House)
- Address and postcode
- Business sector and size

### Contact Information
- Contact name
- Email address
- Phone number
- Job title

### AI Analysis
- Lead score (0-100)
- Qualification reason
- Potential project value
- Timeline estimate
- AI confidence score
- Full AI analysis JSON

### External Data
- **Google Maps**: Location data, ratings, multiple addresses
- **Companies House**: Registration, financials, directors, SIC codes
- **LinkedIn**: Company profile URL and data
- **Website**: Scraped business information

## 🎯 Lead Scoring

Leads are automatically scored 0-100 based on:
- Business size and sector
- IT infrastructure needs
- Growth indicators
- Website quality
- Contact information availability
- Data completeness

## 🔐 API Configuration

### Required API Keys
1. **OpenAI (GPT-5-mini)**: For AI web search and analysis
2. **Google Maps**: For location and address enrichment
3. **Companies House**: For UK business verification

### Configuration Location
- **Tenant Settings** → API Keys
- Falls back to system-wide keys if tenant keys not configured
- Status indicators show configuration state

## 💡 Best Practices

### Campaign Design
1. **Start Small**: Begin with 50-100 results to test
2. **Specific Targeting**: Use narrow geographic areas (10-20 miles)
3. **Sector Focus**: Target specific industries for better results
4. **Regular Campaigns**: Run weekly/monthly for continuous lead flow

### Lead Management
1. **Review Quickly**: Process leads within 24-48 hours
2. **Convert Best Leads**: Move high-scoring leads to CRM immediately
3. **Add Context**: Use AI analysis to personalize outreach
4. **Track Progress**: Monitor conversion rates by campaign type

### Data Quality
1. **Enable Deduplication**: Always keep this on
2. **Exclude Existing**: Don't re-target existing customers
3. **Verify Before Contact**: Check lead data before reaching out
4. **Update Records**: Enhance leads with additional research

## 🔧 Technical Details

### Backend Architecture
```
FastAPI → Lead Generation Service → Multiple APIs
   ↓
Background Tasks (async)
   ↓
SQLAlchemy ORM → PostgreSQL
```

### AI Configuration
```python
Model: gpt-5-mini
Tokens: 20,000+ (comprehensive results)
Timeout: 240 seconds
Tools: [{"type": "web_search"}]
API: OpenAI Responses API
```

### Database Schema
```sql
-- Lead Generation Campaigns
campaigns (
  id, tenant_id, name, prompt_type,
  postcode, distance_miles, max_results,
  status, total_found, leads_created, duplicates_found
)

-- Leads
leads (
  id, tenant_id, campaign_id, company_name,
  website, company_registration, contact info,
  lead_score, ai_analysis, external_data
)
```

## 📈 Performance Expectations

### Typical Campaign Duration
- **50 businesses**: 3-5 minutes
- **100 businesses**: 5-8 minutes
- **250 businesses**: 10-15 minutes
- **500 businesses**: 15-25 minutes

### Success Rates
- **IT/MSP Campaigns**: 70-90% valid leads
- **Sector Campaigns**: 60-80% valid leads
- **Location-Based**: 50-70% valid leads

### Data Enrichment
- **Google Maps**: 80-95% match rate
- **Companies House**: 60-80% match rate (UK companies)
- **LinkedIn**: 40-60% profile found

## 🚨 Troubleshooting

### Common Issues

**Campaign Stuck in "Running"**
- Wait 10-15 minutes (AI web search can be slow)
- Check API keys are configured
- Review backend logs for errors

**No Results Found**
- Try broader search area (increase miles)
- Use different campaign type
- Check postcode is valid UK postcode

**Too Many Duplicates**
- Your database already has these companies
- Consider different geographic area
- Try different business sector

**Low Lead Scores**
- Refine campaign targeting
- Use more specific campaign types
- Adjust business sector filters

## 🎓 Examples

### Example 1: Local IT Company Expansion
```
Campaign: IT/MSP Expansion
Postcode: LE1 1AA
Distance: 15 miles
Max Results: 100
Expected: 70-80 valid leads
Duration: 6-8 minutes
```

### Example 2: Education Sector Targeting
```
Campaign: Education
Postcode: M1 1AA
Distance: 25 miles
Max Results: 50
Expected: 30-40 valid leads
Duration: 4-6 minutes
```

### Example 3: Competitor Research
```
Campaign: Competitor Verification
Custom: Add specific company names
Expected: High-quality data on each
Duration: 8-12 minutes
```

## 🔮 Future Enhancements

- **Celery Integration**: Move to Celery for distributed processing
- **Email Enrichment**: Find email addresses via Hunter.io or similar
- **Social Media**: Extract Twitter, Facebook, Instagram profiles
- **News Monitoring**: Track recent company news and events
- **Automated Outreach**: Generate personalized email templates
- **Campaign Templates**: Save and reuse successful campaigns
- **A/B Testing**: Compare campaign type effectiveness
- **Lead Nurturing**: Automated follow-up sequences

## 📞 Support

For technical issues or questions:
1. Check this guide first
2. Review backend logs: `docker-compose logs backend`
3. Verify API keys are configured
4. Contact system administrator

## 🎉 Success Tips

1. **Run Multiple Campaign Types**: Diversify your lead sources
2. **Monitor Conversion Rates**: Track which campaigns work best
3. **Act Quickly**: Contact leads within 24 hours of discovery
4. **Personalize Outreach**: Use AI analysis in your messaging
5. **Keep Data Clean**: Regular deduplication and data hygiene
6. **Continuous Improvement**: Refine targeting based on results

---

**Version**: 2.2.2  
**Last Updated**: October 2025  
**Status**: Production Ready  





