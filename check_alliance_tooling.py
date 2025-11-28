#!/usr/bin/env python3
"""Check data for Alliance Tooling Ltd"""
import sys
sys.path.insert(0, '/app')

from app.core.database import SessionLocal
from app.models.leads import Lead
from app.models.crm import Customer
import json

db = SessionLocal()

# Check discovery
lead = db.query(Lead).filter(Lead.company_name.ilike('%Alliance Tooling%')).first()

# Check customer
customer = db.query(Customer).filter(Customer.company_name.ilike('%Alliance Tooling%')).first()

print("=" * 80)
print("ALLIANCE TOOLING LTD - DATA CHECK")
print("=" * 80)

if lead:
    print("\n📋 DISCOVERY DATA:")
    print(f"   ID: {lead.id}")
    print(f"   Company: {lead.company_name}")
    print(f"   Website: {lead.website or 'N/A'}")
    print(f"   Email: {lead.contact_email or 'N/A'}")
    print(f"   Phone: {lead.contact_phone or 'N/A'}")
    print(f"   Contact Name: {lead.contact_name or 'N/A'}")
    print(f"   Lead Score: {lead.lead_score}")
    print(f"   Status: {lead.status}")
    print(f"   Converted: {bool(lead.converted_to_customer_id)}")
    if lead.converted_to_customer_id:
        print(f"   Converted to Customer ID: {lead.converted_to_customer_id}")
    print(f"   AI Analysis exists: {bool(lead.ai_analysis)}")
    if lead.ai_analysis and isinstance(lead.ai_analysis, dict):
        print(f"   AI Analysis Keys: {list(lead.ai_analysis.keys())}")
    print(f"   Companies House Data: {bool(lead.companies_house_data)}")
    print(f"   Google Maps Data: {bool(lead.google_maps_data)}")
    print(f"   Website Data: {bool(lead.website_data)}")
    print(f"   LinkedIn Data: {bool(lead.linkedin_data)}")
else:
    print("\n❌ No discovery found")

if customer:
    print("\n👤 CRM CUSTOMER DATA:")
    print(f"   ID: {customer.id}")
    print(f"   Company: {customer.company_name}")
    print(f"   Status: {customer.status}")
    print(f"   Website: {customer.website or 'N/A'}")
    print(f"   Email: {customer.main_email or 'N/A'}")
    print(f"   Phone: {customer.main_phone or 'N/A'}")
    print(f"   Lead Score: {customer.lead_score}")
    print(f"   AI Analysis Raw exists: {bool(customer.ai_analysis_raw)}")
    if customer.ai_analysis_raw and isinstance(customer.ai_analysis_raw, dict):
        print(f"   AI Analysis Keys: {list(customer.ai_analysis_raw.keys())}")
        if 'similar_companies' in customer.ai_analysis_raw:
            print(f"   Similar Companies: {len(customer.ai_analysis_raw.get('similar_companies', []))} found")
    print(f"   Companies House Data: {bool(customer.companies_house_data)}")
    print(f"   Google Maps Data: {bool(customer.google_maps_data)}")
    print(f"   Website Data: {bool(customer.website_data)}")
    print(f"   LinkedIn Data: {bool(customer.linkedin_data)}")
    print(f"   LinkedIn URL: {customer.linkedin_url or 'N/A'}")
    contacts = customer.contacts
    print(f"   Contacts: {len(contacts)}")
    for contact in contacts:
        print(f"     - {contact.first_name} {contact.last_name} ({contact.job_title or 'N/A'})")
else:
    print("\n❌ No CRM customer found")

# If both exist, check if they're linked
if lead and customer:
    if lead.converted_to_customer_id == customer.id:
        print("\n✅ Discovery and Customer are linked correctly")
    else:
        print(f"\n⚠️  Discovery converted to different customer: {lead.converted_to_customer_id}")

db.close()

