#!/usr/bin/env python3
"""Check detailed data comparison"""
import sys
sys.path.insert(0, '/app')

from app.core.database import SessionLocal
from app.models.leads import Lead
from app.models.crm import Customer
import json

db = SessionLocal()

lead = db.query(Lead).filter(Lead.company_name.ilike('%Precision Engineering UK%')).first()
if not lead:
    print("Lead not found")
    sys.exit(1)

customer = db.query(Customer).filter(Customer.id == lead.converted_to_customer_id).first()
if not customer:
    print("Customer not found")
    sys.exit(1)

print("=" * 80)
print("DATA COMPARISON - DETAILED")
print("=" * 80)

print("\n1. COMPANIES HOUSE DATA:")
print(f"   Discovery: {type(lead.companies_house_data)} - {bool(lead.companies_house_data)}")
if lead.companies_house_data:
    if isinstance(lead.companies_house_data, dict):
        print(f"   Discovery keys: {list(lead.companies_house_data.keys())[:5]}")
    elif isinstance(lead.companies_house_data, str):
        print(f"   Discovery (string, length): {len(lead.companies_house_data)}")
print(f"   Customer: {type(customer.companies_house_data)} - {bool(customer.companies_house_data)}")
if customer.companies_house_data:
    if isinstance(customer.companies_house_data, dict):
        print(f"   Customer keys: {list(customer.companies_house_data.keys())[:5]}")

print("\n2. GOOGLE MAPS DATA:")
print(f"   Discovery: {type(lead.google_maps_data)} - {bool(lead.google_maps_data)}")
if lead.google_maps_data:
    if isinstance(lead.google_maps_data, dict):
        print(f"   Discovery keys: {list(lead.google_maps_data.keys())[:5]}")
    elif isinstance(lead.google_maps_data, str):
        print(f"   Discovery (string, length): {len(lead.google_maps_data)}")
print(f"   Customer: {type(customer.google_maps_data)} - {bool(customer.google_maps_data)}")
if customer.google_maps_data:
    if isinstance(customer.google_maps_data, dict):
        print(f"   Customer keys: {list(customer.google_maps_data.keys())[:5]}")

print("\n3. WEBSITE DATA:")
print(f"   Discovery: {type(lead.website_data)} - {bool(lead.website_data)}")
if lead.website_data:
    if isinstance(lead.website_data, dict):
        print(f"   Discovery keys: {list(lead.website_data.keys())[:5]}")
    elif isinstance(lead.website_data, str):
        print(f"   Discovery (string, length): {len(lead.website_data)}")
print(f"   Customer: {type(customer.website_data)} - {bool(customer.website_data)}")
if customer.website_data:
    if isinstance(customer.website_data, dict):
        print(f"   Customer keys: {list(customer.website_data.keys())[:5]}")

print("\n4. LINKEDIN DATA:")
print(f"   Discovery: {type(lead.linkedin_data)} - {bool(lead.linkedin_data)}")
if lead.linkedin_data:
    if isinstance(lead.linkedin_data, dict):
        print(f"   Discovery keys: {list(lead.linkedin_data.keys())[:5]}")
    elif isinstance(lead.linkedin_data, str):
        print(f"   Discovery (string, length): {len(lead.linkedin_data)}")
print(f"   Customer: {type(customer.linkedin_data)} - {bool(customer.linkedin_data)}")
if customer.linkedin_data:
    if isinstance(customer.linkedin_data, dict):
        print(f"   Customer keys: {list(customer.linkedin_data.keys())[:5]}")

print("\n5. AI ANALYSIS RAW:")
print(f"   Discovery AI Analysis type: {type(lead.ai_analysis)}")
print(f"   Customer AI Analysis Raw type: {type(customer.ai_analysis_raw)}")
if customer.ai_analysis_raw and isinstance(customer.ai_analysis_raw, dict):
    print(f"   Customer AI Analysis keys: {list(customer.ai_analysis_raw.keys())}")

db.close()

