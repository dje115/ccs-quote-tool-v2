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
    
    # 7. Quote Analysis Prompt (from v1 - Enhanced)
    quote_analysis_prompt = """You are a structured cabling contractor. The client has supplied the information below.

Project Title: {project_title}
Description: {project_description}
Building Type: {building_type}
Building Size: {building_size} sqm
Number of Floors: {number_of_floors}
Number of Rooms/Areas: {number_of_rooms}
Site Address: {site_address}

Solution Requirements:
- WiFi installation needed: {wifi_requirements}
- CCTV installation needed: {cctv_requirements}
- Door entry installation needed: {door_entry_requirements}
- Special requirements or constraints: {special_requirements}

Your tasks:
1. Identify any missing critical details (containment type, ceiling construction, patch panel counts, testing & certification, rack power, etc.). Ask up to 5 short clarification questions.
2. When sufficient information is available (or you must make reasonable assumptions), prepare a structured cabling quotation that includes: client requirement restatement, scope of works, materials list, labour estimate, and assumptions/exclusions.

Response rules:
- Always respond in JSON format.
- When the caller is only requesting questions (questions_only mode) return: {{"clarifications": [..]}}.
- Otherwise return a JSON object with these keys:
  - analysis: concise narrative summary (string).
  - products: array of recommended products with EXACT pricing data:
      * item: product name (string)
      * quantity: numeric quantity only (number, not text like "Allowance")
      * unit: unit type (string: "each", "meters", "box", etc.)
      * unit_price: exact unit price in GBP (number)
      * total_price: exact total price in GBP (number)
      * part_number: manufacturer part number (string)
      * notes: installation notes (string)
  - alternatives: array describing optional approaches with pros/cons.
  - estimated_time: total installation hours (number).
  - labour_breakdown: array of objects describing tasks with hours, engineer_count, day_rate, cost, notes.
  - clarifications: array of outstanding clarification questions (if any remain).
  - quotation: object containing:
      * client_requirement (string summary)
      * scope_of_works (array of bullet strings)
      * materials (array of objects with item, quantity, unit_price, total_price, part_number, notes)
      * labour (object with engineers, hours, day_rate, total_cost, notes)
      * assumptions_exclusions (array of strings)

CRITICAL PRICING REQUIREMENTS:
- All quantities MUST be numeric values only (e.g., 52.0, not "52.0 each" or "Allowance")
- All prices MUST be real GBP amounts (e.g., 125.00 for U6-Pro, 89.00 for U6-Lite)
- Include part numbers for all products when available
- Use real pricing from supplier websites when possible
- If you cannot find real pricing, use realistic estimates but note that these will be marked as estimated (*)
- Always provide unit_price and total_price as numbers, never as text

If details are missing, state the assumption you are making inside the quotation sections and keep questions short and specific."""
    
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
    
    # 8. Product Search Prompt (from v1)
    product_search_prompt = """Search for {category} products related to: {query}

Provide a list of specific products with:
- Product name and model
- Brief description
- Typical use case
- Estimated price range

Format as JSON array of objects with:
- name: Product name
- model: Model number
- description: Brief description
- use_case: Typical use case
- price_range_min: Minimum estimated price
- price_range_max: Maximum estimated price
- category: Product category"""
    
    product_search_system = "You are a product expert for structured cabling, networking, and security equipment. Provide accurate product recommendations."
    
    existing = db.query(AIPrompt).filter(
        AIPrompt.category == PromptCategory.PRODUCT_SEARCH.value,
        AIPrompt.is_system == True
    ).first()
    
    if not existing:
        service.create_prompt(
            name="Product Search",
            category=PromptCategory.PRODUCT_SEARCH.value,
            system_prompt=product_search_system,
            user_prompt_template=product_search_prompt,
            model="gpt-5-mini",
            temperature=0.7,
            max_tokens=10000,
            is_system=True,
            tenant_id=None,
            created_by=None,
            variables={
                "category": "Product category (cabling, wifi, cctv, etc.)",
                "query": "Search query"
            },
            description="Search for products using AI"
        )
        print("✅ Created product_search prompt")
    else:
        print("⏭️  product_search prompt already exists")
    
    # 9. Building Analysis Prompt (from v1)
    building_analysis_prompt = """Analyze this building for structured cabling requirements:

Address: {address}
Building Type: {building_type}
Size: {building_size} sqm

Provide recommendations for:
- Cable routing
- Equipment placement
- Power requirements
- Access considerations
- Estimated installation complexity
- Special considerations

Format as JSON object with:
- cable_routing: Recommendations for cable routing
- equipment_placement: Recommended equipment locations
- power_requirements: Power needs assessment
- access_considerations: Access challenges and solutions
- complexity: Low/Medium/High
- special_considerations: Array of special notes"""
    
    building_analysis_system = "You are a building analysis expert. Analyze building information and provide technical insights for cabling projects."
    
    existing = db.query(AIPrompt).filter(
        AIPrompt.category == PromptCategory.BUILDING_ANALYSIS.value,
        AIPrompt.is_system == True
    ).first()
    
    if not existing:
        service.create_prompt(
            name="Building Analysis",
            category=PromptCategory.BUILDING_ANALYSIS.value,
            system_prompt=building_analysis_system,
            user_prompt_template=building_analysis_prompt,
            model="gpt-5-mini",
            temperature=0.7,
            max_tokens=8000,
            is_system=True,
            tenant_id=None,
            created_by=None,
            variables={
                "address": "Building address",
                "building_type": "Type of building",
                "building_size": "Building size in sqm"
            },
            description="Analyze building for cabling requirements"
        )
        print("✅ Created building_analysis prompt")
    else:
        print("⏭️  building_analysis prompt already exists")
    
    # 10. Lead Generation Prompt
    lead_generation_prompt_template = """You are a UK business research specialist. 
Find REAL, VERIFIED UK businesses based on your training data and knowledge. 
Return ONLY valid JSON matching the schema provided — do not include explanations or text outside the JSON.

---

## CONTEXT:
Company: {company_name}
Description: {company_description}
Services: {services}
Location: {location}
Primary Market: {primary_market}
Installation Provider: {is_installation_provider}

Sector: {sector_name}
Sector Focus: {sector_description}
Search Area: {postcode} (within {distance_miles} miles)
Campaign Type: {prompt_type}
Maximum Results: {max_results}
Target Company Size: {company_size_category}

---

## OBJECTIVE
Generate a list of {max_results} REAL UK businesses in the {sector_name} sector.
Focus on well-known UK retail chains, independent stores, and e-commerce businesses.

IMPORTANT: You MUST provide actual UK businesses. Do not return an empty results array.
If you cannot find businesses in the specific area, provide UK businesses from your training data that match the sector.

---

## SEARCH APPROACH
1. Use your knowledge of UK businesses to find companies in the {sector_name} sector
2. Focus on businesses that would be located near {postcode} or in the surrounding area
3. Ensure each company is a real UK business with valid contact information
4. Use the keywords below to understand the sector focus
{company_size_filter}

## KEYWORDS TO CONSIDER:
{example_keywords}

---

## DATA TO RETURN
For each business, extract:
- `company_name` (official name)
- `website` (URL, or null if not verifiable)
- `description` (short summary of services)
- `contact_phone` (or null)
- `contact_email` (or null)
- `postcode`
- `sector` (from context)
- `lead_score` (60–95, based on relevance)
- `fit_reason` (why this business fits as a customer or partner)
- `source_url` (where you found it)
- `quick_telesales_summary` (2-3 sentences for telesales team)
- `ai_business_intelligence` (comprehensive analysis, 300+ words)

---

## DYNAMIC INSIGHTS TO INCLUDE
Generate these automatically based on the sector and company data:

**Recommended Customer Type:**  
{customer_type}

**Recommended Partner Type:**  
{partner_type}

---

## OUTPUT FORMAT
Return only valid JSON in this structure:
{{
  "query_area": "{postcode} + {distance_miles} miles",
  "sector": "{sector_name}",
  "results": [
    {{
      "company_name": "string",
      "website": "string or null",
      "description": "string",
      "contact_phone": "string or null",
      "contact_email": "string or null",
      "postcode": "string",
      "lead_score": 60–95,
      "fit_reason": "string",
      "source_url": "string",
      "recommended_customer_type": "{customer_type}",
      "recommended_partner_type": "{partner_type}",
      "quick_telesales_summary": "string",
      "ai_business_intelligence": "string"
    }}
  ]
}}

---

## QUALITY RULES
- Prioritise *real, verifiable SMEs* over quantity.
- Skip duplicates and large national chains.
- Businesses must be **within {distance_miles} miles of {postcode}**.
- If fewer than {max_results} genuine businesses are found, return only verified ones.
{company_size_rule}
- Never include fictional examples or template data.
"""
    
    lead_generation_system = "You are a UK business research specialist with access to live web search. Analyze the provided information and return comprehensive business intelligence for UK companies. Always return valid JSON matching the schema provided."
    
    existing = db.query(AIPrompt).filter(
        AIPrompt.category == PromptCategory.LEAD_GENERATION.value,
        AIPrompt.is_system == True
    ).first()
    
    if not existing:
        service.create_prompt(
            name="Lead Generation - Sector Search",
            category=PromptCategory.LEAD_GENERATION.value,
            system_prompt=lead_generation_system,
            user_prompt_template=lead_generation_prompt_template,
            model="gpt-5-mini",
            temperature=0.7,
            max_tokens=16000,
            is_system=True,
            tenant_id=None,
            created_by=None,
            variables={
                "company_name": "Your company name",
                "company_description": "Your company description",
                "services": "Comma-separated list of your services",
                "location": "Your company location",
                "primary_market": "Your primary target market",
                "is_installation_provider": "Whether you provide installation services (true/false)",
                "sector_name": "Target sector name",
                "sector_description": "Description of the target sector",
                "postcode": "Search postcode",
                "distance_miles": "Search radius in miles",
                "prompt_type": "Campaign type (sector_search, company_list, etc.)",
                "max_results": "Maximum number of results to return",
                "company_size_category": "Target company size (Small, Medium, Large, Enterprise, or Any Size)",
                "example_keywords": "Sector-specific keywords",
                "customer_type": "Recommended customer type",
                "partner_type": "Recommended partner type",
                "company_size_filter": "Optional filter instruction for company size",
                "company_size_rule": "Optional rule about company size prioritization"
            },
            description="AI prompt for lead generation campaigns - finding UK businesses by sector and location"
        )
        print("✅ Created lead_generation prompt")
    else:
        print("⏭️  lead_generation prompt already exists")
    
    # 11. Company Profile Analysis Prompt (for tenant's own company)
    company_profile_prompt_template = """Analyze the following company profile and provide comprehensive business intelligence:

COMPANY NAME: {company_name}

COMPANY WEBSITES:
{company_websites}

COMPANY DESCRIPTION:
{company_description}

PRODUCTS & SERVICES:
{products_services}

UNIQUE SELLING POINTS:
{unique_selling_points}

TARGET MARKETS:
{target_markets}

SALES METHODOLOGY:
{sales_methodology}

ELEVATOR PITCH:
{elevator_pitch}

Please provide:
1. Business model analysis
2. Competitive positioning and strengths
3. Ideal customer profile (ICP)
4. Key pain points this company solves
5. Recommended sales approach and messaging
6. Cross-selling and upselling opportunities
7. Common objections and how to handle them
8. Industry trends and opportunities

Format as JSON with keys: business_model, competitive_position, ideal_customer_profile, 
pain_points_solved, sales_approach, cross_sell_opportunities, objection_handling, industry_trends
"""
    
    company_profile_system = "You are a business intelligence analyst specializing in analyzing company profiles and providing actionable sales insights. Provide detailed, actionable insights in JSON format."
    
    existing = db.query(AIPrompt).filter(
        AIPrompt.category == PromptCategory.COMPANY_PROFILE_ANALYSIS.value,
        AIPrompt.is_system == True
    ).first()
    
    if not existing:
        service.create_prompt(
            name="Company Profile Analysis",
            category=PromptCategory.COMPANY_PROFILE_ANALYSIS.value,
            system_prompt=company_profile_system,
            user_prompt_template=company_profile_prompt_template,
            model="gpt-5-mini",
            temperature=0.7,
            max_tokens=15000,
            is_system=True,
            tenant_id=None,
            created_by=None,
            variables={
                "company_name": "Company name",
                "company_websites": "Comma-separated list of company websites",
                "company_description": "Company description",
                "products_services": "Comma-separated list of products and services",
                "unique_selling_points": "Comma-separated list of unique selling points",
                "target_markets": "Comma-separated list of target markets",
                "sales_methodology": "Sales methodology description",
                "elevator_pitch": "Company elevator pitch"
            },
            description="AI prompt for analyzing tenant's own company profile to generate business intelligence and sales insights"
        )
        print("✅ Created company_profile_analysis prompt")
    else:
        print("⏭️  company_profile_analysis prompt already exists")
    
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

