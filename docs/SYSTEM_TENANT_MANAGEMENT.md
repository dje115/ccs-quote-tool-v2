# System Tenant Management Guide

## Overview

The System Tenant is a special tenant created automatically on application startup. It serves as a centralized location for storing global API keys and system-wide configuration that can be used as fallbacks for all tenants.

## Auto-Seeding

The system tenant is automatically created during database initialization (`init_db()`) in `backend/app/core/database.py`. This happens:

1. **On application startup** - When the backend starts, `init_db()` is called
2. **On database rebuild** - When tables are recreated, the system tenant is re-seeded
3. **Idempotent** - The creation function checks if the tenant already exists before creating it

## Configuration

The system tenant is configured via environment variables (see `backend/app/core/config.py`):

```bash
# System Tenant Configuration
SYSTEM_TENANT_NAME="System Tenant"              # Default: "System Tenant"
SYSTEM_TENANT_SLUG="system"                     # Default: "system"
SYSTEM_TENANT_ADMIN_EMAIL="system-admin@ccs.local"  # Default: "system-admin@ccs.local"
SYSTEM_TENANT_ADMIN_PASSWORD="<password>"      # Optional, falls back to SUPER_ADMIN_PASSWORD

# API Keys (automatically copied to system tenant on creation)
OPENAI_API_KEY="<key>"
COMPANIES_HOUSE_API_KEY="<key>"
GOOGLE_MAPS_API_KEY="<key>"
```

## Verification

After a rebuild or deployment, verify the system tenant exists:

### Option 1: Using Verification Script

```bash
cd backend
python scripts/verify_system_tenant.py
```

Expected output:
```
✅ System tenant FOUND
   ID: <uuid>
   Slug: system
   Name: System Tenant
   Plan: system

✅ System admin user FOUND
   ID: <uuid>
   Email: system-admin@ccs.local
   Username: system_admin
   Role: SUPER_ADMIN
   Active: True
   Verified: True

📋 API Keys Status:
   OpenAI: ✅ Configured
   Companies House: ✅ Configured
   Google Maps: ✅ Configured
```

### Option 2: Direct Database Query

```sql
-- Check system tenant
SELECT id, slug, name, plan 
FROM tenants 
WHERE plan = 'system' OR slug = 'system';

-- Check system admin user
SELECT id, email, username, role, is_active, is_verified
FROM users
WHERE email = 'system-admin@ccs.local' 
  AND tenant_id = (SELECT id FROM tenants WHERE plan = 'system');

-- Check API keys
SELECT 
    openai_api_key IS NOT NULL as has_openai,
    companies_house_api_key IS NOT NULL as has_companies_house,
    google_maps_api_key IS NOT NULL as has_google_maps
FROM tenants
WHERE plan = 'system';
```

## API Key Management

### Viewing System API Keys

System API keys can be viewed and managed through:

1. **Admin Portal** - Navigate to Settings → API Keys
2. **API Endpoint** - `GET /api/v1/admin/global-api-keys` (requires authentication)
3. **Database** - Direct query to `tenants` table where `plan = 'system'`

### Rotating API Keys

#### Method 1: Admin Portal (Recommended)

1. Log in to the admin portal as a super admin
2. Navigate to **Settings** → **API Keys**
3. Update the desired API key
4. Click **Save**
5. Keys are automatically updated in the system tenant

#### Method 2: API Endpoint

```bash
# Update system API keys via API
curl -X PUT http://localhost:8000/api/v1/admin/global-api-keys \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "openai_api_key": "sk-new-key-here",
    "companies_house_api_key": "new-key-here",
    "google_maps_api_key": "new-key-here"
  }'
```

#### Method 3: Direct Database Update

```sql
-- Update API keys directly (use with caution)
UPDATE tenants
SET 
    openai_api_key = 'sk-new-key-here',
    companies_house_api_key = 'new-key-here',
    google_maps_api_key = 'new-key-here',
    updated_at = NOW()
WHERE plan = 'system';
```

**Note:** After direct database updates, you may need to:
- Clear Redis cache (if API keys are cached)
- Restart the backend service to pick up changes

### Key Rotation Best Practices

1. **Test First** - Always test new keys in a development environment
2. **Update Gradually** - Update one key at a time to minimize disruption
3. **Monitor** - Watch for errors after key rotation
4. **Document** - Keep a record of when keys were rotated
5. **Backup** - Keep old keys for 24-48 hours in case of rollback

## System Tenant Usage

### How System Keys Work

1. **Tenant-Specific Keys First** - Each tenant can have its own API keys
2. **System Tenant Fallback** - If a tenant doesn't have a key, the system tenant's key is used
3. **Environment Variable Fallback** - If system tenant doesn't have a key, environment variables are checked

### Key Resolution Order

For any API key (OpenAI, Companies House, Google Maps):

1. ✅ Tenant-specific key (from `tenants` table, `tenant_id = <current_tenant>`)
2. ✅ System tenant key (from `tenants` table, `plan = 'system'`)
3. ✅ Environment variable (from `settings.OPENAI_API_KEY`, etc.)

This ensures maximum flexibility:
- Tenants can have their own keys (multi-tenant isolation)
- System-wide keys provide fallback (cost efficiency)
- Environment variables provide ultimate fallback (deployment flexibility)

## Troubleshooting

### System Tenant Not Created

**Symptoms:**
- API calls fail with "No API key configured"
- Verification script shows tenant not found

**Solutions:**

1. **Check Startup Logs**
   ```bash
   docker-compose logs backend | grep -i "system tenant"
   ```

2. **Manually Trigger Creation**
   ```python
   # In Python shell or script
   from app.core.database import create_system_tenant
   import asyncio
   asyncio.run(create_system_tenant())
   ```

3. **Check Environment Variables**
   ```bash
   # Ensure required env vars are set
   echo $SYSTEM_TENANT_SLUG
   echo $SYSTEM_TENANT_ADMIN_EMAIL
   ```

### System Admin User Missing

**Symptoms:**
- Cannot log in with `system-admin@ccs.local`
- Verification script shows user not found

**Solutions:**

1. **Check if tenant exists first**
   ```sql
   SELECT id FROM tenants WHERE plan = 'system';
   ```

2. **Manually create admin user**
   ```python
   from app.core.database import SessionLocal, pwd_context, SUPER_ADMIN_PERMISSIONS
   from app.models.tenant import User, UserRole
   from app.core.config import settings
   import uuid
   
   db = SessionLocal()
   tenant = db.query(Tenant).filter(Tenant.plan == 'system').first()
   
   if tenant:
       admin = User(
           id=str(uuid.uuid4()),
           tenant_id=tenant.id,
           email=settings.SYSTEM_TENANT_ADMIN_EMAIL,
           username="system_admin",
           first_name="System",
           last_name="Admin",
           hashed_password=pwd_context.hash(settings.SUPER_ADMIN_PASSWORD),
           is_active=True,
           is_verified=True,
           role=UserRole.SUPER_ADMIN,
           permissions=list(SUPER_ADMIN_PERMISSIONS)
       )
       db.add(admin)
       db.commit()
   ```

### API Keys Not Working

**Symptoms:**
- API calls fail even though keys are configured
- Keys show as configured but requests fail

**Solutions:**

1. **Verify Key Format**
   - OpenAI: Should start with `sk-`
   - Companies House: Should be a valid API key string
   - Google Maps: Should be a valid API key string

2. **Check Key Permissions**
   - Ensure keys have correct permissions/scopes
   - Check API provider dashboard for key status

3. **Clear Cache**
   ```python
   # Clear Redis cache if keys are cached
   from app.core.redis import get_redis
   import asyncio
   
   async def clear_cache():
       redis = await get_redis()
       # Clear all API key caches
       await redis.delete("api_keys:*")
   
   asyncio.run(clear_cache())
   ```

4. **Check Logs**
   ```bash
   docker-compose logs backend | grep -i "api key"
   ```

## Security Considerations

1. **System Admin Credentials**
   - Default password should be changed immediately after first login
   - Use strong passwords (minimum 12 characters)
   - Consider enabling 2FA when available

2. **API Key Storage**
   - Keys are stored encrypted at rest (database encryption)
   - Keys are never logged in plain text
   - Keys are only accessible to super admins

3. **Access Control**
   - Only super admin users can view/update system tenant keys
   - Regular tenant admins cannot access system tenant
   - API endpoints require authentication

4. **Audit Trail**
   - Consider logging all API key changes
   - Monitor for unauthorized access attempts
   - Regular security audits

## Related Files

- `backend/app/core/database.py` - System tenant creation
- `backend/app/core/config.py` - Configuration settings
- `backend/app/core/api_keys.py` - API key resolution logic
- `backend/scripts/verify_system_tenant.py` - Verification script
- `backend/app/api/v1/endpoints/admin.py` - Admin API endpoints

## Support

For issues or questions:
1. Check application logs: `docker-compose logs backend`
2. Run verification script: `python scripts/verify_system_tenant.py`
3. Check database directly: `psql -U <user> -d <database>`
4. Review this documentation



