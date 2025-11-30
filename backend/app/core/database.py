#!/usr/bin/env python3
"""
Database configuration and initialization
"""

from sqlalchemy import create_engine, text, event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool, NullPool
import asyncio
from typing import AsyncGenerator
from contextvars import ContextVar

from app.core.config import settings
from app.models.base import Base
from app.models.tenant import Tenant, User, TenantStatus, UserRole
from app.models.crm import Customer, Contact, CustomerInteraction
from app.models.leads import LeadGenerationCampaign, Lead, LeadInteraction, LeadGenerationPrompt
from app.models.quotes import Quote, QuoteItem, QuoteTemplate, PricingItem
from app.models.product import Product, PricingRule, QuoteVersion
from app.models.ai_prompt import AIPrompt, AIPromptVersion
from app.models.opportunities import Opportunity
from passlib.context import CryptContext
import uuid


# Password hashing - using Argon2 (most secure and modern algorithm)
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# Shared permission set for any seeded super admin accounts
SUPER_ADMIN_PERMISSIONS = [
    "tenant:create",
    "tenant:read",
    "tenant:update",
    "tenant:delete",
    "user:create",
    "user:read",
    "user:update",
    "user:delete",
    "customer:create",
    "customer:read",
    "customer:update",
    "customer:delete",
    "lead:create",
    "lead:read",
    "lead:update",
    "lead:delete",
    "quote:create",
    "quote:read",
    "quote:update",
    "quote:delete",
    "system:admin"
]

# Context variable for storing current tenant ID (for RLS)
# This is set by get_current_tenant() and used by get_db() to set PostgreSQL session variable
current_tenant_id_context: ContextVar[str] = ContextVar('current_tenant_id', default=None)

# Create database engine with connection pooling
# QueuePool allows connection reuse, improving performance for async routes
# pool_size: number of connections to maintain
# max_overflow: additional connections that can be created on demand
# pool_pre_ping: verify connections before using them (handles stale connections)
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,  # Base pool size
    max_overflow=20,  # Additional connections allowed
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,  # Recycle connections after 1 hour
    echo=settings.DEBUG
)

# Create async engine for async operations with connection pooling
# Async engines use AsyncAdaptedQueuePool by default - don't specify poolclass
# The pool parameters work the same way for async engines
async_engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    echo=settings.DEBUG,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600
)

# Create session factories
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionLocal = async_sessionmaker(
    async_engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)


async def init_db():
    """Initialize database with tables and default data"""
    print("🗄️ Initializing database...")
    
    # Create all tables
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create default tenant and super admin
    await create_default_tenant()
    await create_system_tenant()
    
    print("✅ Database initialized successfully")


async def create_default_tenant():
    """Create default CCS tenant and super admin user"""
    async with AsyncSessionLocal() as session:
        # Check if default tenant already exists
        existing_tenant = await session.execute(
            text("SELECT id FROM tenants WHERE slug = :slug"),
            {"slug": settings.DEFAULT_TENANT}
        )
        
        if existing_tenant.fetchone():
            print(f"✅ Default tenant '{settings.DEFAULT_TENANT}' already exists")
            return
        
        # Create default tenant
        tenant = Tenant(
            id=str(uuid.uuid4()),
            name="CCS Quote Tool",
            slug=settings.DEFAULT_TENANT,
            domain="ccs.localhost",
            status=TenantStatus.ACTIVE,
            settings={
                "timezone": "Europe/London",
                "currency": "GBP",
                "date_format": "DD/MM/YYYY",
                "features": {
                    "ai_analysis": True,
                    "lead_generation": True,
                    "quoting": True,
                    "companies_house": True,
                    "google_maps": True,
                    "multilingual": True
                }
            },
            plan="enterprise",
            api_limit_monthly=100000
        )
        
        session.add(tenant)
        await session.flush()
        
        # Create super admin user
        hashed_password = pwd_context.hash(settings.SUPER_ADMIN_PASSWORD)
        
        super_admin = User(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            email=settings.SUPER_ADMIN_EMAIL,
            username="admin",
            first_name="Super",
            last_name="Admin",
            hashed_password=hashed_password,
            is_active=True,
            is_verified=True,
            role=UserRole.SUPER_ADMIN,
            permissions=list(SUPER_ADMIN_PERMISSIONS),
            preferences={
                "theme": "light",
                "language": "en",
                "notifications": True,
                "email_notifications": True
            }
        )
        
        session.add(super_admin)
        await session.commit()
        
        print(f"✅ Created default tenant '{settings.DEFAULT_TENANT}' with super admin user")
        print(f"   Tenant ID: {tenant.id}")
        print(f"   Admin Email: {settings.SUPER_ADMIN_EMAIL}")
        # SECURITY: Never print passwords to console, even in development
        # Password is set via SUPER_ADMIN_PASSWORD environment variable
        if settings.ENVIRONMENT == "development":
            print(f"   ⚠️  Admin Password: Set via SUPER_ADMIN_PASSWORD environment variable")
        else:
            print(f"   Admin Password: [REDACTED - Set via environment variable]")


async def create_system_tenant():
    """Ensure dedicated system tenant exists for storing global API keys and defaults"""
    async with AsyncSessionLocal() as session:
        existing_tenant = await session.execute(
            text("SELECT id FROM tenants WHERE slug = :slug OR plan = :plan"),
            {"slug": settings.SYSTEM_TENANT_SLUG, "plan": "system"}
        )
        
        if existing_tenant.fetchone():
            print(f"✅ System tenant '{settings.SYSTEM_TENANT_SLUG}' already exists")
            return
        
        tenant_id = str(uuid.uuid4())
        tenant = Tenant(
            id=tenant_id,
            name=settings.SYSTEM_TENANT_NAME,
            company_name=settings.SYSTEM_TENANT_NAME,
            slug=settings.SYSTEM_TENANT_SLUG,
            domain=f"{settings.SYSTEM_TENANT_SLUG}.localhost",
            status=TenantStatus.ACTIVE,
            plan="system",
            settings={
                "timezone": "UTC",
                "currency": "GBP",
                "features": {
                    "ai_analysis": True,
                    "lead_generation": True,
                    "quoting": True,
                    "companies_house": True,
                    "google_maps": True,
                    "multilingual": True
                }
            },
            openai_api_key=settings.OPENAI_API_KEY,
            companies_house_api_key=settings.COMPANIES_HOUSE_API_KEY,
            google_maps_api_key=settings.GOOGLE_MAPS_API_KEY,
            api_limit_monthly=100000
        )
        
        session.add(tenant)
        await session.flush()
        
        admin_email = settings.SYSTEM_TENANT_ADMIN_EMAIL
        existing_admin = await session.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": admin_email}
        )
        
        if existing_admin.fetchone():
            print(f"⚠️  System admin user '{admin_email}' already exists; skipping creation")
        else:
            password_source = settings.SYSTEM_TENANT_ADMIN_PASSWORD or settings.SUPER_ADMIN_PASSWORD
            hashed_password = pwd_context.hash(password_source)
            
            system_admin = User(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                email=admin_email,
                username=f"{settings.SYSTEM_TENANT_SLUG}_admin",
                first_name="System",
                last_name="Admin",
                hashed_password=hashed_password,
                is_active=True,
                is_verified=True,
                role=UserRole.SUPER_ADMIN,
                permissions=list(SUPER_ADMIN_PERMISSIONS),
                preferences={
                    "theme": "light",
                    "language": "en",
                    "notifications": True,
                    "email_notifications": True
                }
            )
            session.add(system_admin)
            print(f"✅ Created system admin user '{admin_email}'")
        
        await session.commit()
        print(f"✅ Created system tenant '{settings.SYSTEM_TENANT_SLUG}' for global configuration")


def get_db():
    """
    Get database session.
    
    SECURITY: Tenant isolation is enforced at multiple levels:
    1. Application-level filtering with current_user.tenant_id (see get_current_tenant())
    2. Row-level security (RLS) - sets app.current_tenant_id per transaction
    
    RLS requires tenant context to be set. This is done by:
    - Setting current_tenant_id_context in get_current_tenant()
    - Using SQLAlchemy event listener to set PostgreSQL session variable before queries
    
    All endpoints using get_current_user() or get_current_tenant() automatically
    filter by tenant_id, preventing cross-tenant data access.
    """
    db = SessionLocal()
    
    # Set tenant ID for RLS if available in context
    # This enables database-level row-level security policies
    tenant_id = current_tenant_id_context.get(None)
    if tenant_id:
        _apply_rls_tenant_sync(db, tenant_id)
    
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get async database session with RLS support
    
    SECURITY: Tenant isolation is enforced at multiple levels:
    1. Application-level filtering with current_user.tenant_id (see get_current_tenant())
    2. Row-level security (RLS) - sets app.current_tenant_id per transaction
    
    RLS requires tenant context to be set. This is done by:
    - Setting current_tenant_id_context in get_current_tenant()
    - Setting PostgreSQL session variable before queries
    """
    async with AsyncSessionLocal() as session:
        tenant_id = current_tenant_id_context.get(None)
        if tenant_id:
            await _apply_rls_tenant_async(session, tenant_id)
        yield session


async def close_db():
    """Close database connections"""
    await async_engine.dispose()
    engine.dispose()


# Row-level security setup for multi-tenancy
async def setup_row_level_security():
    """Set up row-level security for tenant isolation"""
    async with async_engine.begin() as conn:
        # Enable RLS on all tenant-aware tables
        tables = [
            "customers", "contacts", "customer_interactions",
            "leads", "lead_interactions", "lead_generation_campaigns", "lead_generation_prompts",
            "quotes", "quote_items", "quote_templates", "pricing_items"
        ]
        
        for table in tables:
            await conn.execute(text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY"))
            
            # Create RLS policy for tenant isolation
            policy_sql = f"""
            CREATE POLICY tenant_isolation_policy ON {table}
            FOR ALL TO PUBLIC
            USING (tenant_id = current_setting('app.current_tenant_id', true))
            """
            
            try:
                await conn.execute(text(policy_sql))
            except Exception as e:
                # Policy might already exist
                if "already exists" not in str(e):
                    print(f"Warning: Could not create RLS policy for {table}: {e}")
        
        print("✅ Row-level security configured for multi-tenancy")


def _escape_tenant_id(value: str) -> str:
    return str(value).replace("'", "''")


def _apply_rls_tenant_sync(db_session, tenant_id: str):
    safe_tenant_id = _escape_tenant_id(tenant_id)
    db_session.execute(text(f"SET LOCAL app.current_tenant_id = '{safe_tenant_id}'"))


async def _apply_rls_tenant_async(async_session, tenant_id: str):
    safe_tenant_id = _escape_tenant_id(tenant_id)
    await async_session.execute(text(f"SET LOCAL app.current_tenant_id = '{safe_tenant_id}'"))
