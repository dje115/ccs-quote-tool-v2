#!/usr/bin/env python3
"""
Campaign management endpoints
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_campaigns():
    """List all campaigns"""
    return {"message": "Campaigns endpoint - coming soon"}

