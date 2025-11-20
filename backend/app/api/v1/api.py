#!/usr/bin/env python3
"""
Main API router for v1
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, tenants, users, customers, contacts, leads, campaigns, quotes, settings, translation, ai_analysis, admin, dashboard, activities, sectors, campaign_monitor, planning, ai_prompts, products, version, websocket, suppliers, product_search, building_analysis, pricing_import, provider_keys, emails, storage, pricing_config, support_contracts, contract_renewals, dynamic_pricing, helpdesk, reporting, sla, revenue, customer_portal, customer_portal_access, trends, metrics, quote_prompts

# Create main API router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(tenants.router, prefix="/tenants", tags=["tenants"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(customers.router, prefix="/customers", tags=["customers"])
api_router.include_router(contacts.router, prefix="/contacts", tags=["contacts"])
api_router.include_router(leads.router, prefix="/leads", tags=["leads"])
api_router.include_router(campaigns.router, prefix="/campaigns", tags=["campaigns"])
api_router.include_router(sectors.router, prefix="/sectors", tags=["sectors"])
api_router.include_router(activities.router, prefix="/activities", tags=["activities"])
api_router.include_router(quotes.router, prefix="/quotes", tags=["quotes"])
api_router.include_router(quote_prompts.router)
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(translation.router, prefix="/translation", tags=["translation"])
api_router.include_router(ai_analysis.router, prefix="/ai-analysis", tags=["ai-analysis"])
api_router.include_router(campaign_monitor.router, prefix="/campaign-monitor", tags=["campaign-monitor"])
api_router.include_router(planning.router, prefix="/planning", tags=["planning-applications"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(ai_prompts.router, tags=["ai-prompts"])
api_router.include_router(products.router, tags=["products"])
api_router.include_router(suppliers.router, prefix="/suppliers", tags=["suppliers"])
api_router.include_router(product_search.router, prefix="/products", tags=["product-search"])
api_router.include_router(building_analysis.router, prefix="/buildings", tags=["building-analysis"])
api_router.include_router(pricing_import.router, prefix="/pricing", tags=["pricing-import"])
api_router.include_router(provider_keys.router, tags=["provider-keys"])
api_router.include_router(emails.router, prefix="/emails", tags=["emails"])
api_router.include_router(storage.router, prefix="/storage", tags=["storage"])
api_router.include_router(pricing_config.router, prefix="/pricing-config", tags=["pricing-config"])
api_router.include_router(dynamic_pricing.router, tags=["dynamic-pricing"])
api_router.include_router(helpdesk.router, tags=["helpdesk"])
api_router.include_router(sla.router, tags=["sla"])
api_router.include_router(reporting.router, tags=["reporting"])
api_router.include_router(revenue.router, tags=["revenue"])
api_router.include_router(customer_portal.router, tags=["customer-portal"])
api_router.include_router(customer_portal_access.router, tags=["customer-portal-access"])
api_router.include_router(support_contracts.router, prefix="/support-contracts", tags=["support-contracts"])
api_router.include_router(contract_renewals.router, prefix="/support-contracts", tags=["contract-renewals"])
api_router.include_router(version.router, tags=["version"])
api_router.include_router(websocket.router, tags=["websocket"])
api_router.include_router(trends.router)
api_router.include_router(metrics.router)

