#!/usr/bin/env python3
"""
Test AI Analysis with Central Technology Ltd using database API keys
"""

import asyncio
import json
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.database import SessionLocal
from app.models.tenant import Tenant
from app.services.ai_analysis_service import AIAnalysisService


async def test_central_technology():
    """Test comprehensive AI analysis for Central Technology Ltd"""
    
    # Get API keys from database
    db = SessionLocal()
    try:
        default_tenant = db.query(Tenant).filter(Tenant.name == 'CCS Quote Tool').first()
        
        if not default_tenant:
            print("❌ Default tenant not found")
            return
        
        openai_key = default_tenant.openai_api_key
        companies_house_key = default_tenant.companies_house_api_key
        google_maps_key = default_tenant.google_maps_api_key
        
        print("🔑 API Keys Status:")
        print(f"  OpenAI: {'✅ Configured' if openai_key else '❌ Not configured'}")
        print(f"  Companies House: {'✅ Configured' if companies_house_key else '❌ Not configured'}")
        print(f"  Google Maps: {'✅ Configured' if google_maps_key else '❌ Not configured'}")
        print()
        
        if not all([openai_key, companies_house_key, google_maps_key]):
            print("❌ Please configure all API keys in the Settings page")
            return
        
        # Initialize AI Analysis Service with database keys
        service = AIAnalysisService(
            openai_api_key=openai_key,
            companies_house_api_key=companies_house_key,
            google_maps_api_key=google_maps_key
        )
        
        print("🏢 Testing AI Analysis for Central Technology Limited")
        print("   Company Number: 04579191")
        print("=" * 80)
        print()
        
        # Run comprehensive analysis
        result = await service.analyze_company(
            company_name='Central Technology Limited',
            company_number='04579191'
        )
        
        print("📊 ANALYSIS RESULTS")
        print("=" * 80)
        print(json.dumps(result, indent=2))
        print()
        
        # Summary
        if result.get('success'):
            print("✅ Analysis completed successfully!")
            
            # Check what data was retrieved
            source_data = result.get('source_data', {})
            
            print("\n📦 Data Retrieved:")
            ch_data = source_data.get('companies_house', {})
            if not ch_data.get('error'):
                print(f"  ✅ Companies House: {ch_data.get('company_name', 'N/A')}")
                print(f"     Status: {ch_data.get('status', 'N/A')}")
                print(f"     Directors: {len(ch_data.get('officers', []))}")
                if ch_data.get('financials'):
                    print(f"     Financial Records: {len(ch_data.get('financials', []))}")
            else:
                print(f"  ❌ Companies House: {ch_data.get('error')}")
            
            gm_data = source_data.get('google_maps', {})
            if not gm_data.get('error'):
                print(f"  ✅ Google Maps: {gm_data.get('total_results', 0)} locations found")
                for loc in gm_data.get('locations', [])[:3]:
                    print(f"     - {loc.get('name')} ({loc.get('formatted_address', 'N/A')})")
            else:
                print(f"  ❌ Google Maps: {gm_data.get('error')}")
            
            # Show AI Analysis
            analysis = result.get('analysis', {})
            if not analysis.get('error'):
                print("\n🤖 AI Analysis:")
                if 'overall_assessment' in analysis:
                    print(f"  Assessment: {analysis['overall_assessment'][:200]}...")
                if 'lead_score' in analysis:
                    print(f"  Lead Score: {analysis['lead_score']}/100")
                if 'financial_health' in analysis:
                    print(f"  Financial Health: {analysis['financial_health'].get('rating', 'N/A')}")
            else:
                print(f"\n❌ AI Analysis Error: {analysis.get('error')}")
        else:
            print("❌ Analysis failed")
            
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(test_central_technology())

