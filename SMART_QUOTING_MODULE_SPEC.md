# Smart Quoting Module - Comprehensive Specification
**Version:** 1.0  
**Last Updated:** Current  
**Status:** Implementation Ready  
**Target Version:** 3.1.0

---

## 📋 Table of Contents

1. [Overview & Architecture](#overview--architecture)
2. [Database Schema Extensions](#database-schema-extensions)
3. [AI Prompts Specification](#ai-prompts-specification)
4. [Backend Services](#backend-services)
5. [API Endpoints](#api-endpoints)
6. [Frontend Components](#frontend-components)
7. [Workflows](#workflows)
8. [Implementation Checklist](#implementation-checklist)

---

## 🎯 Overview & Architecture

### Purpose
The Smart Quoting Module provides an AI-powered, industry-specific quote builder that assists users in creating comprehensive quotes with:
- AI-generated scope analysis
- Product catalog integration
- Component pricing from suppliers
- Day rate calculations
- Labor hour estimates
- Real-time price calculations
- Upsell/cross-sell suggestions
- Professional quote generation

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Quote Builder│  │ Product      │  │ AI Suggestions│     │
│  │ (Step-by-Step)│ │ Catalog      │  │ Panel        │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
└─────────┼──────────────────┼──────────────────┼─────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    API Layer (FastAPI)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Quote Builder│  │ Product      │  │ AI Copilot   │      │
│  │ Endpoints    │  │ Catalog API  │  │ Endpoints    │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
└─────────┼──────────────────┼──────────────────┼─────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                  Service Layer (Python)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Quote Builder│  │ Product      │  │ Day Rate     │      │
│  │ Service      │  │ Catalog      │  │ Service      │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Component    │  │ Knowledge    │  │ AI           │      │
│  │ Pricing      │  │ Base Service │  │ Orchestration│      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
└─────────┼──────────────────┼──────────────────┼─────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    Data Layer                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ PostgreSQL   │  │ Redis Cache  │  │ MinIO Storage│      │
│  │ (Quotes,      │  │ (AI Responses│  │ (Product     │      │
│  │  Products,    │  │  Caching)    │  │  Images)     │      │
│  │  Suppliers)   │  │              │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### Component Relationships

- **Quote Builder** → Uses **Product Catalog** → Fetches from **Suppliers**
- **Quote Builder** → Uses **Day Rate Service** → Calculates labor costs
- **Quote Builder** → Uses **AI Orchestration** → Generates suggestions
- **AI Orchestration** → Uses **Knowledge Base** → Provides context
- **Component Pricing** → Fetches from **Supplier Pricing** → Applies **Markup Rules**

### Data Flow

1. User starts quote creation → Selects quote type and customer
2. AI analyzes requirements → Generates scope summary
3. User selects products → Product Catalog Service fetches products
4. AI suggests components → Based on quote type and requirements
5. User adds labor → Day Rate Service calculates costs
6. System calculates totals → Applies markup rules and taxes
7. AI generates email copy → For sending quote to customer
8. User reviews and sends → Quote PDF generated

---

## 🗄️ Database Schema Extensions

### 1. Extend Product Model

**File:** `backend/app/models/product.py`

```python
# Add to existing Product model:
- category_hierarchy = Column(JSON, nullable=True)  # ["Cables", "Cat6", "Outdoor"]
- specifications = Column(JSON, nullable=True)  # {"length": "305m", "speed": "1Gbps"}
- compatibility = Column(JSON, nullable=True)  # ["product_id_1", "product_id_2"]
- installation_notes = Column(Text, nullable=True)
- warranty_period_months = Column(Integer, nullable=True)
- lead_time_days = Column(Integer, nullable=True)
- minimum_order_quantity = Column(Integer, default=1, nullable=False)
- bulk_pricing_tiers = Column(JSON, nullable=True)  # [{"min_qty": 10, "price": 50.00}]
- supplier_product_id = Column(String(100), nullable=True)  # Link to SupplierPricing
- is_consumable = Column(Boolean, default=False, nullable=False)
- requires_certification = Column(Boolean, default=False, nullable=False)
```

### 2. Day Rate Model (New)

**File:** `backend/app/models/day_rate.py`

```python
class DayRate(BaseModel):
    __tablename__ = "day_rates"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Role definition
    role = Column(String(100), nullable=False)  # "Engineer", "Technician", "Project Manager"
    skill_level = Column(String(50), nullable=False)  # "junior", "senior", "specialist"
    
    # Pricing
    base_rate_per_day = Column(Numeric(10, 2), nullable=False)
    base_rate_per_hour = Column(Numeric(10, 2), nullable=True)
    overtime_multiplier = Column(Float, default=1.5, nullable=False)  # 1.5x for overtime
    
    # Location adjustments
    location_adjustments = Column(JSON, nullable=True)  # {"London": 1.2, "Remote": 0.9}
    
    # Travel
    travel_rate_per_hour = Column(Numeric(10, 2), nullable=True)
    travel_rate_per_km = Column(Numeric(10, 2), nullable=True)
    
    # Settings
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    effective_from = Column(DateTime(timezone=True), nullable=True)
    effective_to = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="day_rates")
```

### 3. Knowledge Base Model (New)

**File:** `backend/app/models/knowledge_base.py`

```python
class KnowledgeBaseArticle(BaseModel):
    __tablename__ = "knowledge_base_articles"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=True, index=True)  # Nullable for system articles
    
    # Article details
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    
    # Categorization
    category = Column(String(100), nullable=False, index=True)  # "installation", "troubleshooting", "best_practices"
    tags = Column(JSON, nullable=True)  # ["cabling", "cat6", "outdoor"]
    quote_types = Column(JSON, nullable=True)  # ["cabling", "network_build"]
    
    # Product relationships
    linked_products = Column(JSON, nullable=True)  # ["product_id_1", "product_id_2"]
    linked_categories = Column(JSON, nullable=True)  # ["Cables", "Connectors"]
    
    # Metadata
    author = Column(String(36), ForeignKey("users.id"), nullable=True)
    version = Column(Integer, default=1, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_system = Column(Boolean, default=False, nullable=False)  # System vs tenant-specific
    
    # Search
    search_keywords = Column(JSON, nullable=True)  # For better search matching
    
    # Relationships
    tenant = relationship("Tenant", back_populates="knowledge_articles")
    author_user = relationship("User", foreign_keys=[author])
```

### 4. Markup Rule Model (New)

**File:** `backend/app/models/markup_rule.py`

```python
class MarkupRule(BaseModel):
    __tablename__ = "markup_rules"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Rule definition
    name = Column(String(200), nullable=False)
    rule_type = Column(String(50), nullable=False)  # "percentage", "fixed", "tiered"
    
    # Conditions (JSON)
    conditions = Column(JSON, nullable=False)  # {
    #   "product_categories": ["Cables", "Connectors"],
    #   "quote_types": ["cabling"],
    #   "customer_types": ["new", "existing"],
    #   "min_amount": 1000.00,
    #   "max_amount": 50000.00
    # }
    
    # Markup
    markup_percentage = Column(Numeric(5, 2), nullable=True)  # 15.00 for 15%
    markup_amount = Column(Numeric(10, 2), nullable=True)  # Fixed amount
    tiered_markups = Column(JSON, nullable=True)  # [
    #   {"min_amount": 0, "max_amount": 1000, "markup": 20},
    #   {"min_amount": 1001, "max_amount": 10000, "markup": 15}
    # ]
    
    # Priority (higher = applied first)
    priority = Column(Integer, default=0, nullable=False, index=True)
    
    # Settings
    is_active = Column(Boolean, default=True, nullable=False)
    effective_from = Column(DateTime(timezone=True), nullable=True)
    effective_to = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="markup_rules")
```

### 5. Extend Quote Model

**File:** `backend/app/models/quotes.py`

```python
# Add to existing Quote model:
- smart_quote_data = Column(JSON, nullable=True)  # {
  #   "ai_scope_summary": "...",
  #   "suggested_products": [...],
  #   "labor_breakdown": {...},
  #   "markup_applied": {...},
  #   "calculation_log": [...]
  # }
- template_applied_id = Column(String(36), ForeignKey("quote_templates.id"), nullable=True)
- knowledge_articles_used = Column(JSON, nullable=True)  # ["article_id_1", "article_id_2"]
- ai_suggestions_accepted = Column(JSON, nullable=True)  # Track which AI suggestions were accepted
```

### 6. Extend QuoteTemplate Model

**File:** `backend/app/models/quotes.py`

```python
# Add to existing QuoteTemplate model:
- industry = Column(String(100), nullable=True, index=True)  # "IT", "Software", "Cabling"
- quote_types = Column(JSON, nullable=True)  # ["cabling", "network_build"]
- sections = Column(JSON, nullable=True)  # [
  #   {"id": "header", "title": "Project Overview", "required": true},
  #   {"id": "materials", "title": "Materials", "required": true},
  #   {"id": "labor", "title": "Labor", "required": true}
  # ]
- variables = Column(JSON, nullable=True)  # {
  #   "customer_name": "{{customer.company_name}}",
  #   "project_title": "{{quote.title}}",
  #   "total_amount": "{{quote.total_amount}}"
  # }
- approval_workflow = Column(JSON, nullable=True)  # {
  #   "stages": ["draft", "review", "approval", "send"],
  #   "approvers": {"review": ["user_id_1"], "approval": ["user_id_2"]}
  # }
```

---

## 🤖 AI Prompts Specification

### Prompt Categories

Add to `backend/app/models/ai_prompt.py`:

```python
class PromptCategory(str, enum.Enum):
    # ... existing categories ...
    QUOTE_SCOPE_ANALYSIS = "quote_scope_analysis"
    PRODUCT_RECOMMENDATION = "product_recommendation"
    COMPONENT_SELECTION = "component_selection"
    PRICING_RECOMMENDATION = "pricing_recommendation"
    LABOR_ESTIMATION = "labor_estimation"
    UPSELL_CROSSSELL = "upsell_crosssell"
    QUOTE_EMAIL_COPY = "quote_email_copy"
    QUOTE_SUMMARY = "quote_summary"
```

### 1. Quote Scope Analysis Prompt

**Category:** `quote_scope_analysis`  
**Quote Types:** `cabling`, `network_build`, `server_build`, `software_dev`, `testing`, `design`

#### System Prompt

```
You are an expert quote analyst specializing in {quote_type} projects. Your role is to analyze project requirements and provide comprehensive scope analysis, risk assessment, and recommendations for creating accurate quotes.

You have deep knowledge of:
- Industry best practices for {quote_type} projects
- Common requirements and specifications
- Typical project complexities and challenges
- Material and labor requirements
- Risk factors and mitigation strategies

Always provide detailed, actionable analysis that helps create accurate and competitive quotes.
```

#### User Prompt Template

```
Analyze the following {quote_type} project requirements and provide comprehensive scope analysis:

**Project Details:**
Title: {quote_title}
Description: {quote_description}
Project Type: {quote_type}

**Customer Information:**
Company: {customer_company_name}
Industry: {customer_industry}
Business Size: {customer_size}

**Project Requirements:**
{project_requirements}

**Building/Site Details:**
Building Type: {building_type}
Building Size: {building_size} sqm
Number of Floors: {number_of_floors}
Number of Rooms: {number_of_rooms}
Site Address: {site_address}

**Specific Requirements:**
{special_requirements}

**Historical Context:**
{similar_projects_context}

---

Provide your analysis in the following JSON format:

{{
    "scope_summary": "Comprehensive summary of the project scope (2-3 paragraphs)",
    "key_requirements": [
        "Requirement 1",
        "Requirement 2",
        "Requirement 3"
    ],
    "complexity_assessment": "low|medium|high|very_high",
    "complexity_reasoning": "Explanation of complexity level",
    "estimated_duration_days": number,
    "estimated_duration_reasoning": "Explanation of duration estimate",
    "risk_factors": [
        {{
            "risk": "Risk description",
            "severity": "low|medium|high",
            "mitigation": "Mitigation strategy"
        }}
    ],
    "required_materials": [
        {{
            "category": "Material category (e.g., 'Cables', 'Connectors')",
            "items": [
                {{
                    "name": "Specific material name",
                    "quantity_estimate": "Estimated quantity with unit",
                    "specifications": "Key specifications",
                    "notes": "Additional notes"
                }}
            ]
        }}
    ],
    "required_labor": [
        {{
            "role": "Role name (e.g., 'Engineer', 'Technician')",
            "skill_level": "junior|senior|specialist",
            "estimated_days": number,
            "estimated_hours": number,
            "reasoning": "Explanation of labor requirement"
        }}
    ],
    "recommended_products": [
        {{
            "product_name": "Product name",
            "category": "Product category",
            "reason": "Why this product is recommended",
            "priority": "required|recommended|optional"
        }}
    ],
    "clarifying_questions": [
        "Question 1 to gather more information",
        "Question 2 to clarify requirements"
    ],
    "best_practices": [
        "Best practice recommendation 1",
        "Best practice recommendation 2"
    ],
    "industry_standards": [
        "Relevant industry standard 1",
        "Relevant industry standard 2"
    ]
}}
```

#### Variables

```json
{
    "quote_title": "Project title",
    "quote_description": "Project description",
    "quote_type": "Quote type (cabling, network_build, etc.)",
    "customer_company_name": "Customer company name",
    "customer_industry": "Customer industry sector",
    "customer_size": "Customer business size",
    "project_requirements": "Detailed project requirements",
    "building_type": "Type of building",
    "building_size": "Building size in square meters",
    "number_of_floors": "Number of floors",
    "number_of_rooms": "Number of rooms",
    "site_address": "Site address",
    "special_requirements": "Special requirements or constraints",
    "similar_projects_context": "Context from similar historical projects (optional)"
}
```

#### Example Response

```json
{
    "scope_summary": "This is a comprehensive network infrastructure project for a 3-story office building requiring Cat6 cabling, WiFi access points, and CCTV installation. The project involves approximately 50 rooms across 3 floors, requiring careful planning for cable routing and access point placement.",
    "key_requirements": [
        "Cat6 cabling to all 50 rooms",
        "WiFi coverage throughout building",
        "CCTV system with 12 cameras",
        "Network equipment installation",
        "Testing and certification"
    ],
    "complexity_assessment": "high",
    "complexity_reasoning": "High complexity due to multi-floor installation, multiple systems integration, and need for minimal disruption to ongoing operations",
    "estimated_duration_days": 12,
    "estimated_duration_reasoning": "12 days estimated based on 50 rooms, 3 floors, WiFi and CCTV installation, and testing requirements",
    "risk_factors": [
        {
            "risk": "Building access restrictions during business hours",
            "severity": "medium",
            "mitigation": "Schedule work during off-hours or coordinate with building management"
        },
        {
            "risk": "Existing infrastructure conflicts",
            "severity": "high",
            "mitigation": "Conduct site survey before starting work"
        }
    ],
    "required_materials": [
        {
            "category": "Cables",
            "items": [
                {
                    "name": "Cat6 UTP Cable",
                    "quantity_estimate": "3000 meters",
                    "specifications": "Cat6, UTP, solid core",
                    "notes": "Allow 10% extra for waste"
                }
            ]
        }
    ],
    "required_labor": [
        {
            "role": "Engineer",
            "skill_level": "senior",
            "estimated_days": 8,
            "estimated_hours": 64,
            "reasoning": "Senior engineer required for planning, installation supervision, and testing"
        },
        {
            "role": "Technician",
            "skill_level": "junior",
            "estimated_days": 10,
            "estimated_hours": 80,
            "reasoning": "Junior technicians for cable pulling and basic installation work"
        }
    ],
    "recommended_products": [
        {
            "product_name": "Cat6 UTP Cable 305m",
            "category": "Cables",
            "reason": "Standard Cat6 cable suitable for office environments",
            "priority": "required"
        }
    ],
    "clarifying_questions": [
        "What is the ceiling height? (affects cable length calculations)",
        "Are there existing cable trays or conduits?",
        "What is the preferred WiFi access point brand/model?"
    ],
    "best_practices": [
        "Follow TIA/EIA-568-B standards for cable installation",
        "Test all connections before finalizing installation",
        "Document cable routes for future maintenance"
    ],
    "industry_standards": [
        "TIA/EIA-568-B (Cabling Standards)",
        "ISO/IEC 11801 (Generic Cabling)"
    ]
}
```

### 2. Product Recommendation Prompt

**Category:** `product_recommendation`

#### System Prompt

```
You are a product recommendation expert with deep knowledge of IT infrastructure, cabling, networking equipment, and related products. Your role is to recommend specific products based on project requirements, ensuring compatibility, quality, and value.

You understand:
- Product specifications and compatibility
- Industry standards and certifications
- Price-performance trade-offs
- Supplier availability and lead times
- Installation requirements

Always recommend products that are:
- Compatible with project requirements
- From reputable suppliers
- Within reasonable price ranges
- Available with acceptable lead times
```

#### User Prompt Template

```
Recommend products for the following {quote_type} project:

**Project Requirements:**
{project_requirements}

**Required Product Categories:**
{required_categories}

**Budget Constraints:**
Budget Range: {budget_range}
Budget Priority: {budget_priority}  # "low_cost", "balanced", "premium"

**Existing Products in Quote:**
{existing_products}

**Customer Preferences:**
{customer_preferences}

**Available Products (from catalog):**
{available_products}

---

Provide product recommendations in JSON format:

{{
    "recommendations": [
        {{
            "product_id": "product_id_from_catalog",
            "product_name": "Product name",
            "category": "Product category",
            "recommendation_reason": "Why this product is recommended",
            "priority": "required|highly_recommended|recommended|optional",
            "estimated_quantity": number,
            "estimated_unit_price": number,
            "compatibility_notes": "Compatibility with other products",
            "alternatives": [
                {{
                    "product_id": "alternative_product_id",
                    "reason": "Why this is an alternative"
                }}
            ]
        }}
    ],
    "missing_products": [
        {{
            "product_name": "Product name that should be in catalog",
            "category": "Category",
            "reason": "Why this product is needed"
        }}
    ],
    "compatibility_warnings": [
        "Warning about product compatibility issue 1",
        "Warning about product compatibility issue 2"
    ],
    "cost_optimization_suggestions": [
        "Suggestion for cost optimization 1",
        "Suggestion for cost optimization 2"
    ]
}}
```

### 3. Component Selection Prompt

**Category:** `component_selection`

#### System Prompt

```
You are an expert in selecting components for {quote_type} projects. Your role is to identify all required and optional components based on project specifications, ensuring nothing is missed and optimal selections are made.

You understand:
- Component dependencies and requirements
- Industry-standard component combinations
- Compatibility matrices
- Installation sequences
- Testing requirements
```

#### User Prompt Template

```
Select components for this {quote_type} project:

**Project Scope:**
{project_scope}

**Selected Products:**
{selected_products}

**Component Requirements:**
{component_requirements}

---

Provide component selection in JSON format:

{{
    "required_components": [
        {{
            "component_name": "Component name",
            "category": "Component category",
            "quantity": number,
            "specifications": "Required specifications",
            "reason": "Why this component is required",
            "linked_to_product": "product_id"  # If linked to a selected product
        }}
    ],
    "optional_components": [
        {{
            "component_name": "Component name",
            "category": "Component category",
            "quantity": number,
            "specifications": "Required specifications",
            "reason": "Why this component is optional but recommended",
            "benefit": "Benefit of including this component"
        }}
    ],
    "component_dependencies": [
        {{
            "component": "Component name",
            "depends_on": ["Component 1", "Component 2"],
            "reason": "Why this dependency exists"
        }}
    ],
    "installation_sequence": [
        "Step 1: Install component X",
        "Step 2: Install component Y",
        "Step 3: Test components"
    ]
}}
```

### 4. Pricing Recommendation Prompt

**Category:** `pricing_recommendation`

#### System Prompt

```
You are a pricing expert specializing in {quote_type} projects. Your role is to recommend appropriate pricing, markups, and discounts based on project complexity, customer relationship, market conditions, and business objectives.

You understand:
- Industry-standard pricing practices
- Markup strategies by product category
- Volume discount structures
- Competitive pricing analysis
- Profit margin requirements
```

#### User Prompt Template

```
Recommend pricing for this {quote_type} quote:

**Quote Details:**
Total Material Cost: £{material_cost}
Total Labor Cost: £{labor_cost}
Total Travel Cost: £{travel_cost}
Project Complexity: {complexity}  # low, medium, high, very_high

**Customer Information:**
Customer Type: {customer_type}  # new, existing, strategic
Customer History: {customer_history}
Previous Quote Value: £{previous_quote_value}

**Market Context:**
Competitive Situation: {competitive_situation}
Market Conditions: {market_conditions}

**Tenant Pricing Rules:**
{tenant_pricing_rules}

---

Provide pricing recommendations in JSON format:

{{
    "material_markup_percentage": number,
    "material_markup_reasoning": "Explanation of material markup",
    "labor_markup_percentage": number,
    "labor_markup_reasoning": "Explanation of labor markup",
    "travel_markup_percentage": number,
    "travel_markup_reasoning": "Explanation of travel markup",
    "recommended_discount_percentage": number,
    "discount_reasoning": "Explanation of discount recommendation",
    "volume_discounts": [
        {{
            "threshold": number,
            "discount_percentage": number,
            "reason": "Why this volume discount applies"
        }}
    ],
    "pricing_strategy": "competitive|standard|premium",
    "pricing_strategy_reasoning": "Explanation of pricing strategy",
    "profit_margin_estimate": number,
    "competitive_analysis": "Analysis of competitive positioning",
    "pricing_risks": [
        "Risk factor 1",
        "Risk factor 2"
    ],
    "pricing_recommendations": [
        "Recommendation 1",
        "Recommendation 2"
    ]
}}
```

### 5. Labor Estimation Prompt

**Category:** `labor_estimation`

#### System Prompt

```
You are a labor estimation expert for {quote_type} projects. Your role is to accurately estimate labor hours and days required for projects, considering complexity, site conditions, team composition, and industry standards.

You understand:
- Standard labor hours for common tasks
- Complexity multipliers
- Site condition impacts
- Team efficiency factors
- Industry benchmarks
```

#### User Prompt Template

```
Estimate labor requirements for this {quote_type} project:

**Project Scope:**
{project_scope}

**Site Conditions:**
Site Type: {site_type}
Access Difficulty: {access_difficulty}  # easy, medium, difficult
Working Hours: {working_hours}  # "standard", "off_hours", "24/7"

**Team Composition:**
Available Roles: {available_roles}

**Historical Data:**
Similar Projects: {similar_projects_data}

---

Provide labor estimation in JSON format:

{{
    "labor_breakdown": [
        {{
            "role": "Role name",
            "skill_level": "junior|senior|specialist",
            "tasks": [
                "Task description 1",
                "Task description 2"
            ],
            "estimated_hours": number,
            "estimated_days": number,
            "complexity_multiplier": number,
            "reasoning": "Explanation of labor estimate"
        }}
    ],
    "total_labor_hours": number,
    "total_labor_days": number,
    "team_composition_recommendation": [
        {{
            "role": "Role name",
            "skill_level": "junior|senior|specialist",
            "count": number,
            "reason": "Why this team composition"
        }}
    ],
    "efficiency_factors": [
        {{
            "factor": "Factor name",
            "impact": "positive|negative",
            "adjustment_percentage": number,
            "reason": "Explanation"
        }}
    ],
    "risk_adjustments": [
        {{
            "risk": "Risk description",
            "additional_hours": number,
            "reason": "Why additional hours needed"
        }}
    ]
}}
```

### 6. Upsell/Cross-sell Prompt

**Category:** `upsell_crosssell`

#### System Prompt

```
You are a sales expert specializing in identifying upsell and cross-sell opportunities for {quote_type} projects. Your role is to suggest additional products or services that would add value to the customer while increasing quote value.

You understand:
- Product complementarity
- Customer needs and pain points
- Value-add opportunities
- Service bundling strategies
- Customer buying patterns
```

#### User Prompt Template

```
Identify upsell and cross-sell opportunities for this quote:

**Current Quote:**
Quote Type: {quote_type}
Selected Products: {selected_products}
Quote Value: £{quote_value}

**Customer Information:**
Customer Type: {customer_type}
Customer Industry: {customer_industry}
Customer Size: {customer_size}

**Project Context:**
Project Requirements: {project_requirements}
Budget Indication: {budget_indication}

**Available Products/Services:**
{available_products_services}

---

Provide upsell/cross-sell recommendations in JSON format:

{{
    "upsell_opportunities": [
        {{
            "product_id": "product_id",
            "product_name": "Product name",
            "category": "Product category",
            "upsell_type": "upgrade|addon|premium",
            "current_product": "Product being upgraded/replaced",
            "value_proposition": "Why customer should consider this",
            "estimated_additional_value": number,
            "customer_benefit": "Benefit to customer",
            "sales_talking_points": [
                "Talking point 1",
                "Talking point 2"
            ],
            "priority": "high|medium|low"
        }}
    ],
    "cross_sell_opportunities": [
        {{
            "product_id": "product_id",
            "product_name": "Product name",
            "category": "Product category",
            "complementary_to": "Product/service this complements",
            "value_proposition": "Why this complements the quote",
            "estimated_additional_value": number,
            "customer_benefit": "Benefit to customer",
            "sales_talking_points": [
                "Talking point 1",
                "Talking point 2"
            ],
            "priority": "high|medium|low"
        }}
    ],
    "service_addons": [
        {{
            "service_name": "Service name",
            "service_description": "Service description",
            "value_proposition": "Why this service adds value",
            "estimated_additional_value": number,
            "customer_benefit": "Benefit to customer"
        }}
    ],
    "bundling_opportunities": [
        {{
            "bundle_name": "Bundle name",
            "products_included": ["product_1", "product_2"],
            "discount_percentage": number,
            "value_proposition": "Why this bundle is attractive",
            "estimated_total_value": number
        }}
    ]
}}
```

### 7. Quote Email Copy Generation Prompt

**Category:** `quote_email_copy`

#### System Prompt

```
You are a professional business communication expert specializing in quote presentation emails. Your role is to create compelling, professional email copy that presents quotes effectively, builds trust, and encourages customer action.

You understand:
- Professional business communication
- Sales psychology and persuasion
- Customer relationship building
- Quote presentation best practices
- Follow-up strategies
```

#### User Prompt Template

```
Generate email copy for presenting this quote:

**Quote Details:**
Quote Number: {quote_number}
Quote Title: {quote_title}
Quote Value: £{quote_value}
Valid Until: {valid_until}

**Customer Information:**
Customer Name: {customer_name}
Contact Name: {contact_name}
Relationship: {relationship}  # new, existing, strategic

**Quote Highlights:**
{quote_highlights}

**Key Value Propositions:**
{value_propositions}

**Email Type:**
{email_type}  # "initial", "follow_up", "negotiation", "reminder"

**Tone:**
{tone}  # "professional", "friendly", "formal", "consultative"

---

Provide email copy in JSON format:

{{
    "subject_line": "Email subject line",
    "greeting": "Personalized greeting",
    "opening_paragraph": "Opening paragraph that engages the customer",
    "quote_summary": "Brief summary of the quote",
    "key_benefits": [
        "Benefit 1",
        "Benefit 2",
        "Benefit 3"
    ],
    "value_proposition": "Clear value proposition",
    "call_to_action": "Clear call to action",
    "closing_paragraph": "Professional closing paragraph",
    "signature": "Professional signature",
    "next_steps": [
        "Next step 1",
        "Next step 2"
    ],
    "alternative_subject_lines": [
        "Alternative subject line 1",
        "Alternative subject line 2"
    ],
    "personalization_notes": "Notes on how to personalize this email"
}}
```

### 8. Quote Summary Prompt

**Category:** `quote_summary`

#### System Prompt

```
You are an expert at creating comprehensive quote summaries for different audiences. Your role is to distill complex quote information into clear, actionable summaries suitable for executives, technical teams, or customers.

You understand:
- Executive communication
- Technical documentation
- Customer-facing communication
- Information hierarchy
- Key message prioritization
```

#### User Prompt Template

```
Create a {summary_type} summary for this quote:

**Quote Details:**
{quote_details}

**Summary Type:**
{summary_type}  # "executive", "technical", "customer_facing"

**Audience:**
{audience}  # "c_level", "technical_team", "end_customer"

**Key Points to Highlight:**
{key_points}

---

Provide summary in JSON format:

{{
    "summary": "Main summary text (2-3 paragraphs)",
    "key_highlights": [
        "Highlight 1",
        "Highlight 2",
        "Highlight 3"
    ],
    "scope_overview": "Overview of project scope",
    "pricing_breakdown": {{
        "materials": number,
        "labor": number,
        "travel": number,
        "subtotal": number,
        "tax": number,
        "total": number
    }},
    "timeline": "Project timeline summary",
    "deliverables": [
        "Deliverable 1",
        "Deliverable 2"
    ],
    "risks_and_mitigations": [
        {{
            "risk": "Risk description",
            "mitigation": "Mitigation strategy"
        }}
    ],
    "recommendations": [
        "Recommendation 1",
        "Recommendation 2"
    ]
}}
```

---

## 🔧 Backend Services

### 1. Product Catalog Service

**File:** `backend/app/services/product_catalog_service.py`

```python
class ProductCatalogService:
    """
    Service for managing product catalog operations
    
    Features:
    - Product search and filtering
    - Category management
    - Product recommendations
    - Supplier integration
    - Pricing updates
    """
    
    async def search_products(
        self,
        query: str,
        category: Optional[str] = None,
        filters: Optional[Dict] = None
    ) -> List[Product]:
        """Search products with filters"""
        
    async def get_product_recommendations(
        self,
        quote_type: str,
        requirements: Dict
    ) -> List[Product]:
        """Get AI-powered product recommendations"""
        
    async def get_product_by_id(self, product_id: str) -> Product:
        """Get product by ID"""
        
    async def update_product_pricing(
        self,
        product_id: str,
        supplier_pricing_id: str
    ) -> Product:
        """Update product pricing from supplier"""
```

### 2. Day Rate Service

**File:** `backend/app/services/day_rate_service.py`

```python
class DayRateService:
    """
    Service for calculating day rates and labor costs
    
    Features:
    - Day rate calculations
    - Labor cost estimation
    - Travel cost calculations
    - Overtime calculations
    """
    
    async def calculate_labor_cost(
        self,
        role: str,
        skill_level: str,
        days: float,
        hours: Optional[float] = None,
        location: Optional[str] = None,
        overtime_hours: Optional[float] = None
    ) -> Dict[str, Any]:
        """Calculate labor cost for a role"""
        
    async def calculate_travel_cost(
        self,
        distance_km: float,
        time_hours: float,
        role: str
    ) -> Dict[str, Any]:
        """Calculate travel costs"""
        
    async def estimate_project_labor(
        self,
        quote_type: str,
        requirements: Dict
    ) -> Dict[str, Any]:
        """AI-powered labor estimation"""
```

### 3. Component Pricing Service

**File:** `backend/app/services/component_pricing_service.py`

```python
class ComponentPricingService:
    """
    Service for component pricing and markup calculations
    
    Features:
    - Supplier pricing integration
    - Markup rule application
    - Bulk pricing calculations
    - Price history tracking
    """
    
    async def get_component_price(
        self,
        product_id: str,
        quantity: int,
        customer_type: str = "standard"
    ) -> Dict[str, Any]:
        """Get price for component with markup applied"""
        
    async def apply_markup_rules(
        self,
        base_cost: Decimal,
        product_category: str,
        quote_type: str,
        customer_type: str
    ) -> Dict[str, Any]:
        """Apply markup rules to base cost"""
        
    async def calculate_bulk_pricing(
        self,
        product_id: str,
        quantity: int
    ) -> Decimal:
        """Calculate bulk pricing based on tiers"""
```

### 4. Quote Builder Service

**File:** `backend/app/services/quote_builder_service.py`

```python
class QuoteBuilderService:
    """
    Service for building quotes with AI assistance
    
    Features:
    - Quote creation workflow
    - AI scope analysis
    - Product selection assistance
    - Price calculations
    - Template application
    """
    
    async def create_quote_with_ai(
        self,
        quote_data: Dict,
        customer_id: str,
        user_id: str
    ) -> Quote:
        """Create quote with AI assistance"""
        
    async def analyze_quote_scope(
        self,
        quote: Quote
    ) -> Dict[str, Any]:
        """Get AI scope analysis"""
        
    async def suggest_products(
        self,
        quote: Quote
    ) -> List[Dict]:
        """Get AI product suggestions"""
        
    async def calculate_quote_totals(
        self,
        quote: Quote
    ) -> Quote:
        """Calculate all quote totals"""
```

### 5. Knowledge Base Service

**File:** `backend/app/services/knowledge_base_service.py`

```python
class KnowledgeBaseService:
    """
    Service for knowledge base operations
    
    Features:
    - Article search
    - Article recommendations
    - Product linking
    - Category management
    """
    
    async def search_articles(
        self,
        query: str,
        quote_type: Optional[str] = None,
        category: Optional[str] = None
    ) -> List[KnowledgeBaseArticle]:
        """Search knowledge base articles"""
        
    async def get_recommended_articles(
        self,
        quote_type: str,
        selected_products: List[str]
    ) -> List[KnowledgeBaseArticle]:
        """Get AI-recommended articles"""
        
    async def link_article_to_quote(
        self,
        article_id: str,
        quote_id: str
    ) -> None:
        """Link article to quote for reference"""
```

---

## 🌐 API Endpoints

### 1. Product Catalog Endpoints

**File:** `backend/app/api/v1/endpoints/product_catalog.py`

```python
router = APIRouter(prefix="/product-catalog", tags=["Product Catalog"])

@router.get("/products")
async def search_products(
    query: Optional[str] = None,
    category: Optional[str] = None,
    # ... filters
):
    """Search products"""
    
@router.get("/products/{product_id}")
async def get_product(product_id: str):
    """Get product by ID"""
    
@router.post("/products/recommendations")
async def get_product_recommendations(request: ProductRecommendationRequest):
    """Get AI product recommendations"""
    
@router.get("/categories")
async def get_categories():
    """Get product categories"""
```

### 2. Day Rate Endpoints

**File:** `backend/app/api/v1/endpoints/day_rates.py`

```python
router = APIRouter(prefix="/day-rates", tags=["Day Rates"])

@router.get("/rates")
async def get_day_rates():
    """Get available day rates"""
    
@router.post("/calculate")
async def calculate_labor_cost(request: LaborCostRequest):
    """Calculate labor cost"""
    
@router.post("/estimate")
async def estimate_project_labor(request: LaborEstimationRequest):
    """AI-powered labor estimation"""
```

### 3. Quote Builder Endpoints

**File:** `backend/app/api/v1/endpoints/quote_builder.py`

```python
router = APIRouter(prefix="/quote-builder", tags=["Quote Builder"])

@router.post("/create")
async def create_quote_with_ai(request: CreateQuoteRequest):
    """Create quote with AI assistance"""
    
@router.post("/{quote_id}/analyze-scope")
async def analyze_scope(quote_id: str):
    """Get AI scope analysis"""
    
@router.post("/{quote_id}/suggest-products")
async def suggest_products(quote_id: str):
    """Get AI product suggestions"""
    
@router.post("/{quote_id}/calculate-totals")
async def calculate_totals(quote_id: str):
    """Calculate quote totals"""
```

---

## 🎨 Frontend Components

### 1. Step-by-Step Quote Builder

**File:** `frontend/src/components/QuoteBuilder/QuoteBuilderWizard.tsx`

```typescript
interface QuoteBuilderWizardProps {
  customerId?: string;
  leadId?: string;
  quoteType?: string;
  onComplete: (quote: Quote) => void;
}

const QuoteBuilderWizard: React.FC<QuoteBuilderWizardProps> = ({
  customerId,
  leadId,
  quoteType,
  onComplete
}) => {
  // Steps:
  // 1. Customer/Project Selection
  // 2. Project Requirements
  // 3. Product Selection
  // 4. Labor & Services
  // 5. Review & Pricing
  // 6. Terms & Conditions
};
```

### 2. Product Catalog Browser

**File:** `frontend/src/components/QuoteBuilder/ProductCatalogBrowser.tsx`

```typescript
interface ProductCatalogBrowserProps {
  quoteType: string;
  onProductSelect: (product: Product) => void;
  selectedProducts: string[];
}
```

### 3. AI Suggestions Panel

**File:** `frontend/src/components/QuoteBuilder/AISuggestionsPanel.tsx`

```typescript
interface AISuggestionsPanelProps {
  quoteId: string;
  suggestionType: 'products' | 'components' | 'upsells';
  onAccept: (suggestion: any) => void;
  onReject: (suggestionId: string) => void;
}
```

---

## 📋 Workflows

### Quote Creation Workflow

1. User selects customer/lead and quote type
2. System loads quote template (if applicable)
3. User enters project requirements
4. AI analyzes scope and generates summary
5. AI suggests products and components
6. User selects products from catalog
7. User adds labor requirements
8. System calculates totals (materials + labor + markup + tax)
9. AI suggests upsells/cross-sells
10. User reviews and adjusts
11. User saves quote (draft or sends)

### Product Selection Workflow

1. User searches/browses product catalog
2. AI suggests products based on quote type
3. User selects products
4. System checks compatibility
5. System applies pricing (with markup)
6. User adjusts quantities
7. System updates totals in real-time

---

## ✅ Implementation Checklist

### Phase 1: Database & Models
- [ ] Extend Product model
- [ ] Create DayRate model
- [ ] Create KnowledgeBaseArticle model
- [ ] Create MarkupRule model
- [ ] Extend Quote model
- [ ] Extend QuoteTemplate model
- [ ] Create database migrations
- [ ] Seed initial data

### Phase 2: AI Prompts
- [ ] Create quote scope analysis prompts (all quote types)
- [ ] Create product recommendation prompt
- [ ] Create component selection prompt
- [ ] Create pricing recommendation prompt
- [ ] Create labor estimation prompt
- [ ] Create upsell/cross-sell prompt
- [ ] Create quote email copy prompt
- [ ] Create quote summary prompt
- [ ] Test all prompts
- [ ] Seed prompts to database

### Phase 3: Backend Services
- [ ] Implement ProductCatalogService
- [ ] Implement DayRateService
- [ ] Implement ComponentPricingService
- [ ] Implement QuoteBuilderService
- [ ] Implement KnowledgeBaseService
- [ ] Add unit tests
- [ ] Add integration tests

### Phase 4: API Endpoints
- [ ] Create product catalog endpoints
- [ ] Create day rate endpoints
- [ ] Create quote builder endpoints
- [ ] Create knowledge base endpoints
- [ ] Add API documentation
- [ ] Add error handling
- [ ] Add validation

### Phase 5: Frontend Components
- [ ] Create QuoteBuilderWizard component
- [ ] Create ProductCatalogBrowser component
- [ ] Create AISuggestionsPanel component
- [ ] Create ProductSelector component
- [ ] Create LaborCalculator component
- [ ] Create PriceCalculator component
- [ ] Integrate with existing QuoteNew page
- [ ] Add loading states
- [ ] Add error handling

### Phase 6: Integration & Testing
- [ ] End-to-end workflow testing
- [ ] AI prompt testing
- [ ] Performance testing
- [ ] User acceptance testing
- [ ] Bug fixes
- [ ] Documentation updates

---

## 📝 Notes

- All AI prompts should be stored in database with versioning
- All services should be tenant-aware
- All API endpoints should follow existing patterns
- All frontend components should use Material-UI
- All calculations should be precise (use Decimal for money)
- All AI responses should be cached appropriately
- All errors should be logged and handled gracefully

---

**Document Version:** 1.0  
**Last Updated:** Current  
**Next Review:** After Phase 1 completion

