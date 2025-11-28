#!/usr/bin/env python3
"""Check why external data wasn't copied"""
import sys
sys.path.insert(0, '/app')

from app.core.database import SessionLocal
from app.models.leads import Lead
from app.models.crm import Customer
import json

db = SessionLocal()

lead = db.query(Lead).filter(Lead.company_name.ilike('%Alliance Tooling%')).first()
if not lead or not lead.converted_to_customer_id:
    print("Discovery not converted")
    sys.exit(1)

customer = db.query(Customer).filter(Customer.id == lead.converted_to_customer_id).first()

print("=" * 80)
print("EXTERNAL DATA COPY ISSUE - DETAILED CHECK")
print("=" * 80)

print("\n1. COMPANIES HOUSE DATA:")
print(f"   Discovery type: {type(lead.companies_house_data)}")
print(f"   Discovery value: {repr(lead.companies_house_data)[:200]}")
if isinstance(lead.companies_house_data, str):
    print(f"   Discovery string length: {len(lead.companies_house_data)}")
    if lead.companies_house_data.strip():
        try:
            parsed = json.loads(lead.companies_house_data)
            print(f"   Parsed type: {type(parsed)}")
            if isinstance(parsed, dict):
                print(f"   Parsed keys: {list(parsed.keys())[:5]}")
        except:
            print(f"   Could not parse as JSON")
print(f"   Customer type: {type(customer.companies_house_data)}")
print(f"   Customer value: {bool(customer.companies_house_data)}")

print("\n2. GOOGLE MAPS DATA:")
print(f"   Discovery type: {type(lead.google_maps_data)}")
print(f"   Discovery value: {repr(lead.google_maps_data)[:200]}")
if isinstance(lead.google_maps_data, str):
    print(f"   Discovery string length: {len(lead.google_maps_data)}")
print(f"   Customer type: {type(customer.google_maps_data)}")
print(f"   Customer value: {bool(customer.google_maps_data)}")

print("\n3. WEBSITE DATA:")
print(f"   Discovery type: {type(lead.website_data)}")
print(f"   Discovery value: {repr(lead.website_data)[:200]}")
if isinstance(lead.website_data, str):
    print(f"   Discovery string length: {len(lead.website_data)}")
print(f"   Customer type: {type(customer.website_data)}")
print(f"   Customer value: {bool(customer.website_data)}")

print("\n4. LINKEDIN DATA:")
print(f"   Discovery type: {type(lead.linkedin_data)}")
print(f"   Discovery value: {repr(lead.linkedin_data)[:200]}")
if isinstance(lead.linkedin_data, str):
    print(f"   Discovery string length: {len(lead.linkedin_data)}")
print(f"   Customer type: {type(customer.linkedin_data)}")
print(f"   Customer value: {bool(customer.linkedin_data)}")

db.close()

