# CCS Quote Tool v2 - TODO List
## Comprehensive Task List for Development

**Last Updated**: October 11, 2025  
**Current Version**: 2.2.0  
**Target Version**: 2.3.0

---

## 🎯 **HIGH PRIORITY - Next Sprint (v2.3.0)**

### **1. Database-Driven AI Prompts System** 🔥
**Status**: Not Started  
**Priority**: Critical  
**Estimated Effort**: 3-5 days

#### Backend Tasks:
- [ ] Create `ai_prompts` table in database
  - Fields: id, name, category, prompt_text, model, temperature, max_tokens, version, is_active, tenant_id, created_at, updated_at
  - Categories: customer_analysis, lead_generation, financial_analysis, competitor_analysis, website_analysis
- [ ] Create SQLAlchemy model for `AIPrompt`
- [ ] Create API endpoints for prompt management:
  - `GET /api/v1/prompts/` - List all prompts (with filtering by category)
  - `GET /api/v1/prompts/{id}` - Get specific prompt
  - `POST /api/v1/prompts/` - Create new prompt
  - `PUT /api/v1/prompts/{id}` - Update prompt
  - `DELETE /api/v1/prompts/{id}` - Delete prompt
  - `POST /api/v1/prompts/{id}/test` - Test prompt with sample data
- [ ] Migrate existing prompts from code to database:
  - `AIAnalysisService._perform_ai_analysis()` comprehensive prompt
  - `AIAnalysisService._calculate_lead_score()` prompt
  - Website analysis prompt
  - LinkedIn analysis prompt
  - Financial analysis prompt
- [ ] Update `AIAnalysisService` to fetch prompts from database
- [ ] Add prompt versioning system
- [ ] Add prompt rollback functionality
- [ ] Add tenant-specific prompt overrides

#### Frontend Tasks:
- [ ] Create Admin Portal "AI Prompts" page:
  - List all prompts with category filter
  - Search and filter functionality
  - Inline editing with syntax highlighting
  - Test prompt with sample data
  - View prompt history/versions
  - Create/duplicate prompts
- [ ] Add prompt editor component (Monaco or CodeMirror)
- [ ] Add prompt testing dialog with sample data input
- [ ] Add prompt variable documentation/hints
- [ ] Create CRM Settings section for tenant prompt customization

#### Migration Tasks:
- [ ] Create Alembic migration for `ai_prompts` table
- [ ] Create seed script to populate initial prompts
- [ ] Test migration on development database
- [ ] Document prompt variable system

---

### **2. Lead Generation Module** 🎯
**Status**: Not Started  
**Priority**: High  
**Estimated Effort**: 7-10 days

#### Database Schema:
- [ ] Create `lead_campaigns` table
  - Fields: id, name, description, status, target_type, target_criteria, created_by, tenant_id, created_at, updated_at
- [ ] Create `lead_campaign_targets` table (many-to-many with addresses/competitors)
  - Fields: id, campaign_id, target_type, target_id, status, notes, created_at
- [ ] Create `lead_campaign_messages` table
  - Fields: id, campaign_id, subject, body_template, channel, sent_at, status, created_at
- [ ] Create SQLAlchemy models

#### Backend API:
- [ ] Campaign Management Endpoints:
  - `GET /api/v1/campaigns/` - List campaigns
  - `POST /api/v1/campaigns/` - Create campaign
  - `GET /api/v1/campaigns/{id}` - Get campaign details
  - `PUT /api/v1/campaigns/{id}` - Update campaign
  - `DELETE /api/v1/campaigns/{id}` - Delete campaign
  - `POST /api/v1/campaigns/{id}/start` - Start campaign
  - `POST /api/v1/campaigns/{id}/pause` - Pause campaign
  - `GET /api/v1/campaigns/{id}/stats` - Get campaign statistics
- [ ] Lead Target Endpoints:
  - `POST /api/v1/campaigns/{id}/targets` - Add targets to campaign
  - `DELETE /api/v1/campaigns/{id}/targets/{target_id}` - Remove target
  - `GET /api/v1/campaigns/{id}/targets` - List campaign targets
- [ ] Message Template Endpoints:
  - `GET /api/v1/campaigns/templates` - List templates
  - `POST /api/v1/campaigns/templates` - Create template
- [ ] Integration with existing address/competitor "Add to Lead Campaign" buttons

#### Frontend:
- [ ] Lead Campaigns Dashboard:
  - Campaign list with status indicators
  - Create new campaign wizard
  - Campaign analytics cards
- [ ] Campaign Builder:
  - Select target type (addresses/competitors/custom)
  - Filter and select targets
  - Create message templates with variables
  - Schedule sending
- [ ] Campaign Detail Page:
  - View all targets
  - Track delivery status
  - View engagement metrics
  - Edit campaign settings
- [ ] Update Customer Detail page:
  - Connect "Add to Lead Campaign" buttons to campaign system
  - Show which campaigns an address/competitor is in
- [ ] Email Template Editor:
  - Rich text editor
  - Variable insertion (company name, address, etc.)
  - Preview functionality

#### Integration:
- [ ] Email service integration (SendGrid/Mailgun/AWS SES)
- [ ] Tracking pixels for email opens
- [ ] Link tracking for click-through rates
- [ ] Unsubscribe management

---

### **3. Address Management Enhancements** 📍
**Status**: Partially Complete  
**Priority**: Medium  
**Estimated Effort**: 2-3 days

#### Tasks:
- [ ] Create address management UI at top of customer page:
  - Display confirmed addresses with type badges
  - Drag-and-drop to reorder addresses
  - Quick actions: Edit, Delete, Set as Primary
- [ ] Add address types:
  - Primary (main office)
  - Billing address
  - Delivery address
  - Warehouse/storage
  - Custom types
- [ ] Manual address addition:
  - Address form dialog
  - Postcode lookup integration
  - Validate against Google Maps
- [ ] Address editing:
  - Edit existing addresses
  - Change address type
  - Add internal notes
- [ ] Backend endpoints:
  - `POST /api/v1/customers/{id}/addresses` - Add address manually
  - `PUT /api/v1/customers/{id}/addresses/{address_id}` - Update address
  - `DELETE /api/v1/customers/{id}/addresses/{address_id}` - Delete address
  - `PUT /api/v1/customers/{id}/addresses/{address_id}/type` - Set address type
  - `PUT /api/v1/customers/{id}/addresses/{address_id}/primary` - Set as primary

---

## 📊 **MEDIUM PRIORITY - Future Sprints**

### **4. Quoting Module** 💰
**Status**: Not Started  
**Priority**: Medium  
**Estimated Effort**: 10-15 days

#### Database Schema:
- [ ] Create `products` table (product/service catalog)
- [ ] Create `quotes` table
- [ ] Create `quote_items` table (line items)
- [ ] Create `quote_templates` table
- [ ] Create `pricing_rules` table

#### Features:
- [ ] Product/service catalog management
- [ ] Dynamic quote builder
- [ ] Pricing rules engine (volume discounts, bundles)
- [ ] Quote templates with variables
- [ ] PDF quote generation
- [ ] Email quote to customer
- [ ] Quote approval workflow
- [ ] Quote versioning
- [ ] Convert quote to invoice
- [ ] Quote analytics (conversion rates, avg value)

#### Backend API:
- [ ] Product CRUD endpoints
- [ ] Quote CRUD endpoints
- [ ] Quote PDF generation endpoint
- [ ] Quote approval endpoints
- [ ] Quote statistics endpoints

#### Frontend:
- [ ] Product catalog page
- [ ] Quote builder interface
- [ ] Quote list and search
- [ ] Quote detail view
- [ ] Quote PDF preview
- [ ] Email quote dialog
- [ ] Quote approval interface

---

### **5. Accounting Integration** 💳
**Status**: Not Started  
**Priority**: Medium  
**Estimated Effort**: 7-10 days

#### Xero Integration:
- [ ] OAuth2 authentication flow
- [ ] Sync customers to Xero contacts
- [ ] Push invoices from quotes
- [ ] Pull payment status
- [ ] Sync chart of accounts
- [ ] Tax rate mapping

#### QuickBooks Integration:
- [ ] OAuth2 authentication flow
- [ ] Customer sync
- [ ] Invoice creation
- [ ] Payment tracking

#### Generic Accounting API:
- [ ] Abstract accounting interface
- [ ] Support for multiple providers
- [ ] Webhook handlers for status updates

---

### **6. Email Marketing & Communication** 📧
**Status**: Not Started  
**Priority**: Medium  
**Estimated Effort**: 5-7 days

#### Features:
- [ ] Email template library
- [ ] Merge field system
- [ ] Scheduled email sending
- [ ] Email tracking (opens, clicks)
- [ ] Unsubscribe management
- [ ] Email campaign analytics
- [ ] GDPR compliance (consent tracking)
- [ ] Email service provider integration (SendGrid/Mailgun)

---

### **7. Advanced Reporting & Analytics** 📈
**Status**: Not Started  
**Priority**: Medium  
**Estimated Effort**: 7-10 days

#### Features:
- [ ] Sales pipeline reporting
- [ ] Lead conversion funnel
- [ ] Financial performance dashboards
- [ ] Activity tracking reports
- [ ] Custom report builder
- [ ] Export to Excel/CSV/PDF
- [ ] Scheduled report delivery
- [ ] Data visualization library (Chart.js/D3.js)

---

## 🔧 **TECHNICAL DEBT & IMPROVEMENTS**

### **Code Quality**
- [ ] Add comprehensive unit tests (target: 80% coverage)
  - [ ] Backend service layer tests
  - [ ] Frontend component tests
  - [ ] Integration tests
- [ ] Add E2E tests (Playwright/Cypress)
- [ ] Implement proper error handling across all endpoints
- [ ] Add request/response logging
- [ ] Implement rate limiting on API endpoints
- [ ] Add API request validation with better error messages

### **Performance Optimization**
- [ ] Implement Redis caching for frequently accessed data
  - [ ] Customer data cache
  - [ ] AI analysis results cache (30-day TTL)
  - [ ] Company House data cache
- [ ] Add database indexes for slow queries
- [ ] Implement pagination for all list endpoints
- [ ] Lazy loading for customer detail tabs
- [ ] Image optimization and CDN integration
- [ ] Implement data export to reduce large payloads

### **Security Enhancements**
- [ ] Implement RBAC (Role-Based Access Control)
  - [ ] Define roles (Admin, Manager, User, Viewer)
  - [ ] Permission system per resource
  - [ ] UI permission-based rendering
- [ ] Add audit logging for sensitive operations
- [ ] Implement API key rotation system
- [ ] Add 2FA (Two-Factor Authentication)
- [ ] Security headers (CSP, HSTS, etc.)
- [ ] Input sanitization and XSS prevention
- [ ] SQL injection prevention audit
- [ ] Secrets management (HashiCorp Vault/AWS Secrets Manager)

### **DevOps & Infrastructure**
- [ ] Set up CI/CD pipeline (GitHub Actions/GitLab CI)
  - [ ] Automated testing on push
  - [ ] Docker image building
  - [ ] Deployment automation
- [ ] Add Kubernetes deployment manifests
- [ ] Implement health check endpoints
- [ ] Set up monitoring and alerting (Prometheus/Grafana)
- [ ] Implement log aggregation (ELK stack)
- [ ] Database backup automation
- [ ] Disaster recovery plan
- [ ] Staging environment setup
- [ ] Production deployment documentation

---

## 🐛 **KNOWN ISSUES & BUGS**

### **High Priority**
- [x] ~~Contact notes not displaying~~ - FIXED v2.2.0
- [x] ~~Known facts not saving/clearing properly~~ - FIXED v2.2.0
- [x] ~~Arkel Computer Services causing React error~~ - FIXED v2.2.0 (deleted)
- [ ] AI analysis sometimes times out on large companies
- [ ] Google Maps API quota can be exceeded with multiple searches

### **Medium Priority**
- [ ] Tab state occasionally resets on page refresh (localStorage issue)
- [ ] Some directors have address as object instead of string
- [ ] Health score calculation needs refinement
- [ ] Lead score weights need adjustment based on real data

### **Low Priority**
- [ ] Contact dialog loses focus when clicking outside
- [ ] Some UI elements not fully responsive on mobile
- [ ] Loading spinners inconsistent across pages

---

## 🎨 **UI/UX IMPROVEMENTS**

### **CRM Interface**
- [ ] Add keyboard shortcuts for common actions
- [ ] Implement command palette (Cmd+K)
- [ ] Add dark mode theme
- [ ] Improve mobile responsiveness
- [ ] Add customer activity timeline
- [ ] Implement quick search (global search bar)
- [ ] Add bulk operations for customers
- [ ] Implement drag-and-drop file uploads
- [ ] Add customer comparison view

### **Admin Portal**
- [ ] Add dashboard widgets customization
- [ ] Implement tenant activity logs
- [ ] Add system health monitoring page
- [ ] Create tenant onboarding wizard
- [ ] Add bulk user import functionality

---

## 🚀 **FUTURE FEATURES (v3.0+)**

### **Sales Pipeline Management**
- Kanban board for deal stages
- Custom pipeline stages
- Deal probability scoring
- Forecasting and projections
- Win/loss analysis

### **Task & Activity Management**
- Task assignment and tracking
- Calendar integration
- Email integration
- Call logging
- Meeting notes
- Follow-up reminders

### **Document Management**
- File storage and organization
- Version control
- Document templates
- E-signature integration (DocuSign)
- Contract management

### **Mobile App**
- React Native mobile app
- Offline mode
- Push notifications
- Quick actions
- Mobile-optimized forms

### **Advanced AI Features**
- Sentiment analysis on communications
- Predictive lead scoring improvements
- Churn risk prediction
- Recommended next actions
- AI-powered email drafting
- Voice-to-text note taking

### **Collaboration Features**
- Team chat/messaging
- @mentions and notifications
- Shared notes and comments
- Customer ownership and permissions
- Activity feed

### **Marketplace & Integrations**
- Plugin/extension system
- Zapier integration
- Microsoft 365 integration
- Google Workspace integration
- Slack notifications
- Calendar sync (Google/Outlook)

---

## 📝 **DOCUMENTATION TASKS**

- [ ] API documentation (expand Swagger/OpenAPI)
- [ ] User manual (end-user documentation)
- [ ] Admin guide (tenant management)
- [ ] Developer guide (contribution guidelines)
- [ ] Architecture decision records (ADRs)
- [ ] Deployment guides for different cloud providers:
  - [ ] AWS deployment
  - [ ] Azure deployment
  - [ ] Google Cloud deployment
  - [ ] DigitalOcean deployment
- [ ] Video tutorials
- [ ] FAQ section
- [ ] Troubleshooting guide

---

## 🎯 **SPRINT PLANNING**

### **Sprint 1 (2 weeks)**: Database-Driven AI Prompts
- Implement AI prompts table and models
- Create admin UI for prompt management
- Migrate existing prompts
- Test and document

### **Sprint 2 (2 weeks)**: Lead Generation Foundation
- Database schema for campaigns
- Basic campaign CRUD
- Target selection from addresses/competitors
- Simple email template system

### **Sprint 3 (2 weeks)**: Lead Generation Completion
- Email service integration
- Campaign analytics
- Tracking and reporting
- Testing and refinement

### **Sprint 4 (2 weeks)**: Address Management & Quoting Prep
- Complete address management UI
- Manual address addition
- Begin quoting module schema
- Product catalog foundation

### **Sprint 5 (2 weeks)**: Quoting Module
- Quote builder interface
- PDF generation
- Quote workflow
- Basic pricing rules

---

## ✅ **COMPLETED FEATURES (v2.2.0)**

- [x] Multi-tenant architecture with row-level security
- [x] JWT authentication with Argon2 password hashing
- [x] Admin portal for tenant management
- [x] User management system
- [x] API key management (global and tenant-level)
- [x] Customer CRM module with tabbed interface
- [x] AI-powered company analysis (GPT-5)
- [x] Companies House integration (company data, officers, financials)
- [x] Companies House Document API (iXBRL parsing)
- [x] Google Maps multi-location search
- [x] "Not this business" address exclusion
- [x] Multi-year financial analysis with trends
- [x] Lead scoring system
- [x] Health score calculation
- [x] Director information display
- [x] Competitor identification
- [x] Risk factor analysis
- [x] Opportunity recommendations
- [x] Website and LinkedIn analysis
- [x] Contact management with multiple emails/phones per contact
- [x] Contact detail dialog with full information display
- [x] Known facts system for AI context
- [x] Company registration confirmation workflow
- [x] Multilingual support (10 languages)
- [x] Tab state persistence (localStorage)
- [x] Vite build system for frontend

---

## 📊 **METRICS & GOALS**

### **Quality Metrics**
- Test Coverage: Target 80% (Current: ~20%)
- Code Quality: A grade on CodeClimate
- Performance: <2s page load, <500ms API response
- Uptime: 99.9% availability

### **Feature Completion**
- v2.3.0: Database AI Prompts + Lead Generation
- v2.4.0: Quoting Module
- v2.5.0: Accounting Integration
- v3.0.0: Advanced features (pipeline, tasks, mobile)

---

**Last Updated**: October 11, 2025  
**Maintained By**: Development Team  
**Review Cycle**: Weekly
