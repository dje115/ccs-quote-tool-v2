#!/usr/bin/env python3
"""
Main API router for v1
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, tenants, users, customers, contacts, leads, campaigns, quotes, settings, translation, ai_analysis

# Create main API router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(tenants.router, prefix="/tenants", tags=["tenants"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(customers.router, prefix="/customers", tags=["customers"])
api_router.include_router(contacts.router, prefix="/contacts", tags=["contacts"])
api_router.include_router(leads.router, prefix="/leads", tags=["leads"])
api_router.include_router(campaigns.router, prefix="/campaigns", tags=["campaigns"])
api_router.include_router(quotes.router, prefix="/quotes", tags=["quotes"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(translation.router, prefix="/translation", tags=["translation"])
api_router.include_router(ai_analysis.router, prefix="/ai-analysis", tags=["ai-analysis"])

