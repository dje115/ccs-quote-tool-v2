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
from app.core.dependencies import get_current_user, check_permission, get_current_tenant
from app.models.tenant import Tenant
from app.schemas.sales import TenantProfileUpdate, TenantProfileResponse
from app.services.ai_analysis_service import AIAnalysisService
from app.core.api_keys import get_api_keys

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
async def get_api_key_status(
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


# ============================================================================
# TENANT COMPANY PROFILE ENDPOINTS
# ============================================================================

@router.get("/company-profile", response_model=TenantProfileResponse)
async def get_company_profile(
    current_user = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Get tenant company profile
    
    Returns the tenant's company profile including:
    - Company description
    - Products/services offered
    - Unique selling points
    - Target markets
    - Sales methodology
    - Elevator pitch
    - AI analysis of tenant's business
    """
    return TenantProfileResponse(
        company_name=current_tenant.company_name,
        company_address=current_tenant.company_address,
        company_phone_numbers=current_tenant.company_phone_numbers or [],
        company_email_addresses=current_tenant.company_email_addresses or [],
        company_contact_names=current_tenant.company_contact_names or [],
        company_description=current_tenant.company_description,
        company_websites=current_tenant.company_websites or [],
        products_services=current_tenant.products_services or [],
        unique_selling_points=current_tenant.unique_selling_points or [],
        target_markets=current_tenant.target_markets or [],
        sales_methodology=current_tenant.sales_methodology,
        elevator_pitch=current_tenant.elevator_pitch,
        logo_url=current_tenant.logo_url,
        logo_text=current_tenant.logo_text,
        use_text_logo=current_tenant.use_text_logo or False,
        company_analysis=current_tenant.company_analysis or {},
        company_analysis_date=current_tenant.company_analysis_date,
        website_keywords=current_tenant.website_keywords or {}
    )


@router.put("/company-profile", response_model=TenantProfileResponse)
async def update_company_profile(
    profile: TenantProfileUpdate,
    current_user = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Update tenant company profile
    
    This information is used by the AI Sales Assistant to provide
    intelligent, context-aware sales guidance.
    """
    try:
        from sqlalchemy.orm.attributes import flag_modified
        
        # Update fields if provided
        if profile.company_name is not None:
            current_tenant.company_name = profile.company_name
        if profile.company_address is not None:
            current_tenant.company_address = profile.company_address
        if profile.company_phone_numbers is not None:
            current_tenant.company_phone_numbers = profile.company_phone_numbers
            flag_modified(current_tenant, "company_phone_numbers")
        if profile.company_email_addresses is not None:
            current_tenant.company_email_addresses = profile.company_email_addresses
            flag_modified(current_tenant, "company_email_addresses")
        if profile.company_contact_names is not None:
            current_tenant.company_contact_names = profile.company_contact_names
            flag_modified(current_tenant, "company_contact_names")
        if profile.company_description is not None:
            current_tenant.company_description = profile.company_description
        if profile.company_websites is not None:
            current_tenant.company_websites = profile.company_websites
            flag_modified(current_tenant, "company_websites")
        if profile.products_services is not None:
            current_tenant.products_services = profile.products_services
            flag_modified(current_tenant, "products_services")
        if profile.unique_selling_points is not None:
            current_tenant.unique_selling_points = profile.unique_selling_points
            flag_modified(current_tenant, "unique_selling_points")
        if profile.target_markets is not None:
            current_tenant.target_markets = profile.target_markets
            flag_modified(current_tenant, "target_markets")
        if profile.sales_methodology is not None:
            current_tenant.sales_methodology = profile.sales_methodology
        if profile.elevator_pitch is not None:
            current_tenant.elevator_pitch = profile.elevator_pitch
        if profile.logo_url is not None:
            current_tenant.logo_url = profile.logo_url
        if profile.logo_text is not None:
            current_tenant.logo_text = profile.logo_text
        if profile.use_text_logo is not None:
            current_tenant.use_text_logo = profile.use_text_logo
        
        db.commit()
        db.refresh(current_tenant)
        
        return TenantProfileResponse(
            company_name=current_tenant.company_name,
            company_address=current_tenant.company_address,
            company_phone_numbers=current_tenant.company_phone_numbers or [],
            company_email_addresses=current_tenant.company_email_addresses or [],
            company_contact_names=current_tenant.company_contact_names or [],
            company_description=current_tenant.company_description,
            company_websites=current_tenant.company_websites or [],
            products_services=current_tenant.products_services or [],
            unique_selling_points=current_tenant.unique_selling_points or [],
            target_markets=current_tenant.target_markets or [],
            sales_methodology=current_tenant.sales_methodology,
            elevator_pitch=current_tenant.elevator_pitch,
            logo_url=current_tenant.logo_url,
            logo_text=current_tenant.logo_text,
            use_text_logo=current_tenant.use_text_logo or False,
            company_analysis=current_tenant.company_analysis or {},
            company_analysis_date=current_tenant.company_analysis_date,
            website_keywords=current_tenant.website_keywords or {}
        )
        
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Failed to update company profile: {e}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating company profile: {str(e)}"
        )


@router.post("/company-profile/analyze")
async def analyze_company_profile(
    current_user = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Run AI analysis on tenant's own company
    
    This generates comprehensive insights about the tenant's business including:
    - Business model analysis
    - Competitive positioning
    - Sales opportunities
    - Target customer profiles
    - Recommended sales approaches
    
    This analysis is then used by the AI Sales Assistant to provide
    intelligent, personalized sales guidance.
    """
    try:
        # Get API keys
        api_keys = get_api_keys(db, current_tenant)
        
        if not api_keys.openai:
            raise HTTPException(
                status_code=400,
                detail="OpenAI API key not configured. Please add your API key in settings."
            )
        
        # Initialize AI service
        ai_service = AIAnalysisService(
            openai_api_key=api_keys.openai,
            companies_house_api_key=api_keys.companies_house,
            google_maps_api_key=api_keys.google_maps
        )
        
        # Build context for AI analysis
        context = f"""
Analyze the following company profile and provide comprehensive business intelligence:

COMPANY NAME: {current_tenant.company_name or current_tenant.name}

COMPANY WEBSITES:
{', '.join(current_tenant.company_websites or ['None provided - consider crawling these to gather more information'])}

COMPANY DESCRIPTION:
{current_tenant.company_description or 'Not provided'}

PRODUCTS & SERVICES:
{', '.join(current_tenant.products_services or [])}

UNIQUE SELLING POINTS:
{', '.join(current_tenant.unique_selling_points or [])}

TARGET MARKETS:
{', '.join(current_tenant.target_markets or [])}

SALES METHODOLOGY:
{current_tenant.sales_methodology or 'Not specified'}

ELEVATOR PITCH:
{current_tenant.elevator_pitch or 'Not provided'}

Please provide:
1. Business model analysis
2. Competitive positioning and strengths
3. Ideal customer profile (ICP)
4. Key pain points this company solves
5. Recommended sales approach and messaging
6. Cross-selling and upselling opportunities
7. Common objections and how to handle them
8. Industry trends and opportunities

Format as JSON with keys: business_model, competitive_position, ideal_customer_profile, 
pain_points_solved, sales_approach, cross_sell_opportunities, objection_handling, industry_trends
"""
        
        # Get AI analysis
        # Use the AI service to get analysis
        response = ai_service.openai_client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": "You are a business intelligence analyst. Provide detailed, actionable insights in JSON format."},
                {"role": "user", "content": context}
            ],
            max_completion_tokens=15000,
            timeout=180.0,
            response_format={"type": "json_object"}
        )
        
        analysis_text = response.choices[0].message.content
        
        # Parse JSON response
        import json
        analysis = json.loads(analysis_text)
        
        # Store analysis in tenant record
        current_tenant.company_analysis = analysis
        current_tenant.company_analysis_date = datetime.utcnow()
        
        db.commit()
        db.refresh(current_tenant)
        
        return {
            "success": True,
            "message": "Company analysis completed successfully",
            "analysis": analysis,
            "analysis_date": current_tenant.company_analysis_date
        }
        
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Company analysis failed: {e}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing company profile: {str(e)}"
        )


@router.post("/company-profile/auto-fill")
async def auto_fill_company_profile(
    current_user = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    AI-powered auto-fill for tenant company profile
    
    This endpoint uses AI to automatically gather and fill in company information
    from web sources including:
    - Company website scraping
    - LinkedIn data
    - Public business information
    - Keyword analysis
    
    Similar to customer analysis but for the tenant's own company.
    """
    try:
        # Get API keys
        api_keys = get_api_keys(db, current_tenant)
        
        if not api_keys.openai:
            raise HTTPException(
                status_code=400,
                detail="OpenAI API key not configured. Please add your API key in settings."
            )
        
        # Initialize AI service
        ai_service = AIAnalysisService(
            openai_api_key=api_keys.openai,
            companies_house_api_key=api_keys.companies_house,
            google_maps_api_key=api_keys.google_maps
        )
        
        company_name = current_tenant.company_name or current_tenant.name
        websites = current_tenant.company_websites or []
        
        if not company_name:
            raise HTTPException(
                status_code=400,
                detail="Please set your company name first in Settings → Profile"
            )
        
        # Step 1: Scrape website data if available
        website_data = {}
        keywords = []
        
        if websites:
            try:
                # Use the primary website
                primary_website = websites[0]
                
                import requests
                from bs4 import BeautifulSoup
                
                response = requests.get(primary_website, timeout=10, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract text content
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                
                text = soup.get_text()
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = ' '.join(chunk for chunk in chunks if chunk)
                
                # Limit to first 5000 characters for processing
                website_text = text[:5000]
                
                website_data = {
                    "url": primary_website,
                    "text_sample": website_text,
                    "title": soup.title.string if soup.title else None
                }
                
            except Exception as e:
                website_data = {"error": str(e)}
        
        # Step 2: Try to find and scrape LinkedIn profile
        linkedin_data = None
        linkedin_url = None
        try:
            # Try common LinkedIn URL patterns
            possible_linkedin_urls = [
                f"https://www.linkedin.com/company/{company_name.lower().replace(' ', '-').replace('ltd', '').replace('.', '').strip()}",
                f"https://www.linkedin.com/company/{company_name.lower().replace(' ', '').replace('ltd', '').replace('.', '').strip()}",
            ]
            
            # Try to scrape LinkedIn (if accessible)
            for linkedin_test_url in possible_linkedin_urls:
                try:
                    linkedin_response = requests.get(linkedin_test_url, timeout=5, headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }, allow_redirects=True)
                    
                    if linkedin_response.status_code == 200 and 'linkedin.com' in linkedin_response.url:
                        linkedin_url = linkedin_response.url
                        soup = BeautifulSoup(linkedin_response.text, 'html.parser')
                        
                        # Extract basic info if available
                        linkedin_text = soup.get_text()[:1000]  # First 1000 chars
                        linkedin_data = {
                            "url": linkedin_url,
                            "found": True,
                            "text_sample": linkedin_text
                        }
                        break
                except Exception as e:
                    continue
            
            if not linkedin_url:
                # Construct a suggested URL
                linkedin_url = f"https://www.linkedin.com/company/{company_name.lower().replace(' ', '-')}"
                linkedin_data = {"url": linkedin_url, "found": False, "suggested": True}
                
        except Exception as e:
            linkedin_data = {"error": str(e)}
        
        # Step 3: Try to find additional sources (Companies House, Social Media, etc.)
        additional_sources = []
        social_media_links = {}
        
        # Try Companies House if we have the API key
        if api_keys.companies_house:
            try:
                # Search for company
                ch_response = requests.get(
                    f"https://api.company-information.service.gov.uk/search/companies?q={company_name}",
                    auth=(api_keys.companies_house, ''),
                    timeout=5
                )
                if ch_response.status_code == 200:
                    ch_data = ch_response.json()
                    if ch_data.get('items') and len(ch_data['items']) > 0:
                        company_info = ch_data['items'][0]
                        additional_sources.append({
                            "source": "Companies House",
                            "data": f"Company Number: {company_info.get('company_number')}, Status: {company_info.get('company_status')}, Type: {company_info.get('company_type')}, Address: {company_info.get('address_snippet')}"
                        })
            except Exception as e:
                pass
        
        # Step 3b: Try to find social media and other interesting sources from website
        if website_data.get("text_sample") or websites:
            try:
                # Look for social media links in the website HTML
                if websites:
                    web_response = requests.get(websites[0], timeout=10, headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    })
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(web_response.text, 'html.parser')
                    
                    # Find all links
                    for link in soup.find_all('a', href=True):
                        href = link['href'].lower()
                        # YouTube
                        if 'youtube.com' in href or 'youtu.be' in href:
                            if 'youtube' not in social_media_links:
                                social_media_links['youtube'] = link['href']
                        # Twitter/X
                        elif 'twitter.com' in href or 'x.com' in href:
                            if 'twitter' not in social_media_links:
                                social_media_links['twitter'] = link['href']
                        # Facebook
                        elif 'facebook.com' in href:
                            if 'facebook' not in social_media_links:
                                social_media_links['facebook'] = link['href']
                        # Instagram
                        elif 'instagram.com' in href:
                            if 'instagram' not in social_media_links:
                                social_media_links['instagram'] = link['href']
                        # GitHub
                        elif 'github.com' in href:
                            if 'github' not in social_media_links:
                                social_media_links['github'] = link['href']
                        # Crunchbase
                        elif 'crunchbase.com' in href:
                            if 'crunchbase' not in social_media_links:
                                social_media_links['crunchbase'] = link['href']
            except Exception as e:
                pass
        
        # Step 4: Use AI to analyze and extract information
        
        analysis_prompt = f"""
You are analyzing a company to auto-fill its business profile. Extract and generate the following information:

COMPANY NAME: {company_name}
WEBSITES: {', '.join(websites) if websites else 'None provided'}

WEBSITE DATA:
{website_data.get('text_sample', 'No website data available')}

LINKEDIN DATA:
{linkedin_data.get('text_sample', 'Not accessible') if linkedin_data and linkedin_data.get('found') else 'LinkedIn profile suggested but not scraped'}
LinkedIn URL: {linkedin_url if linkedin_url else 'Not found'}

ADDITIONAL SOURCES:
{chr(10).join([f"- {src['source']}: {src['data']}" for src in additional_sources]) if additional_sources else 'None available'}

Based on ALL the available information above and your knowledge, provide:

1. **Company Description**: A clear, comprehensive description of what the company does (2-3 sentences)
2. **Products & Services**: List 5-10 main products or services offered
3. **Unique Selling Points**: List 3-7 key differentiators or competitive advantages
4. **Target Markets**: List 3-7 industries or customer segments they serve
5. **Sales Methodology**: Suggest the most appropriate sales approach (e.g., "Consultative", "Solution-Based", "Value-Based")
6. **Elevator Pitch**: Create a compelling 30-second pitch for the company
7. **Contact Information**:
   - Primary email address (look for contact@, info@, or sales@ emails)
   - Phone numbers found on website
   - Business address if available
8. **Marketing Keywords**: Extract 15-20 relevant keywords from the website for SEO and marketing
9. **LinkedIn URL**: {linkedin_url if linkedin_url else 'Not found'}

Format your response as JSON with these keys:
- company_description
- products_services (array)
- unique_selling_points (array)
- target_markets (array)
- sales_methodology (string)
- elevator_pitch (string)
- contact_emails (array of objects with email and suggested role)
- contact_phones (array)
- company_address (string or null)
- keywords (array)
- linkedin_url (string or null)
- confidence_score (0-100, how confident you are in the extracted data)

If information is missing or unclear, make reasonable inferences based on the company name and industry.
"""
        
        response = ai_service.openai_client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": "You are a business intelligence analyst specializing in company research and data extraction. Provide detailed, accurate information in JSON format."},
                {"role": "user", "content": analysis_prompt}
            ],
            max_completion_tokens=20000,
            timeout=240.0,
            response_format={"type": "json_object"}
        )
        
        result_text = response.choices[0].message.content
        import json
        result = json.loads(result_text)
        
        # Save the keywords to the database immediately (they'll be used in future marketing modules)
        # Store keywords mapped to the primary website
        from sqlalchemy.orm.attributes import flag_modified
        keywords = result.get("keywords", [])
        if keywords and websites:
            primary_website = websites[0]
            # Initialize website_keywords dict if needed
            if not current_tenant.website_keywords:
                current_tenant.website_keywords = {}
            # Store keywords for this website
            current_tenant.website_keywords[primary_website] = keywords
            flag_modified(current_tenant, "website_keywords")
            db.commit()
            db.refresh(current_tenant)
        
        # Build sources array
        sources_list = []
        if website_data.get("text_sample"):
            sources_list.append("Primary Website: ✓ Scraped & Analyzed")
        if linkedin_data and linkedin_data.get("found"):
            sources_list.append("LinkedIn: ✓ Profile Found & Scraped")
        elif linkedin_url:
            sources_list.append("LinkedIn: ⚠ Profile Suggested (not scraped)")
        if any(src["source"] == "Companies House" for src in additional_sources):
            sources_list.append("Companies House: ✓ Company Data Retrieved")
        for src in additional_sources:
            if src["source"] != "Companies House":
                sources_list.append(f"{src['source']}: {src.get('status', '✓ Data Retrieved')}")
        sources_list.append("AI Inference: ✓ Enhanced with AI analysis")
        
        # Return the auto-filled data (don't save yet - let user review)
        return {
            "success": True,
            "message": "Company profile auto-filled successfully",
            "data": {
                "company_description": result.get("company_description", ""),
                "products_services": result.get("products_services", []),
                "unique_selling_points": result.get("unique_selling_points", []),
                "target_markets": result.get("target_markets", []),
                "sales_methodology": result.get("sales_methodology", ""),
                "elevator_pitch": result.get("elevator_pitch", ""),
                "company_phone_numbers": result.get("contact_phones", []),
                "company_email_addresses": [
                    {"email": email.get("email") if isinstance(email, dict) else email, "is_default": i == 0}
                    for i, email in enumerate(result.get("contact_emails", []))
                ],
                "company_contact_names": [],  # Will be manually added by user
                "company_address": result.get("company_address"),
                "keywords": result.get("keywords", []),
                "linkedin_url": result.get("linkedin_url"),
                "website_keywords": current_tenant.website_keywords,
                "social_media_links": social_media_links
            },
            "confidence_score": result.get("confidence_score", 0),
            "sources": sources_list
        }
        
    except Exception as e:
        print(f"[ERROR] Auto-fill failed: {e}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error auto-filling company profile: {str(e)}"
        )
