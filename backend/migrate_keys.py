import sqlite3
import os
from app.core.database import SessionLocal
from app.models.tenant import Tenant

# Path to v1 database
v1_db_path = '/app/../CCS quote tool/ccs_quotes.db'
print(f'Looking for v1 database at: {v1_db_path}')

if os.path.exists(v1_db_path):
    print('V1 database found!')
    
    # Extract API keys from v1
    conn = sqlite3.connect(v1_db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT service_name, api_key FROM api_settings WHERE api_key IS NOT NULL AND api_key != ''")
    results = cursor.fetchall()
    conn.close()
    
    openai_key = None
    companies_house_key = None
    google_maps_key = None
    
    for service_name, api_key in results:
        if service_name == 'openai':
            openai_key = api_key
        elif service_name == 'companies_house':
            companies_house_key = api_key
        elif service_name == 'google_maps':
            google_maps_key = api_key
    
    print(f'Found API keys:')
    print(f'  OpenAI: {"Configured" if openai_key else "Not found"}')
    print(f'  Companies House: {"Configured" if companies_house_key else "Not found"}')
    print(f'  Google Maps: {"Configured" if google_maps_key else "Not found"}')
    
    # Update v2 database
    db = SessionLocal()
    tenant = db.query(Tenant).filter(Tenant.name == "CCS Quote Tool").first()
    
    if tenant:
        if openai_key:
            tenant.openai_api_key = openai_key
            print('✓ Updated OpenAI API key')
        if companies_house_key:
            tenant.companies_house_api_key = companies_house_key
            print('✓ Updated Companies House API key')
        if google_maps_key:
            tenant.google_maps_api_key = google_maps_key
            print('✓ Updated Google Maps API key')
        
        db.commit()
        print('✓ API keys successfully migrated to v2 database')
    else:
        print('Default tenant not found in v2 database')
    
    db.close()
else:
    print('V1 database not found at expected path')
