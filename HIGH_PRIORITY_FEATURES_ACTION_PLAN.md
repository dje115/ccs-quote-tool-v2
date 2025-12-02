# High-Priority Features - Action Plan

**Focus Areas:** Enhanced Multi-Part Quoting, Contract-to-Quote, Helpdesk Completion  
**Target Completion:** 3-4 months  
**Last Updated:** 2025-11-24

---

## 🎯 Feature 1: Enhanced Multi-Part Quoting System

**Status:** 20% Complete  
**Priority:** HIGH  
**Estimated Effort:** 8-12 weeks

### Phase 1: Database & Backend Foundation (Week 1-2)

#### Task 1.1: Verify & Enhance Database Schema
- [ ] **Verify quote_documents table exists**
  - Check: `backend/app/models/quote_documents.py` ✅ (already exists)
  - Verify migration has been run
  - **File:** `backend/migrations/verify_quote_documents.sql` (create if needed)

- [ ] **Add missing fields to Quote model**
  - Add `tier_type` field (single, 3-tier)
  - Add `ai_generation_data` JSON field
  - Add `quote_documents` relationship
  - **File:** `backend/app/models/quotes.py`
  - **Migration:** `backend/migrations/add_quote_tier_fields.sql`

- [ ] **Create database migration**
  ```sql
  -- Add tier_type to quotes
  ALTER TABLE quotes ADD COLUMN IF NOT EXISTS tier_type VARCHAR(20) DEFAULT 'single';
  ALTER TABLE quotes ADD COLUMN IF NOT EXISTS ai_generation_data JSONB;
  
  -- Verify quote_documents table structure
  -- Ensure indexes exist
  CREATE INDEX IF NOT EXISTS idx_quote_documents_quote_type ON quote_documents(quote_id, document_type);
  ```

#### Task 1.2: Enhance Quote Builder Service
- [ ] **Extend QuoteBuilderService for multi-part documents**
  - Generate all 4 document types (parts_list, technical, overview, build)
  - Create QuoteDocument records for each type
  - **File:** `backend/app/services/quote_builder_service.py`
  - **Method:** `_create_documents()` (new)

- [ ] **Add document generation logic**
  - Parts list: Extract from quote items
  - Technical: Generate from AI analysis
  - Overview: Customer-friendly summary
  - Build: Internal instructions
  - **File:** `backend/app/services/quote_builder_service.py`
  - **Methods:** 
    - `_generate_parts_list_document()`
    - `_generate_technical_document()`
    - `_generate_overview_document()`
    - `_generate_build_document()`

#### Task 1.3: Create Quote AI Generation Service
- [ ] **Create/Enhance QuoteAIGenerationService**
  - Universal quote generation prompt
  - Industry detection from tenant context
  - 1-tier or 3-tier generation logic
  - **File:** `backend/app/services/quote_ai_generation_service.py`
  - **Method:** `generate_quote_documents()`

- [ ] **Add QUOTE_GENERATION prompt category**
  - Create system prompt for quote generation
  - Support tenant-specific overrides
  - **File:** `backend/scripts/seed_ai_prompts.py`
  - **Category:** `QUOTE_GENERATION`

#### Task 1.4: Create Quote Tier Service
- [ ] **Create QuoteTierService**
  - Generate 3-tier quotes (Basic/Standard/Premium)
  - Tier comparison logic
  - **File:** `backend/app/services/quote_tier_service.py` (new)
  - **Methods:**
    - `generate_tiered_quotes()`
    - `compare_tiers()`

### Phase 2: API Endpoints (Week 3-4)

#### Task 2.1: Quote Generation Endpoints
- [ ] **POST /api/v1/quotes/generate**
  - Generate quote with AI
  - Create all 4 document types
  - **File:** `backend/app/api/v1/endpoints/quotes.py`
  - **Method:** `generate_quote()`

- [ ] **POST /api/v1/quotes/{id}/regenerate-document/{type}**
  - Regenerate specific document type
  - Create new version
  - **File:** `backend/app/api/v1/endpoints/quotes.py`
  - **Method:** `regenerate_document()`

#### Task 2.2: Document Management Endpoints
- [ ] **Create quote_documents.py endpoint file**
  - `GET /api/v1/quotes/{id}/documents` - Get all documents
  - `GET /api/v1/quotes/{id}/documents/{type}` - Get specific document
  - `PUT /api/v1/quotes/{id}/documents/{type}` - Update document
  - `POST /api/v1/quotes/{id}/documents/{type}/version` - Create version
  - `GET /api/v1/quotes/{id}/documents/{type}/versions` - Get version history
  - **File:** `backend/app/api/v1/endpoints/quote_documents.py` (new)

#### Task 2.3: Document Versioning Service
- [ ] **Create QuoteVersioningService**
  - Auto-version on save
  - Version history with diffs
  - Rollback capability
  - **File:** `backend/app/services/quote_versioning_service.py` (new or enhance)
  - **Methods:**
    - `create_version()`
    - `get_version_history()`
    - `rollback_to_version()`

### Phase 3: Pricing Integration (Week 5-6)

#### Task 3.1: Enhance Quote Pricing Service
- [ ] **Integrate with SupplierPricingService**
  - Pull real-time pricing from supplier_pricing table
  - Fallback to product catalog
  - **File:** `backend/app/services/quote_pricing_service.py` (new or enhance)
  - **Dependencies:** `supplier_pricing_service.py`

- [ ] **Add price history tracking**
  - Track price changes over time
  - Show price history in UI
  - **File:** `backend/app/models/supplier_pricing.py` (may need enhancement)

#### Task 3.2: Day Rate Integration
- [ ] **Integrate PricingConfigService**
  - Pull day rates from pricing_config
  - Role-based calculations (engineer, technician, PM)
  - Skill level multipliers
  - **File:** `backend/app/services/quote_pricing_service.py`
  - **Dependencies:** `pricing_config_service.py`

#### Task 3.3: Own Products Database
- [ ] **Add "Own Products" to Suppliers**
  - Extend supplier model to support own products
  - Support hire rates, hosting rates, services
  - **File:** `backend/app/models/supplier.py`
  - **File:** `backend/app/models/product.py`

- [ ] **Create migration for own products**
  - Add `is_own_product` flag
  - Add product categories for own products
  - **File:** `backend/migrations/add_own_products.sql`

### Phase 4: Frontend Components (Week 7-10)

#### Task 4.1: Quote Builder Wizard
- [ ] **Create QuoteBuilderWizard component**
  - Step 1: Customer/Project Selection
  - Step 2: Requirements Description (plain English)
  - Step 3: AI Generation (with progress)
  - Step 4: Review & Edit Documents
  - Step 5: Pricing Review
  - Step 6: Finalize & Send
  - **File:** `frontend/src/components/QuoteBuilderWizard.tsx` (new)

- [ ] **Update QuoteNew page**
  - Use QuoteBuilderWizard
  - Remove old form logic
  - **File:** `frontend/src/pages/QuoteNew.tsx` (rewrite)

#### Task 4.2: Document Editors
- [ ] **Create QuoteDocumentEditor component**
  - Rich text editor (use react-quill or similar)
  - Auto-save functionality
  - Version history sidebar
  - **File:** `frontend/src/components/QuoteDocumentEditor.tsx` (new)

- [ ] **Create document-specific components**
  - `QuotePartsList.tsx` - Parts list editor
  - `QuoteTechnicalDoc.tsx` - Technical document editor
  - `QuoteOverviewDoc.tsx` - Overview document editor
  - `QuoteBuildDoc.tsx` - Build document editor
  - **Files:** `frontend/src/components/` (new)

#### Task 4.3: Document Viewer
- [ ] **Create QuoteDocumentViewer component**
  - View all 4 document types
  - PDF export button
  - Print-friendly layouts
  - **File:** `frontend/src/components/QuoteDocumentViewer.tsx` (new or enhance)

#### Task 4.4: Pricing Integration UI
- [ ] **Create QuotePricingPanel component**
  - Real-time price updates
  - Price history display
  - Markup configuration
  - **File:** `frontend/src/components/QuotePricingPanel.tsx` (new)

- [ ] **Add to QuoteDetail page**
  - Integrate pricing panel
  - Show price history
  - **File:** `frontend/src/pages/QuoteDetail.tsx` (enhance)

### Phase 5: Testing & Refinement (Week 11-12)

#### Task 5.1: Backend Testing
- [ ] **Unit tests for services**
  - QuoteBuilderService tests
  - QuoteAIGenerationService tests
  - QuoteTierService tests
  - **File:** `backend/tests/unit/services/test_quote_builder.py` (new)

- [ ] **API endpoint tests**
  - Document generation endpoints
  - Versioning endpoints
  - **File:** `backend/tests/integration/test_quote_documents.py` (new)

#### Task 5.2: Frontend Testing
- [ ] **Component tests**
  - QuoteBuilderWizard tests
  - DocumentEditor tests
  - **File:** `frontend/src/components/__tests__/` (new)

- [ ] **E2E tests**
  - Full quote generation flow
  - Document editing flow
  - **File:** `frontend/tests/e2e/quote-generation.spec.ts` (new)

---

## 🎯 Feature 2: Contract-to-Quote Enhancement

**Status:** 40% Complete  
**Priority:** HIGH  
**Estimated Effort:** 3-4 weeks

### Phase 1: Enhance Contract Quote Service (Week 1)

#### Task 1.1: Enhance Proposal Generation
- [ ] **Improve generate_quote_from_contract method**
  - Currently only generates basic quote
  - Generate full proposal document
  - Include contract terms and conditions
  - **File:** `backend/app/services/contract_quote_service.py`
  - **Method:** `generate_quote_from_contract()` (enhance)

- [ ] **Add proposal document generation**
  - Create proposal-specific document
  - Include contract details
  - **File:** `backend/app/services/contract_quote_service.py`
  - **Method:** `_generate_proposal_document()` (new)

#### Task 1.2: Improve Contract Data Mapping
- [ ] **Enhance _build_customer_request_from_contract**
  - Better mapping of all contract fields
  - Support for all contract types
  - Handle SLA requirements properly
  - **File:** `backend/app/services/contract_quote_service.py`
  - **Method:** `_build_customer_request_from_contract()` (enhance)

- [ ] **Add contract type-specific mapping**
  - Managed services mapping
  - Software license mapping
  - SaaS subscription mapping
  - **File:** `backend/app/services/contract_quote_service.py`
  - **Method:** `_map_contract_type_to_quote_data()` (new)

#### Task 1.3: Contract Template Integration
- [ ] **Use contract templates for quote generation**
  - Load template with JSON placeholders
  - Fill placeholders from contract data
  - **File:** `backend/app/services/contract_quote_service.py`
  - **Method:** `_apply_contract_template()` (new)

- [ ] **Map quote documents to contract template sections**
  - Link quote sections to contract sections
  - **File:** `backend/app/services/contract_quote_service.py`
  - **Method:** `_map_quote_to_contract_sections()` (new)

### Phase 2: Quote-to-Contract Workflow (Week 2)

#### Task 2.1: Create Contract Generator Service
- [ ] **Create/Enhance ContractGeneratorService**
  - Convert approved quotes to contracts
  - Auto-populate contract from quote data
  - Link quote and contract in database
  - **File:** `backend/app/services/contract_generator_service.py` (new or enhance)
  - **Method:** `generate_contract_from_quote()`

- [ ] **Map quote data to contract fields**
  - Quote items → Contract services
  - Quote pricing → Contract pricing
  - Quote terms → Contract terms
  - **File:** `backend/app/services/contract_generator_service.py`
  - **Method:** `_map_quote_to_contract_data()` (new)

#### Task 2.2: Contract Template Application
- [ ] **Apply contract template to quote**
  - Use EnhancedContractTemplate
  - Fill JSON placeholders from quote
  - Generate contract content
  - **File:** `backend/app/services/contract_generator_service.py`
  - **Method:** `_apply_template_to_quote()` (new)

### Phase 3: API Endpoints (Week 3)

#### Task 3.1: Contract-to-Quote Endpoints
- [ ] **POST /api/v1/contracts/{id}/generate-quote**
  - Generate quote from contract
  - Create all quote documents
  - **File:** `backend/app/api/v1/endpoints/contracts.py`
  - **Method:** `generate_quote_from_contract()`

- [ ] **GET /api/v1/contracts/{id}/quote**
  - Get associated quote if exists
  - **File:** `backend/app/api/v1/endpoints/contracts.py`
  - **Method:** `get_contract_quote()`

#### Task 3.2: Quote-to-Contract Endpoints
- [ ] **POST /api/v1/quotes/{id}/generate-contract**
  - Generate contract from quote
  - Apply template if specified
  - **File:** `backend/app/api/v1/endpoints/quotes.py`
  - **Method:** `generate_contract_from_quote()`

- [ ] **GET /api/v1/quotes/{id}/contract**
  - Get associated contract if exists
  - **File:** `backend/app/api/v1/endpoints/quotes.py`
  - **Method:** `get_quote_contract()`

### Phase 4: Frontend Integration (Week 4)

#### Task 4.1: Contract Detail Page Enhancements
- [ ] **Add "Generate Quote" button**
  - Button in ContractDetail page
  - Opens quote generation dialog
  - **File:** `frontend/src/pages/ContractDetail.tsx` (enhance)

- [ ] **Show associated quote**
  - Display quote status and link
  - Show quote number
  - **File:** `frontend/src/pages/ContractDetail.tsx` (enhance)

- [ ] **Quote generation dialog**
  - Select quote type
  - Preview contract data mapping
  - **File:** `frontend/src/components/ContractToQuoteDialog.tsx` (new)

#### Task 4.2: Quote Detail Page Enhancements
- [ ] **Add "Generate Contract" button**
  - Button in QuoteDetail page
  - Only show for approved quotes
  - **File:** `frontend/src/pages/QuoteDetail.tsx` (enhance)

- [ ] **Show associated contract**
  - Display contract status and link
  - Show contract number
  - **File:** `frontend/src/pages/QuoteDetail.tsx` (enhance)

- [ ] **Contract generation dialog**
  - Select contract template
  - Preview quote data mapping
  - **File:** `frontend/src/components/QuoteToContractDialog.tsx` (new)

#### Task 4.3: Quote Builder Wizard Integration
- [ ] **Add contract selection step**
  - Step 0: Select contract (optional)
  - Pre-fill quote data from contract
  - **File:** `frontend/src/components/QuoteBuilderWizard.tsx` (enhance)

---

## 🎯 Feature 3: Helpdesk Completion

**Status:** 70% Complete  
**Priority:** HIGH  
**Estimated Effort:** 2-3 weeks

### Phase 1: Email Ticket Ingestion (Week 1)

#### Task 1.1: Email Service Setup
- [ ] **Create EmailTicketService**
  - IMAP/POP3 integration
  - Email-to-ticket conversion
  - Attachment handling
  - **File:** `backend/app/services/email_ticket_service.py` (new)
  - **Methods:**
    - `connect_to_email_server()`
    - `fetch_emails()`
    - `convert_email_to_ticket()`

- [ ] **Per-tenant email configuration**
  - Store email credentials per tenant
  - Support multiple email providers
  - **File:** `backend/app/models/tenant.py` (may need extension)
  - **Migration:** `backend/migrations/add_email_config.sql`

#### Task 1.2: Email Parser Service
- [ ] **Create EmailParserService**
  - Extract ticket details from email
  - Identify customer from email address
  - Parse email body and subject
  - **File:** `backend/app/services/email_parser_service.py` (new)
  - **Methods:**
    - `parse_email_subject()`
    - `parse_email_body()`
    - `identify_customer()`

#### Task 1.3: Celery Task for Email Processing
- [ ] **Create email processing task**
  - Periodic task to check emails
  - Background processing
  - **File:** `backend/app/tasks/email_ticket_tasks.py` (new)
  - **Task:** `process_email_tickets()`

- [ ] **Add to Celery Beat schedule**
  - Run every 5-15 minutes
  - **File:** `backend/app/core/celery_app.py` (enhance)

#### Task 1.4: API Endpoints
- [ ] **POST /api/v1/helpdesk/email/configure**
  - Configure email for ticket ingestion
  - **File:** `backend/app/api/v1/endpoints/helpdesk.py` (enhance)

- [ ] **POST /api/v1/helpdesk/email/test**
  - Test email connection
  - **File:** `backend/app/api/v1/endpoints/helpdesk.py` (enhance)

### Phase 2: WhatsApp Integration (Week 2)

#### Task 2.1: WhatsApp Service
- [ ] **Create WhatsAppService**
  - WhatsApp Business API integration
  - Message-to-ticket conversion
  - Two-way communication
  - **File:** `backend/app/services/whatsapp_service.py` (new)
  - **Methods:**
    - `send_message()`
    - `receive_message()`
    - `convert_message_to_ticket()`

- [ ] **WhatsApp webhook handler**
  - Handle incoming messages
  - Process message events
  - **File:** `backend/app/api/v1/endpoints/whatsapp.py` (new)
  - **Endpoint:** `POST /api/v1/whatsapp/webhook`

#### Task 2.2: WhatsApp Configuration
- [ ] **Per-tenant WhatsApp configuration**
  - Store WhatsApp API credentials
  - Phone number management
  - **File:** `backend/app/models/tenant.py` (may need extension)
  - **Migration:** `backend/migrations/add_whatsapp_config.sql`

#### Task 2.3: Frontend Integration
- [ ] **WhatsApp configuration UI**
  - Settings page for WhatsApp
  - Test connection button
  - **File:** `frontend/src/pages/Settings.tsx` (enhance)

- [ ] **WhatsApp in ticket detail**
  - Send WhatsApp from ticket
  - Show WhatsApp conversation
  - **File:** `frontend/src/pages/TicketDetail.tsx` (enhance)

### Phase 3: Advanced SLA & Knowledge Base (Week 3)

#### Task 3.1: SLA Intelligence Enhancements
- [ ] **Enhance SLAIntelligenceService**
  - Real-time SLA monitoring
  - Predictive breach alerts
  - SLA performance analytics
  - **File:** `backend/app/services/sla_intelligence_service.py` (enhance)
  - **Methods:**
    - `monitor_sla_compliance()`
    - `predict_breach_risk()`
    - `get_sla_analytics()`

- [ ] **SLA automation workflows**
  - Auto-escalation rules
  - SLA-based routing
  - **File:** `backend/app/services/sla_service.py` (enhance)

#### Task 3.2: Knowledge Base System
- [ ] **Create Knowledge Base models**
  - Article model
  - Category model
  - **File:** `backend/app/models/knowledge_base.py` (new)

- [ ] **Create KnowledgeBaseService**
  - Article CRUD
  - Search functionality
  - AI-powered suggestions
  - **File:** `backend/app/services/knowledge_base_service.py` (new)

- [ ] **Ticket-to-KB linking**
  - Suggest KB articles for tickets
  - Auto-link resolved tickets to KB
  - **File:** `backend/app/services/helpdesk_ai_service.py` (enhance)

#### Task 3.3: Ticket Automation Workflows
- [ ] **Create WorkflowService**
  - Rule-based automation
  - Conditional actions
  - Multi-step workflows
  - **File:** `backend/app/services/workflow_service.py` (new)

- [ ] **Predefined workflows**
  - Auto-assignment rules
  - Auto-categorization
  - Auto-escalation
  - **File:** `backend/app/services/helpdesk_service.py` (enhance)

#### Task 3.4: Frontend for Knowledge Base
- [ ] **Knowledge Base UI**
  - Article list and search
  - Article editor
  - **File:** `frontend/src/pages/KnowledgeBase.tsx` (new)

- [ ] **KB suggestions in tickets**
  - Show suggested articles
  - Link articles to tickets
  - **File:** `frontend/src/pages/TicketDetail.tsx` (enhance)

---

## 📋 Implementation Checklist

### Week 1-2: Enhanced Multi-Part Quoting - Phase 1
- [ ] Database schema verification and enhancements
- [ ] Quote Builder Service enhancements
- [ ] Quote AI Generation Service
- [ ] Quote Tier Service

### Week 3-4: Enhanced Multi-Part Quoting - Phase 2
- [ ] API endpoints for quote generation
- [ ] Document management endpoints
- [ ] Versioning service

### Week 5-6: Enhanced Multi-Part Quoting - Phase 3
- [ ] Pricing integration
- [ ] Day rate integration
- [ ] Own products database

### Week 7-10: Enhanced Multi-Part Quoting - Phase 4
- [ ] Quote Builder Wizard
- [ ] Document editors
- [ ] Document viewer
- [ ] Pricing UI

### Week 11-12: Enhanced Multi-Part Quoting - Phase 5
- [ ] Testing
- [ ] Refinement

### Week 1: Contract-to-Quote - Phase 1
- [ ] Enhance Contract Quote Service
- [ ] Improve contract data mapping
- [ ] Contract template integration

### Week 2: Contract-to-Quote - Phase 2
- [ ] Contract Generator Service
- [ ] Quote-to-contract workflow

### Week 3: Contract-to-Quote - Phase 3
- [ ] API endpoints

### Week 4: Contract-to-Quote - Phase 4
- [ ] Frontend integration

### Week 1: Helpdesk - Phase 1
- [ ] Email ticket ingestion

### Week 2: Helpdesk - Phase 2
- [ ] WhatsApp integration

### Week 3: Helpdesk - Phase 3
- [ ] Advanced SLA
- [ ] Knowledge Base
- [ ] Automation workflows

---

## 🚀 Quick Start Guide

### For Enhanced Multi-Part Quoting:
1. Start with database schema verification
2. Enhance QuoteBuilderService
3. Create API endpoints
4. Build frontend components

### For Contract-to-Quote:
1. Enhance ContractQuoteService
2. Create ContractGeneratorService
3. Add API endpoints
4. Update frontend pages

### For Helpdesk:
1. Set up email service
2. Add WhatsApp integration
3. Enhance SLA intelligence
4. Build knowledge base

---

## 📊 Success Metrics

### Enhanced Multi-Part Quoting:
- ✅ Generate 4 document types from single quote
- ✅ AI generates quotes in < 30 seconds
- ✅ 3-tier quotes available when applicable
- ✅ Document versioning working

### Contract-to-Quote:
- ✅ Generate quote from contract in < 10 seconds
- ✅ Convert quote to contract seamlessly
- ✅ All contract fields mapped correctly

### Helpdesk:
- ✅ Email tickets auto-created
- ✅ WhatsApp integration working
- ✅ SLA intelligence providing insights
- ✅ Knowledge base reducing ticket volume

---

**Next Steps:** Start with Enhanced Multi-Part Quoting Phase 1, then Contract-to-Quote, then Helpdesk completion.

