#!/usr/bin/env python3
"""
Quote management endpoints
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_quotes():
    """List all quotes"""
    return {"message": "Quotes endpoint - coming soon"}

