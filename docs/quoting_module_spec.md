# Enhanced Quoting & Order Management – Functional Specification

_Last updated: 2025‑11‑20_

## 1. Vision

Deliver a modern quoting workspace that allows CCS users to:

1. **Author quotes two ways** – AI‑assisted wizard _and_ spreadsheet‑style manual builder.
2. **Control the lifecycle** – draft → review → send → accept/decline → convert to customer order → issue supplier POs.
3. **Collaborate with AI** – prompt editing, QA review, sales narrative generation, customer insight cards.
4. **Reuse assets** – templates, bundles, supplier price feeds, internal product catalogues.
5. **Report & audit** – workflow logs, approval status, margin dashboards, notification hooks.

Benchmark UX against ITQuoter, QuoteWerks, ConnectWise Sell, PandaDoc, Loopio – adopt best components plus CCS specific automation.

## 2. Personas

| Persona | Needs |
| --- | --- |
| **Sales Engineer** | Rapid line item editing, import/export, optional bundles, AI QA check. |
| **Account Manager** | Workflow status, approvals, send email package, duplicate/adapt quotes. |
| **Operations / Procurement** | Convert quote to order, split supplier POs, track receipt/install dates. |
| **Customer** | Clean summary, ability to approve/decline, immediate follow‑up info. |

## 3. Experience Pillars

1. **Dual Authoring Paths**
   - _AI Builder_: improved wizard with preview & per‑section regeneration.
   - _Manual Builder_: Excel-like grid with sections, alternates, margin & tax columns.
2. **Lifecycle & Workflow**
   - Statuses: `draft → internal_review → sent → viewed → accepted → converted` (+ reject/cancel).
   - Actions: duplicate, amend (v2), cancel, resend, convert to order.
   - Approval thresholds based on margin/discount with notification queue.
3. **Order & Procurement Loop**
   - Customer order inherits line items & schedule.
   - Supplier purchase orders per vendor, including PO PDF/email, status updates.
4. **AI Assistants**
   - Prompt editor (existing) + partial regen.
   - AI QA button (consistency, gaps, compliance).
   - Sales copy generator; follow-up email suggestions; customer insight card (Companies House + CRM).
5. **Document & Template System**
   - Multi-part docs: parts list, technical, overview, build, customer summary, internal work order.
   - Template manager with merge fields, versioning, WYSIWYG editor.
6. **Reporting & Portal**
   - Pipeline view, margin analytics, PO spend, AI usage metrics.
   - Customer portal upgrade for approvals (future e-sign).

## 4. Data Model Extensions

### 4.1 Quotes
- Fields: `version_number`, `parent_quote_id`, `manual_mode`, `approval_state`, `sent_at`, `accepted_at`, `rejected_at`, `cancelled_at`, `cancel_reason`.
- Relationships: `workflow_logs`, `customer_order`, `child_versions`.

### 4.2 Quote Items
- Fields: `item_type`, `unit_type`, `unit_cost`, `margin_percent`, `tax_rate`, `supplier_id`, `section_name`, `is_optional`, `is_alternate`, `alternate_group`, `bundle_parent_id`, `metadata`.
- Support sections, alternates, bundles, supplier references.

### 4.3 Workflow Log
- Tracks transitions (from_status → to_status, action, comment, metadata, created_by).

### 4.4 Customer Orders & Supplier POs
- `customer_orders`: status, PO numbers, billing/shipping, payment terms, deposit, metadata.
- `supplier_purchase_orders`: status, supplier_id, expected_date, total_cost, metadata.

### 4.5 Documents/Templates
- `quote_documents` (already exists) – extend metadata to link templates + version history.
- `document_templates` (future) with WYSIWYG content, merge fields, usage type.

## 5. API / Service Changes

### Phase 1 (Manual Builder + Workflow)
1. Quote endpoints:
   - `PATCH /quotes/{id}/items` for bulk grid updates.
   - `POST /quotes/{id}/duplicate`, `/amend`, `/cancel`, `/send`, `/accept`, `/reject`.
   - `GET /quotes/{id}/workflow-log`, `POST /quotes/{id}/status`.
2. Manual builder service:
   - Validations (section ordering, optional bundles).
   - Totals engine (labour vs material, margin, tax).
3. Versioning:
   - `POST /quotes/{id}/versions` to clone quote + docs + items.
4. Order scaffold:
   - `POST /quotes/{id}/convert-to-order` → creates `customer_order` (draft state).

### Phase 2 (Orders + AI QA)
- Order endpoints for status updates, PO creation, PDF generation.
- AI QA endpoint (`POST /quotes/{id}/ai/qa`) – returns checklist + suggestions.
- Sales insight endpoint (customer persona + email text).

### Phase 3 (Templates & Portal)
- Template CRUD, assignments to quote types.
- Document generation pipeline.
- Portal endpoints for approval/decline, comment thread.

## 6. Frontend Changes

1. **Quote Detail Layout**
   - Tabs: Overview, Line Items, Documents, AI Prompt, Workflow, Orders.
   - Context providers for quote + permissions.
2. **Line Item Grid**
   - Spreadsheet component with keyboard nav, inline copy/paste, multi-select.
   - Section headers, optional toggles, alternate groups, margin & tax columns.
   - Autosave + optimistic updates.
3. **Workflow Panel**
   - Status timeline, action buttons, approval prompts, log feed.
4. **Orders Tab**
   - Visual summary of customer order + supplier PO cards.
5. **Manual Quote Entry**
   - New “Manual Quote” button (bypass AI wizard).
   - Quick actions: duplicate line, add bundle, import CSV.
6. **AI Prompt Tab Enhancements**
   - Already added base editor – extend with AI suggestions, preview diffs.
7. **Dashboard**
   - Pipeline metrics, tasks awaiting approval, expiring quotes, order progress.

## 7. AI Integrations

| Feature | Prompt Inputs | Outputs |
| --- | --- | --- |
| Prompt QA | Quote JSON (line items, totals, assumptions) | Checklist (issue + severity + fix) |
| Sales Insight | Customer profile, quote summary, CRM stats | Persona summary, talk tracks, email draft |
| Partial Regeneration | Section-specific instructions, existing context | Replacement content (parts list, doc section) |

Logs recorded via `quote_prompt_history` with `prompt_text`, `variables`, model metadata, success flag.

## 8. Workflow Logic

1. Draft → _Send for Approval (optional)_: triggers approval rules.
2. Approved → _Send to Customer_: sets `sent_at`, email via template.
3. Customer acts: Accept (creates order), Reject (needs reason), Viewed (webhooks).
4. Amend: clone to new version, mark old version `superseded`.
5. Cancellation: set `cancelled_at` + reason; lock editing.

## 9. Reporting & Notifications

- Slack/email hooks for status changes, approvals, order events.
- Dashboards:
  - Quote pipeline by stage.
  - Margin vs target.
  - Supplier PO summary (open/late).
  - AI usage (manual vs AI quotes, QA issues found).

## 10. Security & Permissions

- Roles: Sales, Sales Engineer, Manager, Procurement, Admin.
- Permissions:
  - Manual grid editing requires `quotes:edit`.
  - Approvals require `quotes:approve`.
  - Order conversion & POs require `orders:manage`.
- Audit: store `created_by`, `updated_by` on workflow log, orders, POs.

## 11. Delivery Plan

- **Phase 1**: Manual builder, workflow fields/log, quote duplication/amend/cancel, order scaffold.
- **Phase 2**: Customer order UI + supplier POs, AI QA + sales insight, improved dashboard.
- **Phase 3**: Template manager, document exports, approvals, portal upgrade.
- **Phase 4**: Reporting suite, integration hooks, supplier API connectors.

Each phase includes migrations, backend services, frontend components, Cypress tests, and documentation.



