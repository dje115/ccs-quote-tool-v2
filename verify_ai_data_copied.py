#!/usr/bin/env python3
"""Verify AI analysis data was copied to customer"""
import sys
sys.path.insert(0, '/app')

from app.core.database import SessionLocal
from app.models.crm import Customer

db = SessionLocal()

customer = db.query(Customer).filter(Customer.company_name.ilike('%Alliance Tooling%')).first()

if not customer:
    print("Customer not found")
    sys.exit(1)

print("=" * 80)
print("ALLIANCE TOOLING LTD - CRM CUSTOMER AI DATA VERIFICATION")
print("=" * 80)

print(f"\nCustomer ID: {customer.id}")
print(f"Company: {customer.company_name}")
print(f"Lead Score: {customer.lead_score}")

print("\n" + "=" * 80)
print("AI ANALYSIS RAW DATA")
print("=" * 80)

if customer.ai_analysis_raw:
    if isinstance(customer.ai_analysis_raw, dict):
        print(f"\n✅ AI Analysis Raw exists (dict with {len(customer.ai_analysis_raw)} keys)")
        print(f"Keys: {list(customer.ai_analysis_raw.keys())}")
        
        # Show content for each key
        for key, value in customer.ai_analysis_raw.items():
            if isinstance(value, str):
                print(f"\n{key}:")
                print(f"  Type: str, Length: {len(value)}")
                print(f"  Preview: {value[:200]}...")
            elif isinstance(value, list):
                print(f"\n{key}:")
                print(f"  Type: list, Count: {len(value)}")
                if len(value) > 0:
                    print(f"  First item: {value[0][:100] if isinstance(value[0], str) else value[0]}...")
            elif isinstance(value, (int, float)):
                print(f"\n{key}: {value}")
            else:
                print(f"\n{key}: {type(value)} = {value}")
    else:
        print(f"⚠️  AI Analysis Raw exists but is not a dict: {type(customer.ai_analysis_raw)}")
else:
    print("\n❌ AI Analysis Raw is missing or empty")

print("\n" + "=" * 80)
print("EXTERNAL DATA")
print("=" * 80)
print(f"Companies House Data: {type(customer.companies_house_data)} - {bool(customer.companies_house_data)}")
print(f"Google Maps Data: {type(customer.google_maps_data)} - {bool(customer.google_maps_data)}")
print(f"Website Data: {type(customer.website_data)} - {bool(customer.website_data)}")
print(f"LinkedIn Data: {type(customer.linkedin_data)} - {bool(customer.linkedin_data)}")
print(f"LinkedIn URL: {customer.linkedin_url or 'N/A'}")

db.close()

