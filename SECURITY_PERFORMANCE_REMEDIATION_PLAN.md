# Security and Performance Remediation Plan

## Phase 1: Critical Security Fixes (Immediate)

### 1.1 Upgrade Python-JOSE (CRITICAL)
**File**: `backend/requirements.txt:16`
- Replace `python-jose[cryptography]==3.3.0` with `python-jose-cryptodome>=4.0.0`
- Update JWT encoding/decoding in `backend/app/core/security.py` if API changes
- Test authentication flow: login, token refresh, protected endpoints
- Update any JWT-related tests

### 1.2 Fix XSS Vulnerabilities (CRITICAL)
**Files**: `frontend/src/pages/CustomerDetail.tsx:834`, `frontend/src/pages/LeadDetail.tsx`
- Install DOMPurify: `npm install dompurify @types/dompurify`
- Create sanitization utility: `frontend/src/utils/sanitize.ts`
- Replace all `dangerouslySetInnerHTML` usage with sanitized HTML
- Add unit tests for sanitization

### 1.3 Fix Information Disclosure in Error Handling (CRITICAL)
**Files**: `backend/app/api/v1/endpoints/admin.py:125,169,211`, `backend/main.py:183`
- Create environment-based error handler utility: `backend/app/core/error_handler.py`
- Update all exception handlers to use generic messages in production
- Implement structured logging for debugging (keep detailed errors in logs only)
- Update global exception handler in `backend/main.py:155-187`

### 1.4 Add Security Headers Middleware (HIGH)
**File**: `backend/app/core/middleware.py`
- Create `SecurityHeadersMiddleware` class
- Add headers: X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, HSTS, CSP
- Integrate into `backend/main.py` before other middleware
- Test headers are present in all responses

## Phase 2: High Priority Security Fixes

### 2.1 Implement CSRF Protection (HIGH)
**Files**: `backend/app/api/v1/endpoints/auth.py`, `frontend/src/services/api.ts`
- Install `fastapi-csrf-protect`
- Add CSRF token generation endpoint
- Update all PUT/POST/DELETE endpoints to validate CSRF tokens
- Update frontend axios interceptor to include CSRF token in requests
- Add CSRF token refresh mechanism

### 2.2 Complete Refresh Token Implementation (HIGH)
**Files**: `backend/app/models/`, `backend/app/api/v1/endpoints/auth.py`
- Create `RefreshToken` model in `backend/app/models/auth.py`
- Implement token storage, rotation, and family detection
- Update refresh endpoint to validate against database
- Add token revocation capability
- Create migration: `backend/migrations/add_refresh_tokens_table.sql`

### 2.3 Update Frontend Dependencies (MEDIUM-HIGH)
**File**: `frontend/package.json`
- Run `npm audit fix` to resolve vulnerabilities
- Update `esbuild` to latest version (if used)
- Update `js-yaml` to version without prototype pollution
- Test frontend build and runtime after updates

## Phase 3: Performance Optimization

### 3.1 Fix N+1 Query Problems (HIGH)
**Files**: `backend/app/api/v1/endpoints/customers.py:144-204,257-304`
- Use `selectinload()` for eager loading relationships
- Update customer queries to load `sales_activities` and `tickets` in single query
- Add database indexes for frequently queried fields
- Create migration for new indexes: `backend/migrations/add_performance_indexes.sql`
- Add query performance logging for slow operations

### 3.2 Fix Async/Await Anti-patterns (HIGH)
**File**: `backend/app/tasks/campaign_tasks.py:77`
- Remove `asyncio.run()` from Celery tasks
- Restructure `LeadGenerationService` to work synchronously or use sync wrapper
- Create async-to-sync bridge if needed: `backend/app/core/async_bridge.py`
- Test Celery task execution after changes

### 3.3 Implement Strategic Caching (MEDIUM)
**Files**: `backend/app/services/`, `backend/app/core/caching.py`
- Create caching utility: `backend/app/core/caching.py`
- Cache tenant configurations (TTL: 1 hour)
- Cache AI analysis results (TTL: 24 hours)
- Cache frequently accessed customer data (TTL: 15 minutes)
- Implement cache invalidation strategies
- Add Redis cache hit rate monitoring

## Phase 4: Security Hardening

### 4.1 Enhanced Rate Limiting (MEDIUM)
**File**: `backend/app/core/middleware.py`
- Create `RateLimitMiddleware` class
- Implement rate limits:
  - Admin endpoints: 1000 req/min
  - Login endpoints: 5 req/min (with progressive delays)
  - Public endpoints: 60 req/min
  - Authenticated endpoints: 300 req/min
- Store rate limit data in Redis
- Add rate limit headers to responses

### 4.2 API Key Security Enhancement (MEDIUM)
**Files**: `backend/app/models/ai_provider.py`, `backend/app/services/`
- Encrypt API keys at rest using Fernet (symmetric encryption)
- Create key encryption utility: `backend/app/core/encryption.py`
- Implement key rotation mechanism
- Add audit logging for key usage
- Create migration to encrypt existing keys

### 4.3 Password Security Enhancement (MEDIUM)
**File**: `backend/app/api/v1/endpoints/auth.py`
- Implement password complexity policies (min length, special chars, etc.)
- Add account lockout after 5 failed attempts (15-minute lockout)
- Implement password history tracking (prevent reuse of last 5 passwords)
- Create `PasswordPolicy` model and validation
- Add password strength meter to frontend

## Testing Requirements

### Unit Tests
- JWT token generation/validation after python-jose upgrade
- XSS sanitization functions
- Error handler environment-based responses
- CSRF token validation
- Refresh token rotation and family detection
- Password policy validation
- Rate limiting logic

### Integration Tests
- Authentication flow (login, refresh, logout)
- Protected endpoint access with CSRF tokens
- N+1 query fixes (verify single query execution)
- Caching behavior (hit/miss scenarios)
- Rate limiting enforcement

### Security Tests
- XSS injection attempts (verify sanitization)
- CSRF attack simulation
- JWT token manipulation attempts
- Rate limit bypass attempts
- SQL injection attempts (verify parameterized queries still work)

## Implementation Order

1. **Week 1**: Critical security fixes (1.1-1.4) + comprehensive testing
2. **Week 2**: High priority security (2.1-2.3) + performance fixes (3.1-3.2) + testing
3. **Week 3**: Remaining performance (3.3) + security hardening (4.1-4.3) + testing
4. **Week 4**: Final testing, documentation, deployment preparation

## Success Metrics

- Zero critical vulnerabilities in security scan
- All XSS vectors eliminated (verified with security testing)
- Sub-100ms response times for 95% of requests
- N+1 queries eliminated (verified with query logging)
- 100% test coverage for security-critical code paths
- Security rating: 9/10 (Enterprise-grade)
- Performance rating: 9/10 (Optimized for high load)

## TODO List

### Phase 1: Critical Security
- [x] Upgrade python-jose to >=4.0.0 and test JWT functionality ✅ COMPLETED
- [x] Install DOMPurify, create sanitization utility, replace dangerouslySetInnerHTML ✅ COMPLETED
- [x] Create environment-based error handler, update all exception handlers ✅ COMPLETED
- [x] Create SecurityHeadersMiddleware with CSP, HSTS, X-Frame-Options, etc. ✅ COMPLETED

### Phase 2: High Priority Security
- [x] Install fastapi-csrf-protect, add CSRF validation to all state-changing operations ✅ COMPLETED
- [x] Create RefreshToken model, implement database storage and rotation ✅ COMPLETED
- [x] Run npm audit fix, update vulnerable dependencies ✅ COMPLETED

### Phase 3: Performance Optimization
- [ ] Use selectinload() for eager loading, add performance indexes
- [ ] Remove asyncio.run() from Celery tasks, restructure async operations
- [ ] Create caching utility, cache tenant configs, AI results, customer data

### Phase 4: Security Hardening
- [ ] Create RateLimitMiddleware with different limits per endpoint type
- [ ] Encrypt API keys at rest, implement rotation and audit logging
- [ ] Implement password complexity, account lockout, password history

### Testing
- [ ] Create comprehensive security tests for all fixes
- [ ] Create integration tests for N+1 fixes, caching, and async patterns

