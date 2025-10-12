# Changelog
All notable changes to the CCS Quote Tool v2 project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

