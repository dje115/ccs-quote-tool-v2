#!/usr/bin/env python3
"""
Simple API test script for CCS Quote Tool v2
"""

import asyncio
import os
import sys
from app.services.companies_house_service import CompaniesHouseService
from app.services.google_maps_service import GoogleMapsService
from app.services.ai_analysis_service import AIAnalysisService

async def test_apis():
    """Test API connections"""
    print("🔍 Testing API Connections...")
    
    # Test Companies House API
    print("\n1. Testing Companies House API...")
    ch_service = CompaniesHouseService()
    if ch_service.api_key:
        print(f"   ✅ API Key configured: {ch_service.api_key[:8]}...")
        try:
            result = await ch_service.search_company("test")
            if "error" in result:
                print(f"   ❌ API Error: {result['error']}")
            else:
                print(f"   ✅ API Working: Found {result.get('total_results', 0)} results")
        except Exception as e:
            print(f"   ❌ Connection Error: {e}")
    else:
        print("   ⚠️  No API key configured")
    
    # Test Google Maps API
    print("\n2. Testing Google Maps API...")
    gmaps_service = GoogleMapsService()
    if gmaps_service.api_key:
        print(f"   ✅ API Key configured: {gmaps_service.api_key[:8]}...")
        try:
            result = await gmaps_service.search_place("London, UK")
            if result:
                print(f"   ✅ API Working: Found location data")
            else:
                print("   ❌ No results returned")
        except Exception as e:
            print(f"   ❌ Connection Error: {e}")
    else:
        print("   ⚠️  No API key configured")
    
    # Test OpenAI API
    print("\n3. Testing OpenAI API...")
    ai_service = AIAnalysisService()
    if ai_service.openai_client:
        print("   ✅ OpenAI client initialized")
        try:
            # Simple test call
            result = await ai_service._call_openai(
                "You are a helpful assistant.",
                "Say 'API test successful'",
                max_tokens=50
            )
            if result:
                print(f"   ✅ API Working: {result}")
            else:
                print("   ❌ No response from API")
        except Exception as e:
            print(f"   ❌ API Error: {e}")
    else:
        print("   ⚠️  OpenAI client not initialized (check API key)")
    
    print("\n📋 Summary:")
    print("   - Add API keys to api-keys.env file")
    print("   - Restart the backend container after adding keys")
    print("   - Keys can also be set via Settings page in the UI")

if __name__ == "__main__":
    asyncio.run(test_apis())






