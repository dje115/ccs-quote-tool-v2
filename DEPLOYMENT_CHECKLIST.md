# Deployment Checklist

**Date:** 2025-11-24  
**Status:** Ready for Deployment

---

## 📋 **PRE-DEPLOYMENT CHECKLIST**

### 1. Database Migrations ✅

Run these migrations in order:

```bash
# 1. Quote documents and versioning
psql -d your_database -f backend/migrations/add_quote_documents_tables.sql

# 2. Own products support
psql -d your_database -f backend/migrations/add_own_products_support.sql

# 3. Knowledge base ticket links
psql -d your_database -f backend/migrations/add_knowledge_base_ticket_links.sql

# 4. Knowledge base status column
psql -d your_database -f backend/migrations/update_knowledge_base_status.sql
```

**Note:** The helpdesk tables migration (`add_helpdesk_tables.sql`) should already be run.

### 2. Environment Variables

Ensure these are set:

```bash
# Database
DATABASE_URL=postgresql://user:password@host:5432/database

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# AI Provider (for quote generation)
OPENAI_API_KEY=your_key_here
# or
ANTHROPIC_API_KEY=your_key_here
```

### 3. Celery Configuration

Verify Celery Beat schedule is configured:
- Email processing task runs every 5 minutes
- Check `backend/app/core/celery_app.py` for schedule

### 4. Dependencies

Install any new Python packages:
```bash
pip install httpx  # For WhatsApp service
```

---

## 🔧 **CONFIGURATION REQUIRED**

### Email Ticket Ingestion

For each tenant that wants email-to-ticket:

1. Configure email settings in tenant metadata:
```json
{
  "email_settings": {
    "imap_server": "imap.gmail.com",
    "imap_port": 993,
    "email": "support@yourcompany.com",
    "password": "app_password",
    "folder": "INBOX"
  }
}
```

2. Verify Celery Beat is running:
```bash
celery -A app.core.celery_app beat --loglevel=info
```

### WhatsApp Integration

1. Set up WhatsApp Business API:
   - Create app in Facebook Developer Console
   - Get Phone Number ID and Access Token
   - Set up webhook URL: `https://yourdomain.com/api/v1/whatsapp/webhook`

2. Configure tenant metadata:
```json
{
  "whatsapp_config": {
    "phone_number_id": "your_phone_number_id",
    "access_token": "your_access_token",
    "verify_token": "your_verify_token",
    "app_secret": "your_app_secret"
  }
}
```

3. Verify webhook:
   - Facebook will send GET request to verify
   - Ensure `/api/v1/whatsapp/webhook` endpoint is accessible

### Knowledge Base

1. Create initial articles via API or database
2. Set up categories as needed
3. Articles will be automatically suggested for tickets

---

## 🧪 **TESTING CHECKLIST**

### Backend API Testing

```bash
# 1. Test quote generation
curl -X POST http://localhost:8000/api/v1/quotes/generate \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "customer_id",
    "customer_request": "Install Cat6 cabling for office",
    "quote_title": "Office Cabling Quote"
  }'

# 2. Test document retrieval
curl http://localhost:8000/api/v1/quotes/{quote_id}/documents

# 3. Test contract-to-quote
curl -X POST http://localhost:8000/api/v1/contracts/{contract_id}/generate-quote

# 4. Test quote-to-contract
curl -X POST http://localhost:8000/api/v1/quotes/{quote_id}/generate-contract

# 5. Test WhatsApp webhook (verification)
curl "http://localhost:8000/api/v1/whatsapp/webhook?hub.mode=subscribe&hub.verify_token=your_token&hub.challenge=test"
```

### Frontend Testing

1. **Quote Generation:**
   - Navigate to `/quotes/new`
   - Use QuoteBuilderWizard
   - Verify all 4 documents are generated

2. **Document Editing:**
   - Open a quote
   - Go to Documents tab
   - Edit each document type
   - Verify versioning works

3. **Contract-to-Quote:**
   - Open a contract
   - Click "Generate Quote from Contract"
   - Verify quote is created with contract data

4. **Quote-to-Contract:**
   - Open an accepted quote
   - Click "Generate Contract"
   - Verify contract is created

---

## 🚨 **KNOWN LIMITATIONS**

1. **PDF Export:** Currently placeholder - needs implementation
2. **Email Sending:** Quote sending via email needs integration
3. **WhatsApp:** Requires WhatsApp Business API setup
4. **Workflow Rules:** Currently hardcoded - needs UI for configuration

---

## 📊 **MONITORING**

### Key Metrics to Monitor

1. **Quote Generation:**
   - Success rate
   - Average generation time
   - AI API usage/costs

2. **Email Processing:**
   - Tickets created from emails
   - Processing errors
   - Celery task execution

3. **WhatsApp:**
   - Messages received
   - Tickets created
   - Webhook errors

4. **SLA Compliance:**
   - Breach rate
   - Average resolution time
   - Risk alerts triggered

---

## 🔄 **ROLLBACK PLAN**

If issues occur:

1. **Database Rollback:**
   - Migrations are idempotent (use `IF NOT EXISTS`)
   - Can safely re-run migrations

2. **Code Rollback:**
   - All changes are in separate files
   - Can disable new endpoints by commenting out router includes

3. **Feature Flags:**
   - Can disable features via tenant metadata
   - Email processing can be disabled per tenant
   - WhatsApp can be disabled per tenant

---

## ✅ **POST-DEPLOYMENT VERIFICATION**

1. ✅ All migrations run successfully
2. ✅ Celery workers running
3. ✅ Celery Beat running
4. ✅ API endpoints accessible
5. ✅ Frontend components loading
6. ✅ Test quote generation works
7. ✅ Test document editing works
8. ✅ Test contract-to-quote works
9. ✅ Test email processing (if configured)
10. ✅ Test WhatsApp webhook (if configured)

---

## 📞 **SUPPORT**

If issues arise:
1. Check application logs
2. Check Celery logs
3. Check database logs
4. Review error messages in API responses
5. Check tenant metadata configuration

---

**Deployment Status:** ✅ Ready  
**Last Updated:** 2025-11-24

