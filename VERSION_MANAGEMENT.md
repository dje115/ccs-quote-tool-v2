# Version Management System

## 🎯 Single Source of Truth

**CRITICAL: The `VERSION` file in the project root is the SINGLE SOURCE OF TRUTH for all version numbers.**

```
VERSION
```

This file contains only the version number (e.g., `3.0.0`). All components MUST read from or reference this file.

---

## 📋 Version Update Checklist

When updating the version number, you MUST update ALL of the following:

### 1. Core Version File
- [ ] `VERSION` - **PRIMARY SOURCE** (update this first!)

### 2. Backend Files
- [ ] `backend/app/__init__.py` - `__version__` variable
- [ ] `backend/app/core/config.py` - `VERSION` field in `Settings` class
- [ ] `backend/Dockerfile` - `ARG APP_VERSION` default value

### 3. Frontend Files
- [ ] `frontend/package.json` - `"version"` field
- [ ] `frontend/src/pages/Login.tsx` - Fallback version in `useState` (line ~20)
- [ ] `frontend/src/components/VersionDisplay.tsx` - Fallback version (line ~24)

### 4. Admin Portal Files
- [ ] `admin-portal/package.json` - `"version"` field
- [ ] `admin-portal/src/App.vue` - Fallback versions (lines ~55, 69, 70)

### 5. Docker Configuration
- [ ] `docker-compose.yml` - `APP_VERSION` defaults (3 occurrences: backend, celery-worker, celery-beat)
- [ ] `docker-compose.prod.yml` - `APP_VERSION` default (1 occurrence: backend)

### 6. Documentation
- [ ] `README.md` - Version badge/header
- [ ] `NEXT_AGENT_TODO.md` - Version references
- [ ] `CHANGELOG.md` - Add new version entry

---

## 🔄 How Version Numbers Work

### Backend (FastAPI)
1. **Build Time**: Docker reads `VERSION` file or `APP_VERSION` env var
2. **Runtime**: Backend reads from:
   - `APP_VERSION` environment variable (set by Docker)
   - Falls back to `backend/app/__init__.py` `__version__`
   - Exposed via `/api/v1/version` endpoint

### Frontend (React)
1. **Build Time**: `package.json` version is used for npm builds
2. **Runtime**: Fetches version from `/api/v1/version` endpoint
3. **Fallback**: Uses hardcoded fallback if API call fails

### Admin Portal (Vue.js)
1. **Build Time**: `package.json` version is used for npm builds
2. **Runtime**: Fetches version from `/api/v1/version` endpoint
3. **Fallback**: Uses hardcoded fallback if API call fails

### Docker Containers
- Version is passed as `APP_VERSION` build argument
- Set as environment variable in container
- Available to all backend services (backend, celery-worker, celery-beat)

---

## 🚀 Quick Version Update Script

**For Agents:** Use this checklist when updating versions:

```bash
# 1. Update VERSION file (PRIMARY SOURCE)
echo "3.0.0" > VERSION

# 2. Update backend files
# - backend/app/__init__.py
# - backend/app/core/config.py
# - backend/Dockerfile

# 3. Update frontend files
# - frontend/package.json
# - frontend/src/pages/Login.tsx
# - frontend/src/components/VersionDisplay.tsx

# 4. Update admin-portal files
# - admin-portal/package.json
# - admin-portal/src/App.vue

# 5. Update Docker files
# - docker-compose.yml (3 places)
# - docker-compose.prod.yml (1 place)

# 6. Rebuild Docker containers
docker-compose down
docker-compose build --no-cache backend celery-worker celery-beat
docker-compose up -d

# 7. Verify version
docker exec ccs-backend python -c "from app import __version__; print(__version__)"
```

---

## 📝 Version Number Format

Use [Semantic Versioning](https://semver.org/):
- **MAJOR.MINOR.PATCH** (e.g., `3.0.0`)
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

---

## ⚠️ Important Notes

1. **Never hardcode versions** - Always reference the `VERSION` file or use the API endpoint
2. **Fallback versions** - Frontend/admin-portal fallbacks should match current `VERSION` file
3. **Docker rebuild** - Always rebuild containers after version changes
4. **Git commit** - Include version update in commit message: `v3.0.0: Description`
5. **Environment variables** - Clear `APP_VERSION` env var if set (it overrides defaults)

---

## 🔍 Verification

After updating versions, verify:

```bash
# Check VERSION file
cat VERSION

# Check backend version
docker exec ccs-backend python -c "from app import __version__; print(__version__)"
docker exec ccs-backend python -c "from app.core.config import settings; print(settings.VERSION)"

# Check API endpoint
curl http://localhost:8000/api/v1/version

# Check Docker environment
docker exec ccs-backend env | grep APP_VERSION
```

---

## 📚 Related Documentation

- `INFRASTRUCTURE.md` - Port numbers and service configuration
- `VERSION_SYSTEM.md` - Detailed version system architecture
- `README.md` - Quick start and overview

---

**Last Updated:** 2025-01-XX  
**Current Version:** 3.0.0

