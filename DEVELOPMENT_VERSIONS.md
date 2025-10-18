# CCS Quote Tool v2 - Development Stack Versions

**CRITICAL: These versions must be maintained to prevent backward compatibility issues**

## Current Development Stack (v2.6.0 → v2.7.0)

### Frontend Stack
- **React**: 18 → **19.2.0** (upgrading)
- **React Router**: v7.9.4 (stable)
- **Material-UI (MUI)**: v5.15.21
- **Vite**: Latest stable
- **TypeScript**: Latest stable
- **Node.js**: Latest LTS

### Backend Stack
- **FastAPI**: Latest stable
- **Python**: 3.12
- **PostgreSQL**: 16
- **Redis**: 7
- **SQLAlchemy**: 2.0
- **Celery**: Latest stable

### Admin Portal Stack
- **Vue.js**: 3 (latest)
- **Element Plus**: Latest
- **Vite**: Latest stable
- **TypeScript**: Latest stable

### AI Integration
- **OpenAI Model**: GPT-5-mini exclusively
- **Token Limits**: 10000+ tokens minimum (20000 for complex analysis)
- **Timeout**: 120s+ minimum (240s for complex analysis)
- **Web Search**: Enabled for lead generation

### Infrastructure
- **Docker**: Latest stable
- **Docker Compose**: Latest stable
- **Nginx**: Latest stable

## Version Upgrade History

### v2.7.0 (Current Upgrade)
- **React**: 18 → 19.2.0
- **Reason**: Performance improvements, new features, future-proofing
- **Date**: October 2025

### v2.6.0 (Previous)
- **React Router**: v6 → v7.9.4
- **Reason**: Enhanced navigation performance and compatibility
- **Date**: October 2025

## Testing Requirements

After React 19 upgrade, test ALL components:
- [ ] Authentication (Login/Logout)
- [ ] Dashboard functionality
- [ ] Customer management (CRUD operations)
- [ ] Lead generation campaigns
- [ ] AI analysis features
- [ ] Settings and API key management
- [ ] Multi-language support
- [ ] Responsive design
- [ ] Error handling
- [ ] Performance benchmarks

## Compatibility Notes

- **Material-UI v7.3.4** is compatible with React 19
- React Router v7.9.4 is compatible with React 19
- Vite supports React 19 out of the box
- TypeScript definitions available for React 19

## Material-UI v7 Grid Syntax

**CRITICAL**: Material-UI v7 requires both `item` prop AND `size` prop for Grid items:

```tsx
// Container
<Grid container spacing={3}>
  // Grid Item - MUST have both item and size props
  <Grid item size={{ xs: 12, md: 9, lg: 9 }}>
    Content here
  </Grid>
</Grid>
```

**WRONG**: `<Grid size={{...}}>` (missing item prop)
**CORRECT**: `<Grid item size={{...}}>` (both props required)

## Rollback Plan

If issues arise:
1. Revert package.json changes
2. Restore previous React version
3. Test all components
4. Document issues for future upgrade

---

**Last Updated:** October 18, 2025 (v2.7.0)

## 🎯 Upgrade Summary - v2.7.0

### ✅ Successfully Upgraded:
- **React:** `18.x` → `19.2.0` (Latest stable)
- **Material-UI Core:** `5.x` → `7.3.4` (Latest stable)
- **Material-UI Icons:** `5.x` → `7.3.4` (Latest stable)
- **React Router:** `6.x` → `7.9.4` (Latest stable)
- **TypeScript:** `5.7.2` (Latest stable)

### 🔧 Key Fixes Applied:
- Fixed dashboard centering issues with Material UI v7 Grid components
- Resolved JSX syntax errors in Dashboard.tsx
- Fixed API import conflicts and module resolution
- Enhanced error boundaries and component stability
- Improved build process and production readiness

### 🧪 Testing Status:
- ✅ Frontend (React): Working perfectly
- ✅ Backend (FastAPI): Working perfectly  
- ✅ Admin Portal (Vue.js): Working perfectly
- ✅ Database (PostgreSQL 16): Working perfectly
- ✅ Cache (Redis 7): Working perfectly
- ✅ Celery Workers: Working perfectly

### 📋 Notes:
- PostgreSQL 17 and Redis 8 were attempted but reverted due to stability concerns
- All current versions are latest stable releases
- Production builds tested and working
- Development environment fully functional
