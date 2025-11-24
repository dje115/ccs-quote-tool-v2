# CCS Quote Tool v2 - Next Agent TODO List
**Version**: 3.1.0  
**Last Updated**: 2025-11-24  
**Status**: Ready for continuation

---

## ⚡ Session Hand-off (2025-11-24)

### ✅ Completed
- Automated **System Tenant** creation on startup (configurable env vars + admin seeding) so rebuilds always include required API keys.
- Reloaded **Action Suggestions** prompt (60k tokens, references quote/ticket summaries) and flushed Redis to ensure backend picks it up.
- Rebuilt entire Docker stack from scratch and confirmed backend timeline API imports fixed (no more HTTP 500).

### 🎯 Immediate Follow-ups
1. **Action Suggestions Missing Quote/Ticket Context**
   - [ ] Inspect Celery worker logs for `[ACTION PROMPT - SYSTEM]` to confirm updated prompt text is used.
   - [ ] Verify `ActivityService.generate_action_suggestions()` attaches `quote_summary` & `ticket_summary` to payload.
   - [ ] Refresh suggestions in UI and confirm OpenAI response references relevant quotes/tickets.
   - [ ] If responses still stale, ensure Redis cache is cleared again and prompt text matches DB record `f63f0d4f-4608-4fd4-8af5-b4ac6f6d6e28`.
2. **Customer Timeline & AI Suggestion Layout**
   - [ ] Refactor `CustomerTimeline.tsx` to remove nested `<p>` warnings (use `Typography component="span/div"` or `Box` wrappers).
   - [ ] Update layout so timeline spans full width at bottom and AI suggestion cards show 3 wider columns per user request.
   - [ ] Resize manual quote builder inputs (description, part number, supplier, qty, unit cost) to avoid scrollbars and support requested character lengths.
3. **System Tenant Verification & Tests**
   - [ ] After next rebuild, run `SELECT slug, plan FROM tenants WHERE plan='system';` to confirm auto-seeding works.
   - [ ] Ensure `system-admin@ccs.local` user exists and has SUPER_ADMIN role + permissions.
   - [ ] Document steps for rotating system API keys via admin portal once tenant is present.
4. **Testing Checklist**
   - [ ] `docker compose restart backend celery-worker` → tail logs for prompt payload + OpenAI responses.
   - [ ] `npm run dev` (frontend) → confirm console free of Grid + DOM nesting warnings.
   - [ ] Trigger manual quote build & AI suggestion refresh flows end-to-end to validate UX + data quality.

---

## 🎯 **IMMEDIATE PRIORITIES**

### **1. Complete Async SQLAlchemy Migration** 🔥
**Status**: ~95% Complete - MAJOR MILESTONE ACHIEVED! 🎉  
**Priority**: Critical (P0.2)  
**Estimated Effort**: Remaining work minimal

#### **Completed Endpoints** ✅ (This Session):
- **`quotes.py`** - All endpoints migrated (15+ endpoints)
- **`helpdesk.py`** - Completed remaining sync operations
- **`provider_keys.py`** - 6 endpoints migrated
- **`pricing_config.py`** - 8 endpoints migrated
- **`customer_portal.py`** - 7 endpoints migrated
- **`campaigns.py`** - 11 endpoints migrated
- **`ai_prompts.py`** - 10 endpoints migrated
- **`planning.py`** - 18 endpoints migrated
- **Cleanup**: Removed unused `Session` imports from all endpoint files

#### **Previously Completed** ✅:
- `suppliers.py`: All 15 endpoints - COMPLETE
- `products.py`: All 10 endpoints - COMPLETE
- `dashboard.py`: `ai_dashboard_query`, `change_customer_status`
- `leads.py`: `get_lead`, `update_lead`, `delete_lead`, `create_leads_from_competitors`
- `contacts.py`: All endpoints already async
- `users.py`: `list_users`, `create_user`, `update_user`, `delete_user`
- `customers.py`: All endpoints - COMPLETE
- `auth.py`: 2 endpoints - COMPLETE
- `tenants.py`: 6 endpoints - COMPLETE
- `pricing_import.py`: 2 endpoints - COMPLETE
- `building_analysis.py`: 2 endpoints - COMPLETE
- `product_search.py`: 2 endpoints - COMPLETE
- `revenue.py`: 4 endpoints - COMPLETE
- `customer_portal_access.py`: 4 endpoints - COMPLETE
- `contract_renewals.py`: 5 endpoints - COMPLETE
- `reporting.py`: 5 endpoints - COMPLETE
- `sla.py`: 6 endpoints - COMPLETE
- `support_contracts.py`: 7 endpoints - COMPLETE
- `dynamic_pricing.py`: 6 endpoints - COMPLETE

#### **Remaining Work** (Minimal):
- Verify all endpoints are using `AsyncSession` (audit complete)
- Only `websocket.py` uses sync query (acceptable for WebSocket auth)
- All high-traffic endpoints are now fully async! 🚀

#### **Migration Pattern**:
```python
# OLD (Sync):
from sqlalchemy.orm import Session
from app.core.database import get_db

@router.get("/")
async def endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = db.query(Model).filter(...).all()
    return result

# NEW (Async):
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_async_db

@router.get("/")
async def endpoint(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    from sqlalchemy import select
    stmt = select(Model).where(...)
    result = await db.execute(stmt)
    return result.scalars().all()
```

#### **Migration Complete** ✅:
All endpoint files have been migrated to use `AsyncSession`. The async migration is essentially complete with all high-traffic endpoints now fully async and non-blocking.

---

### **2. Complete Security Fixes** 🔒
**Status**: 6/9 Fixed, 3/9 Partial  
**Priority**: Critical (P0.1-P0.11)

#### **Completed** ✅:
- P0.3: Refresh Token Rotation - Fixed (uses Pydantic body model)
- P0.4: Hard-coded Super-Admin Credentials - Fixed (env vars)
- P0.7: AI Analysis Service Missing DB/Tenant - Fixed
- P0.8: WebSocket Authentication Token Leak - Fixed (HttpOnly cookies prioritized)
- P0.9: Resource Lifecycle Leaks - Fixed (proper shutdown hooks)
- P0.10: Quote Endpoints Block on Heavy Work - Fixed (Celery offloading)
- P0.11: Authentication State Security - Fixed (API validation)

#### **Partially Fixed** ⚠️:
- **P0.1: Multi-Tenant Isolation Bypass** - Needs comprehensive endpoint audit
  - Current: JWT-based tenant derivation implemented
  - Current: Headers validated against JWT
  - Current: RLS configured
  - **TODO**: Audit ALL endpoints to ensure `get_current_tenant()` is used
  - **TODO**: Verify RLS policies are working correctly
  - **TODO**: Test cross-tenant data access prevention

- **P0.2: Async/Sync SQLAlchemy Mismatch** - In progress (~35% complete)
  - See section 1 above

#### **Remaining Work**:
- Complete async migration (see section 1)
- Comprehensive tenant isolation audit
- Security testing and penetration testing

---

### **3. Remove Hardcoded AI Prompt Fallbacks** 🤖
**Status**: 90% Complete  
**Priority**: High  
**Estimated Effort**: 1-2 days

#### **Completed** ✅:
- Removed hardcoded fallbacks from:
  - `ai_analysis_service.py` - `COMPETITOR_ANALYSIS`, `CUSTOMER_ANALYSIS`
  - `activity_service.py` - `ACTIVITY_ENHANCEMENT`, `ACTION_SUGGESTIONS`
  - `translation_service.py` - `TRANSLATION`

#### **Remaining Work**:
- [ ] Verify all services raise `ValueError` when prompts not found (no fallbacks)
- [ ] Test with empty database to ensure proper error handling
- [ ] Update seed script to ensure all prompts are seeded
- [ ] Document prompt requirements in API docs

---

## 📋 **MEDIUM PRIORITY TASKS**

### **4. Helpdesk System Enhancements** 🎧
**Status**: Not Started  
**Priority**: Medium  
**Estimated Effort**: 12-16 weeks

#### **Immediate Tasks**:
- [ ] Fix AI prompt for helpdesk ticket enhancement (use database prompts)
- [ ] Add ticket assignment UI (assign to users)
- [ ] Add status/priority update UI
- [ ] Implement email notifications for ticket updates
- [ ] Add ticket comment threading
- [ ] Add ticket attachment support

#### **Future Tasks** (see `PHASE_5_HELPDESK_DETAILED.md`):
- Per-tenant email provider support (Google Workspace, Microsoft 365, IMAP/POP3)
- WhatsApp Business API integration
- PSA/RMM platform integrations
- Email ticket ingestion
- Ticket synchronization

---

### **5. Lead Generation Module** 🎯
**Status**: Not Started  
**Priority**: Medium  
**Estimated Effort**: 7-10 days

#### **Database Schema**:
- [ ] Create `lead_campaigns` table
- [ ] Create `lead_campaign_targets` table
- [ ] Create `lead_campaign_messages` table
- [ ] Create SQLAlchemy models

#### **Backend API**:
- [ ] Campaign Management Endpoints
- [ ] Lead Target Endpoints
- [ ] Message Template Endpoints

#### **Frontend**:
- [ ] Lead Campaigns Dashboard
- [ ] Campaign Builder
- [ ] Campaign Detail Page
- [ ] Email Template Editor

---

### **6. Address Management UI** 📍
**Status**: Partially Complete  
**Priority**: Medium  
**Estimated Effort**: 2-3 days

#### **Tasks**:
- [ ] Create address management UI at top of customer page
- [ ] Add drag-and-drop reordering
- [ ] Add address types (Primary, Billing, Delivery, etc.)
- [ ] Manual address addition form
- [ ] Address editing functionality
- [ ] Backend endpoints for address management

---

## 🔧 **TECHNICAL DEBT**

### **7. Testing** 🧪
**Status**: Not Started  
**Priority**: Medium  
**Estimated Effort**: 10-15 days

#### **Tasks**:
- [ ] Add comprehensive integration tests:
  - Multi-tenant isolation tests
  - Authentication flow tests
  - WebSocket messaging tests
  - Async endpoint tests
- [ ] Add unit tests for services (target: 80% coverage)
- [ ] Add E2E tests (Playwright/Cypress)
- [ ] Set up CI/CD pipeline with automated testing

---

### **8. Performance Optimization** ⚡
**Status**: Not Started  
**Priority**: Medium  
**Estimated Effort**: 5-7 days

#### **Tasks**:
- [ ] Implement Redis caching for frequently accessed data
- [ ] Add database indexes for slow queries
- [ ] Implement pagination for all list endpoints
- [ ] Lazy loading for customer detail tabs
- [ ] Image optimization and CDN integration

---

### **9. Documentation** 📚
**Status**: Partial  
**Priority**: Low  
**Estimated Effort**: 3-5 days

#### **Tasks**:
- [ ] Expand API documentation (Swagger/OpenAPI)
- [ ] User manual (end-user documentation)
- [ ] Admin guide (tenant management)
- [ ] Developer guide (contribution guidelines)
- [ ] Architecture decision records (ADRs)

---

## 📊 **PROGRESS SUMMARY**

### **Version 3.0.0 Changes**:
- ✅ **MAJOR**: Completed async SQLAlchemy migration (~95% complete)
  - Migrated 60+ endpoints across 6 files (quotes.py, helpdesk.py, provider_keys.py, pricing_config.py, customer_portal.py, campaigns.py, ai_prompts.py, planning.py)
  - All high-traffic endpoints now fully async and non-blocking
  - Cleaned up unused `Session` imports from all endpoint files
- ✅ Fixed remaining sync operations in quotes.py and helpdesk.py
- ✅ **MAJOR**: Centralized version management system
  - Created `VERSION_MANAGEMENT.md` documentation
  - Created `INFRASTRUCTURE.md` with port numbers
  - Updated all version numbers to 3.0.0 across all components
  - Single source of truth: `VERSION` file
- ✅ Updated version number to 3.0.0
- ✅ Ready to push to GitHub and rebuild Docker

### **Next Version Target (3.1.0)**:
- Complete final async migration verification
- Comprehensive tenant isolation audit
- Helpdesk enhancements (AI prompt fix, assignment UI, notifications)
- Performance optimization (Redis caching, database indexes)

---

## 🚀 **QUICK START GUIDE**

### **To Continue Async Migration**:
1. Start with `backend/app/api/v1/endpoints/suppliers.py`
2. Replace `Session = Depends(get_db)` with `AsyncSession = Depends(get_async_db)`
3. Replace `db.query()` with `select()` and `await db.execute()`
4. Replace `.all()` with `.scalars().all()`
5. Test each endpoint after migration
6. Update TODO.md when complete

### **To Continue Security Fixes**:
1. Review `backend/app/core/middleware.py` for tenant isolation
2. Audit all endpoints for `get_current_tenant()` usage
3. Test cross-tenant data access prevention
4. Document findings in `FIXES_STATUS_REPORT.md`

### **To Continue Helpdesk Work**:
1. Review `backend/app/api/v1/endpoints/helpdesk.py`
2. Check AI prompt usage (should use database prompts)
3. Add ticket assignment UI in frontend
4. Implement email notifications

---

## 📝 **NOTES**

- **Version**: Current version is 3.0.0 (see `VERSION_MANAGEMENT.md` for update checklist)
- **Git Status**: Changes committed locally, ready to push (push was canceled by user)
- **Database**: Ensure migrations are applied before testing
- **Services**: Some services still use sync sessions - migrate gradually
- **Testing**: Always test async migrations thoroughly before moving to next endpoint

---

## 🔗 **REFERENCE DOCUMENTS**

- `TODO.md` - Comprehensive task list
- `FIXES_STATUS_REPORT.md` - Security fixes status
- `COMPLETE_PROGRESS_REPORT.md` - Overall progress
- `SESSION_COMPLETE_SUMMARY.md` - Latest session summary
- `PHASE_5_HELPDESK_DETAILED.md` - Helpdesk implementation plan
- `AI_PROMPTS_SYSTEM.md` - AI prompts system documentation

---

**Last Updated**: 2025-01-XX  
**Next Review**: After async migration milestone

