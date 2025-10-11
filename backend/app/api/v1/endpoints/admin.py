"""Admin endpoints for system administration"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from typing import List
from pydantic import BaseModel

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.security import get_password_hash
from app.models.tenant import User, Tenant, UserRole

router = APIRouter()


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    tenant_id: str
    tenant_name: str
    created_at: str
    
    class Config:
        from_attributes = True


class ResetPasswordRequest(BaseModel):
    new_password: str


@router.get("/users", response_model=List[UserResponse])
async def list_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all users across all tenants (admin only)"""
    # Check if user is admin
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Query all users with their tenant information
        stmt = select(User, Tenant.name).join(
            Tenant, User.tenant_id == Tenant.id
        ).where(
            User.is_deleted == False
        ).order_by(Tenant.name, User.full_name)
        
        result = db.execute(stmt)
        rows = result.all()
        
        users = []
        for user, tenant_name in rows:
            users.append(UserResponse(
                id=str(user.id),
                email=user.email,
                full_name=user.full_name,
                role=user.role.value if hasattr(user.role, 'value') else str(user.role),
                is_active=user.is_active,
                tenant_id=str(user.tenant_id),
                tenant_name=tenant_name,
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
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Find the user
        stmt = select(User).where(User.id == user_id, User.is_deleted == False)
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
