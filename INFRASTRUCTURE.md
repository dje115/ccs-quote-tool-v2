# Infrastructure Documentation

## 🏗️ CCS Quote Tool v2 - Infrastructure Overview

**Version:** 3.0.0  
**Last Updated:** 2025-01-XX

---

## 🌐 Port Numbers

### Development Environment (`docker-compose.yml`)

| Service | Container Name | Internal Port | External Port | URL |
|---------|---------------|---------------|---------------|-----|
| **Frontend (React)** | `ccs-frontend` | 3000 | 3000 | http://localhost:3000 |
| **Admin Portal (Vue.js)** | `ccs-admin-portal` | 3010 | 3010 | http://localhost:3010 |
| **Backend API (FastAPI)** | `ccs-backend` | 8000 | 8000 | http://localhost:8000 |
| **API Documentation** | `ccs-backend` | 8000 | 8000 | http://localhost:8000/docs |
| **PostgreSQL** | `ccs-postgres` | 5432 | 5432 | localhost:5432 |
| **Redis** | `ccs-redis` | 6379 | 6379 | localhost:6379 |
| **MinIO API** | `ccs-minio` | 9000 | 9002 | http://localhost:9002 |
| **MinIO Console** | `ccs-minio` | 9001 | 9092 | http://localhost:9092 |
| **MailHog SMTP** | `ccs-mailhog` | 1025 | 1026 | localhost:1026 |
| **MailHog Web UI** | `ccs-mailhog` | 8025 | 3006 | http://localhost:3006 |

### Production Environment (`docker-compose.prod.yml`)

| Service | Container Name | Internal Port | External Port | URL |
|---------|---------------|---------------|---------------|-----|
| **Frontend (React)** | `ccs-frontend` | 80 | 80 | http://localhost |
| **Admin Portal (Vue.js)** | `ccs-admin-portal` | 80 | 8080 | http://localhost:8080 |
| **Backend API (FastAPI)** | `ccs-backend` | 8000 | 8000 | http://localhost:8000 |
| **API Documentation** | `ccs-backend` | 8000 | 8000 | http://localhost:8000/docs |
| **PostgreSQL** | `ccs-postgres` | 5432 | 5432 | localhost:5432 |
| **Redis** | `ccs-redis` | 6379 | 6379 | localhost:6379 |
| **MinIO API** | `ccs-minio` | 9000 | 9000 | http://localhost:9000 |
| **MinIO Console** | `ccs-minio` | 9001 | 9001 | http://localhost:9001 |

---

## 🐳 Docker Services

### Core Services

#### 1. PostgreSQL Database
- **Image:** `postgres:16-alpine`
- **Container:** `ccs-postgres`
- **Database:** `ccs_quote_tool`
- **User:** `postgres`
- **Password:** `postgres_password_2025` (change in production!)
- **Volume:** `postgres_data`
- **Health Check:** `pg_isready -U postgres`

#### 2. Redis Cache
- **Image:** `redis:7-alpine`
- **Container:** `ccs-redis`
- **Purpose:** Session storage, caching, Celery broker
- **Volume:** `redis_data`
- **Health Check:** `redis-cli ping`

#### 3. Backend API (FastAPI)
- **Image:** Built from `backend/Dockerfile`
- **Container:** `ccs-backend`
- **Python:** 3.12
- **Framework:** FastAPI 0.115.6+
- **Port:** 8000
- **Volume:** `./backend:/app` (development mode)
- **Dependencies:** PostgreSQL, Redis, MinIO

#### 4. Frontend (React)
- **Image:** Built from `frontend/Dockerfile.dev`
- **Container:** `ccs-frontend`
- **Framework:** React 19.2.0
- **Port:** 3000 (dev) / 80 (prod)
- **Volume:** `./frontend:/app` (development mode)
- **Hot Reload:** Enabled in development

#### 5. Admin Portal (Vue.js)
- **Image:** Built from `admin-portal/Dockerfile.dev`
- **Container:** `ccs-admin-portal`
- **Framework:** Vue.js 3.4.0
- **Port:** 3010 (dev) / 8080 (prod)
- **Volume:** `./admin-portal:/app` (development mode)
- **Hot Reload:** Enabled in development

### Background Services

#### 6. Celery Worker
- **Image:** Built from `backend/Dockerfile`
- **Container:** `ccs-celery-worker`
- **Purpose:** Background task processing
- **Command:** `celery -A app.core.celery_app worker --loglevel=info --concurrency=2`
- **Dependencies:** PostgreSQL, Redis, Backend

#### 7. Celery Beat
- **Image:** Built from `backend/Dockerfile`
- **Container:** `ccs-celery-beat`
- **Purpose:** Scheduled task execution
- **Command:** `celery -A app.core.celery_app beat --loglevel=info`
- **Dependencies:** PostgreSQL, Redis, Backend

### Storage & Utilities

#### 8. MinIO (Object Storage)
- **Image:** `minio/minio:latest`
- **Container:** `ccs-minio`
- **Purpose:** File storage (product images, documents)
- **API Port:** 9000 (internal) / 9002 (external dev) / 9000 (external prod)
- **Console Port:** 9001 (internal) / 9092 (external dev) / 9001 (external prod)
- **Root User:** `minioadmin`
- **Root Password:** `minioadmin123` (change in production!)
- **Bucket:** `ccs-quote-tool`
- **Volume:** `minio_data`
- **Health Check:** `curl -f http://localhost:9000/minio/health/live`

#### 9. MailHog (Email Testing)
- **Image:** `mailhog/mailhog:latest`
- **Container:** `ccs-mailhog`
- **Purpose:** SMTP testing and email capture
- **SMTP Port:** 1025 (internal) / 1026 (external)
- **Web UI Port:** 8025 (internal) / 3006 (external)
- **Health Check:** `wget --quiet --tries=1 --spider http://localhost:8025`

---

## 🔗 Service Dependencies

```
frontend
  └── depends_on: backend

admin-portal
  └── depends_on: backend

backend
  ├── depends_on: postgres (healthy)
  ├── depends_on: redis (healthy)
  └── depends_on: minio (started)

celery-worker
  ├── depends_on: postgres (healthy)
  ├── depends_on: redis (healthy)
  ├── depends_on: backend (started)
  └── depends_on: minio (started)

celery-beat
  ├── depends_on: postgres (healthy)
  ├── depends_on: redis (healthy)
  ├── depends_on: backend (started)
  └── depends_on: minio (started)
```

---

## 🌍 Network Configuration

### Network Name
- **Development:** `ccsquotetoolv2_ccs-network`
- **Production:** `ccsquotetoolv2_ccs-network`
- **Driver:** `bridge`

All services communicate via this internal network. External access is only available through exposed ports.

---

## 💾 Volumes

### Development Volumes
- `postgres_data` - PostgreSQL data persistence
- `redis_data` - Redis data persistence
- `minio_data` - MinIO object storage data
- `./backend:/app` - Backend code (mounted for hot-reload)
- `./frontend:/app` - Frontend code (mounted for hot-reload)
- `./admin-portal:/app` - Admin portal code (mounted for hot-reload)

### Production Volumes
- `postgres_data_prod` - PostgreSQL data persistence
- `redis_data_prod` - Redis data persistence
- `minio_data_prod` - MinIO object storage data
- Code is baked into images (no volume mounts)

---

## 🔐 Environment Variables

### Backend Environment Variables

| Variable | Description | Default (Dev) | Required |
|----------|-------------|---------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:postgres_password_2025@postgres:5432/ccs_quote_tool` | Yes |
| `REDIS_URL` | Redis connection string | `redis://redis:6379/0` | Yes |
| `SECRET_KEY` | JWT secret key | `ccs_super_secret_key_2025_change_in_production` | Yes |
| `DEFAULT_TENANT` | Default tenant ID | `ccs` | Yes |
| `SUPER_ADMIN_EMAIL` | Super admin email | `admin@ccs.com` | Yes |
| `SUPER_ADMIN_PASSWORD` | Super admin password | `admin123` | Yes |
| `OPENAI_API_KEY` | OpenAI API key | (from env) | Optional |
| `COMPANIES_HOUSE_API_KEY` | Companies House API key | (from env) | Optional |
| `GOOGLE_MAPS_API_KEY` | Google Maps API key | (from env) | Optional |
| `MINIO_ENDPOINT` | MinIO endpoint | `minio:9000` | Yes |
| `MINIO_ACCESS_KEY` | MinIO access key | `minioadmin` | Yes |
| `MINIO_SECRET_KEY` | MinIO secret key | `minioadmin123` | Yes |
| `MINIO_BUCKET` | MinIO bucket name | `ccs-quote-tool` | Yes |
| `MINIO_SECURE` | MinIO secure connection | `false` | Yes |
| `APP_VERSION` | Application version | `3.0.0` | No |

### Frontend Environment Variables

| Variable | Description | Default (Dev) | Required |
|----------|-------------|---------------|----------|
| `REACT_APP_API_URL` | Backend API URL | `http://localhost:8000` | Yes |

### Admin Portal Environment Variables

| Variable | Description | Default (Dev) | Required |
|----------|-------------|---------------|----------|
| `VITE_API_URL` | Backend API URL | `http://localhost:8000` | Yes |

---

## 🚀 Startup Sequence

1. **Infrastructure Services** (PostgreSQL, Redis, MinIO)
   - Start first
   - Wait for health checks
   
2. **Backend Services** (Backend API, Celery Worker, Celery Beat)
   - Start after infrastructure is healthy
   - Backend API starts first
   - Celery services start after backend
   
3. **Frontend Services** (Frontend, Admin Portal)
   - Start after backend is ready
   - Can start in parallel

---

## 🔍 Health Checks

All critical services have health checks:

- **PostgreSQL:** `pg_isready -U postgres` (every 10s)
- **Redis:** `redis-cli ping` (every 10s)
- **MinIO:** `curl -f http://localhost:9000/minio/health/live` (every 10s)
- **MailHog:** `wget --quiet --tries=1 --spider http://localhost:8025` (every 10s)

---

## 📊 Resource Requirements

### Minimum Requirements (Development)
- **CPU:** 2 cores
- **RAM:** 4 GB
- **Disk:** 10 GB

### Recommended Requirements (Development)
- **CPU:** 4 cores
- **RAM:** 8 GB
- **Disk:** 20 GB

### Production Requirements
- **CPU:** 4+ cores
- **RAM:** 16+ GB
- **Disk:** 100+ GB (with backups)

---

## 🔧 Troubleshooting

### Port Conflicts
If a port is already in use:
1. Check what's using it: `netstat -ano | findstr :PORT`
2. Stop conflicting service or change port in `docker-compose.yml`

### Service Won't Start
1. Check logs: `docker-compose logs SERVICE_NAME`
2. Verify dependencies are healthy: `docker-compose ps`
3. Check environment variables: `docker exec CONTAINER env`

### Database Connection Issues
1. Verify PostgreSQL is healthy: `docker exec ccs-postgres pg_isready -U postgres`
2. Check connection string in environment variables
3. Verify network connectivity: `docker network inspect ccsquotetoolv2_ccs-network`

---

## 📚 Related Documentation

- `VERSION_MANAGEMENT.md` - Version number management
- `DEVELOPMENT_ENVIRONMENT.md` - Development setup guide
- `README.md` - Quick start guide

---

**Last Updated:** 2025-01-XX  
**Version:** 3.0.0

