# AI Discovery Analysis System

## Overview
The CCS Quote Tool v2 includes a comprehensive AI-powered analysis system for discoveries (campaign-generated leads). This system uses GPT-5-mini to analyze companies and extract valuable business intelligence, including automatic contact information discovery.

## Features

### 🤖 AI-Powered Analysis
- **Model**: GPT-5-mini (Chat Completions API)
- **Tokens**: 20,000 max completion tokens
- **Timeout**: 240 seconds
- **Temperature**: 0.7 (balanced creativity/accuracy)

### 📊 Data Sources Analyzed
1. **Google Maps Data**
   - Business ratings and reviews
   - Formatted address
   - Phone number
   - Website URL
   - Business hours

2. **Companies House Data**
   - Company number and status
   - Company type
   - Date of creation
   - SIC codes (business classification)
   - Financial information (turnover, shareholders' funds, cash)
   - Director/Officer information
   - Registered office address

3. **LinkedIn Data**
   - LinkedIn URL
   - Industry classification
   - Company size
   - Company description

4. **Existing Lead Data**
   - Company name
   - Website
   - Postcode and address
   - Business sector
   - Company size

### 📋 Analysis Output

The AI provides comprehensive business intelligence including:

#### 1. Company Classification
- **Business Sector**: office, retail, industrial, healthcare, education, hospitality, manufacturing, technology, finance, government, other
- **Company Size**: Small, Medium, Large, Enterprise
- **Estimated Employees**: Numeric estimate
- **Estimated Revenue**: Revenue range (e.g., "£1-5M")

#### 2. Business Profile
- **Primary Business Activities**: Detailed description of what the company does
- **Company Profile**: Comprehensive company summary
- **Technology Maturity**: Basic, Intermediate, Advanced, Enterprise

#### 3. Financial Analysis
- **Financial Health Analysis**: Assessment of financial position, profitability trends, and stability
- **IT Budget Estimate**: Likely annual IT spending range
- **Growth Potential**: High, Medium, or Low with reasoning

#### 4. Opportunity Assessment
- **Technology Needs**: Predicted IT infrastructure requirements
- **Business Opportunities**: Potential IT infrastructure projects
- **Competitive Landscape**: Competitor analysis
- **Risk Factors**: Challenges or risks that might affect projects

#### 5. Contact Information (NEW!)
- **Contact Name**: Key contact person (Director, CEO, IT Manager, or general contact)
- **Contact Email**: Email address (info@, sales@, enquiries@, or specific contacts)
- **Contact Phone**: Direct phone number if available

The AI searches for contact information in:
- Website contact pages
- Google Maps business listing
- Companies House director information
- Any email addresses or contact names in the provided data

## API Endpoints

### Run AI Analysis
```http
POST /api/v1/campaigns/leads/{lead_id}/analyze
Authorization: Bearer {token}
```

**Response:**
```json
{
  "success": true,
  "analysis": {
    "business_sector": "technology",
    "estimated_employees": 25,
    "estimated_revenue": "£1-5M",
    "business_size_category": "Small",
    "primary_business_activities": "IT support and managed services for SMEs...",
    "technology_maturity": "Advanced",
    "it_budget_estimate": "£50k-100k annually",
    "growth_potential": "High",
    "technology_needs": "Modern infrastructure, cloud services, cybersecurity...",
    "competitors": "Similar IT service providers in the region...",
    "opportunities": "Network upgrade projects, cybersecurity implementations...",
    "risks": "Budget constraints, competitive market...",
    "company_profile": "Established IT services company...",
    "financial_health_analysis": "Strong financial position with growing revenue...",
    "contact_name": "John Smith (Director)",
    "contact_email": "info@company.co.uk",
    "contact_phone": "0116 240 8820"
  },
  "message": "AI analysis completed successfully"
}
```

## Frontend Integration

### Discovery Detail Page

#### Run AI Analysis Button
- Located in "Quick Actions" section
- Primary blue button
- Shows "Analyzing..." during processing
- Automatically refreshes page after completion

#### AI Analysis Display
The analysis is displayed in a structured, professional format:

1. **Company Profile** - Comprehensive summary at the top
2. **Key Metrics Grid** - 2-column grid showing:
   - Business Sector
   - Company Size
   - Estimated Employees
   - Estimated Revenue
   - Technology Maturity
   - IT Budget Estimate
   - Growth Potential (color-coded chip)

3. **Detailed Sections**:
   - Primary Business Activities
   - Financial Health Analysis
   - Technology Needs
   - Business Opportunities (green heading)
   - Competitive Landscape
   - Risk Factors (red heading)

### Contact Information Auto-Population

When AI analysis finds contact information, it automatically updates the lead record:
- **Contact Name**: Populated if found and field is empty
- **Contact Email**: Populated if found and field is empty
- **Contact Phone**: Populated if found and field is empty

**Note**: AI only updates empty fields to preserve manually entered data.

## Database Schema

### Lead Model Updates
The `ai_analysis` field stores the complete JSON response:

```python
class Lead(Base):
    # ... other fields ...
    ai_analysis = Column(JSON, nullable=True)  # Stores full AI analysis
    contact_name = Column(String(200), nullable=True)  # Auto-populated by AI
    contact_email = Column(String(255), nullable=True)  # Auto-populated by AI
    contact_phone = Column(String(50), nullable=True)  # Auto-populated by AI
```

## Usage Workflow

### For Users
1. Navigate to Discoveries page (`/leads`)
2. Click on a discovery to view details
3. Click "Run AI Analysis" button
4. Confirm the action
5. Wait for analysis (typically 10-30 seconds)
6. View comprehensive business intelligence
7. Contact information automatically populated if found

### For Developers

#### Backend Service
```python
from app.services.lead_generation_service import LeadGenerationService

service = LeadGenerationService(db, tenant_id)
result = await service.analyze_lead_with_ai(lead_id)

if result['success']:
    analysis = result['analysis']
    # Analysis data available
    # Contact info auto-saved to lead record
```

#### Frontend API Call
```typescript
import { campaignAPI } from '../services/api';

const handleRunAIAnalysis = async () => {
  try {
    const response = await campaignAPI.analyzeLead(leadId);
    if (response.data?.success) {
      // Reload lead to get updated data
      loadLead();
    }
  } catch (error) {
    console.error('Error:', error);
  }
};
```

## Performance Considerations

### Token Usage
- **Average**: 15,000-20,000 tokens per analysis
- **Cost**: ~$0.10-0.15 per analysis (GPT-5-mini pricing)
- **Time**: 10-30 seconds depending on data complexity

### Optimization
- Analysis results are cached in the `ai_analysis` field
- Re-running analysis on the same lead overwrites previous results
- Only updates empty contact fields (preserves manual data)

### Rate Limiting
- OpenAI API rate limits apply
- Recommend: Max 10 concurrent analyses
- Consider queuing for bulk analysis operations

## Error Handling

### Common Errors

1. **"OpenAI client not initialized"**
   - Cause: API key not configured
   - Solution: Add OpenAI API key in Settings

2. **"Lead not found"**
   - Cause: Invalid lead ID
   - Solution: Verify lead exists and user has access

3. **"Failed to parse AI response"**
   - Cause: AI returned invalid JSON
   - Solution: Retry analysis (rare occurrence)

4. **Timeout Errors**
   - Cause: Analysis taking >240 seconds
   - Solution: Retry or check API connectivity

### Logging
All analysis operations are logged with prefixes:
- `[AI ANALYSIS]` - General operations
- `[AI ANALYSIS] ✓` - Success messages
- `[AI ANALYSIS] ✗` - Error messages

Example logs:
```
[AI ANALYSIS] Running analysis for Quatrix Limited
[AI ANALYSIS] ✓ Found contact name: Steven David Wheat (Director)
[AI ANALYSIS] ✓ Found contact email: hello@quatrix.co.uk
[AI ANALYSIS] ✓ Analysis completed for Quatrix Limited
```

## Best Practices

### When to Run AI Analysis

**✅ Good Times:**
- After campaign generates new discoveries
- Before converting discovery to CRM lead
- When contact information is missing
- When assessing lead quality/priority

**❌ Avoid:**
- Running multiple times on same lead (wastes tokens)
- Running on leads with complete manual data
- Bulk analysis without rate limiting

### Data Quality

**To Get Best Results:**
1. Ensure external data is collected first (Google Maps, Companies House)
2. Verify website URL is correct
3. Run analysis after all API data is gathered
4. Review and validate AI-suggested contact information

### Contact Information Validation

**Important Notes:**
- AI-extracted contacts are suggestions, not guaranteed accurate
- Always verify contact information before use
- Check email format and phone number validity
- Consider manual verification for high-value leads

## Future Enhancements

### Planned Features
1. **Bulk Analysis** - Analyze multiple discoveries at once
2. **Analysis Scheduling** - Auto-analyze new discoveries
3. **Confidence Scores** - Rate reliability of extracted data
4. **Contact Verification** - Validate email addresses
5. **Historical Tracking** - Track analysis changes over time
6. **Custom Prompts** - Tenant-specific analysis criteria

### Integration Opportunities
1. **Email Verification API** - Validate extracted emails
2. **Phone Validation** - Verify UK phone numbers
3. **LinkedIn API** - Enhanced contact discovery
4. **CRM Enrichment** - Auto-update customer records

## Security & Privacy

### Data Handling
- All data sent to OpenAI is encrypted in transit
- No PII stored in AI analysis results beyond what's publicly available
- Contact information sourced from public business listings
- Complies with GDPR for business contact data

### API Key Security
- OpenAI API keys stored encrypted in database
- Tenant-specific keys supported
- System-wide fallback keys available
- Keys never exposed in frontend

## Troubleshooting

### Analysis Not Running
1. Check OpenAI API key is configured
2. Verify API key has sufficient credits
3. Check backend logs for errors
4. Ensure lead has sufficient data

### Poor Quality Results
1. Verify external data was collected
2. Check website URL is accessible
3. Ensure company has online presence
4. Try re-running after updating lead data

### Contact Information Not Found
- Not all companies have publicly available contacts
- AI can only find what's in the provided data
- Consider manual research for high-priority leads
- Check company website directly

## Files Modified/Created

### Backend
- `backend/app/services/lead_generation_service.py` - AI analysis service
- `backend/app/api/v1/endpoints/campaigns.py` - Analysis endpoint
- `backend/app/models/leads.py` - Lead model with ai_analysis field

### Frontend
- `frontend/src/pages/LeadDetail.tsx` - Analysis UI and display
- `frontend/src/services/api.ts` - API integration
- `frontend/src/pages/Leads.tsx` - Discoveries list page

### Documentation
- `AI_DISCOVERY_ANALYSIS.md` - This file
- `DISCOVERY_TO_CRM_WORKFLOW.md` - Discovery workflow documentation

## Support

For issues or questions:
1. Check backend logs for detailed error messages
2. Verify API key configuration in Settings
3. Review this documentation
4. Contact system administrator

## Version History

### v2.1.0 (Current)
- ✅ AI-powered discovery analysis
- ✅ Automatic contact information extraction
- ✅ Comprehensive business intelligence
- ✅ Structured UI display
- ✅ Auto-population of contact fields

### Future Versions
- v2.2.0: Bulk analysis and scheduling
- v2.3.0: Contact verification and validation
- v2.4.0: Custom analysis prompts



