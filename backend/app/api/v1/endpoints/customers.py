#!/usr/bin/env python3
"""
Customer management endpoints
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_customers():
    """List all customers"""
    return {"message": "Customers endpoint - coming soon"}


@router.post("/")
async def create_customer():
    """Create new customer"""
    return {"message": "Create customer - coming soon"}

