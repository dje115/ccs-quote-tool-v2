# Sales Module Implementation Guide

## Overview
Comprehensive sales module with AI-powered assistance, activity tracking, and tenant profile management for intelligent, personalized sales guidance.

## Phase 1: Backend Foundation ✅ COMPLETE

### 1. Database Models

#### Tenant Profile Fields (Added to `tenants` table)
```sql
- company_description (TEXT): What does the tenant company do?
- products_services (JSONB): List of products/services offered
- unique_selling_points (JSONB): USPs that differentiate the tenant
- target_markets (JSONB): Industries/sectors targeted
- sales_methodology (VARCHAR): Preferred sales approach
- elevator_pitch (TEXT): 30-second company pitch
- company_analysis (JSONB): AI-generated business intelligence
- company_analysis_date (TIMESTAMP): When AI analysis was last run
```

#### Sales Activity Tracking
**Table: `sales_activities`**
- Tracks all sales interactions (calls, meetings, emails, notes)
- Links to customer, user, and optionally a contact
- Stores detailed notes, outcomes, and follow-up actions
- Tracks which AI suggestions were used
- Duration tracking for calls/meetings

**Table: `sales_notes`**
- Quick notes for observations and reminders
- Can be marked as important
- Simple, lightweight note-taking

**Enums:**
- `activitytype`: call, meeting, email, note, task
- `activityoutcome`: successful, no_answer, voicemail, follow_up_required, not_interested, meeting_scheduled, quote_requested, won, lost

### 2. API Endpoints

#### Tenant Profile Management
- **GET `/api/v1/settings/company-profile`**: Get tenant company profile
- **PUT `/api/v1/settings/company-profile`**: Update company profile
- **POST `/api/v1/settings/company-profile/analyze`**: Run AI analysis on tenant's business

### 3. AI Analysis Features

#### Tenant Business Analysis
The AI analyzes the tenant's company profile and provides:
1. **Business Model Analysis**: Understanding of how the business operates
2. **Competitive Positioning**: Strengths and differentiators
3. **Ideal Customer Profile (ICP)**: Who to target
4. **Pain Points Solved**: What problems the company addresses
5. **Sales Approach**: Recommended messaging and methodology
6. **Cross-sell Opportunities**: Additional services to offer
7. **Objection Handling**: Common objections and responses
8. **Industry Trends**: Market opportunities

## Phase 2: Frontend - Settings Page (IN PROGRESS)

### Company Profile Tab
Location: Settings → Company Profile

**Sections:**
1. **Company Information**
   - Company description (multi-line text)
   - Elevator pitch (text area)
   - Sales methodology (dropdown: consultative, solution-based, value-based, etc.)

2. **Products & Services**
   - Add/remove products/services (chip input)
   - Categorize by type (managed services, hardware, software, consulting, etc.)

3. **Unique Selling Points**
   - Add/remove USPs (chip input)
   - What makes you different from competitors?

4. **Target Markets**
   - Industries/sectors targeted (chip input with suggestions)
   - Company sizes (micro, small, medium, large)
   - Geographic focus

5. **AI Analysis Section**
   - Button: "Analyze My Company with AI"
   - Display analysis results in expandable sections:
     - Business Model
     - Competitive Position
     - Ideal Customer Profile
     - Pain Points We Solve
     - Recommended Sales Approach
     - Cross-selling Opportunities
     - Objection Handling Guide
     - Industry Trends & Opportunities
   - Show last analysis date
   - Re-run button

## Phase 3: Sales Tab (PENDING)

### Customer Detail → Sales Tab

**Layout: Timeline-based Activity Feed**

#### Top Section: Quick Actions
```
[📞 Log Call] [🤝 Log Meeting] [📧 Log Email] [📝 Add Note] [✅ Add Task]
```

#### Middle Section: AI Sales Assistant
**Intelligent Sales Guidance Panel**
- Input: "How should I approach selling [product] to this company?"
- AI has full context:
  - Customer data (industry, size, financials, pain points)
  - Tenant profile (what you sell, your USPs)
  - Interaction history
  - Quote history
- Suggested prompts:
  - "Draft a call script for [product/service]"
  - "What objections might they raise?"
  - "Suggest a meeting agenda"
  - "What are their likely pain points?"
  - "How can I position [your solution] vs [competitor]?"

#### Main Section: Activity Timeline
- Chronological list of all interactions
- Filterable by type (calls, meetings, emails, notes)
- Search functionality
- Each activity shows:
  - Type icon and color
  - Date/time
  - Subject
  - User who logged it
  - Contact involved (if applicable)
  - Duration (for calls/meetings)
  - Outcome
  - Notes (expandable)
  - Follow-up flag
  - Edit/delete actions

#### Bottom Section: Statistics
- Total interactions
- Last contact date
- Average response time
- Call-to-meeting conversion
- Meeting-to-quote conversion

## Phase 4: Call Logging Modal

### When "Log Call" is clicked:
```
╔═══════════════════════════════════════════════════════╗
║  Log Sales Call                                       ║
╠═══════════════════════════════════════════════════════╣
║  Contact: [Dropdown: Select Contact]                 ║
║  Date/Time: [DateTime Picker] [Now]                  ║
║  Duration: [Input] minutes                            ║
║  Outcome: [Dropdown: Select Outcome]                  ║
║                                                       ║
║  Subject: [Text Input]                                ║
║                                                       ║
║  Notes:                                               ║
║  [Large Text Area]                                    ║
║  - What was discussed?                                ║
║  - Pain points mentioned?                             ║
║  - Objections raised?                                 ║
║  - Next steps agreed?                                 ║
║                                                       ║
║  [💡 Get AI Suggestions]                             ║
║                                                       ║
║  ☑ Follow-up required                                ║
║  Follow-up date: [Date Picker]                       ║
║  Follow-up notes: [Text Input]                       ║
║                                                       ║
║  [Click-to-Call: Launch Phone App]                   ║
║                                                       ║
║  [Cancel] [Save Activity]                             ║
╚═══════════════════════════════════════════════════════╝
```

### AI Suggestions in Call Logging:
When clicked, shows:
- Call summary template
- Key points to document
- Suggested follow-up actions
- Relevant products/services to mention next time

## Phase 5: Click-to-Call Integration

### Implementation:
```typescript
// Uses tel: protocol to launch system phone app
const handleClickToCall = (phoneNumber: string) => {
  window.location.href = `tel:${phoneNumber}`;
  // Optionally open call logging modal immediately
  setCallLoggingOpen(true);
};
```

### User Flow:
1. Click "Call" button on contact
2. System phone app opens with number dialed
3. Call logging modal opens simultaneously
4. User makes call
5. After call, user fills in notes, outcome, duration
6. Save activity → logged in timeline

## Data Flow: AI Sales Assistant Context

### When user asks AI for sales guidance:
```
AI receives full context:

TENANT PROFILE:
- Company description
- Products/services offered
- USPs
- Target markets
- Sales methodology
- Company analysis (business model, ICP, positioning)

CUSTOMER DATA:
- Company name, industry, size
- Financial data (from Companies House)
- Business intelligence (from AI customer analysis)
- Lead score
- Status (LEAD, PROSPECT, CUSTOMER)

INTERACTION HISTORY:
- All past calls, meetings, emails
- Outcomes and notes
- Follow-up status

QUOTE HISTORY:
- Previous quotes (if any)
- Accepted/rejected quotes
- Price sensitivity indicators

AI then provides:
- Personalized sales approach
- Specific messaging aligned with tenant's USPs
- Objection handling tailored to customer's industry
- Next best action recommendations
```

## Technical Implementation Details

### Backend Structure
```
backend/
├── app/
│   ├── models/
│   │   ├── tenant.py (updated with profile fields)
│   │   └── sales.py (new: SalesActivity, SalesNote)
│   ├── schemas/
│   │   └── sales.py (new: Pydantic schemas)
│   ├── api/v1/endpoints/
│   │   ├── settings.py (updated with profile endpoints)
│   │   └── sales.py (new: activity endpoints - TODO)
│   └── services/
│       └── ai_analysis_service.py (existing, will add sales methods)
└── migrations/
    └── add_tenant_profile_and_sales_models.sql (✅ applied)
```

### Frontend Structure (TODO)
```
frontend/src/
├── pages/
│   ├── Settings.tsx (update with Company Profile tab)
│   └── CustomerDetail.tsx (add Sales tab)
├── components/
│   ├── CompanyProfileForm.tsx (new)
│   ├── SalesActivityTimeline.tsx (new)
│   ├── SalesActivityModal.tsx (new)
│   ├── AISalesAssistant.tsx (new)
│   └── CallLoggingModal.tsx (new)
└── services/
    └── api.ts (add sales endpoints)
```

## Benefits of This Approach

### 1. Intelligent Sales Guidance
- AI understands what YOU sell (tenant profile)
- AI understands who THEY are (customer data)
- AI provides specific, actionable advice

### 2. Complete Audit Trail
- Every interaction logged
- Full history visible
- Follow-up tracking

### 3. Scalable & Flexible
- Easy to add new activity types
- Extensible for future features (email integration, calendar sync)
- Works with any sales methodology

### 4. Data-Driven Insights
- Track conversion rates
- Identify best practices
- Optimize sales process

## Next Steps

### Immediate (Phase 2 - Frontend Settings):
1. ✅ Create Company Profile form component
2. ✅ Add Company Profile tab to Settings
3. ✅ Implement "Analyze My Company" button
4. ✅ Display AI analysis results

### Short-term (Phase 3 - Sales Tab):
1. Create Sales tab on customer detail
2. Build activity timeline component
3. Create activity logging modals
4. Implement AI Sales Assistant component

### Medium-term (Phase 4 - Advanced Features):
1. Click-to-call integration
2. Email tracking integration
3. Calendar integration
4. Quote linkage and tracking
5. Sales pipeline visualization

### Long-term (Phase 5 - Intelligence):
1. Predictive lead scoring
2. Automated follow-up suggestions
3. Win/loss analysis
4. Sales coaching recommendations

## Version History
- **v2.4.0** (2025-10-12): Initial sales module implementation
  - Database models for tenant profile and sales activities
  - API endpoints for company profile management
  - AI analysis of tenant's business
  - Migration applied successfully

Last Updated: 2025-10-12



