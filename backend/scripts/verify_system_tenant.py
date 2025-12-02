#!/usr/bin/env python3
"""
System Tenant Verification Script

Verifies that the system tenant and admin user are properly configured.
This script can be run after database initialization or rebuilds to confirm
the system tenant auto-seeding worked correctly.
"""

import sys
import os

# Add backend directory to path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, backend_dir)

from sqlalchemy import text
from app.core.database import SessionLocal, AsyncSessionLocal
from app.models.tenant import Tenant, User, UserRole
from app.core.config import settings
import asyncio


async def verify_system_tenant_async():
    """Verify system tenant using async session"""
    async with AsyncSessionLocal() as session:
        # Check for system tenant
        result = await session.execute(
            text("SELECT id, slug, name, plan FROM tenants WHERE plan = 'system' OR slug = :slug"),
            {"slug": settings.SYSTEM_TENANT_SLUG}
        )
        tenant_row = result.fetchone()
        
        if not tenant_row:
            print("❌ System tenant NOT FOUND")
            print(f"   Expected slug: {settings.SYSTEM_TENANT_SLUG}")
            print(f"   Expected plan: 'system'")
            return False
        
        tenant_id, slug, name, plan = tenant_row
        print(f"✅ System tenant FOUND")
        print(f"   ID: {tenant_id}")
        print(f"   Slug: {slug}")
        print(f"   Name: {name}")
        print(f"   Plan: {plan}")
        
        # Check for system admin user
        result = await session.execute(
            text("""
                SELECT id, email, username, role, is_active, is_verified 
                FROM users 
                WHERE tenant_id = :tenant_id AND email = :email
            """),
            {"tenant_id": tenant_id, "email": settings.SYSTEM_TENANT_ADMIN_EMAIL}
        )
        user_row = result.fetchone()
        
        if not user_row:
            print(f"❌ System admin user NOT FOUND")
            print(f"   Expected email: {settings.SYSTEM_TENANT_ADMIN_EMAIL}")
            return False
        
        user_id, email, username, role, is_active, is_verified = user_row
        print(f"✅ System admin user FOUND")
        print(f"   ID: {user_id}")
        print(f"   Email: {email}")
        print(f"   Username: {username}")
        print(f"   Role: {role}")
        print(f"   Active: {is_active}")
        print(f"   Verified: {is_verified}")
        
        # Verify role is SUPER_ADMIN
        if role != UserRole.SUPER_ADMIN.value:
            print(f"⚠️  WARNING: User role is '{role}', expected 'SUPER_ADMIN'")
            return False
        
        # Check API keys
        result = await session.execute(
            text("""
                SELECT 
                    openai_api_key IS NOT NULL as has_openai,
                    companies_house_api_key IS NOT NULL as has_companies_house,
                    google_maps_api_key IS NOT NULL as has_google_maps
                FROM tenants 
                WHERE id = :tenant_id
            """),
            {"tenant_id": tenant_id}
        )
        keys_row = result.fetchone()
        
        if keys_row:
            has_openai, has_companies_house, has_google_maps = keys_row
            print(f"\n📋 API Keys Status:")
            print(f"   OpenAI: {'✅ Configured' if has_openai else '❌ Not configured'}")
            print(f"   Companies House: {'✅ Configured' if has_companies_house else '❌ Not configured'}")
            print(f"   Google Maps: {'✅ Configured' if has_google_maps else '❌ Not configured'}")
        
        print(f"\n✅ System tenant verification PASSED")
        return True


def verify_system_tenant():
    """Verify system tenant using sync session (for compatibility)"""
    db = SessionLocal()
    try:
        # Check for system tenant
        result = db.execute(
            text("SELECT id, slug, name, plan FROM tenants WHERE plan = 'system' OR slug = :slug"),
            {"slug": settings.SYSTEM_TENANT_SLUG}
        )
        tenant_row = result.fetchone()
        
        if not tenant_row:
            print("❌ System tenant NOT FOUND")
            print(f"   Expected slug: {settings.SYSTEM_TENANT_SLUG}")
            print(f"   Expected plan: 'system'")
            return False
        
        tenant_id, slug, name, plan = tenant_row
        print(f"✅ System tenant FOUND")
        print(f"   ID: {tenant_id}")
        print(f"   Slug: {slug}")
        print(f"   Name: {name}")
        print(f"   Plan: {plan}")
        
        # Check for system admin user
        result = db.execute(
            text("""
                SELECT id, email, username, role, is_active, is_verified 
                FROM users 
                WHERE tenant_id = :tenant_id AND email = :email
            """),
            {"tenant_id": tenant_id, "email": settings.SYSTEM_TENANT_ADMIN_EMAIL}
        )
        user_row = result.fetchone()
        
        if not user_row:
            print(f"❌ System admin user NOT FOUND")
            print(f"   Expected email: {settings.SYSTEM_TENANT_ADMIN_EMAIL}")
            return False
        
        user_id, email, username, role, is_active, is_verified = user_row
        print(f"✅ System admin user FOUND")
        print(f"   ID: {user_id}")
        print(f"   Email: {email}")
        print(f"   Username: {username}")
        print(f"   Role: {role}")
        print(f"   Active: {is_active}")
        print(f"   Verified: {is_verified}")
        
        # Verify role is SUPER_ADMIN
        if role != UserRole.SUPER_ADMIN.value:
            print(f"⚠️  WARNING: User role is '{role}', expected 'SUPER_ADMIN'")
            return False
        
        # Check API keys
        result = db.execute(
            text("""
                SELECT 
                    openai_api_key IS NOT NULL as has_openai,
                    companies_house_api_key IS NOT NULL as has_companies_house,
                    google_maps_api_key IS NOT NULL as has_google_maps
                FROM tenants 
                WHERE id = :tenant_id
            """),
            {"tenant_id": tenant_id}
        )
        keys_row = result.fetchone()
        
        if keys_row:
            has_openai, has_companies_house, has_google_maps = keys_row
            print(f"\n📋 API Keys Status:")
            print(f"   OpenAI: {'✅ Configured' if has_openai else '❌ Not configured'}")
            print(f"   Companies House: {'✅ Configured' if has_companies_house else '❌ Not configured'}")
            print(f"   Google Maps: {'✅ Configured' if has_google_maps else '❌ Not configured'}")
        
        print(f"\n✅ System tenant verification PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Error verifying system tenant: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 80)
    print("System Tenant Verification")
    print("=" * 80)
    print(f"Expected tenant slug: {settings.SYSTEM_TENANT_SLUG}")
    print(f"Expected admin email: {settings.SYSTEM_TENANT_ADMIN_EMAIL}")
    print("=" * 80)
    print()
    
    # Try async first, fall back to sync
    try:
        result = asyncio.run(verify_system_tenant_async())
    except Exception as e:
        print(f"Async verification failed, trying sync: {e}")
        result = verify_system_tenant()
    
    sys.exit(0 if result else 1)


