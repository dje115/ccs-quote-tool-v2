# CCS Quote Tool v2 - Quick Setup Guide

## Prerequisites

- Docker and Docker Compose installed
- Git (for cloning the repository)
- PowerShell (Windows) or Bash (Linux/Mac)

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd "CCS Quote Tool v2"
```

### 2. Set Up Environment Variables

```bash
# Copy the example environment file
cp env.example .env

# Edit .env with your API keys and configuration
# At minimum, update:
# - OPENAI_API_KEY (required for AI features)
# - COMPANIES_HOUSE_API_KEY (required for UK company data)
# - GOOGLE_MAPS_API_KEY (required for address search)
```

### 3. Start Development Environment

**Windows PowerShell:**
```powershell
.\dev-start.ps1
```

**Linux/Mac:**
```bash
docker-compose up -d
```

### 4. Access the Application

Once containers are running, access:

- **Frontend (CRM):** http://localhost:3000
- **Admin Portal:** http://localhost:3010
- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs
- **MailHog Web UI:** http://localhost:3006 (Email testing)
- **MinIO Console:** http://localhost:9092 (Object storage)

**Default Login:**
- Email: `admin@ccs.com`
- Password: `admin123`

### 5. Verify Installation

```bash
# Check all services are running
docker-compose ps

# View logs
docker-compose logs -f backend

# Test API health
curl http://localhost:8000/health
```

## Development Workflow

### Making Code Changes

1. **Frontend Changes:** Edit files in `frontend/src/` - changes appear automatically (hot-reload)
2. **Backend Changes:** Edit files in `backend/app/` - FastAPI auto-reloads
3. **Admin Portal Changes:** Edit files in `admin-portal/src/` - Vite HMR updates automatically

### Database Migrations

```bash
# Run SQL migrations
docker-compose exec postgres psql -U postgres -d ccs_quote_tool -f /path/to/migration.sql

# Or copy migration file content and run:
Get-Content "backend/migrations/my_migration.sql" | docker-compose exec -T postgres psql -U postgres -d ccs_quote_tool
```

### Running Tests

```bash
# Run backend tests
docker-compose exec backend pytest backend/tests/

# Run specific test file
docker-compose exec backend pytest backend/tests/test_pricing_import_service.py
```

## Service Configuration

### MailHog (Email Testing)

MailHog is automatically configured for development. All emails sent by the application are captured in MailHog's web UI at http://localhost:3006.

**Configuration:**
- SMTP Host: `mailhog` (internal container name)
- SMTP Port: `1025` (internal container port)
- Web UI: http://localhost:3006 (host port, changed from 3005 to avoid conflicts)

### MinIO (Object Storage)

MinIO provides S3-compatible object storage for product images, quote attachments, and customer documents.

**Configuration:**
- API Endpoint: `minio:9000` (internal container port)
- Console: http://localhost:9092 (host port, changed from 9090 to avoid conflicts)
- Default Credentials: `minioadmin` / `minioadmin123`
- Default Bucket: `ccs-quote-tool`

**Access MinIO Console:**
1. Navigate to http://localhost:9092 (changed from 9090 to avoid conflicts)
2. Login with `minioadmin` / `minioadmin123`

**Note:** MinIO API is available on localhost:9002 (changed from 9000 to avoid conflicts)
3. Create buckets and manage files

## Troubleshooting

### Port Already in Use

If a port is already in use, either:
1. Stop the conflicting service
2. Modify port mappings in `docker-compose.yml`

### Database Connection Issues

```bash
# Check database is healthy
docker-compose exec postgres pg_isready

# Reset database (WARNING: deletes all data)
docker-compose down -v
docker-compose up -d
```

### Services Not Starting

```bash
# View detailed logs
docker-compose logs [service-name]

# Rebuild containers
docker-compose down
docker-compose up -d --build
```

## Production Setup

For production deployment:

1. Update `.env` with production secrets
2. Use `docker-compose.prod.yml`:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d --build
   ```
3. Configure production SMTP (not MailHog)
4. Configure production object storage (S3, Azure Blob, etc.)
5. Set up SSL/TLS certificates
6. Configure domain names and DNS

## Additional Resources

- **Development Guide:** See `DEVELOPMENT_ENVIRONMENT.md`
- **API Documentation:** http://localhost:8000/docs (when running)
- **Architecture:** See project README.md

## Getting Help

If you encounter issues:

1. Check `DEVELOPMENT_ENVIRONMENT.md` for detailed troubleshooting
2. Review container logs: `docker-compose logs -f`
3. Verify environment variables are set correctly
4. Ensure all prerequisites are installed

---

**Version:** 2.2.0  
**Last Updated:** Current Date

