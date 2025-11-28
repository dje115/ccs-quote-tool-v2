#!/usr/bin/env python3
"""Script to check discovery data before and after conversion"""
import sys
sys.path.insert(0, '/app')

from app.core.database import SessionLocal
from app.models.leads import Lead
from app.models.crm import Customer
import json

db = SessionLocal()

# Find the discovery
lead = db.query(Lead).filter(Lead.company_name.ilike('%Precision Engineering UK%')).first()

if not lead:
    print("❌ Discovery not found")
    sys.exit(1)

print("=" * 80)
print("BEFORE CONVERSION - DISCOVERY DATA")
print("=" * 80)
print(f"ID: {lead.id}")
print(f"Company: {lead.company_name}")
print(f"Website: {lead.website or 'N/A'}")
print(f"Email: {lead.contact_email or 'N/A'}")
print(f"Phone: {lead.contact_phone or 'N/A'}")
print(f"Contact Name: {lead.contact_name or 'N/A'}")
print(f"Contact Title: {lead.contact_title or 'N/A'}")
print(f"Lead Score: {lead.lead_score}")
print(f"Status: {lead.status}")
print(f"Qualification Reason: {lead.qualification_reason[:200] if lead.qualification_reason else 'N/A'}")
print(f"\nAI Analysis Data:")
print(f"  - AI Analysis exists: {bool(lead.ai_analysis)}")
if lead.ai_analysis:
    if isinstance(lead.ai_analysis, dict):
        print(f"  - AI Analysis Keys: {list(lead.ai_analysis.keys())}")
        if 'similar_companies' in lead.ai_analysis:
            print(f"  - Similar Companies: {len(lead.ai_analysis.get('similar_companies', []))} found")
    else:
        print(f"  - AI Analysis Type: {type(lead.ai_analysis)}")
print(f"  - AI Confidence Score: {lead.ai_confidence_score or 'N/A'}")
print(f"  - AI Recommendation: {lead.ai_recommendation[:100] if lead.ai_recommendation else 'N/A'}...")
print(f"  - AI Notes: {lead.ai_notes[:100] if lead.ai_notes else 'N/A'}...")
print(f"\nExternal Data:")
print(f"  - Companies House Data: {bool(lead.companies_house_data)}")
print(f"  - Google Maps Data: {bool(lead.google_maps_data)}")
print(f"  - Website Data: {bool(lead.website_data)}")
print(f"  - LinkedIn URL: {lead.linkedin_url or 'N/A'}")
print(f"  - LinkedIn Data: {bool(lead.linkedin_data)}")
print(f"  - Social Media Links: {bool(lead.social_media_links)}")
print(f"\nProject Info:")
print(f"  - Potential Project Value: {lead.potential_project_value or 'N/A'}")
print(f"  - Timeline Estimate: {lead.timeline_estimate or 'N/A'}")
print(f"  - Annual Revenue: {lead.annual_revenue or 'N/A'}")
print(f"\nOther:")
print(f"  - Notes: {lead.notes[:200] if lead.notes else 'N/A'}")
print(f"  - Converted to Customer ID: {lead.converted_to_customer_id or 'Not converted yet'}")

# Check if already converted
if lead.converted_to_customer_id:
    customer = db.query(Customer).filter(Customer.id == lead.converted_to_customer_id).first()
    if customer:
        print("\n" + "=" * 80)
        print("AFTER CONVERSION - CRM CUSTOMER DATA")
        print("=" * 80)
        print(f"Customer ID: {customer.id}")
        print(f"Company: {customer.company_name}")
        print(f"Status: {customer.status}")
        print(f"Website: {customer.website or 'N/A'}")
        print(f"Email: {customer.main_email or 'N/A'}")
        print(f"Phone: {customer.main_phone or 'N/A'}")
        print(f"Lead Score: {customer.lead_score}")
        print(f"Description: {customer.description[:200] if customer.description else 'N/A'}...")
        print(f"\nAI Analysis Data:")
        print(f"  - AI Analysis Raw exists: {bool(customer.ai_analysis_raw)}")
        if customer.ai_analysis_raw:
            if isinstance(customer.ai_analysis_raw, dict):
                print(f"  - AI Analysis Keys: {list(customer.ai_analysis_raw.keys())}")
                if 'similar_companies' in customer.ai_analysis_raw:
                    print(f"  - Similar Companies: {len(customer.ai_analysis_raw.get('similar_companies', []))} found")
                if 'ai_confidence_score' in customer.ai_analysis_raw:
                    print(f"  - AI Confidence Score: {customer.ai_analysis_raw.get('ai_confidence_score')}")
                if 'potential_project_value' in customer.ai_analysis_raw:
                    print(f"  - Potential Project Value: {customer.ai_analysis_raw.get('potential_project_value')}")
        print(f"\nExternal Data:")
        print(f"  - Companies House Data: {bool(customer.companies_house_data)}")
        print(f"  - Google Maps Data: {bool(customer.google_maps_data)}")
        print(f"  - Website Data: {bool(customer.website_data)}")
        print(f"  - LinkedIn URL: {customer.linkedin_url or 'N/A'}")
        print(f"  - LinkedIn Data: {bool(customer.linkedin_data)}")
        print(f"\nContacts:")
        contacts = customer.contacts
        print(f"  - Number of Contacts: {len(contacts)}")
        for contact in contacts:
            print(f"    - {contact.first_name} {contact.last_name} ({contact.job_title or 'N/A'})")

db.close()

