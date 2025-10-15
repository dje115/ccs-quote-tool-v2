# Changelog
All notable changes to the CCS Quote Tool v2 project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.5.0] - 2025-10-14

### 🔧 Bug Fixes & UI Improvements
- **FIXED: Campaign Name Display in Discoveries**
  - Discoveries page now correctly shows actual campaign names instead of "N/A campaign"
  - Added campaign name field to LeadResponse schema
  - Enhanced backend endpoint to join with campaign table for complete campaign information
  - Improved lead-to-campaign relationship tracking

- **NEW: Advanced Sorting Functionality**
  - Added clickable column headers with visual sort indicators (arrows)
  - Sortable columns: Company Name, Location (Postcode), Lead Score, Created Date
  - Backend API now supports sort_by and sort_order parameters
  - Default sorting by lead score (descending) for optimal lead prioritization
  - Real-time sorting without page refresh

- **FIXED: Campaign Stop Button Functionality**
  - Added missing `/campaigns/{campaign_id}/stop` backend endpoint
  - Campaign stop buttons now actually work instead of showing "coming soon"
  - Proper campaign status management (RUNNING/QUEUED → CANCELLED)
  - Enhanced campaign control and user experience

- **Enhanced Google Maps Data Extraction**
  - Fixed website and phone number extraction from Google Maps during campaign execution
  - Added place details API call to fetch comprehensive business information
  - Improved lead enrichment with contact information (phone, website, address)
  - Better data quality for campaign-generated leads

- **UI/UX Improvements**
  - Added sorting icons (ArrowUpward/ArrowDownward) for clear visual feedback
  - Improved table header styling with hover effects and cursor pointers
  - Enhanced campaign management with working stop/start functionality
  - Better error handling and user feedback throughout the application

### 🔄 Technical Improvements
- Enhanced backend API endpoints with proper relationship loading
- Improved SQL queries with joinedload for campaign information
- Better error handling and validation in campaign management
- Enhanced data consistency between frontend and backend

---

## [2.4.0] - 2025-10-13

### 🚀 Dynamic Campaign Prompts & Advanced Campaign Types
- **NEW: Dynamic Campaign Prompts Based on Tenant Profile**
  - Campaign prompts now automatically adapt to each tenant's business profile
  - Includes tenant's company name, description, services, target markets, and USPs
  - All campaign types now use tenant-specific targeting for better lead relevance
  - Enhanced lead generation accuracy and targeting precision

- **NEW: Advanced Campaign Types**
  - **Dynamic Business Search** - AI-powered search based on tenant's services and target markets
  - **Service Gap Analysis** - Find businesses missing services the tenant offers
  - **Custom Search** - Allow users to write their own AI search queries with tenant context
  - **Enhanced Company List Import** - Analyze specific companies with tenant targeting
  - **Improved Similar Business Lookup** - Find companies like existing customers with tenant context

- **Enhanced Campaign Intelligence**
  - Campaigns now identify specific opportunities for each tenant's services
  - Better lead qualification based on tenant's unique selling points
  - Improved targeting alignment with tenant's business profile
  - Enhanced search terms generation based on tenant services

### 🔧 Campaign System Improvements
- **Dynamic Prompt Building**
  - Automatic tenant context integration in all campaign prompts
  - Service-specific targeting in campaign instructions
  - Target market alignment in campaign focus areas
  - USP integration for better lead qualification

- **Enhanced Campaign Types Support**
  - Added support for all new campaign types in prompt building
  - Improved search terms generation for advanced campaign types
  - Better campaign validation and error handling
  - Enhanced campaign type descriptions and user guidance

---

## [2.3.0] - 2025-10-13

### 🤖 AI Discovery Analysis System
- **NEW: Comprehensive AI-Powered Analysis for Discoveries**
  - Analyzes companies using GPT-5-mini (20,000 tokens, 240s timeout)
  - Extracts business intelligence from multiple data sources:
    - Google Maps (ratings, reviews, contact info)
    - Companies House (financials, directors, SIC codes)
    - LinkedIn (industry, company size, description)
    - Website information
  
- **Automatic Contact Information Extraction**
  - AI searches for and extracts:
    - Contact person name (Director, CEO, IT Manager, or general contact)
    - Contact email address (info@, sales@, enquiries@, or specific contacts)
    - Contact phone number (direct lines if available)
  - Auto-populates contact fields on lead record
  - Only updates empty fields (preserves manual data)
  - Searches in: website contact pages, Google Maps listings, Companies House directors

- **Comprehensive Business Intelligence Output**
  - Business sector classification (11 categories)
  - Company size assessment (employees, revenue, category)
  - Primary business activities description
  - Technology maturity level (Basic/Intermediate/Advanced/Enterprise)
  - IT budget estimate
  - Financial health analysis
  - Growth potential assessment (High/Medium/Low)
  - Technology needs prediction
  - Competitive landscape analysis
  - Business opportunities identification
  - Risk factors assessment

- **Beautiful Structured UI Display**
  - Professional layout with color-coded sections
  - Company profile summary at top
  - Key metrics in 2-column grid
  - Growth potential with color-coded chips
  - Opportunities section (green heading)
  - Risk factors section (red heading)
  - Expandable detailed sections

### 🔐 User Permissions & Role-Based Access Control (RBAC)
- **NEW: Granular Permission System**
  - 33 individual permissions across 7 categories:
    - Dashboard (2 permissions)
    - Customers (5 permissions)
    - Discoveries (4 permissions)
    - Campaigns (6 permissions)
    - Quotes (7 permissions)
    - Users (5 permissions)
    - Settings (4 permissions)

- **5 Pre-Defined User Roles**
  - **Super Admin**: All permissions (cannot be restricted)
  - **Tenant Admin**: Full tenant access
  - **Manager**: Can manage but not delete
  - **Sales Rep**: Create/edit, limited delete
  - **User**: Read-only access

- **Backend API for Permission Management**
  - `GET /api/v1/users/permissions/available` - Get all permissions by category
  - `GET /api/v1/users/permissions/defaults/{role}` - Get default permissions for role
  - `POST /api/v1/users/` - Create user with custom permissions
  - Permission validation on every request
  - Super admin bypass for all checks

- **Permission Storage**
  - Stored as JSON array in user record
  - Default permissions auto-populated by role
  - Custom permissions override role defaults
  - Extensible for future permissions

### 🔍 Discovery System Enhancements
- **Renamed "Leads" to "Discoveries" in UI**
  - Updated sidebar menu label
  - Consistent terminology throughout app
  - Reflects campaign-generated nature of leads

- **Multi-Select & Bulk Operations**
  - Checkbox column in discoveries table
  - "Select All" functionality
  - Bulk convert to CRM leads
  - Selected rows highlighted
  - Bulk action button shows count
  - Progress tracking during bulk operations

- **Enhanced Discovery Detail Page**
  - "Run AI Analysis" button in Quick Actions
  - Loading states ("Analyzing...")
  - Auto-refresh after analysis completion
  - Display of all discovery fields:
    - Company name, business sector
    - Company size, postcode, address
    - Contact details (name, email, phone)
    - Website, campaign name, source
    - Description, project value, timeline
  - External data display (Google Maps, Companies House)

- **Campaign Queue Management**
  - Added "Reset to Draft" button for queued campaigns
  - Allows un-queuing campaigns before execution
  - "Cancel" button for queued campaigns
  - Workflow: DRAFT → QUEUED → RUNNING → COMPLETED
  - Can reset QUEUED → DRAFT for editing

### 🐛 Bug Fixes
- Fixed discovery detail page error (undefined `handleConvertToCustomer`)
- Fixed attribute error in AI analysis (missing `description` field)
- Added safe attribute checking with `hasattr()`
- Fixed "Convert to CRM Lead" button functionality
- Updated all references to use correct function names

### 📚 Documentation
- **NEW: AI_DISCOVERY_ANALYSIS.md**
  - Complete guide to AI analysis system
  - API endpoints and usage examples
  - Frontend integration guide
  - Performance considerations
  - Troubleshooting guide

- **NEW: USER_PERMISSIONS_SYSTEM.md**
  - Comprehensive RBAC documentation
  - Permission categories and descriptions
  - Role definitions and defaults
  - API usage examples
  - Security considerations

- **NEW: DISCOVERY_TO_CRM_WORKFLOW.md**
  - Status progression workflow
  - Discovery to CRM lead conversion
  - Multi-select and bulk operations
  - Database schema reference

- **Updated: README.md**
  - Version bumped to 2.3.0
  - Added links to new documentation
  - Updated feature list

### 🔧 Technical Improvements
- Enhanced error handling in AI analysis service
- Added comprehensive logging for AI operations
- Improved contact information extraction logic
- Better JSON parsing with markdown code block removal
- Safe attribute access throughout codebase

### 🎨 UI/UX Improvements
- Professional AI analysis display layout
- Color-coded sections (green=opportunities, red=risks)
- Growth potential chips with dynamic colors
- Improved discovery table with checkboxes
- Better loading states and user feedback
- Consistent button styling and placement

---

## [2.2.3] - 2025-10-12

### 🎯 Major Features Added
- **Development Environment with Hot-Reload**: Complete Docker development/production separation
  - Development mode with instant code changes (no rebuilds required)
  - Production mode with optimized builds for deployment
  - Separate Docker Compose configurations for each environment
  - Frontend hot-reload via Vite dev server (updates in <2 seconds)
  - Backend auto-reload via uvicorn --reload
  - Admin portal hot-reload via Vue + Vite HMR
  
- **Lead Generation Campaign System**: Complete migration from v1 to v2
  - AI-powered lead discovery using OpenAI GPT-5-mini with Responses API (web search enabled)
  - 10+ predefined campaign types (IT/MSP, Education, Healthcare, Manufacturing, etc.)
  - Multi-source data enrichment:
    - Google Maps API (location, ratings, reviews)
    - Companies House API (financial data, directors)
    - LinkedIn profile detection
    - Website scraping for additional insights
  - Intelligent deduplication against existing customers and leads
  - Background processing via FastAPI BackgroundTasks (3-10 minutes per campaign)
  - Real-time campaign monitoring with auto-refresh
  - Lead-to-customer conversion with DISCOVERY status assignment
  
- **Enhanced Customer Lifecycle**: New status workflow stages
  - **DISCOVERY**: Companies identified via campaigns but not yet contacted (shown in Leads section)
  - **OPPORTUNITY**: Active sales opportunity with quote/proposal (between PROSPECT and CUSTOMER)
  - Complete workflow: DISCOVERY → LEAD → PROSPECT → OPPORTUNITY → CUSTOMER

### ✨ Enhancements

- **Development Experience**:
  - `docker-compose.yml` → Development mode (default)
  - `docker-compose.dev.yml` → Development mode (explicit)
  - `docker-compose.prod.yml` → Production mode (optimized builds)
  - `dev-start.ps1` → Quick start script for Windows
  - Volume mounts for live code updates in development
  - No volume mounts in production (immutable containers)
  
- **Campaign UI/UX**:
  - Dashboard-style campaigns page with gradient statistics cards
  - Emoji icons for visual hierarchy (🎯 📊 ✅ ❌ ⏱️)
  - Real-time status updates with auto-refresh every 10 seconds
  - Campaign type selection with card-based interface
  - Sticky preview panel on campaign creation
  - Detailed campaign view with lead table and conversion options
  - Tabbed filtering (All, Running, Completed, Failed)
  
- **Backend Architecture**:
  - `LeadGenerationService` with async operations
  - Integration with OpenAI Responses API for web search
  - Increased token limits: 10,000+ for all AI operations
  - Timeout increased to 120 seconds for complex AI queries
  - `created_by` and `updated_by` tracking for campaigns
  - Background task execution for non-blocking campaign runs
  
- **Database Schema**:
  - Added `DISCOVERY` and `OPPORTUNITY` to `customerstatus` enum
  - Added `created_by` and `updated_by` columns to `lead_generation_campaigns` table
  - Migration scripts for all enum and schema changes

### 🐛 Bug Fixes
- Fixed campaign creation failing due to missing user tracking fields
- Fixed frontend TypeScript build errors with Chip component icon prop
- Fixed database enum case sensitivity issues (UPPERCASE required)
- Fixed lead deduplication logic to check both leads and customers tables
- Fixed campaign status display in UI

### 📚 Documentation
- **DEVELOPMENT_ENVIRONMENT.md**: Comprehensive 500+ line guide covering:
  - Development vs Production modes
  - Quick start commands
  - Docker configuration details
  - Development workflow best practices
  - Troubleshooting guide
  - File watching and hot-reload setup
  - Environment variables
  - Common issues and solutions
  
- **CAMPAIGNS_GUIDE.md**: Complete user guide for lead generation system:
  - Features overview
  - Campaign types and use cases
  - Step-by-step usage instructions
  - Performance expectations
  - Troubleshooting tips
  
- **CAMPAIGN_MIGRATION.md**: Technical migration documentation:
  - v1 to v2 architectural changes
  - Model and service enhancements
  - API endpoint comparisons
  - Testing instructions
  
- **README.md**: Root-level documentation with:
  - Quick start for dev and prod modes
  - Architecture overview
  - Features list
  - Project structure
  - Development workflow
  - Troubleshooting
  - Version history

### 🎨 Visual Improvements
- Gradient statistics cards with hover effects
- Color-coded campaign status badges
- Modern card-based layouts throughout
- Responsive design for all screen sizes
- Consistent color scheme with purple/blue gradients
- Emoji icons for better visual scanning

### 🔧 Technical Improvements
- Proper SQLAlchemy enum handling with database-first approach
- AsyncHTTPClient for external API calls
- Comprehensive error handling and logging
- Type hints throughout Python codebase
- TypeScript strict mode enabled
- Docker multi-stage builds for production
- Development Dockerfiles for hot-reload

### 🚀 Performance
- Development: <2 second hot-reload for frontend changes
- Development: <3 second auto-reload for backend changes
- Production: Minified and optimized builds
- Campaign processing: 3-10 minutes for 10-50 leads
- AI analysis: 20-30 seconds per company with GPT-5-mini

---

## [2.2.2] - 2025-10-12

### 🎯 Major Features Added
- **AI Business Intelligence Tab**: New dedicated tab for AI-powered business analysis
  - Strategic insights display with Accept/Discard controls per section
  - 8 key intelligence areas: Business Model, Competitive Position, ICP, Pain Points, Sales Approach, Cross-Sell, Objections, Industry Trends
  - Side-by-side comparison (Current vs AI Suggested) for each insight
  - Smart JSON-to-readable-text formatting with proper bullet points and nested object handling
  - Individual Accept/Discard/Merge controls per section
  - Global Accept All/Discard All actions
  - "Complete your Company Profile first" reminder with best practice guidance

### ✨ Enhancements
- **UI/UX Improvements**:
  - Consistent purple gradient styling across Company Profile and AI Business Intelligence tabs
  - Removed "Analyze My Company" button from Company Profile tab (moved to dedicated AI tab)
  - Cleaner, more focused Company Profile tab with single "AI AUTO-FILL PROFILE" button
  - Enhanced text formatting with proper line breaks, word wrapping, and spacing
  - Intelligent nested object formatting for complex AI responses
  - Professional display of arrays, objects, and nested structures

- **Smart Data Formatting**:
  - Converts JSON arrays to bullet points
  - Formats nested objects with proper indentation
  - Handles complex structures like arrays of objects (e.g., buyer personas)
  - Capitalizes headings and removes underscores
  - Preserves multi-paragraph text with proper line breaks

- **Backend**:
  - Fixed `sales_methodology` field length limitation (VARCHAR(100) → TEXT)
  - Database migration: `fix_sales_methodology_length.sql`
  - Updated Tenant model to support longer sales methodology descriptions
  - Enhanced error handling and logging for AI analysis endpoints

### 🐛 Bug Fixes
- Fixed "failed to save profile" error caused by `sales_methodology` field exceeding 100 characters
- Fixed "[object Object]" display issue for nested JSON structures in AI analysis results
- Fixed text overflow and wrapping issues in analysis display
- Added proper null/undefined checks for nested object formatting

### 📚 Documentation
- Created `AI_SUGGESTION_REVIEW_SYSTEM.md` (from previous release)
- Created `BUGFIX_SALES_METHODOLOGY.md` with migration details
- Updated all spec files with new AI Business Intelligence tab feature

### 🎨 Visual Consistency
- Both Company Profile and AI Business Intelligence tabs now use same gradient: `linear-gradient(135deg, #667eea 0%, #764ba2 100%)`
- Consistent button styling, padding, and border radius
- Professional color-coded sections for different insight types
- Clean, modern Material-UI design throughout

---

## [2.2.1] - 2025-10-12

### 🎯 Major Features Added
- **AI Suggestion Review & Merge System**: Complete overhaul of AI Auto-Fill workflow
  - **Side-by-Side Comparison**: Visual comparison of current data vs AI suggestions
  - **Section-by-Section Control**: Individual actions (Replace/Merge/Discard) for each field
  - **Global Actions**: Quick apply/merge/discard for all sections at once
  - **No Auto-Apply**: AI suggestions never automatically overwrite data
  - **Smart Merge Logic**: Intelligent merging for arrays (removes duplicates) and objects
  - **Visual Design**: Color-coded sections with clear Current vs AI Suggested labels
  - **Transparency**: Shows AI confidence score, data sources, and social media links found

### ✨ Enhancements
- **Frontend (CompanyProfile.tsx)**:
  - Added `autoFillResults` state to store AI suggestions separately from profile data
  - Implemented `applySectionSuggestion()` for granular field-level control
  - Implemented `applyAllSuggestions()` for bulk operations
  - Implemented `discardAllSuggestions()` to clear suggestions
  - Enhanced UI with Paper components for each section (Description, Products, USPs, Markets, Pitch)
  - Added chip-based display with counts for array fields
  - Added console logging for debugging AI responses
  - Fixed response parsing to handle nested `data` object from backend

- **Backend (settings.py)**:
  - Fixed `/company-profile/auto-fill` endpoint response structure
  - Added `sales_methodology` to AI analysis response
  - Enhanced AI prompt to explicitly request marketing keywords and LinkedIn URL
  - Improved error handling and logging

### 🎨 UI/UX Improvements
- Color-coded comparison boxes:
  - Current data: Gray (`#f5f5f5`)
  - Company Description: Light blue (`#e3f2fd`)
  - Products & Services: Light blue (`#e3f2fd`)
  - Unique Selling Points: Light green (`#e8f5e9`)
  - Target Markets: Light purple (`#f3e5f5`)
  - Elevator Pitch: Light red (`#ffebee`)
- Left border colors for each section (warning, info, success, secondary, error)
- Clear button labels: "Use AI Version", "Replace", "Merge (Add New)", "Keep Current"
- Quick action buttons at top: "Replace All", "Merge All", "Discard All"

### 📚 Documentation
- Created `AI_SUGGESTION_REVIEW_SYSTEM.md` with comprehensive implementation details
- Updated `DEVELOPMENT_STATUS.md` to version 2.2.1
- Updated `CHANGELOG.md` with all recent changes

### 🐛 Bug Fixes
- Fixed AI auto-fill data not displaying (was stored but not shown)
- Fixed frontend not parsing nested `response.data.data` structure correctly
- Fixed suggestions being applied immediately instead of showing for review
- Added proper null/undefined checks for all array fields

---

## [2.2.0] - 2025-10-11

### 🎯 Major Features Added
- **Multiple Contact Methods**: Contacts can now have multiple email addresses and phone numbers
  - Each email/phone can be typed (work/personal/mobile/home/other)
  - Primary designation for each contact method
  - Add/remove contact methods dynamically
- **Contact Detail Dialog**: Clickable contact cards with comprehensive information display
  - All emails and phones displayed with types
  - Primary badges
  - Notes section
  - Edit functionality
  - Metadata (created/updated dates)
- **Known Facts System**: User-provided facts for improved AI accuracy
  - Text area for entering multiple facts
  - Facts included in AI analysis prompts
  - Persistent storage with proper save/clear functionality

### ✨ Enhancements
- **Backend API**:
  - Added `emails` and `phones` JSON fields to contacts table
  - Added `notes` and `updated_at` fields to ContactResponse schema
  - Fixed `known_facts` update endpoint (was not saving to database)
  - Added `company_registration` to customer update endpoint
  - Improved customer data reloading after saves
- **Frontend**:
  - Enhanced ContactDialog with dynamic email/phone management
  - Added ContactDetailDialog component for full contact view
  - Made contact cards clickable with hover effects
  - Added "Multiple contacts" badge when additional methods exist
  - Improved save logic for known facts with data refresh
  - Better error handling and user feedback

### 🐛 Bug Fixes
- Fixed known facts not saving/clearing properly
- Fixed contact notes not displaying in API responses
- Fixed customer update endpoint not handling known_facts field
- Removed corrupted "Arkel Computer Services" customer record
- Fixed email validation to allow null values
- Fixed contact role enum mismatch (lowercase with underscores)

### 🗑️ Removed
- Removed early development customer records with malformed data

### 📚 Documentation
- Updated README.md with v2.2.0 features
- Created comprehensive TODO.md with detailed task lists
- Created DEVELOPMENT_PLAN.md with 6-month roadmap
- Created CHANGELOG.md (this file)
- Updated version numbers across all packages

---

## [2.1.0] - 2025-10-09

### 🎯 Major Features Added
- **Multilingual Support**: 10 languages supported (EN, ES, FR, DE, IT, PT, NL, RU, JA, ZH)
  - AI-powered translation using GPT-5
  - User-selectable language preference
  - Frontend internationalization with i18next
- **Admin Portal**: Tenant management interface (Port 3010)
  - Global API key management with status indicators
  - Tenant CRUD operations
  - User management with password reset
  - Dashboard analytics
- **API Key Management System**:
  - Database-stored API keys (not environment variables)
  - System-wide and tenant-specific keys
  - Tenant keys override system keys
  - API connection testing

### ✨ Enhancements
- **Security**: Argon2 password hashing (industry-leading)
- **Frontend Build**: Migrated from Create React App to Vite
- **User Experience**: Working language selector in header
- **Performance**: Faster development builds with Vite

### 🐛 Bug Fixes
- Fixed admin portal login issues
- Fixed API key retrieval from database
- Fixed webpack compilation errors by migrating to Vite
- Fixed tenant portal API testing

### 📚 Documentation
- Updated README with multilingual features
- Added admin portal documentation
- Documented API key management system

---

## [2.0.0] - 2025-10-01

### 🎉 Initial Release

### 🎯 Major Features
- **CRM Module**:
  - Customer management with AI-powered analysis
  - Multi-tab interface (Overview, AI Analysis, Financial, Addresses, Directors, Competitors)
  - Contact management with role-based categorization
  - Address management with Google Maps integration
  - "Not this business" address exclusion system
- **AI Integration**:
  - GPT-5 powered company analysis
  - Automated lead scoring (0-100)
  - Health score calculation
  - Financial analysis with multi-year trends
  - Competitor identification
  - Risk factor analysis
  - Opportunity recommendations
- **External API Integration**:
  - Companies House API (company profiles, officers, financials)
  - Companies House Document API (iXBRL parsing)
  - Google Maps Places API v1 (multi-location search with 70+ queries)
  - OpenAI GPT-5 (business intelligence)
  - Web scraping (LinkedIn, websites)
- **Multi-tenant Architecture**:
  - Complete tenant isolation with row-level security
  - JWT authentication
  - Tenant-specific data and settings
- **Data Management**:
  - PostgreSQL with SQLAlchemy 2.0
  - Redis for caching and sessions
  - Celery for async tasks
  - Alembic for database migrations

### 🏗️ Architecture
- **Frontend**: React 18 + TypeScript + Material-UI
- **Backend**: FastAPI + Python 3.12
- **Database**: PostgreSQL with Row-Level Security
- **Cache**: Redis
- **Infrastructure**: Docker + Docker Compose

### 📚 Initial Documentation
- README.md with quick start guide
- Docker setup documentation
- Environment configuration guide

---

## Version History Summary

| Version | Date | Description |
|---------|------|-------------|
| 2.2.0 | 2025-10-11 | Multiple contact methods, contact detail dialog, known facts system |
| 2.1.0 | 2025-10-09 | Multilingual support, admin portal, Vite migration |
| 2.0.0 | 2025-10-01 | Initial release with CRM module and AI integration |

---

## Upcoming Releases

### [2.3.0] - Planned Q4 2025
- Database-driven AI prompts system
- Lead generation module
- Campaign management
- Email integration

### [2.4.0] - Planned Q1 2026
- Quoting module
- Product catalog
- PDF quote generation
- Accounting integration (Xero, QuickBooks)

### [2.5.0] - Planned Q2 2026
- Advanced reporting
- Sales pipeline management
- Task & activity tracking
- RBAC (Role-Based Access Control)

See [TODO.md](TODO.md) and [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md) for detailed roadmap.

---

[2.2.0]: https://github.com/dje115/ccs-quote-tool-v2/compare/v2.1.0...v2.2.0
[2.1.0]: https://github.com/dje115/ccs-quote-tool-v2/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/dje115/ccs-quote-tool-v2/releases/tag/v2.0.0

