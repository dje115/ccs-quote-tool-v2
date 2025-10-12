# 🚀 CCS Quote Tool v2 - Quick Start Guide

## 📋 Environment Overview

This project has **TWO separate environments** that can run independently:

### 🔧 Development Environment
- **Purpose:** Active development with instant code updates
- **Ports:** Same as production (3000, 8000, 3010)
- **Features:** Hot-reload, volume mounts, faster iteration
- **Database:** Separate dev database (data isolation from production)

### 🏭 Production Environment
- **Purpose:** Production-ready deployment and testing
- **Ports:** Same as development (3000, 8000, 3010)
- **Features:** Optimized builds, minified assets, production configuration
- **Database:** Separate production database (data isolation from dev)

---

## 🎯 Quick Commands

### Start Development
```powershell
.\dev-start.ps1
```
**Access at:**
- Frontend: http://localhost:3000
- Admin Portal: http://localhost:3010
- Backend API: http://localhost:8000/docs

### Stop Development
```powershell
.\dev-stop.ps1
```

---

### Start Production
```powershell
.\prod-start.ps1
```
**Access at:**
- Frontend: http://localhost:3000
- Admin Portal: http://localhost:3010
- Backend API: http://localhost:8000/docs

### Stop Production
```powershell
.\prod-stop.ps1
```

---

## 🔍 Port Reference

| Service | Development | Production |
|---------|-------------|------------|
| Frontend | 3000 | 3000 |
| Admin Portal | 3010 | 3010 |
| Backend API | 8000 | 8000 |
| PostgreSQL | 5432 | 5432 |
| Redis | 6379 | 6379 |

> **💡 Tip:** Both environments use the same ports for simplicity. You can tell which is running by checking the container names or looking at the Vite dev server output (dev has hot-reload messages).

---

## 🛠️ Common Tasks

### View Logs (Development)
```powershell
docker-compose -f docker-compose.dev.yml logs -f
```

### View Logs (Production)
```powershell
docker-compose -f docker-compose.prod.yml logs -f
```

### Rebuild Containers (Development)
```powershell
docker-compose -f docker-compose.dev.yml up -d --build
```

### Rebuild Containers (Production)
```powershell
docker-compose -f docker-compose.prod.yml up -d --build
```

---

## 📝 Key Differences

### Development Mode
- ✅ Hot-reload for frontend and admin portal
- ✅ Source code changes appear instantly
- ✅ Faster development workflow
- ✅ Development-optimized builds
- ✅ Separate dev database (postgres_data_dev)
- ✅ Uses Vite/Vue dev servers

### Production Mode
- ✅ Optimized and minified builds
- ✅ Production-ready configuration
- ✅ Nginx serving static files
- ✅ Better performance
- ✅ Separate production database (postgres_data_prod)
- ✅ Production-ready deployment

---

## 🎓 Default Login

Both environments use the same database:

- **Email:** admin@ccs.com
- **Password:** admin123

---

## ⚠️ Important Notes

1. **Only one environment can run at a time** (they use the same container names)
2. **Always stop one before starting the other** using the stop scripts
3. **Separate databases**: Dev and production have completely separate databases and data
   - Development: `postgres_data_dev` and `redis_data_dev`
   - Production: `postgres_data_prod` and `redis_data_prod`
4. **Data isolation**: Changes in dev won't affect production (and vice versa)
5. **Hot-reload only works in development mode**

---

## 🆘 Troubleshooting

### Port Already in Use
If you see a port conflict, stop the other environment first:
```powershell
.\dev-stop.ps1
.\prod-stop.ps1
```

### Frontend Not Loading
Wait 30-60 seconds after startup for the frontend to compile and become available.

### API Not Responding
Check backend logs:
```powershell
# Development
docker-compose -f docker-compose.dev.yml logs backend

# Production
docker-compose -f docker-compose.prod.yml logs backend
```

---

## 📚 More Information

For detailed documentation, see:
- `DEVELOPMENT_ENVIRONMENT.md` - Full development guide
- `README.md` - Project overview
- `CHANGELOG.md` - Version history
