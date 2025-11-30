# CCS Quote Tool v2 - Next Steps Priority List
**Date:** 2025-11-24  
**Current Version:** 3.0.2  
**Status:** Ready for Development

---

## 🚨 **IMMEDIATE PRIORITIES** (This Week)

### **1. Fix Action Suggestions Missing Quote/Ticket Context** 🔥
**Priority:** P0 - Critical  
**Status:** Needs Verification  
**Estimated Effort:** 2-4 hours

**Tasks:**
- [ ] Inspect Celery worker logs for `[ACTION PROMPT - SYSTEM]` to confirm updated prompt text is being used
- [ ] Verify `ActivityService.generate_action_suggestions()` attaches `quote_summary` & `ticket_summary` to payload
- [ ] Refresh suggestions in UI and confirm OpenAI response references relevant quotes/tickets
- [ ] If responses still stale, ensure Redis cache is cleared again and prompt text matches DB record `f63f0d4f-4608-4fd4-8af5-b4ac6f6d6e28`

**Files to Check:**
- `backend/app/services/activity_service.py` - Verify payload construction
- `backend/app/tasks/activity_tasks.py` - Check Celery task implementation
- Check Celery worker logs during suggestion generation

**Success Criteria:**
- AI suggestions include references to specific quotes and tickets
- Logs show `[ACTION PROMPT - SYSTEM]` entries
- OpenAI responses cite actual quote/ticket numbers

---

### **2. Fix Customer Timeline & AI Suggestion Layout** 🔥
**Priority:** P0 - Critical  
**Status:** Needs Implementation  
**Estimated Effort:** 3-5 hours

**Tasks:**
- [ ] Refactor `CustomerTimeline.tsx` to remove nested `<p>` warnings (use `Typography component="span/div"` or `Box` wrappers)
- [ ] Update layout so timeline spans full width at bottom
- [ ] AI suggestion cards show 3 wider columns (currently likely 4+ narrow columns)
- [ ] Fix deprecated MUI Grid props in `CustomerDetail.tsx`

**Files to Modify:**
- `frontend/src/components/CustomerTimeline.tsx`
- `frontend/src/pages/CustomerDetail.tsx`

**Success Criteria:**
- No console warnings about nested `<p>` tags or Grid deprecation
- Timeline displays full width at bottom of page
- AI suggestions show in 3 wider columns per user request
- All UI elements render correctly

---

### **3. Resize Manual Quote Builder Inputs** 🔥
**Priority:** P0 - Critical  
**Status:** Needs Implementation  
**Estimated Effort:** 2-3 hours

**Tasks:**
- [ ] Resize description, part number, supplier, qty, unit cost inputs
- [ ] Remove scrollbars from input fields
- [ ] Support 8-12 character part numbers
- [ ] Support 7-character unit costs
- [ ] Consider two-row layout if single row cannot fit requested widths

**Files to Modify:**
- `frontend/src/pages/QuoteNew.tsx` (or quote builder component)

**Success Criteria:**
- All inputs display without scrollbars
- Input widths accommodate typical data lengths
- Layout is clean and professional

---

### **4. System Tenant Verification & Testing** ⚠️
**Priority:** P0.1 - High  
**Status:** Needs Verification  
**Estimated Effort:** 1-2 hours

**Tasks:**
- [ ] After next rebuild, run `SELECT slug, plan FROM tenants WHERE plan='system';` to confirm auto-seeding works
- [ ] Ensure `system-admin@ccs.local` user exists and has SUPER_ADMIN role + permissions
- [ ] Document steps for rotating system API keys via admin portal once tenant is present
- [ ] Test that system tenant can access all required APIs

**Success Criteria:**
- System tenant exists in database after rebuild
- System admin user exists with correct permissions
- Documentation created for key rotation
- System tenant functionality verified

---

## 🔥 **HIGH PRIORITY** (Next 2-4 Weeks)

### **5. Enhanced Multi-Part Quoting System** (NEW)
**Priority:** HIGH  
**Status:** Planning Phase  
**Estimated Effort:** 8-12 weeks

**This is the major new feature.** See `TODO.md` Section "🔥 1. Enhanced Multi-Part Quoting System (NEW)" for full specification.

**Key Components:**
- Multi-part quote documents (Parts List, Technical Doc, Overview Doc, Build Doc)
- Document versioning system
- AI-powered quote generation
- 3-tier quote support (Basic/Standard/Premium)
- Own products database integration
- Day rate charts integration

**Start With:**
- [ ] Database schema extensions (`quote_documents`, `quote_document_versions` tables)
- [ ] AI prompt for quote generation
- [ ] Basic document models

**Reference:** `TODO.md` lines 436-629

---

### **6. Complete Async SQLAlchemy Migration Verification** ✅
**Priority:** HIGH  
**Status:** ~95% Complete - Verification Needed  
**Estimated Effort:** 1-2 days

**Tasks:**
- [ ] Audit remaining endpoints to confirm all use `AsyncSession`
- [ ] Verify no sync operations in high-traffic endpoints
- [ ] Test async performance improvements
- [ ] Document migration completion

**Note:** According to `NEXT_AGENT_TODO.md`, this is essentially complete. Just needs final verification.

---

### **7. Complete Smart Quoting Module Implementation**
**Priority:** HIGH  
**Status:** 20% Complete (Spec exists, implementation pending)  
**Estimated Effort:** 6-8 weeks

**Reference:** `SMART_QUOTING_MODULE_SPEC.md`

**Key Components:**
- Product catalog system
- Component pricing from suppliers
- Day rate calculations
- AI scope analysis
- Product recommendations
- Labor estimation

**Start With:**
- Review `SMART_QUOTING_MODULE_SPEC.md`
- Plan integration with Enhanced Multi-Part Quoting System
- Begin with product catalog enhancements

---

## 📋 **MEDIUM PRIORITY** (Next 1-2 Months)

### **8. Helpdesk Enhancements Completion**
**Priority:** MEDIUM  
**Status:** 70% Complete  
**Estimated Effort:** 2-3 weeks

**Remaining Tasks:**
- [ ] Email ticket ingestion (per-tenant email providers)
- [ ] WhatsApp Business API integration
- [ ] PSA/RMM platform integrations
- [ ] Advanced SLA intelligence
- [ ] Knowledge base integration
- [ ] Ticket automation workflows

**Reference:** `PHASE_5_HELPDESK_DETAILED.md`

---

### **9. Address Management UI Enhancements**
**Priority:** MEDIUM  
**Status:** Partially Complete  
**Estimated Effort:** 2-3 days

**Tasks:**
- [ ] Address management UI at top of customer page
- [ ] Drag-and-drop address reordering
- [ ] Address types (Primary, Billing, Delivery, Warehouse)
- [ ] Manual address addition form
- [ ] Address editing dialog

**Files:**
- `frontend/src/pages/CustomerDetail.tsx` (extend)
- `frontend/src/components/AddressManager.tsx` (new)

---

### **10. AI Prompt Management UI (Admin Portal)**
**Priority:** MEDIUM  
**Status:** Backend Complete, Frontend Pending  
**Estimated Effort:** 3-5 days

**Tasks:**
- [ ] Create AI Prompts management page in admin portal
- [ ] CRUD operations for prompts
- [ ] Version history view with rollback
- [ ] Tenant-specific prompt management
- [ ] Prompt testing interface

**Files:**
- `admin-portal/src/views/AIPrompts.vue` (new)
- `admin-portal/src/views/AIPromptVersions.vue` (new)
- `admin-portal/src/views/AIPromptEditor.vue` (new)

---

## 🔧 **TECHNICAL DEBT** (Ongoing)

### **11. Testing Infrastructure**
**Priority:** HIGH  
**Status:** 30% Complete  
**Estimated Effort:** 10-15 days

**Tasks:**
- [ ] Comprehensive integration tests (multi-tenant isolation, auth flows, WebSocket, async endpoints)
- [ ] Unit tests for services (target: 80% coverage)
- [ ] E2E tests (Playwright/Cypress)
- [ ] CI/CD pipeline with automated testing

---

### **12. Performance Optimization**
**Priority:** MEDIUM  
**Status:** 35% Complete  
**Estimated Effort:** 5-7 days

**Tasks:**
- [ ] Redis caching for frequently accessed data
- [ ] Database indexes for slow queries
- [ ] Pagination for all list endpoints
- [ ] Lazy loading for customer detail tabs
- [ ] Image optimization and CDN integration

---

### **13. Security Enhancements**
**Priority:** MEDIUM  
**Status:** 78% Complete  
**Estimated Effort:** 3-5 days

**Remaining Tasks:**
- [ ] Complete tenant isolation audit (verify RLS enforcement)
- [ ] Add audit logging for sensitive operations
- [ ] Implement API key rotation system
- [ ] Add 2FA (Two-Factor Authentication)
- [ ] Security headers (CSP, HSTS, etc.)

---

## 🐛 **KNOWN ISSUES TO FIX**

### **High Priority Bugs:**
- [ ] WebSocket connection errors (partially fixed - needs verification)
- [ ] AI analysis sometimes times out on large companies
- [ ] Google Maps API quota can be exceeded with multiple searches

### **Medium Priority Bugs:**
- [ ] Tab state occasionally resets on page refresh (localStorage issue)
- [ ] Some directors have address as object instead of string
- [ ] Health score calculation needs refinement
- [ ] Lead score weights need adjustment based on real data

---

## 📊 **QUICK REFERENCE**

### **Current Status:**
- **Version:** 3.0.2
- **Overall Completion:** ~76%
- **Backend Infrastructure:** 95% ✅
- **CRM Features:** 90% ✅
- **AI Integration:** 90% ✅
- **Helpdesk System:** 70% 🔄
- **Smart Quoting Module:** 20% 🔄

### **Last Completed Work (2025-11-24):**
- ✅ System Tenant auto-seeding
- ✅ Action Suggestions prompt refresh
- ✅ Stack reset and health checks
- ✅ Docker rebuild fixes

### **Key Documentation:**
- `TODO.md` - Comprehensive task list (most detailed)
- `NEXT_AGENT_TODO.md` - Latest session handoff notes
- `MASTER_TODO.md` - Empty (use TODO.md instead)
- `MASTER_SPECIFICATION.md` - Empty
- `SMART_QUOTING_MODULE_SPEC.md` - Smart quoting specification
- `PHASE_5_HELPDESK_DETAILED.md` - Helpdesk implementation plan

---

## 🎯 **RECOMMENDED WORK ORDER**

### **Week 1 (Immediate Fixes):**
1. Fix Action Suggestions Quote/Ticket Context (#1)
2. Fix Customer Timeline Layout (#2)
3. Resize Quote Builder Inputs (#3)
4. Verify System Tenant (#4)

### **Week 2-4 (Planning & Start Major Feature):**
5. Begin Enhanced Multi-Part Quoting System - Database schema (#5)
6. Complete async migration verification (#6)

### **Week 5-12 (Major Feature Development):**
7. Continue Enhanced Multi-Part Quoting System (#5)
8. Integrate with Smart Quoting Module (#7)

### **Ongoing (Technical Debt):**
9. Testing infrastructure (#11)
10. Performance optimization (#12)
11. Security enhancements (#13)

---

**Last Updated:** 2025-11-24  
**Next Review:** After completing immediate priorities (items 1-4)



