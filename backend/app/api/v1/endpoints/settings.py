#!/usr/bin/env python3
"""
Settings and configuration endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import uuid
from datetime import datetime
import os
from openai import OpenAI
import googlemaps
import httpx

from app.core.database import get_db
from app.core.dependencies import get_current_user, check_permission
from app.models.tenant import Tenant

router = APIRouter()


class APITestResponse(BaseModel):
    success: bool
    message: str

class APIKeyRequest(BaseModel):
    openai_api_key: Optional[str] = None
    companies_house_api_key: Optional[str] = None
    google_maps_api_key: Optional[str] = None

class APIKeyResponse(BaseModel):
    openai_configured: bool
    companies_house_configured: bool
    google_maps_configured: bool


def get_tenant_api_key(tenant: Tenant, key_type: str) -> Optional[str]:
    """Get API key from tenant or environment fallback"""
    if key_type == "openai":
        return tenant.openai_api_key or os.getenv('OPENAI_API_KEY')
    elif key_type == "companies_house":
        return tenant.companies_house_api_key or os.getenv('COMPANIES_HOUSE_API_KEY')
    elif key_type == "google_maps":
        return tenant.google_maps_api_key or os.getenv('GOOGLE_MAPS_API_KEY')
    return None


@router.post("/api-keys", response_model=APIKeyResponse)
async def save_api_keys(
    request: APIKeyRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Save API keys to tenant settings"""
    try:
        # Get current tenant
        tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        # Update API keys if provided
        if request.openai_api_key is not None:
            tenant.openai_api_key = request.openai_api_key
        if request.companies_house_api_key is not None:
            tenant.companies_house_api_key = request.companies_house_api_key
        if request.google_maps_api_key is not None:
            tenant.google_maps_api_key = request.google_maps_api_key
        
        db.commit()
        
        return APIKeyResponse(
            openai_configured=bool(tenant.openai_api_key),
            companies_house_configured=bool(tenant.companies_house_api_key),
            google_maps_configured=bool(tenant.google_maps_api_key)
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving API keys: {str(e)}"
        )


@router.get("/api-keys", response_model=APIKeyResponse)
async def get_api_keys(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current API key status"""
    try:
        # Get current tenant
        tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        return APIKeyResponse(
            openai_configured=bool(get_tenant_api_key(tenant, "openai")),
            companies_house_configured=bool(get_tenant_api_key(tenant, "companies_house")),
            google_maps_configured=bool(get_tenant_api_key(tenant, "google_maps"))
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving API keys: {str(e)}"
        )


@router.post("/test-openai", response_model=APITestResponse)
async def test_openai_api(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Test OpenAI API connection"""
    try:
        # Get API key from tenant or environment fallback
        tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        openai_api_key = get_tenant_api_key(tenant, "openai")
        
        if not openai_api_key:
            return APITestResponse(
                success=False,
                message="OpenAI API key not configured. Please add your API key in Settings."
            )
        
        # Test with a simple request - using proven v1 approach
        try:
            client = OpenAI(api_key=openai_api_key)
            
            response = client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Say 'Connection successful'"}
                ],
                max_completion_tokens=50
            )
            
            result = response.choices[0].message.content
            
            return APITestResponse(
                success=True,
                message=f"OpenAI API connection successful! Response: {result}"
            )
            
        except Exception as api_error:
            return APITestResponse(
                success=False,
                message=f"OpenAI API error: {str(api_error)}"
            )
        
    except Exception as e:
        return APITestResponse(
            success=False,
            message=f"Error testing OpenAI API: {str(e)}"
        )


@router.post("/test-google-maps", response_model=APITestResponse)
async def test_google_maps_api(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Test Google Maps API connection"""
    try:
        # Get API key from tenant or environment fallback
        tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        google_maps_api_key = get_tenant_api_key(tenant, "google_maps")
        
        if not google_maps_api_key:
            return APITestResponse(
                success=False,
                message="Google Maps API key not configured. Please add your API key in the environment variables."
            )
        
        # Test with a simple geocoding request - using proven v1 approach
        try:
            client = googlemaps.Client(key=google_maps_api_key)
            
            # Test geocoding with London, UK (same as v1)
            result = client.geocode("London, UK")
            
            if result:
                return APITestResponse(
                    success=True,
                    message=f"Google Maps API connection successful! Found {len(result)} results for test query."
                )
            else:
                return APITestResponse(
                    success=False,
                    message="Google Maps API connected but returned no results for test query."
                )
                
        except Exception as api_error:
            return APITestResponse(
                success=False,
                message=f"Google Maps API error: {str(api_error)}"
            )
        
    except Exception as e:
        return APITestResponse(
            success=False,
            message=f"Error testing Google Maps API: {str(e)}"
        )


@router.post("/test-companies-house", response_model=APITestResponse)
async def test_companies_house_api(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Test Companies House API connection"""
    try:
        # Get API key from tenant or environment fallback
        tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        companies_house_api_key = get_tenant_api_key(tenant, "companies_house")
        
        if not companies_house_api_key:
            return APITestResponse(
                success=False,
                message="Companies House API key not configured. Please add your API key in Settings."
            )
        
        # Test with a simple search request - using v1 approach
        try:
            headers = {
                'Authorization': companies_house_api_key,  # Companies House uses direct API key, not Bearer
                'Content-Type': 'application/json'
            }
            
            # Test search for a known company
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    'https://api.company-information.service.gov.uk/search/companies',
                    headers=headers,
                    params={'q': 'MICROSOFT', 'items_per_page': 1},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('items'):
                        return APITestResponse(
                            success=True,
                            message="Companies House API connection successful! Search test passed."
                        )
                    else:
                        return APITestResponse(
                            success=False,
                            message="Companies House API responded but returned no results."
                        )
                else:
                    return APITestResponse(
                        success=False,
                        message=f"Companies House API returned status code: {response.status_code}"
                    )
                
        except Exception as api_error:
            return APITestResponse(
                success=False,
                message=f"Companies House API error: {str(api_error)}"
            )
        
    except Exception as e:
        return APITestResponse(
            success=False,
            message=f"Error testing Companies House API: {str(e)}"
        )


@router.get("/api-status")
async def get_api_status(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current API status for all services"""
    try:
        # Get API keys from tenant or environment fallback
        tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        openai_key = get_tenant_api_key(tenant, "openai")
        google_maps_key = get_tenant_api_key(tenant, "google_maps")
        companies_house_key = get_tenant_api_key(tenant, "companies_house")
        
        # Get system-wide keys from default tenant (CCS Quote Tool)
        default_tenant = db.query(Tenant).filter(Tenant.name == "CCS Quote Tool").first()
        
        # Determine status based on tenant key vs system-wide key
        def get_status_info(tenant_key, system_key, key_type):
            if tenant_key:
                return {
                    "configured": True,
                    "status": "configured",
                    "source": "tenant"
                }
            elif system_key:
                return {
                    "configured": True,
                    "status": "configured",
                    "source": "system_wide"
                }
            else:
                return {
                    "configured": False,
                    "status": "not_configured",
                    "source": "none"
                }
        
        return {
            "openai": get_status_info(
                tenant.openai_api_key,
                default_tenant.openai_api_key if default_tenant else None,
                "openai"
            ),
            "google_maps": get_status_info(
                tenant.google_maps_api_key,
                default_tenant.google_maps_api_key if default_tenant else None,
                "google_maps"
            ),
            "companies_house": get_status_info(
                tenant.companies_house_api_key,
                default_tenant.companies_house_api_key if default_tenant else None,
                "companies_house"
            )
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking API status: {str(e)}"
        )
