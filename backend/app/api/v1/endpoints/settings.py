#!/usr/bin/env python3
"""
Settings and configuration endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
import uuid
from datetime import datetime
import os
from openai import OpenAI
import googlemaps
import httpx

from app.core.database import get_db
from app.core.dependencies import get_current_user, check_permission

router = APIRouter()


class APITestResponse(BaseModel):
    success: bool
    message: str


@router.post("/test-openai", response_model=APITestResponse)
async def test_openai_api(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Test OpenAI API connection"""
    try:
        # Get API key from environment or tenant settings
        openai_api_key = os.getenv('OPENAI_API_KEY')
        
        if not openai_api_key:
            return APITestResponse(
                success=False,
                message="OpenAI API key not configured. Please add your API key in the environment variables."
            )
        
        # Test with a simple request
        try:
            client = OpenAI(
                api_key=openai_api_key,
                timeout=30.0,
                # Add proxy support if needed
                http_client=None  # Use default HTTP client
            )
            
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
            error_msg = str(api_error)
            # Handle common proxy/network errors
            if "Proxy" in error_msg or "proxy" in error_msg:
                return APITestResponse(
                    success=False,
                    message=f"Network/Proxy error: {error_msg}. Please check your network settings or contact your IT administrator."
                )
            elif "timeout" in error_msg.lower():
                return APITestResponse(
                    success=False,
                    message=f"Connection timeout: {error_msg}. Please check your internet connection."
                )
            elif "SSL" in error_msg or "certificate" in error_msg.lower():
                return APITestResponse(
                    success=False,
                    message=f"SSL/Certificate error: {error_msg}. Please check your network security settings."
                )
            else:
                return APITestResponse(
                    success=False,
                    message=f"OpenAI API error: {error_msg}"
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
        # Get API key from environment
        google_maps_api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        
        if not google_maps_api_key:
            return APITestResponse(
                success=False,
                message="Google Maps API key not configured. Please add your API key in the environment variables."
            )
        
        # Test with a simple geocoding request
        try:
            gmaps = googlemaps.Client(key=google_maps_api_key)
            
            # Test geocoding with a known address
            geocode_result = gmaps.geocode('1600 Amphitheatre Parkway, Mountain View, CA')
            
            if geocode_result:
                return APITestResponse(
                    success=True,
                    message="Google Maps API connection successful! Geocoding test passed."
                )
            else:
                return APITestResponse(
                    success=False,
                    message="Google Maps API responded but returned no results."
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
        # Get API key from environment
        companies_house_api_key = os.getenv('COMPANIES_HOUSE_API_KEY')
        
        if not companies_house_api_key:
            return APITestResponse(
                success=False,
                message="Companies House API key not configured. Please add your API key in the environment variables."
            )
        
        # Test with a simple search request
        try:
            headers = {
                'Authorization': f'Bearer {companies_house_api_key}',
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
        # Check if API keys are configured
        openai_key = os.getenv('OPENAI_API_KEY')
        google_maps_key = os.getenv('GOOGLE_MAPS_API_KEY')
        companies_house_key = os.getenv('COMPANIES_HOUSE_API_KEY')
        
        return {
            "openai": {
                "configured": bool(openai_key),
                "status": "configured" if openai_key else "not_configured"
            },
            "google_maps": {
                "configured": bool(google_maps_key),
                "status": "configured" if google_maps_key else "not_configured"
            },
            "companies_house": {
                "configured": bool(companies_house_key),
                "status": "configured" if companies_house_key else "not_configured"
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking API status: {str(e)}"
        )
