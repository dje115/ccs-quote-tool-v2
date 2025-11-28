#!/usr/bin/env python3
"""Comprehensive check of conversion data"""
import sys
sys.path.insert(0, '/app')

from app.core.database import SessionLocal
from app.models.leads import Lead
from app.models.crm import Customer
import json

db = SessionLocal()

lead = db.query(Lead).filter(Lead.company_name.ilike('%Alliance Tooling%')).first()

if not lead:
    print("Discovery not found")
    sys.exit(1)

print("=" * 80)
print("CONVERSION DATA VERIFICATION - ALLIANCE TOOLING LTD")
print("=" * 80)

if not lead.converted_to_customer_id:
    print("\n⚠️  Discovery not yet converted")
    print(f"   Status: {lead.status}")
    sys.exit(0)

customer = db.query(Customer).filter(Customer.id == lead.converted_to_customer_id).first()

if not customer:
    print("\n❌ Customer not found for converted discovery")
    sys.exit(1)

print("\n✅ DISCOVERY CONVERTED")
print(f"   Discovery ID: {lead.id}")
print(f"   Customer ID: {customer.id}")
print(f"   Conversion Date: {lead.conversion_date}")

print("\n" + "=" * 80)
print("DATA COMPARISON")
print("=" * 80)

# Basic Info
print("\n1. BASIC INFORMATION:")
print(f"   Discovery Company: {lead.company_name}")
print(f"   Customer Company: {customer.company_name}")
print(f"   Match: {'✅' if lead.company_name == customer.company_name else '❌'}")
print(f"   Discovery Lead Score: {lead.lead_score}")
print(f"   Customer Lead Score: {customer.lead_score}")
print(f"   Match: {'✅' if lead.lead_score == customer.lead_score else '❌'}")

# Contact Info
print("\n2. CONTACT INFORMATION:")
print(f"   Discovery Website: {lead.website or 'N/A'}")
print(f"   Customer Website: {customer.website or 'N/A'}")
print(f"   Match: {'✅' if lead.website == customer.website else '❌'}")
print(f"   Discovery Email: {lead.contact_email or 'N/A'}")
print(f"   Customer Email: {customer.main_email or 'N/A'}")
print(f"   Match: {'✅' if lead.contact_email == customer.main_email else '❌'}")
print(f"   Discovery Phone: {lead.contact_phone or 'N/A'}")
print(f"   Customer Phone: {customer.main_phone or 'N/A'}")
print(f"   Match: {'✅' if lead.contact_phone == customer.main_phone else '❌'}")

# AI Analysis
print("\n3. AI ANALYSIS DATA:")
discovery_ai_keys = list(lead.ai_analysis.keys()) if lead.ai_analysis and isinstance(lead.ai_analysis, dict) else []
customer_ai_keys = list(customer.ai_analysis_raw.keys()) if customer.ai_analysis_raw and isinstance(customer.ai_analysis_raw, dict) else []

print(f"   Discovery AI Keys: {discovery_ai_keys}")
print(f"   Customer AI Keys: {customer_ai_keys}")

# Check each key
all_keys_match = True
for key in discovery_ai_keys:
    if key not in customer_ai_keys:
        print(f"   ❌ Missing key in customer: {key}")
        all_keys_match = False
    else:
        print(f"   ✅ Key present: {key}")

# Check additional AI fields
print("\n4. ADDITIONAL AI FIELDS:")
print(f"   Discovery AI Confidence: {lead.ai_confidence_score}")
if customer.ai_analysis_raw and isinstance(customer.ai_analysis_raw, dict):
    customer_confidence = customer.ai_analysis_raw.get('ai_confidence_score')
    print(f"   Customer AI Confidence: {customer_confidence}")
    print(f"   Match: {'✅' if lead.ai_confidence_score == customer_confidence else '❌'}")

print(f"   Discovery Qualification Reason: {bool(lead.qualification_reason)}")
if customer.ai_analysis_raw and isinstance(customer.ai_analysis_raw, dict):
    customer_qual = customer.ai_analysis_raw.get('qualification_reason')
    print(f"   Customer Qualification Reason: {bool(customer_qual)}")
    print(f"   Match: {'✅' if bool(lead.qualification_reason) == bool(customer_qual) else '❌'}")

# External Data
print("\n5. EXTERNAL DATA:")
print(f"   Discovery Companies House: {bool(lead.companies_house_data)}")
print(f"   Customer Companies House: {bool(customer.companies_house_data)}")
print(f"   Match: {'✅' if bool(lead.companies_house_data) == bool(customer.companies_house_data) else '❌'}")

print(f"   Discovery Google Maps: {bool(lead.google_maps_data)}")
print(f"   Customer Google Maps: {bool(customer.google_maps_data)}")
print(f"   Match: {'✅' if bool(lead.google_maps_data) == bool(customer.google_maps_data) else '❌'}")

print(f"   Discovery Website Data: {bool(lead.website_data)}")
print(f"   Customer Website Data: {bool(customer.website_data)}")
print(f"   Match: {'✅' if bool(lead.website_data) == bool(customer.website_data) else '❌'}")

print(f"   Discovery LinkedIn Data: {bool(lead.linkedin_data)}")
print(f"   Customer LinkedIn Data: {bool(customer.linkedin_data)}")
print(f"   Match: {'✅' if bool(lead.linkedin_data) == bool(customer.linkedin_data) else '❌'}")

print(f"   Discovery LinkedIn URL: {lead.linkedin_url or 'N/A'}")
print(f"   Customer LinkedIn URL: {customer.linkedin_url or 'N/A'}")
print(f"   Match: {'✅' if lead.linkedin_url == customer.linkedin_url else '❌'}")

# Check specific AI analysis content
print("\n6. AI ANALYSIS CONTENT CHECK:")
if lead.ai_analysis and customer.ai_analysis_raw:
    if isinstance(lead.ai_analysis, dict) and isinstance(customer.ai_analysis_raw, dict):
        # Check opportunity_summary
        if 'opportunity_summary' in lead.ai_analysis:
            disc_opp = lead.ai_analysis['opportunity_summary']
            cust_opp = customer.ai_analysis_raw.get('opportunity_summary', '')
            print(f"   Opportunity Summary Length - Discovery: {len(disc_opp) if isinstance(disc_opp, str) else 'N/A'}")
            print(f"   Opportunity Summary Length - Customer: {len(cust_opp) if isinstance(cust_opp, str) else 'N/A'}")
            print(f"   Match: {'✅' if disc_opp == cust_opp else '❌'}")
        
        # Check recommendations count
        if 'recommendations' in lead.ai_analysis:
            disc_recs = lead.ai_analysis['recommendations']
            cust_recs = customer.ai_analysis_raw.get('recommendations', [])
            print(f"   Recommendations Count - Discovery: {len(disc_recs) if isinstance(disc_recs, list) else 'N/A'}")
            print(f"   Recommendations Count - Customer: {len(cust_recs) if isinstance(cust_recs, list) else 'N/A'}")
            if isinstance(disc_recs, list) and isinstance(cust_recs, list):
                print(f"   Match: {'✅' if len(disc_recs) == len(cust_recs) else '❌'}")
            else:
                print(f"   Match: ❌")
        
        # Check next_steps count
        if 'next_steps' in lead.ai_analysis:
            disc_steps = lead.ai_analysis['next_steps']
            cust_steps = customer.ai_analysis_raw.get('next_steps', [])
            print(f"   Next Steps Count - Discovery: {len(disc_steps) if isinstance(disc_steps, list) else 'N/A'}")
            print(f"   Next Steps Count - Customer: {len(cust_steps) if isinstance(cust_steps, list) else 'N/A'}")
            if isinstance(disc_steps, list) and isinstance(cust_steps, list):
                print(f"   Match: {'✅' if len(disc_steps) == len(cust_steps) else '❌'}")
            else:
                print(f"   Match: ❌")

# Contacts
print("\n7. CONTACTS:")
contacts = customer.contacts
print(f"   Number of Contacts: {len(contacts)}")
if len(contacts) == 0 and lead.contact_name:
    print(f"   ⚠️  No contact created, but discovery has contact_name: {lead.contact_name}")
elif len(contacts) > 0:
    for contact in contacts:
        print(f"   ✅ {contact.first_name} {contact.last_name} ({contact.job_title or 'N/A'})")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print("✅ = Data copied correctly")
print("❌ = Data missing or mismatch")
print("⚠️  = Warning/Issue")

db.close()

