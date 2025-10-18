# AI-Powered Dashboard Assistant Implementation

## Overview
The AI-Powered Dashboard Assistant is a comprehensive feature that provides natural language query capabilities with dynamic data visualizations for the CRM system.

## Features

### 1. Natural Language Queries
Users can ask questions about their CRM data in plain English:
- "Who are my top leads?"
- "Show me the breakdown of customers by status"
- "What's the trend over the last 6 months?"
- "Show me the distribution of my customers"

### 2. Dynamic Visualizations
The assistant automatically generates appropriate visualizations based on the query:
- **Bar Charts**: Customer counts, lead scores, status breakdowns
- **Line Charts**: Trends over time, monthly performance
- **Doughnut Charts**: Distribution and percentage breakdowns

### 3. Contextual Data
The assistant has access to comprehensive CRM data:
- Customer counts by status (LEAD, PROSPECT, CUSTOMER, etc.)
- Contact information and averages
- Monthly trends (last 6 months)
- Top performing leads with scores
- Conversion rates and metrics

### 4. Suggested Follow-ups
After each query, the assistant provides relevant follow-up questions to explore the data further.

## Technical Implementation

### Backend Configuration

#### Model: GPT-5-mini
```python
model = "gpt-5-mini"
max_completion_tokens = 10000  # Minimum 10K tokens for comprehensive responses
timeout = 120.0  # 2 minutes timeout
```

#### API Endpoint
**Route:** `/api/v1/dashboard/ai-query`
**Method:** POST
**Request:**
```json
{
  "query": "who are my top leads"
}
```

**Response:**
```json
{
  "answer": "Your top 2 leads are...",
  "data": {...},
  "visualization_type": "bar_chart",
  "chart_data": {
    "labels": ["Central Technology ltd", "Arkel Computer Services"],
    "datasets": [{
      "label": "Lead Score",
      "data": [85, 58],
      "backgroundColor": "#f093fb"
    }]
  },
  "suggested_followup": [
    "Show me the trend over the last 6 months",
    "What's the breakdown of customers by status?"
  ]
}
```

### Context Building
The AI receives comprehensive context including:
```
CUSTOMERS & LEADS:
- Total Customers/Leads in System: X
- Active Leads: X
- Qualified Prospects: X
- Active Customers: X

CONTACTS:
- Total Contacts: X
- Average Contacts per Customer: X

MONTHLY TRENDS (Last 6 Months):
- May 2025: X new leads, X converted
- June 2025: X new leads, X converted
...

TOP PERFORMING LEADS:
- Company Name (Score: X)
...
```

### Visualization Detection
The system automatically detects appropriate visualization types based on query keywords:

| Keywords | Visualization | Use Case |
|----------|--------------|----------|
| "how many", "count", "total", "breakdown" | Bar Chart | Comparing quantities |
| "trend", "over time", "monthly", "growth" | Line Chart | Time-series data |
| "distribution", "percentage", "proportion" | Doughnut Chart | Part-to-whole relationships |
| "top", "best", "highest", "leading" | Bar Chart | Rankings |

### API Key Resolution
The system implements a fallback pattern for API keys:
1. Check tenant-specific API keys
2. Fall back to system-wide keys (admin portal)
3. Return error if neither is configured

```python
from app.core.api_keys import get_api_keys

api_keys = get_api_keys(db, current_tenant)
ai_service = AIAnalysisService(
    openai_api_key=api_keys.openai,
    companies_house_api_key=api_keys.companies_house,
    google_maps_api_key=api_keys.google_maps
)
```

## Frontend Implementation

### Component Structure
- **AI Query Input**: Multi-line text field with send button
- **AI Response Card**: Displays AI-generated insights
- **Visualization Card**: Dynamic chart rendering (Bar, Line, Doughnut)
- **Suggested Questions**: Clickable chips for quick queries
- **Quick Insights**: Pre-defined useful questions

### Chart Integration
Using `react-chartjs-2` for visualizations:
```typescript
import { Bar, Line, Doughnut } from 'react-chartjs-2';
import { Chart as ChartJS } from 'chart.js/auto';
```

### State Management
```typescript
const [aiQuery, setAiQuery] = useState('');
const [aiResponse, setAiResponse] = useState('');
const [aiChartData, setAiChartData] = useState<any>(null);
const [aiChartType, setAiChartType] = useState<string | null>(null);
const [suggestedQuestions, setSuggestedQuestions] = useState<string[]>([]);
```

## Debugging

### Debug Logging
The service includes comprehensive debug logging:
```
[DEBUG] Calling OpenAI API with model: gpt-5-mini
[DEBUG] Context length: 1226 characters
[DEBUG] Raw OpenAI response object: ...
[DEBUG] OpenAI response received: 342 characters
```

### Common Issues

#### Issue: Empty AI Responses
**Symptoms:** Chart displays but no text response
**Cause:** Insufficient tokens or wrong model
**Solution:**
- Ensure `max_completion_tokens >= 10000`
- Use `gpt-5-mini` model
- Increase timeout to 120 seconds

#### Issue: API Key Not Found
**Symptoms:** "AI service is currently unavailable"
**Cause:** API keys not configured
**Solution:**
- Configure tenant API keys in Settings
- Configure system-wide keys in Admin Portal
- Verify keys are stored in database

#### Issue: Slow Responses
**Cause:** Complex queries, large datasets
**Solution:**
- Optimize data queries
- Increase timeout
- Use pagination for large result sets

## Configuration Files

### Backend
- `backend/app/api/v1/endpoints/dashboard.py` - Dashboard endpoints
- `backend/app/services/ai_analysis_service.py` - AI service implementation
- `backend/app/core/api_keys.py` - API key resolution helper

### Frontend
- `frontend/src/pages/Dashboard.tsx` - Dashboard UI component
- `frontend/src/services/api.ts` - API client

## Future Enhancements

### Planned Features
1. **Conversation History**: Store and display past queries
2. **Export Capabilities**: Export insights as PDF/CSV
3. **Task Creation**: Create tasks/reminders from insights
4. **Advanced Analytics**: Predictive analytics, forecasting
5. **Custom Prompts**: User-configurable AI prompts stored in database

### Expandability
The system is designed to expand as new CRM modules are added:
- Quotes module: Add quote metrics to context
- Lead Campaigns: Include campaign performance
- Tasks/Reminders: Show upcoming actions
- Customer Interactions: Analyze interaction patterns

## Best Practices

### Documentation
Always document important technical details in code:
```python
"""
IMPORTANT: Uses GPT-5-mini model for AI responses.
Configure with minimum 10000 tokens and 120s timeout.
"""
```

### API Key Management
- Store keys in database (tenant table)
- Implement fallback to system keys
- Never hardcode keys in source code

### Error Handling
- Provide user-friendly error messages
- Log detailed errors for debugging
- Implement graceful fallbacks

## Performance Metrics

### Response Times
- Average: 3-8 seconds
- With visualizations: 5-10 seconds
- Complex queries: 10-15 seconds

### Token Usage
- Average query: 200-500 tokens
- Complex analysis: 500-2000 tokens
- Allocated: 10,000 tokens (ensures comprehensive responses)

## Version History

### Version 2.1.0 (Current)
- ✅ Implemented AI-powered dashboard assistant
- ✅ Dynamic visualization generation
- ✅ Comprehensive CRM data context
- ✅ API key fallback mechanism
- ✅ Suggested follow-up questions
- ✅ Quick insights shortcuts
- ✅ GPT-5-mini integration with 10K tokens

### Next Version (Planned)
- ⏳ Conversation history tracking
- ⏳ Export capabilities
- ⏳ Task creation from insights
- ⏳ Custom AI prompts in database

## Support

For issues or questions:
1. Check debug logs: `docker-compose logs backend --tail=100`
2. Verify API keys in database
3. Test with simple queries first
4. Review `ENUM_MANAGEMENT.md` for database issues

Last Updated: 2025-10-12





