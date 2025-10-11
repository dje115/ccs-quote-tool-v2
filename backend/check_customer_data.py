#!/usr/bin/env python3
import sys
sys.path.insert(0, '/app')

from app.core.database import SessionLocal
from app.models.crm import Customer
from sqlalchemy import select
import json

db = SessionLocal()
stmt = select(Customer).where(Customer.company_name == 'Arket Computer Services')
result = db.execute(stmt)
customer = result.scalars().first()

if customer:
    print(f'Customer: {customer.company_name}')
    print(f'ID: {customer.id}')
    print(f'Lead Score: {customer.lead_score}')
    print(f'\nAI Analysis Raw exists: {bool(customer.ai_analysis_raw)}')
    if customer.ai_analysis_raw:
        print(f'AI Analysis type: {type(customer.ai_analysis_raw)}')
        print(f'AI Analysis preview: {str(customer.ai_analysis_raw)[:200]}...')
    
    print(f'\nCompanies House Data exists: {bool(customer.companies_house_data)}')
    if customer.companies_house_data:
        print(f'Companies House type: {type(customer.companies_house_data)}')
    
    print(f'\nGoogle Maps Data exists: {bool(customer.google_maps_data)}')
    if customer.google_maps_data:
        print(f'Google Maps type: {type(customer.google_maps_data)}')
        if isinstance(customer.google_maps_data, dict):
            print(f'Google Maps locations count: {len(customer.google_maps_data.get("locations", []))}')
else:
    print('Customer not found!')

db.close()

