# Helpdesk Email & WhatsApp Integration Details

## Per-Tenant Email Provider Support

### Supported Email Providers

1. **Google Workspace (Gmail)**
   - Gmail API integration
   - OAuth2 authentication per tenant
   - Real-time push notifications via Gmail API watch
   - Endpoints: users.messages.list, users.messages.get, users.messages.send
   - Attachment handling via Gmail API

2. **Microsoft 365 Business (Outlook)**
   - Microsoft Graph API integration
   - OAuth2 authentication per tenant
   - Real-time webhook subscriptions
   - Endpoints: /me/messages, /users/{id}/messages, /me/sendMail
   - Attachment handling via Graph API

3. **IMAP/POP3 (Generic Email Servers)**
   - Standard IMAP/POP3 protocol support
   - Username/password or OAuth2 authentication
   - Polling-based email retrieval
   - Support for Exchange, Zimbra, Dovecot, etc.

4. **Cloud Email Services**
   - **SendGrid** - Webhook-based inbound email parsing
   - **Mailgun** - Webhook-based inbound email parsing
   - **AWS SES** - Webhook-based inbound email parsing
   - **Postmark** - Webhook-based inbound email parsing

### Email Configuration Schema

```sql
CREATE TABLE tenant_email_config (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    email_provider_type VARCHAR(50) NOT NULL, -- 'gmail', 'microsoft365', 'imap', 'pop3', 'sendgrid', 'mailgun', 'aws_ses', 'none'
    email_provider_config JSONB NOT NULL, -- Provider-specific configuration
    email_ticket_address VARCHAR(255), -- Dedicated email for ticket creation
    email_parser_config JSONB, -- Parsing rules, filters, routing
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Email Provider Configuration Examples

**Gmail Configuration:**
```json
{
  "client_id": "xxx.apps.googleusercontent.com",
  "client_secret": "xxx",
  "refresh_token": "xxx",
  "email_address": "support@tenant.com",
  "watch_enabled": true,
  "watch_expiry_days": 7
}
```

**Microsoft 365 Configuration:**
```json
{
  "client_id": "xxx",
  "client_secret": "xxx",
  "tenant_id": "xxx.onmicrosoft.com",
  "email_address": "support@tenant.com",
  "webhook_url": "https://api.example.com/webhooks/microsoft365",
  "webhook_secret": "xxx"
}
```

**IMAP Configuration:**
```json
{
  "host": "mail.tenant.com",
  "port": 993,
  "username": "support@tenant.com",
  "password": "xxx",
  "use_ssl": true,
  "use_tls": false,
  "folder": "INBOX"
}
```

**SendGrid Configuration:**
```json
{
  "api_key": "xxx",
  "webhook_secret": "xxx",
  "email_address": "support@tenant.com",
  "webhook_url": "https://api.example.com/webhooks/sendgrid"
}
```

## WhatsApp Business API Integration

### WhatsApp Configuration Schema

```sql
ALTER TABLE tenant_helpdesk_config ADD COLUMN whatsapp_enabled BOOLEAN DEFAULT false;
ALTER TABLE tenant_helpdesk_config ADD COLUMN whatsapp_config JSONB;
```

### WhatsApp Configuration Example

```json
{
  "phone_number": "+1234567890",
  "business_account_id": "xxx",
  "api_key": "xxx",
  "api_secret": "xxx",
  "webhook_verify_token": "xxx",
  "webhook_url": "https://api.example.com/webhooks/whatsapp",
  "ticket_creation_enabled": true,
  "notifications_enabled": true,
  "template_messages": [
    {
      "name": "ticket_created",
      "template_id": "xxx",
      "language": "en"
    }
  ]
}
```

### WhatsApp Features

- **Incoming Messages**: Create tickets from WhatsApp messages
- **Outgoing Messages**: Send ticket updates via WhatsApp
- **Template Messages**: Send pre-approved template messages (24-hour window)
- **Media Support**: Send/receive images, documents, audio, video
- **Thread Detection**: Link messages to existing tickets
- **Delivery Status**: Track message delivery and read receipts

### WhatsApp Business API Requirements

- Requires WhatsApp Business Solution Provider (BSP) account
- API endpoints: /messages, /contacts, /media
- Webhook for incoming messages
- Template messages for outbound (requires approval)
- Free-form messages within 24-hour customer window

## Implementation Files

### Email Integration Services

- `backend/app/services/email_ingestion/email_ingestion_base.py` - Base class
- `backend/app/services/email_ingestion/gmail_ingestion_service.py` - Gmail API
- `backend/app/services/email_ingestion/microsoft365_ingestion_service.py` - Microsoft Graph API
- `backend/app/services/email_ingestion/imap_ingestion_service.py` - IMAP/POP3
- `backend/app/services/email_ingestion/cloud_email_ingestion_service.py` - SendGrid/Mailgun/AWS SES
- `backend/app/services/email_ingestion/email_ingestion_factory.py` - Factory pattern
- `backend/app/services/email_parser_service.py` - Common email parsing logic
- `backend/app/api/v1/endpoints/email_webhooks.py` - Webhook endpoints

### WhatsApp Integration Services

- `backend/app/services/whatsapp/whatsapp_integration_service.py` - WhatsApp service
- `backend/app/services/whatsapp/whatsapp_message_parser.py` - Message parsing
- `backend/app/api/v1/endpoints/whatsapp_webhooks.py` - Webhook endpoints
- `backend/app/tasks/whatsapp_tasks.py` - Celery tasks

### Celery Tasks

- `backend/app/tasks/email_ticket_tasks.py` - Email polling tasks
  - Gmail watch renewal (every 7 days)
  - Microsoft 365 webhook management
  - IMAP/POP3 polling (configurable interval)
  - Cloud provider webhook processing

- `backend/app/tasks/whatsapp_tasks.py` - WhatsApp tasks
  - Message queue processing
  - Template message scheduling
  - Delivery status checking

## Next Actions

1. After email/WhatsApp integration → Create ticket sync workers
2. After sync workers → Continue with ticket system foundation

