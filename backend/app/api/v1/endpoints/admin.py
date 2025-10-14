"""Admin endpoints for system administration"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_
from typing import List, Optional
from pydantic import BaseModel, EmailStr

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.security import get_password_hash
from app.models.tenant import User, Tenant, UserRole, TenantStatus
from app.models.crm import Customer

router = APIRouter()


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    tenant_id: str
    tenant_name: str
    company_name: Optional[str] = None
    created_at: str
    
    class Config:
        from_attributes = True


class ResetPasswordRequest(BaseModel):
    new_password: str


class DashboardStats(BaseModel):
    active_tenants: int
    trial_tenants: int
    suspended_tenants: int
    total_users: int


class TenantSummary(BaseModel):
    id: str
    name: str
    slug: str
    status: str
    created_at: str
    
    class Config:
        from_attributes = True


class DashboardResponse(BaseModel):
    stats: DashboardStats
    recent_tenants: List[TenantSummary]


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get admin dashboard statistics"""
    # Check if user is admin
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Count tenants by status
        active_tenants = db.execute(
            select(func.count(Tenant.id)).where(
                Tenant.status == TenantStatus.ACTIVE
            )
        ).scalar()
        
        trial_tenants = db.execute(
            select(func.count(Tenant.id)).where(
                Tenant.status == TenantStatus.TRIAL
            )
        ).scalar()
        
        suspended_tenants = db.execute(
            select(func.count(Tenant.id)).where(
                Tenant.status == TenantStatus.SUSPENDED
            )
        ).scalar()
        
        # Count total users
        total_users = db.execute(
            select(func.count(User.id))
        ).scalar()
        
        # Get recent tenants (last 5)
        stmt = select(Tenant).order_by(Tenant.created_at.desc()).limit(5)
        
        result = db.execute(stmt)
        recent_tenants_data = result.scalars().all()
        
        recent_tenants = [
            TenantSummary(
                id=str(tenant.id),
                name=tenant.name,
                slug=tenant.slug,
                status=tenant.status.value if hasattr(tenant.status, 'value') else str(tenant.status),
                created_at=tenant.created_at.isoformat()
            )
            for tenant in recent_tenants_data
        ]
        
        return DashboardResponse(
            stats=DashboardStats(
                active_tenants=active_tenants or 0,
                trial_tenants=trial_tenants or 0,
                suspended_tenants=suspended_tenants or 0,
                total_users=total_users or 0
            ),
            recent_tenants=recent_tenants
        )
        
    except Exception as e:
        print(f"[ERROR] Failed to load dashboard stats: {e}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users", response_model=List[UserResponse])
async def list_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all users across all tenants (admin only)"""
    # Check if user is admin
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Query all users with their tenant information (including company_name)
        stmt = select(User, Tenant.name, Tenant.company_name).join(
            Tenant, User.tenant_id == Tenant.id
        ).order_by(Tenant.name, User.email)
        
        result = db.execute(stmt)
        rows = result.all()
        
        users = []
        for user, tenant_name, company_name in rows:
            users.append(UserResponse(
                id=str(user.id),
                email=user.email,
                full_name=user.full_name,
                role=user.role.value if hasattr(user.role, 'value') else str(user.role),
                is_active=user.is_active,
                tenant_id=str(user.tenant_id),
                tenant_name=tenant_name,
                company_name=company_name,
                created_at=user.created_at.isoformat()
            ))
        
        return users
        
    except Exception as e:
        print(f"[ERROR] Failed to list users: {e}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: str,
    request: ResetPasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reset a user's password (admin only)"""
    # Check if user is admin
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Find the user
        stmt = select(User).where(User.id == user_id)
        result = db.execute(stmt)
        user = result.scalars().first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Hash and update the password
        user.hashed_password = get_password_hash(request.new_password)
        db.commit()
        
        return {
            "success": True,
            "message": f"Password reset successfully for {user.email}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Failed to reset password: {e}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


class TenantListResponse(BaseModel):
    id: str
    name: str
    company_name: str | None
    slug: str
    domain: str | None
    status: str
    plan: str
    created_at: str
    
    class Config:
        from_attributes = True


class PaginatedTenantsResponse(BaseModel):
    total: int
    page: int
    size: int
    tenants: List[TenantListResponse]


class TenantCreateRequest(BaseModel):
    name: str
    slug: str
    domain: str | None = None
    admin_email: EmailStr
    admin_password: str
    admin_first_name: str
    admin_last_name: str
    plan: str = "trial"


class TenantUpdateRequest(BaseModel):
    name: str | None = None
    status: str | None = None
    plan: str | None = None


@router.get("/tenants", response_model=PaginatedTenantsResponse)
async def list_tenants_paginated(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: str = Query(""),
    status: str = Query(""),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get paginated list of tenants with search and filter"""
    # Check if user is admin
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Build base query
        stmt = select(Tenant)
        
        # Apply search filter
        if search:
            stmt = stmt.where(
                or_(
                    Tenant.name.ilike(f"%{search}%"),
                    Tenant.slug.ilike(f"%{search}%")
                )
            )
        
        # Apply status filter
        if status:
            if status == "active":
                stmt = stmt.where(Tenant.status == TenantStatus.ACTIVE)
            elif status == "trial":
                stmt = stmt.where(Tenant.status == TenantStatus.TRIAL)
            elif status == "suspended":
                stmt = stmt.where(Tenant.status == TenantStatus.SUSPENDED)
        
        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = db.execute(count_stmt).scalar()
        
        # Apply pagination
        stmt = stmt.order_by(Tenant.created_at.desc())
        stmt = stmt.offset((page - 1) * size).limit(size)
        
        # Execute query
        result = db.execute(stmt)
        tenants_data = result.scalars().all()
        
        tenants = [
            TenantListResponse(
                id=str(tenant.id),
                name=tenant.name,
                company_name=tenant.company_name,
                slug=tenant.slug,
                domain=tenant.domain,
                status=tenant.status.value if hasattr(tenant.status, 'value') else str(tenant.status),
                plan=tenant.plan,
                created_at=tenant.created_at.isoformat()
            )
            for tenant in tenants_data
        ]
        
        return PaginatedTenantsResponse(
            total=total or 0,
            page=page,
            size=size,
            tenants=tenants
        )
        
    except Exception as e:
        print(f"[ERROR] Failed to list tenants: {e}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tenants")
async def create_tenant_admin(
    tenant_data: TenantCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new tenant (admin only)"""
    # Check if user is admin
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Check if slug already exists
        existing = db.query(Tenant).filter(Tenant.slug == tenant_data.slug).first()
        if existing:
            raise HTTPException(status_code=400, detail="Tenant slug already exists")
        
        # Check if email already exists
        existing_user = db.query(User).filter(User.email == tenant_data.admin_email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Admin email already exists")
        
        # Create tenant
        import uuid
        tenant = Tenant(
            id=str(uuid.uuid4()),
            name=tenant_data.name,
            slug=tenant_data.slug,
            domain=tenant_data.domain,
            status=TenantStatus.TRIAL if tenant_data.plan == "trial" else TenantStatus.ACTIVE,
            plan=tenant_data.plan,
            settings={}
        )
        db.add(tenant)
        db.flush()
        
        # Create admin user
        admin_user = User(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            email=tenant_data.admin_email,
            username=f"{tenant_data.slug}_admin",
            first_name=tenant_data.admin_first_name,
            last_name=tenant_data.admin_last_name,
            hashed_password=get_password_hash(tenant_data.admin_password),
            is_active=True,
            is_verified=True,
            role=UserRole.TENANT_ADMIN,
            permissions=[]
        )
        db.add(admin_user)
        db.commit()
        
        return {
            "success": True,
            "message": "Tenant created successfully",
            "tenant_id": str(tenant.id)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Failed to create tenant: {e}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/tenants/{tenant_id}")
async def update_tenant_admin(
    tenant_id: str,
    tenant_data: TenantUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a tenant (admin only)"""
    # Check if user is admin
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        if tenant_data.name:
            tenant.name = tenant_data.name
        if tenant_data.status:
            # Convert string to enum
            if tenant_data.status == "active":
                tenant.status = TenantStatus.ACTIVE
            elif tenant_data.status == "trial":
                tenant.status = TenantStatus.TRIAL
            elif tenant_data.status == "suspended":
                tenant.status = TenantStatus.SUSPENDED
        if tenant_data.plan:
            tenant.plan = tenant_data.plan
        
        db.commit()
        
        return {
            "success": True,
            "message": "Tenant updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Failed to update tenant: {e}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/tenants/{tenant_id}")
async def deactivate_tenant_admin(
    tenant_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Deactivate/suspend a tenant (admin only)"""
    # Check if user is admin
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        tenant.status = TenantStatus.SUSPENDED
        db.commit()
        
        return {
            "success": True,
            "message": "Tenant deactivated successfully"
        }
        
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Failed to deactivate tenant: {e}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


# API Keys endpoints
class ApiKeyResponse(BaseModel):
    service: str
    key: str | None
    is_configured: bool
    last_tested: str | None
    status: str


@router.get("/api-keys", response_model=List[ApiKeyResponse])
async def get_global_api_keys(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get global API keys (admin only)"""
    # Check if user is admin
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Get the first tenant (system tenant) for global keys
        system_tenant = db.query(Tenant).filter(Tenant.slug == "ccs").first()
        
        if not system_tenant:
            return []
        
        return [
            ApiKeyResponse(
                service="OpenAI",
                key=system_tenant.openai_api_key,
                is_configured=bool(system_tenant.openai_api_key),
                last_tested=None,
                status="not_configured" if not system_tenant.openai_api_key else "configured"
            ),
            ApiKeyResponse(
                service="Companies House",
                key=system_tenant.companies_house_api_key,
                is_configured=bool(system_tenant.companies_house_api_key),
                last_tested=None,
                status="not_configured" if not system_tenant.companies_house_api_key else "configured"
            ),
            ApiKeyResponse(
                service="Google Maps",
                key=system_tenant.google_maps_api_key,
                is_configured=bool(system_tenant.google_maps_api_key),
                last_tested=None,
                status="not_configured" if not system_tenant.google_maps_api_key else "configured"
            )
        ]
        
    except Exception as e:
        print(f"[ERROR] Failed to get API keys: {e}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


# Old endpoint removed - duplicate functionality moved to line 854


# API Usage endpoints
class ApiUsageResponse(BaseModel):
    service: str
    calls_this_month: int
    limit: int
    percentage: float


@router.get("/api-usage", response_model=List[ApiUsageResponse])
async def get_api_usage(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get API usage statistics (admin only)"""
    # Check if user is admin
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Get all tenants and sum up their usage
        tenants = db.query(Tenant).all()
        
        total_calls = sum(t.api_calls_this_month or 0 for t in tenants)
        total_limit = sum(t.api_limit_monthly or 0 for t in tenants)
        
        percentage = (total_calls / total_limit * 100) if total_limit > 0 else 0
        
        return [
            ApiUsageResponse(
                service="OpenAI",
                calls_this_month=total_calls,
                limit=total_limit,
                percentage=round(percentage, 2)
            ),
            ApiUsageResponse(
                service="Companies House",
                calls_this_month=0,
                limit=10000,
                percentage=0
            ),
            ApiUsageResponse(
                service="Google Maps",
                calls_this_month=0,
                limit=10000,
                percentage=0
            )
        ]
        
    except Exception as e:
        print(f"[ERROR] Failed to get API usage: {e}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


# Settings endpoints
class SystemSettings(BaseModel):
    system_name: str
    default_tenant: str
    max_api_calls_month: int
    trial_period_days: int
    auto_suspend_inactive: bool
    inactivity_threshold_days: int
    smtp_host: str | None
    smtp_port: int
    smtp_username: str | None
    smtp_password: str | None
    smtp_from_email: str | None
    enable_tls: bool
    session_timeout_minutes: int
    password_min_length: int
    require_special_char: bool
    password_enable_2fa: bool
    max_login_attempts: int
    lockout_duration_minutes: int
    auto_backup: bool
    backup_frequency: str
    backup_retention_days: int
    backup_location: str


@router.get("/settings")
async def get_system_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get system settings (admin only)"""
    # Check if user is admin
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Get the system tenant for settings
        system_tenant = db.query(Tenant).filter(Tenant.slug == "ccs").first()
        
        if not system_tenant or not system_tenant.settings:
            # Return default settings
            return SystemSettings(
                system_name="CCS Quote Tool",
                default_tenant="ccs",
                max_api_calls_month=100000,
                trial_period_days=30,
                auto_suspend_inactive=True,
                inactivity_threshold_days=90,
                smtp_host="",
                smtp_port=587,
                smtp_username="",
                smtp_password="",
                smtp_from_email="",
                enable_tls=True,
                session_timeout_minutes=60,
                password_min_length=8,
                require_special_char=True,
                password_enable_2fa=False,
                max_login_attempts=5,
                lockout_duration_minutes=15,
                auto_backup=True,
                backup_frequency="Daily",
                backup_retention_days=30,
                backup_location="/backups"
            )
        
        settings = system_tenant.settings
        
        return SystemSettings(
            system_name=settings.get("system_name", "CCS Quote Tool"),
            default_tenant=settings.get("default_tenant", "ccs"),
            max_api_calls_month=settings.get("max_api_calls_month", 100000),
            trial_period_days=settings.get("trial_period_days", 30),
            auto_suspend_inactive=settings.get("auto_suspend_inactive", True),
            inactivity_threshold_days=settings.get("inactivity_threshold_days", 90),
            smtp_host=settings.get("smtp_host", ""),
            smtp_port=settings.get("smtp_port", 587),
            smtp_username=settings.get("smtp_username", ""),
            smtp_password=settings.get("smtp_password", ""),
            smtp_from_email=settings.get("smtp_from_email", ""),
            enable_tls=settings.get("enable_tls", True),
            session_timeout_minutes=settings.get("session_timeout_minutes", 60),
            password_min_length=settings.get("password_min_length", 8),
            require_special_char=settings.get("require_special_char", True),
            password_enable_2fa=settings.get("password_enable_2fa", False),
            max_login_attempts=settings.get("max_login_attempts", 5),
            lockout_duration_minutes=settings.get("lockout_duration_minutes", 15),
            auto_backup=settings.get("auto_backup", True),
            backup_frequency=settings.get("backup_frequency", "Daily"),
            backup_retention_days=settings.get("backup_retention_days", 30),
            backup_location=settings.get("backup_location", "/backups")
        )
        
    except Exception as e:
        print(f"[ERROR] Failed to get settings: {e}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/settings")
async def update_system_settings(
    settings_data: SystemSettings,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update system settings (admin only)"""
    # Check if user is admin
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Get the system tenant for settings
        system_tenant = db.query(Tenant).filter(Tenant.slug == "ccs").first()
        
        if not system_tenant:
            raise HTTPException(status_code=404, detail="System tenant not found")
        
        # Update settings
        if not system_tenant.settings:
            system_tenant.settings = {}
        
        system_tenant.settings.update({
            "system_name": settings_data.system_name,
            "default_tenant": settings_data.default_tenant,
            "max_api_calls_month": settings_data.max_api_calls_month,
            "trial_period_days": settings_data.trial_period_days,
            "auto_suspend_inactive": settings_data.auto_suspend_inactive,
            "inactivity_threshold_days": settings_data.inactivity_threshold_days,
            "smtp_host": settings_data.smtp_host,
            "smtp_port": settings_data.smtp_port,
            "smtp_username": settings_data.smtp_username,
            "smtp_password": settings_data.smtp_password,
            "smtp_from_email": settings_data.smtp_from_email,
            "enable_tls": settings_data.enable_tls,
            "session_timeout_minutes": settings_data.session_timeout_minutes,
            "password_min_length": settings_data.password_min_length,
            "require_special_char": settings_data.require_special_char,
            "password_enable_2fa": settings_data.password_enable_2fa,
            "max_login_attempts": settings_data.max_login_attempts,
            "lockout_duration_minutes": settings_data.lockout_duration_minutes,
            "auto_backup": settings_data.auto_backup,
            "backup_frequency": settings_data.backup_frequency,
            "backup_retention_days": settings_data.backup_retention_days,
            "backup_location": settings_data.backup_location
        })
        
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(system_tenant, 'settings')
        
        db.commit()
        
        return {
            "success": True,
            "message": "System settings updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Failed to update settings: {e}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


# ==================== GLOBAL API KEYS ====================

class GlobalAPIKeysResponse(BaseModel):
    openai_api_key: Optional[str] = None
    companies_house_api_key: Optional[str] = None
    google_maps_api_key: Optional[str] = None


class GlobalAPIKeysUpdate(BaseModel):
    openai_api_key: Optional[str] = None
    companies_house_api_key: Optional[str] = None
    google_maps_api_key: Optional[str] = None


@router.get("/api-keys", response_model=GlobalAPIKeysResponse)
async def get_global_api_keys(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get global/system-wide API keys from database
    
    These keys act as fallbacks when tenant-specific keys are not configured.
    Stored in database in a special 'System' tenant for easy management.
    Falls back to environment variables if not set in database.
    """
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        import os
        
        # Try to get System tenant from database
        system_tenant = db.query(Tenant).filter(Tenant.name == "System").first()
        
        if system_tenant:
            # Return keys from database
            return GlobalAPIKeysResponse(
                openai_api_key=system_tenant.openai_api_key or os.getenv("OPENAI_API_KEY", ""),
                companies_house_api_key=system_tenant.companies_house_api_key or os.getenv("COMPANIES_HOUSE_API_KEY", ""),
                google_maps_api_key=system_tenant.google_maps_api_key or os.getenv("GOOGLE_MAPS_API_KEY", "")
            )
        else:
            # Fallback to environment variables if System tenant doesn't exist
            return GlobalAPIKeysResponse(
                openai_api_key=os.getenv("OPENAI_API_KEY", ""),
                companies_house_api_key=os.getenv("COMPANIES_HOUSE_API_KEY", ""),
                google_maps_api_key=os.getenv("GOOGLE_MAPS_API_KEY", "")
            )
    except Exception as e:
        print(f"[ERROR] Failed to get global API keys: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api-keys")
async def update_global_api_keys(
    api_keys: GlobalAPIKeysUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    print(f"[DEBUG] Received API keys update request")
    print(f"[DEBUG] api_keys type: {type(api_keys)}")
    print(f"[DEBUG] api_keys data: {api_keys}")
    """Update global/system-wide API keys in database
    
    IMPORTANT: These keys act as fallbacks for all tenants.
    When a tenant doesn't have their own API keys, these system-wide keys are used.
    
    Keys are stored in the database in a special 'System' tenant.
    This tenant is created automatically if it doesn't exist.
    """
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        from app.models.tenant import TenantStatus
        import uuid
        
        # Get or create System tenant
        system_tenant = db.query(Tenant).filter(Tenant.name == "System").first()
        
        if not system_tenant:
            # Create System tenant for storing global API keys
            system_tenant = Tenant(
                id=str(uuid.uuid4()),
                name="System",
                company_name="System",
                slug="system",
                status=TenantStatus.ACTIVE,
                plan="system"
            )
            db.add(system_tenant)
            db.flush()
        
        # Update API keys
        if api_keys.openai_api_key is not None:
            system_tenant.openai_api_key = api_keys.openai_api_key.strip() or None
        if api_keys.companies_house_api_key is not None:
            system_tenant.companies_house_api_key = api_keys.companies_house_api_key.strip() or None
        if api_keys.google_maps_api_key is not None:
            system_tenant.google_maps_api_key = api_keys.google_maps_api_key.strip() or None
        
        db.commit()
        
        return {
            "success": True,
            "message": "System-wide API keys saved to database successfully"
        }
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Failed to update global API keys: {e}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-openai")
async def test_openai_api(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Test OpenAI API connection using database keys (with env fallback)"""
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        import os
        import httpx
        
        # Check database first (System tenant), then fall back to environment
        api_key = None
        system_tenant = db.query(Tenant).filter(Tenant.name == "System").first()
        if system_tenant and system_tenant.openai_api_key:
            api_key = system_tenant.openai_api_key
        else:
            api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            return {"success": False, "message": "OpenAI API key not configured"}
        
        # Test with a simple API call
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=10.0
            )
            
            if response.status_code == 200:
                return {"success": True, "message": "OpenAI API connection successful"}
            else:
                return {"success": False, "message": f"API returned status {response.status_code}"}
                
    except Exception as e:
        return {"success": False, "message": f"Connection failed: {str(e)}"}


@router.post("/test-companies-house")
async def test_companies_house_api(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Test Companies House API connection using database keys (with env fallback)"""
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        import os
        import httpx
        from base64 import b64encode
        
        # Check database first (System tenant), then fall back to environment
        api_key = None
        system_tenant = db.query(Tenant).filter(Tenant.name == "System").first()
        if system_tenant and system_tenant.companies_house_api_key:
            api_key = system_tenant.companies_house_api_key
        else:
            api_key = os.getenv("COMPANIES_HOUSE_API_KEY")
        
        if not api_key:
            return {"success": False, "message": "Companies House API key not configured"}
        
        # Test with a simple search
        credentials = b64encode(f"{api_key}:".encode()).decode()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.company-information.service.gov.uk/search/companies?q=test",
                headers={"Authorization": f"Basic {credentials}"},
                timeout=10.0
            )
            
            if response.status_code == 200:
                return {"success": True, "message": "Companies House API connection successful"}
            else:
                return {"success": False, "message": f"API returned status {response.status_code}"}
                
    except Exception as e:
        return {"success": False, "message": f"Connection failed: {str(e)}"}


@router.post("/test-google-maps")
async def test_google_maps_api(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Test Google Maps API connection using database keys (with env fallback)"""
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        import os
        import httpx
        
        # Check database first (System tenant), then fall back to environment
        api_key = None
        system_tenant = db.query(Tenant).filter(Tenant.name == "System").first()
        if system_tenant and system_tenant.google_maps_api_key:
            api_key = system_tenant.google_maps_api_key
        else:
            api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        
        if not api_key:
            return {"success": False, "message": "Google Maps API key not configured"}
        
        # Test with a simple geocoding request
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://maps.googleapis.com/maps/api/geocode/json",
                params={"address": "London", "key": api_key},
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "OK":
                    return {"success": True, "message": "Google Maps API connection successful"}
                else:
                    return {"success": False, "message": f"API error: {data.get('status')}"}
            else:
                return {"success": False, "message": f"API returned status {response.status_code}"}
                
    except Exception as e:
        return {"success": False, "message": f"Connection failed: {str(e)}"}


@router.post("/reset-stuck-tasks")
async def reset_stuck_ai_tasks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Reset any stuck AI analysis tasks
    Admin only - manually trigger cleanup of running/queued tasks
    """
    # Only allow admin users
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Find all customers with active AI analysis tasks
        stuck_customers = db.query(Customer).filter(
            Customer.ai_analysis_status.in_(['running', 'queued'])
        ).all()
        
        if not stuck_customers:
            return {
                "success": True,
                "message": "No stuck AI analysis tasks found",
                "reset_count": 0,
                "customers": []
            }
        
        reset_list = []
        for customer in stuck_customers:
            reset_list.append({
                "id": str(customer.id),
                "company_name": customer.company_name,
                "status": customer.ai_analysis_status,
                "task_id": customer.ai_analysis_task_id
            })
            
            customer.ai_analysis_status = None
            customer.ai_analysis_task_id = None
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Successfully reset {len(stuck_customers)} stuck AI analysis task(s)",
            "reset_count": len(stuck_customers),
            "customers": reset_list
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to reset tasks: {str(e)}")
