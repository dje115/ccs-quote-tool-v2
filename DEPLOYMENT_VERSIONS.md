# CCS Quote Tool v2 - Current Deployment Versions

**Last Updated:** October 19, 2025 - All versions verified and running ✅

## 🚀 Frontend Stack (React + Material-UI)

| Component | Version | Status |
|-----------|---------|--------|
| **React** | 19.2.0 | ✅ Running |
| **React DOM** | 19.2.0 | ✅ Running |
| **React Router** | 7.9.4 | ✅ Running |
| **React Router DOM** | 7.9.4 | ✅ Running |
| **Material-UI Core** | 7.3.4 | ✅ Running |
| **Material-UI Icons** | 7.3.4 | ✅ Running |
| **Material-UI X Data Grid** | 7.21.2 | ✅ Running |
| **Material-UI X Date Pickers** | 7.21.2 | ✅ Running |
| **TypeScript** | 5.9.3 | ✅ Running |
| **Vite** | 5.4.11 | ✅ Running |
| **Node.js** | 20 (Alpine) | ✅ Running |

### Frontend Libraries
| Library | Version | Purpose |
|---------|---------|---------|
| Emotion React | 11.14.0 | CSS-in-JS styling |
| Emotion Styled | 11.14.1 | Styled components |
| i18next | 23.7.6 | Multilingual support |
| react-i18next | 13.5.0 | i18next React binding |
| Axios | 1.7.7 | HTTP client |
| Chart.js | 4.4.0 | Charts & graphs |
| react-chartjs-2 | 5.3.0 | React wrapper for Chart.js |
| date-fns | 3.6.0 | Date manipulation |
| Formik | 2.4.6 | Form management |
| Yup | 1.4.0 | Form validation |
| Redux Toolkit | 2.9.0 | State management |
| TanStack Query | 5.90.2 | Data fetching & caching |
| Socket.io Client | 4.8.1 | Real-time communication |

## 🔧 Backend Stack (FastAPI + Python)

| Component | Version | Status |
|-----------|---------|--------|
| **Python** | 3.12 | ✅ Running |
| **FastAPI** | 0.115.6 | ✅ Running |
| **SQLAlchemy** | 2.0.36 | ✅ Running |
| **Celery** | 5.4.0 | ✅ Running |

## 🗄️ Database & Cache

| Component | Version | Container | Status |
|-----------|---------|-----------|--------|
| **PostgreSQL** | 16-alpine | ccs-postgres | ✅ Healthy |
| **Redis** | 7-alpine | ccs-redis | ✅ Healthy |

## 🏢 Admin Portal Stack

| Component | Version | Status |
|-----------|---------|--------|
| **Vue.js** | 3.x | ✅ Running |
| **Element Plus** | Latest | ✅ Running |
| **Vite** | 5.4.11 | ✅ Running |
| **TypeScript** | 5.x | ✅ Running |
| **Node.js** | 20 (Alpine) | ✅ Running |

## 🐳 Container Stack

| Service | Image | Version | Status |
|---------|-------|---------|--------|
| Frontend | ccsquotetoolv2-frontend:latest | Node 20 Alpine | ✅ Up 2+ minutes |
| Backend | ccsquotetoolv2-backend:latest | Python 3.12 | ✅ Up 2+ minutes |
| Admin Portal | ccsquotetoolv2-admin-portal:latest | Node 20 Alpine | ✅ Up 2+ minutes |
| Celery Worker | ccsquotetoolv2-celery-worker:latest | Python 3.12 | ✅ Up 2+ minutes |
| Celery Beat | ccsquotetoolv2-celery-beat:latest | Python 3.12 | ✅ Up 2+ minutes |
| PostgreSQL | postgres:16-alpine | 16 Alpine | ✅ Healthy |
| Redis | redis:7-alpine | 7 Alpine | ✅ Healthy |

## 🤖 AI Integration

| Component | Version | Status |
|-----------|---------|--------|
| **OpenAI Model** | GPT-5-mini | ✅ Active |
| **Token Limit** | 10,000+ (20,000 for complex) | ✅ Configured |
| **Timeout** | 120s+ (240s for complex) | ✅ Configured |
| **Web Search** | Enabled | ✅ Active |

## 📋 Known Compatibility Issues

### React 19 with MUI X Components
- **MUI X Data Grid**: Shows "invalid: ^7.21.2" warnings but functions correctly
- **MUI X Date Pickers**: Shows "invalid: ^7.21.2" warnings but functions correctly
- **Cause**: These components still expect React 17-18 peer dependency
- **Impact**: None - warnings only, functionality is stable
- **Solution**: Downgrade to React 18 if needed (not recommended)

## 🔐 Security Notes

- All containers run as non-root user (appuser)
- PostgreSQL password: Set via environment variable
- Redis: Running with authentication required in production
- SSL/TLS: Configure at reverse proxy level (Nginx)

## 📊 Performance Baseline

- Frontend build time: ~30-40 seconds
- Backend startup time: ~5-10 seconds
- Database initialization: ~5 seconds
- Total full stack startup: ~20-30 seconds

## ✅ Health Checks

All services verified healthy:
```
✅ ccs-frontend          - Up 2+ minutes
✅ ccs-backend           - Up 2+ minutes  
✅ ccs-admin-portal      - Up 2+ minutes
✅ ccs-celery-worker     - Up 2+ minutes
✅ ccs-celery-beat       - Up 2+ minutes
✅ ccs-postgres          - Healthy
✅ ccs-redis             - Healthy
```

## 🚀 Recent Changes (v2.7.0)

- ✅ React upgraded from 18 → 19.2.0
- ✅ Material-UI upgraded to v7.3.4
- ✅ React Router upgraded to v7.9.4
- ✅ All components verified working
- ✅ Two-column layout properly implemented
- ✅ Material-UI v7 Grid syntax verified

## 🔄 Rollback Instructions

If issues arise, revert to previous versions:
1. Update `frontend/package.json` versions
2. Run `npm install` in frontend
3. Rebuild Docker image: `docker-compose -f docker-compose.dev.yml up --build`

---

**System Status**: 🟢 **HEALTHY** - All services running and verified

