# Quoting Module – Implementation TODO

_Status legend:_
- [ ] Pending
- [~] In Progress
- [x] Done

## Phase 1 – Manual Builder & Workflow Foundation

### Data Model / Backend
- [x] Create migration `add_quote_workflow_and_orders.sql`
  - [x] Quotes: add workflow + version fields (`version_number`, `parent_quote_id`, `manual_mode`, `approval_state`, timestamps, cancel_reason).
  - [x] Quote items: extend with manual builder fields (`item_type`, `unit_type`, `unit_cost`, `supplier_id`, `bundle_parent_id`, etc).
  - [x] Workflow log table (`quote_workflow_log`).
  - [x] Customer orders & supplier purchase orders tables (scaffold).
- [x] Update SQLAlchemy models
  - [x] `Quote`, `QuoteItem`, `QuoteWorkflowLog`, `CustomerOrder`, `SupplierPurchaseOrder`.
  - [x] Ensure relationships (parent versions, workflow logs, orders).
- [ ] Services
  - [x] Manual quote builder service (line item validation, totals, sections, optional/bundle logic).
  - [x] Workflow service (status transitions, approvals stub, log insertions).
  - [ ] Quote duplication/amend/cancel endpoints.
  - [x] Autosave/bulk line item update endpoint.
- [ ] Unit tests for builder + workflow services.

### Frontend
- [x] Redesign `QuoteDetail` layout (tabs: Overview, Line Items, Documents, AI Prompt, Workflow, Orders).
- [~] Implement spreadsheet-style Line Item grid
- [x] Workflow tab with status timeline, approval indicators, action buttons, log feed.
- [x] Manual quote entry flow
  - [x] “Create Manual Quote” button + onboarding modal.
  - [ ] Duplicate/Amend/Cancel actions in UI.
- [x] Basic Orders tab stub (display message until Phase 2).
- [x] QuoteCheckAI assistant (GPT-5 Mini review modal) on manual builder tab.
- [ ] Cypress tests for manual editing + workflow transitions.

## Phase 2 – Orders & AI Enhancements
- [ ] Convert quote to customer order UI + API.
- [ ] Supplier PO creation screen, status tracking, PDF/email.
- [ ] AI QA endpoint + UI (issues list, suggestions, severity).
- [ ] Sales insight panel with persona summary & email generator.
- [ ] Dashboard widgets (pipeline, approvals pending, expiring quotes).

## Phase 3 – Templates & Portal
- [ ] Template manager (CRUD, versioning, assignment to quote types).
- [ ] Document generation pipeline (customer summary PDF, internal work order).
- [ ] Customer portal upgrade (view, approve/reject, comments, e-sign placeholder).
- [ ] Approval workflow UI + notifications.

## Phase 4 – Reporting & Integrations
- [ ] Reporting suite (pipeline, margin, PO spend, AI usage).
- [ ] Webhooks / API connectors (ERP, PSA, supplier ordering).
- [ ] Optional supplier API integrations (future).

---

Keep this document updated as tasks are completed. Large items should be broken into GitHub issues / tickets with technical acceptance criteria.

