#!/usr/bin/env python3
"""
Tenant management endpoints
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_tenants():
    """List all tenants (super admin only)"""
    return {"message": "Tenants endpoint - coming soon"}


@router.post("/")
async def create_tenant():
    """Create new tenant"""
    return {"message": "Create tenant - coming soon"}

