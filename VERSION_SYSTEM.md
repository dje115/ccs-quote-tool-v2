# Version System Documentation

## Overview

The CCS Quote Tool v2 now includes a comprehensive version management system that ensures version synchronization between:
- The `VERSION` file (source of truth)
- Docker containers (build-time)
- Backend API (runtime)
- Frontend UI (displayed to users)

## Version Display

The version is displayed in two locations:

1. **Login Page** - Bottom of the login form
2. **Application Footer** - Fixed position in bottom-right corner (visible on all pages)

Hovering over the version displays a tooltip with:
- Version number
- Build date (if available)
- Build hash/Git commit (if available)
- Environment (development/production)

## Version API Endpoint

### Endpoint
```
GET /api/v1/version
```

### Response
```json
{
  "version": "2.5.0",
  "build_date": "2025-01-15T10:30:00Z",
  "build_hash": "abc123def456",
  "environment": "development"
}
```

**Note:** This endpoint is public (no authentication required) so it can be accessed from the login page.

## How It Works

### 1. Version Source (`VERSION` file)
The `VERSION` file in the project root is the single source of truth:
```
2.5.0
```

### 2. Docker Build Process
When building Docker containers, the version is:
- Read from `VERSION` file (or environment variable)
- Passed as build argument `APP_VERSION`
- Set as environment variable in the container
- Available to the backend application

### 3. Backend Application
The backend:
- Reads version from `VERSION` file (or `APP_VERSION` env var)
- Exposes it via `/api/v1/version` endpoint
- Includes it in health check and root endpoints
- Uses it in FastAPI app metadata

### 4. Frontend Application
The frontend:
- Fetches version from `/api/v1/version` endpoint
- Displays it in Login page and Layout footer
- Shows additional build info in tooltip

## Rebuilding with Version

### Using PowerShell Script (Recommended)
```powershell
# Development rebuild
.\rebuild-docker.ps1

# Production rebuild
.\rebuild-docker.ps1 -Environment prod

# Rebuild without cache
.\rebuild-docker.ps1 -NoCache
```

The script automatically:
- Reads version from `VERSION` file
- Gets build date
- Gets Git commit hash (if available)
- Passes all info to Docker build

### Manual Rebuild
```powershell
# Set version from VERSION file
$APP_VERSION = (Get-Content VERSION).Trim()
$BUILD_DATE = Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ"

# Set environment variables
$env:APP_VERSION = $APP_VERSION
$env:BUILD_DATE = $BUILD_DATE

# Rebuild
docker-compose build
docker-compose up -d
```

### Production Build
```powershell
# Set version
$env:APP_VERSION = (Get-Content VERSION).Trim()
$env:BUILD_DATE = Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ"

# Rebuild production
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d
```

## Updating Version

To update the version:

1. **Edit `VERSION` file:**
   ```
   2.6.0
   ```

2. **Rebuild Docker containers:**
   ```powershell
   .\rebuild-docker.ps1
   ```

3. **Verify version display:**
   - Check login page
   - Check footer in application
   - Check API: `GET http://localhost:8000/api/v1/version`

## Version Synchronization

The system ensures version sync through:

1. **Build Time:**
   - Version read from `VERSION` file
   - Passed to Docker as build arg
   - Baked into container image

2. **Runtime:**
   - Backend reads from `VERSION` file or env var
   - API endpoint returns current version
   - Frontend fetches from API

3. **Display:**
   - Version shown in UI
   - Tooltip shows build details
   - Always matches running code

## Files Modified

### Backend
- `backend/app/api/v1/endpoints/version.py` - Version API endpoint
- `backend/app/api/v1/api.py` - Added version router
- `backend/main.py` - Uses version from VERSION file
- `backend/Dockerfile` - Accepts APP_VERSION build arg

### Frontend
- `frontend/src/components/VersionDisplay.tsx` - Version display component
- `frontend/src/components/Layout.tsx` - Added version footer
- `frontend/src/pages/Login.tsx` - Shows version on login
- `frontend/src/services/api.ts` - Added versionAPI

### Docker
- `docker-compose.yml` - Passes version to backend build
- `docker-compose.prod.yml` - Passes version to production build

### Scripts
- `rebuild-docker.ps1` - Automated rebuild script with version management

## Troubleshooting

### Version not updating?
1. Ensure `VERSION` file is updated
2. Rebuild containers: `.\rebuild-docker.ps1`
3. Clear browser cache
4. Check API: `curl http://localhost:8000/api/v1/version`

### Version shows as "2.5.0" but file says different?
- Containers need to be rebuilt
- Run `.\rebuild-docker.ps1` to sync

### Version API returns 404?
- Ensure backend is running
- Check router is included in `api.py`
- Verify endpoint: `GET /api/v1/version`

### Version not displaying in UI?
- Check browser console for errors
- Verify API is accessible
- Check `VersionDisplay` component is imported

## Best Practices

1. **Always update `VERSION` file** before rebuilding
2. **Use the rebuild script** to ensure version sync
3. **Check version display** after deployment
4. **Include version in commit messages** when updating
5. **Document version changes** in CHANGELOG.md

## Example Workflow

```powershell
# 1. Update version
echo "2.6.0" > VERSION

# 2. Commit version change
git add VERSION
git commit -m "chore: bump version to 2.6.0"

# 3. Rebuild with new version
.\rebuild-docker.ps1

# 4. Verify
curl http://localhost:8000/api/v1/version
# Should return: {"version": "2.6.0", ...}

# 5. Check UI
# Open http://localhost:3000 and verify version display
```

---

**Last Updated:** 2025-01-15  
**Version System:** v1.0

