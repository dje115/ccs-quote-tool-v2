#!/usr/bin/env python3
"""
Lead management endpoints
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_leads():
    """List all leads"""
    return {"message": "Leads endpoint - coming soon"}

