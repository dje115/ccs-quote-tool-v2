#!/usr/bin/env python3
"""
Seed script to populate initial AI prompts from existing code
Run this after creating the ai_prompts table
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.ai_prompt import AIPrompt, AIPromptVersion, PromptCategory
from app.services.ai_prompt_service import AIPromptService
import uuid
import asyncio


async def seed_prompts_async(db: Session):
    """Seed initial prompts (async version)"""
    print("🌱 Seeding AI prompts...")
    
    service = AIPromptService(db, tenant_id=None)
    
    # 1. Customer Analysis Prompt
    customer_analysis_prompt = """
Analyze this company and provide comprehensive business intelligence that helps us sell to them.

{tenant_context}

{company_info}

IMPORTANT BUDGET ANALYSIS INSTRUCTION:
When estimating budget ranges in section 5, focus on services that match what WE provide (from the tenant context above). 
For example, if we provide crane hire, lifting services, or construction support, estimate their spending capacity for THOSE services, not generic IT budgets.
Base your budget estimates on their business activities and what services they would actually need from companies like ours.

 CRITICAL INSTRUCTION FOR COMPETITOR ANALYSIS:
When identifying competitors in section 9, find competitors OF THE PROSPECT COMPANY, NOT competitors of our company.
Exclude any companies in our sector (cabling, infrastructure). Return competitors of THE PROSPECT in THEIR sector.

IMPORTANT: Consider how our company's products, services, and strengths align with this prospect's needs. 
Focus on identifying specific opportunities where we can add value based on what we offer.

Please provide a detailed analysis including:

1. **Business Sector Classification**: Choose the most appropriate sector from: office, retail, industrial, healthcare, education, hospitality, manufacturing, technology, finance, government, other

2. **Company Size Assessment**: Use the Companies House financial data to provide accurate estimates:
   - Number of employees (use the employee estimates from Companies House data if available)
   - Revenue range (use actual turnover data from Companies House if available, otherwise estimate)
   - Business size category (Small, Medium, Large, Enterprise)

3. **Primary Business Activities**: Describe what this company does, their main products/services

4. **Technology Maturity**: Assess their likely technology/operational sophistication based on company size and financial data:
   - Basic: Simple needs, basic infrastructure
   - Intermediate: Some advanced systems, growing requirements
   - Advanced: Sophisticated infrastructure, multiple systems
   - Enterprise: Complex, integrated systems, dedicated teams
   (If technology isn't relevant to your industry, assess operational maturity)

5. **Service Budget Estimate**: Based on their revenue and company size, estimate their likely annual spending range for services like ours (crane hire, lifting services, construction support, etc.) - NOT generic IT budgets unless that's what we provide

6. **Financial Health Analysis**: Analyze the financial data from Companies House:
   - Comment on their profitability trend (Growing/Stable/Declining)
   - Assess their financial stability based on shareholders' funds and cash position
   - Evaluate revenue growth trends
   - Identify any financial risks or opportunities

7. **Growth Potential**: Assess potential for business growth and expansion based on financial trends and company size

8. **Needs Assessment**: What needs might they have related to our products/services based on their size, financial position, and business activities?
    Focus on needs that align with what we offer.

9. **COMPETITORS OF THIS COMPANY (NOT OUR COMPANY)**: [SKIP - Handled separately by GPT-5]
    
    [Note: Competitors are identified by a dedicated GPT-5 call with web search - not included here]

10. **Business Opportunities**: What opportunities exist for our company to add value given their financial capacity and growth trajectory?
    Be specific about which of our offerings might align with their needs.

11. **Risk Factors**: What challenges or potential objections might we face when approaching them based on their financial position and business context?

12. **Actionable Sales Strategy** (CRITICAL): Analyze the prospect's business type and determine the best approach:

    **A) If they are a POTENTIAL CUSTOMER (B2C/Direct Sales):**
    - Create 5-10 ways to sell OUR services directly TO them
    - Match each of OUR products/services to one of THEIR specific needs
    - Example: "Provide [our service] to address their [need/pain point]"
    - Focus on how they can BUY from us
    
    **B) If they are in a SIMILAR/COMPLEMENTARY business (B2B/Partnership):**
    - Use the "B2B Partnership Opportunities" section in OUR company information
    - Create 5-10 ways to work WITH them (subcontracting, white-label, joint bids, etc.)
    - Example: "Partner on their customer projects requiring [our expertise]"
    - Example: "Act as their overflow/regional subcontractor for [service type]"
    - Focus on how we can COLLABORATE to serve their customers together
    
    **IMPORTANT**: 
    - Determine which approach fits based on their business activities
    - If they're a potential customer, use approach A
    - If they're a service provider like us (MSP, contractor, consultant, etc.), use approach B
    - If both could apply, provide BOTH approaches clearly labeled
    - Only suggest what we actually offer (as listed in OUR company information)

13. **Address and Location Analysis**: Based on the company information, identify:
    - Primary business address (if different from registered address)
    - ALL additional sites/locations mentioned
    - Geographic spread of operations

Please respond in JSON format with these exact fields:
{{
    "business_sector": "string (one of the sectors listed above)",
    "estimated_employees": number,
    "estimated_revenue": "string (revenue range)",
    "business_size_category": "string (Small/Medium/Large/Enterprise)",
    "primary_business_activities": "string (detailed description)",
    "technology_maturity": "string (Basic/Intermediate/Advanced/Enterprise)",
    "service_budget_estimate": "string (budget range for services like ours - crane hire, lifting, construction support, etc.)",
    "growth_potential": "string (High/Medium/Low)",
    "technology_needs": "string (predicted IT needs)",
    "competitors": ["array of 5-10 competitor company names as strings"],
    "opportunities": "string (business opportunities)",
    "risks": "string (risk factors)",
    "actionable_recommendations": ["array of 5-10 specific strings, each describing how we can help them"],
    "company_profile": "string (comprehensive company summary)",
    "primary_address": "string (main business address if different from registered)",
    "additional_sites": "string (list of additional locations/sites)",
    "location_analysis": "string (geographic spread and location requirements)",
    "financial_health_analysis": "string (detailed analysis of financial position, profitability trends, and stability)",
    "employee_analysis": "string (analysis of employee count and company size based on Companies House data)",
    "revenue_analysis": "string (analysis of turnover trends and revenue growth)",
    "profitability_assessment": "string (assessment of profitability trends and financial performance)"
}}

Focus on UK market context and be realistic in your assessments.
"""
    
    customer_analysis_system = """You are a business intelligence analyst specializing in UK companies. Always respond with valid JSON. When listing companies, people, or specific entities, ONLY include real, verified information. Do NOT make up or hallucinate company names, people names, or details. If you cannot verify something is real, do NOT include it."""
    
    # Check if prompt already exists
    existing = db.query(AIPrompt).filter(
        AIPrompt.category == PromptCategory.CUSTOMER_ANALYSIS.value,
        AIPrompt.is_system == True
    ).first()
    
    if not existing:
        service.create_prompt(
            name="Customer Analysis - Comprehensive",
            category=PromptCategory.CUSTOMER_ANALYSIS.value,
            system_prompt=customer_analysis_system,
            user_prompt_template=customer_analysis_prompt,
            model="gpt-5-mini",
            temperature=0.7,
            max_tokens=8000,
            is_system=True,
            tenant_id=None,
            created_by=None,
            variables={
                "tenant_context": "Tenant company information including products, services, USPs, target markets",
                "company_info": "Company information including Companies House data, Google Maps data, web scraping data"
            },
            description="Comprehensive customer analysis prompt for company intelligence"
        )
        print("✅ Created customer_analysis prompt")
    else:
        print("⏭️  customer_analysis prompt already exists")
    
    # 2. Activity Enhancement Prompt
    activity_enhancement_prompt = """You are a sales assistant AI helping to process activity notes for a CRM system.

ACTIVITY TYPE: {activity_type}
ORIGINAL NOTES (from salesperson):
{notes}

{customer_context}
{tenant_context}
{activity_context}

TASKS:
1. Clean up and restructure the notes to be professional and clear
2. Extract key information (pain points, objections, requirements, commitments)
3. Suggest ONE specific next action that should be taken

IMPORTANT:
- Keep all factual information from the original notes
- Make it concise but complete
- Be specific in next actions (e.g., "Call back on Friday to discuss server room upgrade" not "Follow up later")
- Consider the customer's stage in the sales cycle
- Next action should be realistic and actionable

Respond in JSON format:
{{
  "cleaned_notes": "Professional, structured version of the notes",
  "next_action": "Specific action to take with date/context if mentioned",
  "key_points": ["point1", "point2", "point3"],
  "follow_up_priority": "high|medium|low",
  "suggested_follow_up_date": "YYYY-MM-DD or null"
}}"""
    
    activity_enhancement_system = "You are a sales assistant AI that helps clean up and analyze sales activity notes. Always respond with valid JSON."
    
    existing = db.query(AIPrompt).filter(
        AIPrompt.category == PromptCategory.ACTIVITY_ENHANCEMENT.value,
        AIPrompt.is_system == True
    ).first()
    
    if not existing:
        service.create_prompt(
            name="Activity Enhancement",
            category=PromptCategory.ACTIVITY_ENHANCEMENT.value,
            system_prompt=activity_enhancement_system,
            user_prompt_template=activity_enhancement_prompt,
            model="gpt-5-mini",
            temperature=0.7,
            max_tokens=10000,
            is_system=True,
            tenant_id=None,
            created_by=None,
            variables={
                "activity_type": "Type of activity (call, email, meeting, etc.)",
                "notes": "Original notes from salesperson",
                "customer_context": "Customer information and context",
                "tenant_context": "Tenant company information",
                "activity_context": "Recent activity history"
            },
            description="Enhance and clean up sales activity notes"
        )
        print("✅ Created activity_enhancement prompt")
    else:
        print("⏭️  activity_enhancement prompt already exists")
    
    # 3. Action Suggestions Prompt
    action_suggestions_prompt = """You are a sales advisor AI helping prioritize customer engagement actions.

CUSTOMER INFORMATION:
Company: {company_name}
Status: {status}
Lead Score: {lead_score}
Sector: {sector}
Days Since Last Contact: {days_since_contact}

{activity_summary}

CUSTOMER'S IDENTIFIED NEEDS:
{needs_assessment}

CUSTOMER'S BUSINESS OPPORTUNITIES:
{business_opportunities}

HOW YOUR COMPANY CAN HELP THIS CUSTOMER:
{how_we_can_help}

{tenant_context}

CRITICAL INSTRUCTIONS:
1. Base ALL suggestions on the customer's IDENTIFIED NEEDS and BUSINESS OPPORTUNITIES above
2. Match your company's products/services to their specific needs
3. Use the "How We Can Help" section to craft targeted value propositions
4. If they are in a similar industry, consider B2B partnership opportunities
5. Be SPECIFIC - reference actual needs and solutions, not generic sales talk
6. Each suggestion should have a clear business reason tied to their needs

TASK: Generate 3 prioritized action suggestions (call, email, visit) that directly address the customer's needs with your solutions.

Respond in JSON:
{{
  "call_suggestion": {{
    "priority": "high|medium|low",
    "reason": "Why call now",
    "talking_points": ["point1", "point2", "point3"],
    "best_time": "Suggested time/day"
  }},
  "email_suggestion": {{
    "priority": "high|medium|low",
    "reason": "Why email now",
    "subject": "Email subject line",
    "key_topics": ["topic1", "topic2"]
  }},
  "visit_suggestion": {{
    "priority": "high|medium|low",
    "reason": "Why visit now",
    "objectives": ["objective1", "objective2"],
    "timing": "When to schedule"
  }}
}}"""
    
    action_suggestions_system = "You are a sales strategy AI that provides actionable customer engagement suggestions. Always respond with valid JSON."
    
    existing = db.query(AIPrompt).filter(
        AIPrompt.category == PromptCategory.ACTION_SUGGESTIONS.value,
        AIPrompt.is_system == True
    ).first()
    
    if not existing:
        service.create_prompt(
            name="Action Suggestions",
            category=PromptCategory.ACTION_SUGGESTIONS.value,
            system_prompt=action_suggestions_system,
            user_prompt_template=action_suggestions_prompt,
            model="gpt-5-mini",
            temperature=0.7,
            max_tokens=20000,
            is_system=True,
            tenant_id=None,
            created_by=None,
            variables={
                "company_name": "Customer company name",
                "status": "Customer status",
                "lead_score": "Lead score",
                "sector": "Business sector",
                "days_since_contact": "Days since last contact",
                "activity_summary": "Recent activity summary",
                "needs_assessment": "Customer's identified needs",
                "business_opportunities": "Business opportunities",
                "how_we_can_help": "How company can help customer",
                "tenant_context": "Tenant company information"
            },
            description="Generate action suggestions for customer engagement"
        )
        print("✅ Created action_suggestions prompt")
    else:
        print("⏭️  action_suggestions prompt already exists")
    
    # 4. Competitor Analysis Prompt
    competitor_analysis_prompt = """Find REAL, VERIFIED UK competitors for: {company_name}

COMPANY DETAILS:
- Business: {business_activities}
- Sector: {business_sector}
- Size Category: {company_size}
- Locations: {locations_text}
- Postcode Areas: {postcode_text}
{f'- Turnover: £{turnover:,.0f}' if turnover else ''}
{f'- Employees: {employees}' if employees else ''}

MATCH CRITERIA:
- Services: Same specific business area ({business_sector})
- Size: Similar to company above (within ±50% if financial data available)
- Region: Operates in same regions or nearby {postcode_text}
- Status: Registered and ACTIVE (not shell/dormant)

VERIFICATION REQUIRED:
Each competitor MUST include:
1. Company name
2. Primary location/postcode
3. Website URL or Companies House link
4. Why they compete with {company_name}

SEARCH INSTRUCTIONS:
1. Use web search to find REAL companies
2. Verify each company exists and is active
3. Return company names you can verify via web search
4. Only include companies with legitimate business presence

Return ONLY verified real company names (one per line).
If you find fewer than 5 real competitors, return 2-3 that are verified.
Better 3 verified than 10 unverified."""
    
    competitor_analysis_system = "You are an expert at finding real, verified business competitors. Only return companies that actually exist and are currently trading. Use web search to verify each company before including it."
    
    existing = db.query(AIPrompt).filter(
        AIPrompt.category == PromptCategory.COMPETITOR_ANALYSIS.value,
        AIPrompt.is_system == True
    ).first()
    
    if not existing:
        service.create_prompt(
            name="Competitor Analysis",
            category=PromptCategory.COMPETITOR_ANALYSIS.value,
            system_prompt=competitor_analysis_system,
            user_prompt_template=competitor_analysis_prompt,
            model="gpt-5",
            temperature=0.7,
            max_tokens=8000,
            is_system=True,
            tenant_id=None,
            created_by=None,
            variables={
                "company_name": "Company name to find competitors for",
                "business_activities": "Business activities description",
                "business_sector": "Business sector",
                "company_size": "Company size category",
                "locations_text": "Locations text",
                "postcode_text": "Postcode areas",
                "turnover": "Company turnover (optional)",
                "employees": "Number of employees (optional)"
            },
            description="Find and verify competitors for a company"
        )
        print("✅ Created competitor_analysis prompt")
    else:
        print("⏭️  competitor_analysis prompt already exists")
    
    # 5. Financial Analysis Prompt
    financial_analysis_prompt = """You are a financial analyst specializing in assessing company financial health for B2B sales opportunities.

Analyze the financial data and provide insights on:
1. Financial stability and health
2. Growth trends and patterns
3. Ability to pay for services
4. Risk assessment
5. Budget estimation capabilities
6. Payment terms recommendations

Financial Data:
{financial_data}

Provide analysis in JSON format with:
- financial_health: Overall financial health assessment
- growth_trends: Revenue and profit trends
- payment_ability: Ability to pay for services
- risk_level: Low/Medium/High risk assessment
- budget_estimate: Estimated budget for services
- payment_terms: Recommended payment terms
- financial_strengths: Key financial strengths
- financial_concerns: Potential financial concerns"""
    
    financial_analysis_system = "You are a financial analyst specializing in assessing company financial health for B2B sales opportunities."
    
    existing = db.query(AIPrompt).filter(
        AIPrompt.category == PromptCategory.FINANCIAL_ANALYSIS.value,
        AIPrompt.is_system == True
    ).first()
    
    if not existing:
        service.create_prompt(
            name="Financial Analysis",
            category=PromptCategory.FINANCIAL_ANALYSIS.value,
            system_prompt=financial_analysis_system,
            user_prompt_template=financial_analysis_prompt,
            model="gpt-5-mini",
            temperature=0.7,
            max_tokens=10000,
            is_system=True,
            tenant_id=None,
            created_by=None,
            variables={
                "financial_data": "JSON financial data from Companies House"
            },
            description="Analyze company financial health"
        )
        print("✅ Created financial_analysis prompt")
    else:
        print("⏭️  financial_analysis prompt already exists")
    
    # 6. Translation Prompt
    translation_prompt = """Translate the following text from {source_language} to {target_language}.

Text to translate:
{text}

Please provide:
1. The translated text
2. Any cultural or contextual notes if relevant
3. Confidence level (high/medium/low)"""
    
    translation_system = "You are a professional translator specializing in business and technical translations."
    
    existing = db.query(AIPrompt).filter(
        AIPrompt.category == PromptCategory.TRANSLATION.value,
        AIPrompt.is_system == True
    ).first()
    
    if not existing:
        service.create_prompt(
            name="Translation",
            category=PromptCategory.TRANSLATION.value,
            system_prompt=translation_system,
            user_prompt_template=translation_prompt,
            model="gpt-5-mini",
            temperature=0.3,
            max_tokens=5000,
            is_system=True,
            tenant_id=None,
            created_by=None,
            variables={
                "source_language": "Source language code",
                "target_language": "Target language code",
                "text": "Text to translate"
            },
            description="Translate text between languages"
        )
        print("✅ Created translation prompt")
    else:
        print("⏭️  translation prompt already exists")
    
    # 7. Quote Analysis Prompt (from v1)
    quote_analysis_prompt = """You are a structured cabling contractor. The client has supplied the information below.

{quote_context}

Analyze the requirements and provide:
1. Recommended products/materials with quantities
2. Labour breakdown with time estimates
3. Estimated total time and cost
4. Any assumptions or clarifications needed

Return in JSON format with:
- recommended_products: Array of {{name, quantity, unit, unit_price, total_price, category}}
- labour_breakdown: Array of {{task, hours, days, day_rate, cost}}
- estimated_time: Total hours
- estimated_cost: Total estimated cost
- assumptions: Array of assumptions made
- clarifications: Array of clarification questions if needed"""
    
    quote_analysis_system = """You are a seasoned structured cabling contractor and estimator. You produce practical, buildable quotations, highlight assumptions, and make sensible allowances for labour and materials."""
    
    existing = db.query(AIPrompt).filter(
        AIPrompt.category == PromptCategory.QUOTE_ANALYSIS.value,
        AIPrompt.is_system == True
    ).first()
    
    if not existing:
        service.create_prompt(
            name="Quote Analysis - Requirements",
            category=PromptCategory.QUOTE_ANALYSIS.value,
            system_prompt=quote_analysis_system,
            user_prompt_template=quote_analysis_prompt,
            model="gpt-5-mini",
            temperature=0.7,
            max_tokens=8000,
            is_system=True,
            tenant_id=None,
            created_by=None,
            variables={
                "quote_context": "Quote project details including building type, size, requirements"
            },
            description="Analyze quote requirements and provide product/labour recommendations"
        )
        print("✅ Created quote_analysis prompt")
    else:
        print("⏭️  quote_analysis prompt already exists")
    
    print("✅ AI prompts seeding complete!")


def seed_prompts(db: Session):
    """Seed initial prompts (sync wrapper)"""
    asyncio.run(seed_prompts_async(db))

if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_prompts(db)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding prompts: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

