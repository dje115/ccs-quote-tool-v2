# SLA & Support Contracts System

**Version:** 3.1.0  
**Status:** ✅ Complete  
**Last Updated:** 2025-11-30

---

## 📋 Overview

The SLA (Service Level Agreement) & Support Contracts system provides comprehensive tracking, monitoring, and reporting of service level compliance across the platform. It integrates seamlessly with the helpdesk ticket system, customer management, and support contracts.

---

## 🎯 Key Features

### 1. SLA Policy Management
- **Flexible Policy Configuration**
  - First response time targets (by priority: urgent, high, medium, low)
  - Resolution time targets (by priority)
  - Business hours configuration (start/end times, days of week, timezone)
  - Availability/uptime targets
  - Escalation thresholds (warning and critical percentages)
  - Auto-escalation on breach settings

- **Policy Templates**
  - 8 pre-configured templates for common scenarios:
    - Standard Business Hours (9-5 Mon-Fri)
    - Extended Business Hours (8-6 Mon-Fri)
    - 24/7 Support
    - Premium Support (Gold)
    - Standard Support (Silver)
    - Basic Support (Bronze)
    - Urgent Priority Only
    - Technical Support SLA
  - Quick policy creation from templates
  - Customizable after creation

- **Policy Conditions**
  - Apply to specific ticket priorities
  - Apply to specific ticket types
  - Apply to specific customers
  - Apply to specific contract types
  - Default policy for tenant

### 2. SLA Tracking & Compliance

- **Automatic SLA Application**
  - SLA policies automatically applied to new tickets
  - Policy selection based on ticket priority, type, customer, and contract
  - Real-time SLA target calculation

- **Compliance Monitoring**
  - First response SLA tracking
  - Resolution SLA tracking
  - Real-time compliance checking on ticket updates
  - Breach detection with warning and critical levels
  - Compliance rate calculation

- **Breach Alerts**
  - Automatic breach detection
  - Warning alerts (configurable threshold, default 80%)
  - Critical alerts (configurable threshold, default 95%)
  - Alert acknowledgment system
  - Email notifications to assigned agents and admins

### 3. Auto-Escalation Workflow

When an SLA breach is detected and auto-escalation is enabled:
- **Priority Escalation**: Automatically increases ticket priority
- **Auto-Assignment**: Assigns to admin user if unassigned
- **Status Update**: Changes status to IN_PROGRESS if waiting/open
- **System Comments**: Adds documented comment about breach and actions taken

### 4. Support Contracts

- **Contract Management**
  - Create and manage support contracts
  - Link contracts to SLA policies
  - Track contract metadata (start/end dates, renewal frequency, values)
  - Multi-tenant support
  - Contract linking to opportunities

- **SLA Policy Integration**
  - Contracts can specify SLA policies
  - Tickets from contract customers automatically get contract SLA
  - Contract-level SLA compliance tracking

### 5. Customer & Lead Visibility

- **SLA Breach Indicators**
  - Color-coded flags on Customers and Leads list pages:
    - 🟢 Green: No active SLA breaches
    - 🟠 Orange: Warning-level breaches
    - 🔴 Red: Critical breaches
  - Quick visual identification of customers with SLA issues
  - Sortable by SLA breach status

- **Customer SLA Widget**
  - Displays on customer detail page (Overview tab)
  - Shows overall SLA status
  - Key metrics: total tickets, tickets with SLA, compliance rate
  - Active breach alerts breakdown
  - Recent tickets with SLA status

- **SLA Compliance History**
  - Daily compliance tracking per customer
  - Trend visualization with date range filtering
  - Compliance rate trends over time
  - Breach count tracking

- **Ticket SLA Status**
  - SLA status column in customer tickets tab
  - Visual indicators: Compliant, Breached, No SLA
  - Tooltips showing breach details

### 6. Helpdesk Dashboard Enhancements

- **SLA Metrics Cards**
  - SLA Compliance Rate (color-coded: green ≥95%, orange ≥80%, red <80%)
  - Active Breach Alerts count
  - Tickets with SLA count
  - Breached Tickets count

- **Enhanced Stats**
  - Backend stats endpoint includes SLA metrics
  - Real-time updates via WebSocket

### 7. SLA Analytics Dashboard

- **Visualizations (Chart.js)**
  - Doughnut chart: Compliance rates (First Response vs Resolution)
  - Bar chart: Breach breakdown (Met vs Breached)
  - Line chart: Historical trends over time

- **Tabs**
  - Overview: Key metrics, compliance charts, agent performance
  - Historical Trends: Trend analysis with charts and tables
  - Agent Performance: Individual agent SLA compliance metrics

- **Features**
  - Date range filtering
  - Export buttons (CSV/PDF)
  - Link to Report Builder
  - Link to Policy Management

### 8. Custom Report Builder

- **Report Types**
  - SLA Compliance
  - Customer SLA Summary
  - Agent Performance
  - Breach Analysis
  - Historical Trends

- **Configuration Options**
  - Date range selection
  - Metric selection (checkboxes):
    - Compliance Rate
    - Breach Count
    - Average Response Time
    - Average Resolution Time
    - Agent Performance
    - Customer Breakdown
  - Export formats: CSV, PDF, Excel
  - Preview before export

### 9. Scheduled Reports

- **Automated Reporting**
  - Daily SLA compliance reports
  - Weekly SLA compliance reports
  - Monthly SLA compliance reports
  - Email delivery to tenant admins
  - Celery Beat scheduled tasks

### 10. Customer Health Score Integration

- **SLA Factors in Health Score**
  - 15 points allocated for SLA compliance:
    - 15 points: No SLA breaches
    - 8 points: Warning-level breaches
    - 0 points: Critical breaches
  - Updated health score calculation in CustomerOverviewTab
  - Real-time health score updates based on SLA status

---

## 🗄️ Database Schema

### Tables

**sla_policies**
- Policy configuration (response/resolution hours, business hours, escalation thresholds)
- Conditions (priority, ticket_type, customer_ids, contract_type)
- Status (is_active, is_default)

**sla_compliance_records**
- Historical compliance tracking
- Links to tickets
- Compliance status (met/breached)
- Timestamps

**sla_breach_alerts**
- Breach notifications
- Alert levels (warning, critical)
- Acknowledgment tracking
- Links to tickets/contracts

**support_contracts**
- Contract details
- SLA policy linking (sla_policy_id)
- Contract metadata

**tickets** (enhanced)
- SLA policy linking (sla_policy_id)
- SLA target hours
- SLA breach flags (first_response_breached, resolution_breached)
- SLA breach timestamps
- SLA met timestamps

---

## 🔌 API Endpoints

### SLA Policies
- `GET /api/v1/sla/policies` - List all SLA policies
- `GET /api/v1/sla/policies/{id}` - Get policy details
- `POST /api/v1/sla/policies` - Create new policy
- `PUT /api/v1/sla/policies/{id}` - Update policy
- `DELETE /api/v1/sla/policies/{id}` - Delete policy

### SLA Templates
- `GET /api/v1/sla/templates` - List available templates
- `POST /api/v1/sla/templates/{template_id}/create-policy` - Create policy from template

### SLA Compliance
- `GET /api/v1/sla/compliance` - Get compliance metrics
- `GET /api/v1/sla/tickets/{ticket_id}/compliance` - Get ticket compliance
- `GET /api/v1/sla/customers/{customer_id}/summary` - Get customer SLA summary
- `GET /api/v1/sla/customers/{customer_id}/compliance-history` - Get customer compliance history

### Breach Alerts
- `GET /api/v1/sla/breach-alerts` - List breach alerts
- `POST /api/v1/sla/breach-alerts/{alert_id}/acknowledge` - Acknowledge alert

### Performance & Analytics
- `GET /api/v1/sla/performance/by-agent` - Agent performance metrics
- `GET /api/v1/sla/trends` - Historical trends
- `GET /api/v1/sla/reports/export` - Export reports (CSV/PDF)

### Notification Settings
- `GET /api/v1/sla/notification-rules` - Get notification rules
- `PUT /api/v1/sla/policies/{policy_id}/notification-settings` - Update notification settings

---

## 🎨 Frontend Components

### Pages
- **SLAManagement** (`/sla`) - Policy management and templates
- **SLADashboard** (`/sla/dashboard`) - Analytics and visualizations
- **SLAReportBuilder** (`/sla/reports`) - Custom report generation
- **SupportContracts** (`/support-contracts`) - Support contract management

### Components
- **CustomerSLAWidget** - Customer detail page SLA widget
- **CustomerSLAHistory** - Customer compliance history with trends

### Integration Points
- **CustomerDetail** - Tickets tab with SLA status
- **Customers** - List page with SLA breach flags
- **LeadsCRM** - List page with SLA breach flags
- **Helpdesk** - Dashboard with SLA metrics cards
- **Dashboard** - Main dashboard with SLA widgets

---

## 📊 Usage Guide

### Creating an SLA Policy

1. Navigate to **SLA Management** (`/sla`)
2. Click **"Create from Template"** for quick setup, or **"Create Custom Policy"** for full control
3. Configure:
   - Policy name and description
   - Response and resolution hours (by priority)
   - Business hours (if applicable)
   - Escalation thresholds
   - Conditions (priority, type, customers)
4. Save the policy

### Linking SLA to Support Contracts

1. Navigate to **Support Contracts** (`/support-contracts`)
2. Create or edit a contract
3. Select an SLA policy from the dropdown
4. Save the contract

### Viewing SLA Compliance

1. **Customer Level**: View customer detail page → Overview tab → SLA Widget
2. **Ticket Level**: View customer detail page → Tickets tab → SLA Status column
3. **Dashboard**: Navigate to **SLA Dashboard** (`/sla/dashboard`)
4. **Reports**: Navigate to **SLA Reports** (`/sla/reports`)

### Monitoring SLA Breaches

1. **Visual Indicators**: Check Customers/Leads list pages for colored flags
2. **Dashboard**: View active breach alerts in SLA Dashboard
3. **Email Notifications**: Automatic emails sent on breaches
4. **Alerts Table**: View and acknowledge alerts in SLA Management

### Generating Reports

1. Navigate to **SLA Reports** (`/sla/reports`)
2. Select report type
3. Choose date range
4. Select metrics to include
5. Choose export format
6. Generate preview (optional)
7. Export report

---

## 🔧 Configuration

### Business Hours
Configure in SLA policy:
- Start time (e.g., "09:00")
- End time (e.g., "17:00")
- Business days (e.g., ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
- Timezone (e.g., "Europe/London")

### Escalation Thresholds
- Warning threshold: Default 80% (alert when 80% of SLA time elapsed)
- Critical threshold: Default 95% (alert when 95% of SLA time elapsed)
- Auto-escalate: Enable/disable automatic escalation on breach

### Notification Settings
Configure per policy:
- Warning threshold percentage
- Critical threshold percentage
- Auto-escalate on breach (boolean)
- Email notifications sent automatically

---

## 📈 Metrics & KPIs

### Compliance Metrics
- **First Response Compliance Rate**: % of tickets meeting first response SLA
- **Resolution Compliance Rate**: % of tickets meeting resolution SLA
- **Overall Compliance Rate**: Combined compliance rate

### Breach Metrics
- **Total Breaches**: Count of all SLA breaches
- **Critical Breaches**: Count of critical-level breaches
- **Warning Breaches**: Count of warning-level breaches
- **Active Breach Alerts**: Unacknowledged breach alerts

### Performance Metrics
- **Average Response Time**: Average time to first response
- **Average Resolution Time**: Average time to resolution
- **Agent Performance**: Compliance rates by agent/team

---

## 🚀 Future Enhancements

### Planned Features
- SLA forecasting and predictive analytics
- Custom SLA policy conditions builder
- SLA performance benchmarking
- Customer portal SLA visibility
- SLA-based ticket routing
- Advanced notification rules (SMS, Slack, etc.)
- SLA contract templates
- Multi-level SLA policies (tiered support)

---

## 📝 Notes

- SLA policies are tenant-specific (multi-tenant isolation)
- SLA tracking is automatic - no manual intervention required
- Breach alerts are real-time via WebSocket
- Historical data is preserved for trend analysis
- Reports can be exported for external analysis
- All SLA data is included in customer health scoring

---

## 🔗 Related Documentation

- [Helpdesk System](./HELPDESK_EMAIL_WHATSAPP_INTEGRATIONS.md)
- [Customer Management](./README.md#customer-management)
- [Dashboard Analytics](./README.md#analytics)

---

**Last Updated:** 2025-11-30  
**Version:** 3.1.0

