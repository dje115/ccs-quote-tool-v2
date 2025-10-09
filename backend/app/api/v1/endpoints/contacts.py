#!/usr/bin/env python3
"""
Contact management endpoints
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_contacts():
    """List all contacts"""
    return {"message": "Contacts endpoint - coming soon"}

