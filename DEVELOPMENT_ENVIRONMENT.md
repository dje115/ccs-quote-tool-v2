# Development Environment Guide

## 🎯 Overview

This project uses **Docker** with **separate development and production configurations** to provide the best developer experience while maintaining production-ready builds.

## 🔧 Development vs Production

### Development Mode (Default)
- **Hot-reload enabled** for frontend and admin portal
- Source code mounted as volumes
- Fast iteration and testing
- Real-time code changes without rebuilds
- Runs on `docker-compose.dev.yml`

### Production Mode
- **Optimized builds** for performance
- Minified and bundled assets
- Nginx serving static files
- No volume mounts (containers are self-contained)
- Runs on `docker-compose.prod.yml`

## 🚀 Quick Start

### Start Development Environment

**Windows PowerShell:**
```powershell
.\dev-start.ps1
```

**Manual (any OS):**
```bash
docker-compose -f docker-compose.dev.yml up -d
```

**Default (uses docker-compose.yml which links to dev):**
```bash
docker-compose up -d
```

### Access Applications

**Development Mode (using docker-compose.dev.yml):**
- **Frontend (CRM):** http://localhost:3001
- **Admin Portal:** http://localhost:3011
- **Backend API:** http://localhost:8001
- **API Documentation:** http://localhost:8001/docs

**Production Mode (using docker-compose.prod.yml):**
- **Frontend (CRM):** http://localhost:3000
- **Admin Portal:** http://localhost:3010
- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs

> **Note:** Different ports are used to clearly distinguish between dev and production environments.

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f frontend
docker-compose logs -f backend
docker-compose logs -f admin-portal
```

### Stop Environment

```bash
docker-compose down
```

## 📁 Docker Configuration Files

### `docker-compose.yml` (Symlink to dev)
- **Default configuration** for `docker-compose up`
- Currently points to development mode
- Used for daily development work

### `docker-compose.dev.yml`
- **Development configuration**
- Hot-reload enabled
- Volume mounts for live code changes
- Services:
  - `postgres` - PostgreSQL database
  - `redis` - Redis cache
  - `backend` - FastAPI backend (uvicorn with reload)
  - `frontend` - React app (Vite dev server)
  - `admin-portal` - Vue.js admin (Vite dev server)

### `docker-compose.prod.yml`
- **Production configuration**
- Optimized builds
- Nginx for frontend serving
- No volume mounts
- Used for production deployments

### Dockerfiles

#### Development Dockerfiles
- `frontend/Dockerfile.dev` - React dev server with hot-reload
- `admin-portal/Dockerfile.dev` - Vue dev server with hot-reload
- `backend/Dockerfile` (target: development) - FastAPI with auto-reload

#### Production Dockerfiles
- `frontend/Dockerfile` - Multi-stage build with Nginx
- `admin-portal/Dockerfile` - Multi-stage build with Nginx
- `backend/Dockerfile` (target: production) - Optimized FastAPI

## 🔄 Switching Between Modes

### Currently in Development Mode

To switch to production mode:

```bash
# Stop development environment
docker-compose down

# Start production environment
docker-compose -f docker-compose.prod.yml up -d --build
```

### Currently in Production Mode

To switch back to development:

```bash
# Stop production environment
docker-compose -f docker-compose.prod.yml down

# Start development environment
docker-compose -f docker-compose.dev.yml up -d
```

## 🛠️ Development Workflow

### Making Frontend Changes

1. **Edit files** in `frontend/src/`
2. **Save** - Changes are automatically detected
3. **Browser refreshes** automatically (hot-reload)
4. **See changes** immediately without rebuilding

Example:
```bash
# Edit a file
notepad frontend/src/pages/Campaigns.tsx

# Save the file - changes appear in browser within 1-2 seconds
```

### Making Backend Changes

1. **Edit files** in `backend/app/`
2. **Save** - FastAPI auto-reloads
3. **API reloads** automatically
4. **Test changes** immediately

Example:
```bash
# Edit a file
notepad backend/app/api/v1/endpoints/campaigns.py

# Save - backend restarts automatically (check logs)
docker-compose logs -f backend
```

### Making Admin Portal Changes

1. **Edit files** in `admin-portal/src/`
2. **Save** - Vite HMR (Hot Module Replacement)
3. **Portal updates** immediately
4. **See changes** without page reload

### Database Migrations

```bash
# Create migration
docker-compose exec backend alembic revision --autogenerate -m "description"

# Apply migrations
docker-compose exec backend alembic upgrade head

# Or run SQL directly
Get-Content "backend/migrations/my_migration.sql" | docker-compose exec -T postgres psql -U postgres -d ccs_quote_tool
```

## 🔨 Building for Production

### Frontend Production Build

```bash
# Build production frontend
docker-compose -f docker-compose.prod.yml build frontend

# This creates an optimized build:
# - TypeScript compilation
# - Vite production build
# - Minification
# - Tree-shaking
# - Asset optimization
```

### Full Production Build

```bash
# Build all services for production
docker-compose -f docker-compose.prod.yml build

# Start production environment
docker-compose -f docker-compose.prod.yml up -d
```

### Production Deployment Checklist

- [ ] Update version in `VERSION` file
- [ ] Update `CHANGELOG.md`
- [ ] Run production build: `docker-compose -f docker-compose.prod.yml build`
- [ ] Test production build locally
- [ ] Update environment variables (API keys, secrets)
- [ ] Push images to registry (if using)
- [ ] Deploy to production server
- [ ] Run database migrations
- [ ] Verify all services are healthy
- [ ] Test critical user flows

## 📊 Monitoring Development Environment

### Check Service Health

```bash
# Check running containers
docker-compose ps

# Check resource usage
docker stats

# Check service logs
docker-compose logs -f [service-name]
```

### Troubleshooting

#### Frontend not updating?
```bash
# Restart frontend
docker-compose restart frontend

# Check logs
docker-compose logs -f frontend

# If still issues, rebuild
docker-compose down
docker-compose up -d --build frontend
```

#### Backend not responding?
```bash
# Check backend logs
docker-compose logs -f backend

# Restart backend
docker-compose restart backend

# Check database connection
docker-compose exec backend python -c "from app.core.database import engine; print(engine)"
```

#### Database issues?
```bash
# Connect to database
docker-compose exec postgres psql -U postgres -d ccs_quote_tool

# Check tables
docker-compose exec postgres psql -U postgres -d ccs_quote_tool -c "\dt"

# Reset database (WARNING: deletes all data)
docker-compose down -v
docker-compose up -d
```

## 🎓 Best Practices

### For Daily Development

1. ✅ **Always use development mode** (`docker-compose up -d`)
2. ✅ **Keep containers running** - they restart automatically on code changes
3. ✅ **Monitor logs** when debugging: `docker-compose logs -f`
4. ✅ **Commit regularly** to Git
5. ✅ **Test in production mode** before deploying

### For Production Deployment

1. ✅ **Build fresh** - Always rebuild for production
2. ✅ **Test locally first** - Run production mode locally before deploying
3. ✅ **Update secrets** - Use production secrets, not dev defaults
4. ✅ **Run migrations** - Apply database migrations in production
5. ✅ **Monitor logs** - Check production logs after deployment

### Performance Tips

**Development Mode:**
- Keep only necessary services running
- Use `docker-compose up frontend backend postgres redis` for frontend-only work
- Stop admin-portal if not needed: `docker-compose stop admin-portal`

**Production Mode:**
- Use multi-stage builds (already configured)
- Enable Nginx caching
- Use CDN for static assets (future enhancement)
- Enable Redis caching in backend

## 🔐 Environment Variables

### Development (`.env` file)
```env
# Database
DATABASE_URL=postgresql://postgres:postgres_password_2025@postgres:5432/ccs_quote_tool

# API Keys (optional for dev, required for full functionality)
OPENAI_API_KEY=sk-...
COMPANIES_HOUSE_API_KEY=...
GOOGLE_MAPS_API_KEY=...

# Backend
SECRET_KEY=ccs_super_secret_key_2025_change_in_production
DEFAULT_TENANT=ccs
SUPER_ADMIN_EMAIL=admin@ccs.com
SUPER_ADMIN_PASSWORD=admin123
```

### Production
- Use **actual secrets**, not defaults
- Store in secure secret management (e.g., AWS Secrets Manager)
- Never commit production secrets to Git
- Rotate secrets regularly

## 📝 Important Notes

### File Watching

**Development mode uses file watching:**
- `CHOKIDAR_USEPOLLING=true` for cross-platform compatibility
- `WATCHPACK_POLLING=true` for webpack/vite
- Works on Windows, macOS, and Linux

### Volume Mounts

**Development mode mounts:**
```yaml
volumes:
  - ./frontend:/app          # Source code
  - /app/node_modules        # Exclude node_modules (use container's)
```

**Production mode:**
- No volume mounts
- All code copied into container at build time
- Immutable containers

### Port Mappings

| Service | Dev Port | Prod Port | Purpose |
|---------|----------|-----------|---------|
| Frontend | 3000 | 3000 | React CRM app |
| Admin Portal | 3010 | 3010 | Vue.js admin |
| Backend | 8000 | 8000 | FastAPI REST API |
| PostgreSQL | 5432 | 5432 | Database |
| Redis | 6379 | 6379 | Cache |

## 🆘 Getting Help

### Common Issues

**"Port already in use"**
```bash
# Find what's using the port
netstat -ano | findstr :3000

# Stop the conflicting service or use different port
```

**"Cannot connect to database"**
```bash
# Wait for database to be healthy
docker-compose logs postgres

# Check database is ready
docker-compose exec postgres pg_isready
```

**"Module not found" errors**
```bash
# Reinstall dependencies
docker-compose down
docker-compose up -d --build
```

### Logs Location

- **Container logs:** `docker-compose logs [service]`
- **Backend logs:** Check container output
- **Frontend logs:** Browser console + container logs
- **Database logs:** `docker-compose logs postgres`

## 🎯 Summary

**For AI Agents / Future Development:**

1. **Default mode is DEVELOPMENT** - Run `docker-compose up -d` for development with hot-reload
2. **Edit files directly** - Changes are automatically detected and reloaded
3. **No rebuilds needed** - in development mode unless you change dependencies
4. **Switch to production** - Use `docker-compose -f docker-compose.prod.yml up -d --build` when testing production builds
5. **Files to know:**
   - `docker-compose.yml` → Development (default)
   - `docker-compose.dev.yml` → Development (explicit)
   - `docker-compose.prod.yml` → Production
   - `frontend/Dockerfile.dev` → React dev server
   - `frontend/Dockerfile` → React production build

**IMPORTANT:** Always work in development mode unless explicitly building for production. Development mode provides instant feedback and fast iteration.

---

**Version:** 2.2.2  
**Last Updated:** October 2025  
**Maintained By:** CCS Development Team

