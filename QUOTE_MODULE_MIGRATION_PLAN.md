# Quote Module Migration Plan - v1 to v2

## Overview
Comprehensive migration of the quote module from v1 to v2 as a multi-tenant world-beating quotation tool.

## Key Components to Migrate

### 1. Supplier Configuration System
**Status**: Needs Migration

#### Models Required:
- `Supplier` - Supplier information with categories
- `SupplierCategory` - Categories for organizing suppliers
- `SupplierPricing` - Cached pricing from suppliers
- `Product` - Enhanced with supplier relationships (partially exists)

#### Features:
- Supplier management (CRUD)
- Supplier categories (WiFi, Cabling, CCTV, Door Entry, Network Equipment)
- Preferred supplier marking
- Supplier website/pricing URL tracking
- API key storage for supplier APIs

#### Database Schema:
```sql
CREATE TABLE supplier_categories (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);

CREATE TABLE suppliers (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    category_id VARCHAR(36) NOT NULL,
    name VARCHAR(100) NOT NULL,
    website VARCHAR(200),
    pricing_url VARCHAR(500),
    api_key VARCHAR(200),
    is_preferred BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES supplier_categories(id) ON DELETE CASCADE
);

CREATE TABLE supplier_pricing (
    id VARCHAR(36) PRIMARY KEY,
    supplier_id VARCHAR(36) NOT NULL,
    product_name VARCHAR(200) NOT NULL,
    product_code VARCHAR(100),
    price NUMERIC(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'GBP',
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE CASCADE
);
```

### 2. Web Pricing Scraper Service
**Status**: Needs Migration

#### Features:
- Real-time pricing scraping from supplier websites
- Support for multiple suppliers (Ubiquiti, Cisco, Connectix, etc.)
- Price extraction with multiple selector strategies
- Caching mechanism (24-hour cache)
- Fallback to known pricing database

#### Implementation:
- `WebPricingScraper` service class
- Supplier-specific scraping rules
- BeautifulSoup for HTML parsing
- Rate limiting and error handling

### 3. Pricing Service
**Status**: Needs Migration

#### Features:
- Product price lookup with caching
- Multi-source pricing (database, web scraper, AI estimates)
- Supplier preference handling
- Pricing refresh automation
- Pricing import from spreadsheets (AI-powered)

#### Implementation:
- `PricingService` class
- Integration with WebPricingScraper
- Database caching layer
- Batch pricing updates

### 4. AI Quote Analysis
**Status**: Partially Migrated (needs enhancement)

#### Current v2 Implementation:
- Basic quote analysis exists in `QuoteAnalysisService`
- Uses AI prompts from database
- Calculates travel costs

#### Missing Features from v1:
- Clarification questions workflow
- Brand preferences integration
- Supplier information in prompts
- Consistency checking integration
- Enhanced product recommendations with real pricing

#### Enhancements Needed:
- Add clarification questions endpoint
- Integrate supplier preferences into AI prompts
- Add consistency context to AI analysis
- Enhance product recommendations with supplier pricing

### 5. Quote Consistency Manager
**Status**: Needs Migration

#### Features:
- Historical quote comparison
- Consistency scoring (0-100)
- Variance detection
- Recommendations generation
- Standard pricing templates
- Similar quote finding algorithm

#### Implementation:
- `QuoteConsistencyService` class
- Similarity matching algorithm
- Statistical analysis (mean, median, variance)
- Template application system

### 6. Quote Workflows
**Status**: Needs Enhancement

#### Required Workflows:
1. **Quote Creation Workflow:**
   - Initial quote creation
   - AI analysis trigger
   - Clarification questions
   - Quote refinement
   - Final pricing calculation

2. **Quote Approval Workflow:**
   - Draft → Review → Approved/Rejected
   - Version tracking
   - Approval history
   - Email notifications

3. **Quote Versioning:**
   - Create quote versions
   - Compare versions
   - Revert to previous version

### 7. Document Generation
**Status**: Needs Migration

#### Features:
- Word document generation (.docx)
- PDF generation
- Template-based formatting
- Variable substitution
- Professional quote formatting

#### Implementation:
- `DocumentGenerator` service
- python-docx for Word generation
- ReportLab or WeasyPrint for PDF
- Template system integration

### 8. Pricing Import System
**Status**: Needs Migration

#### Features:
- Excel/CSV import
- AI-powered extraction (handles any format)
- Product name standardization
- Category auto-classification
- Duplicate detection
- Bulk import with validation

#### Implementation:
- `PricingImportService` class
- Integration with AIPricingExtractor
- pandas for spreadsheet reading
- Validation and error handling

## Migration Priority

### Phase 1: Core Infrastructure (High Priority)
1. ✅ Supplier models and database schema
2. ✅ Supplier management API endpoints
3. ✅ Web Pricing Scraper service
4. ✅ Pricing Service with caching

### Phase 2: AI & Analysis (High Priority)
1. ✅ Enhanced Quote Analysis Service
2. ✅ Quote Consistency Manager
3. ✅ Clarification questions workflow
4. ✅ Supplier integration in AI prompts

### Phase 3: Workflows & Features (Medium Priority)
1. ✅ Quote approval workflow
2. ✅ Quote versioning
3. ✅ Document generation
4. ✅ Pricing import system

### Phase 4: Frontend Integration (Medium Priority)
1. ✅ Supplier management UI
2. ✅ Enhanced quote builder
3. ✅ Quote consistency dashboard
4. ✅ Pricing import interface

## Technical Considerations

### Multi-Tenant Isolation
- All models must include `tenant_id`
- Supplier categories are tenant-specific
- Pricing data is tenant-isolated
- API keys stored per tenant

### Performance
- Pricing caching (24-hour TTL)
- Batch pricing updates
- Async pricing scraping
- Database indexing on supplier/product lookups

### Scalability
- Celery tasks for background pricing updates
- Redis caching for frequently accessed pricing
- Rate limiting on web scraping
- Queue system for bulk imports

## Database Migrations Required

1. Create supplier_categories table
2. Create suppliers table
3. Create supplier_pricing table
4. Add supplier_id to products table
5. Add pricing_source to quote_items table
6. Create quote_versions table (if not exists)
7. Create quote_approvals table

## API Endpoints Required

### Supplier Management
- `GET /api/v1/suppliers/` - List suppliers
- `POST /api/v1/suppliers/` - Create supplier
- `GET /api/v1/suppliers/{id}` - Get supplier
- `PUT /api/v1/suppliers/{id}` - Update supplier
- `DELETE /api/v1/suppliers/{id}` - Delete supplier
- `GET /api/v1/suppliers/categories/` - List categories
- `POST /api/v1/suppliers/{id}/refresh-pricing` - Refresh pricing

### Pricing
- `GET /api/v1/pricing/products/{product_name}` - Get product price
- `POST /api/v1/pricing/import` - Import pricing from file
- `GET /api/v1/pricing/suppliers/summary` - Pricing summary by supplier

### Quote Workflows
- `POST /api/v1/quotes/{id}/clarifications` - Submit clarification answers
- `POST /api/v1/quotes/{id}/approve` - Approve quote
- `POST /api/v1/quotes/{id}/reject` - Reject quote
- `GET /api/v1/quotes/{id}/versions` - List quote versions
- `POST /api/v1/quotes/{id}/create-version` - Create new version
- `GET /api/v1/quotes/{id}/consistency` - Get consistency analysis

### Documents
- `GET /api/v1/quotes/{id}/document` - Generate quote document
- `GET /api/v1/quotes/{id}/document/pdf` - Generate PDF

## Testing Requirements

1. Unit tests for all services
2. Integration tests for workflows
3. Multi-tenant isolation tests
4. Pricing accuracy tests
5. AI analysis quality tests
6. Document generation tests

## Success Criteria

1. ✅ All v1 features migrated and enhanced
2. ✅ Multi-tenant isolation working correctly
3. ✅ Real-time pricing integration functional
4. ✅ AI analysis quality matches or exceeds v1
5. ✅ Quote workflows complete and tested
6. ✅ Document generation produces professional outputs
7. ✅ Performance meets or exceeds v1 benchmarks


