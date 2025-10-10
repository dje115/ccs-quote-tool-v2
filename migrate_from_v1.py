#!/usr/bin/env python3
"""
Data migration script from v1 SQLite to v2 PostgreSQL
"""

import sys
import os
import sqlite3
import psycopg2
from datetime import datetime
import uuid

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Paths
V1_DB_PATH = "../ccs_quotes.db"  # v1 SQLite database
V2_DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "ccs_quote_tool",
    "user": "postgres",
    "password": "postgres_password_2025"
}

# Default tenant ID (CCS)
DEFAULT_TENANT_ID = None  # Will be fetched from v2 database


def connect_v1():
    """Connect to v1 SQLite database"""
    db_path = os.path.join(os.path.dirname(__file__), V1_DB_PATH)
    if not os.path.exists(db_path):
        print(f"[ERROR] v1 database not found at: {db_path}")
        return None
    
    print(f"[OK] Connecting to v1 database: {db_path}")
    return sqlite3.connect(db_path)


def connect_v2():
    """Connect to v2 PostgreSQL database"""
    print(f"[OK] Connecting to v2 database: {V2_DB_CONFIG['host']}:{V2_DB_CONFIG['port']}")
    return psycopg2.connect(**V2_DB_CONFIG)


def get_default_tenant_id(v2_conn):
    """Get the default tenant ID (CCS) from v2 database"""
    cursor = v2_conn.cursor()
    cursor.execute("SELECT id FROM tenants WHERE slug = 'ccs' LIMIT 1")
    result = cursor.fetchone()
    cursor.close()
    
    if result:
        return result[0]
    else:
        print("[ERROR] Default tenant 'ccs' not found in v2 database")
        return None


def migrate_customers(v1_conn, v2_conn, tenant_id):
    """Migrate customers from v1 to v2"""
    print("\n[MIGRATE] Customers...")
    
    v1_cursor = v1_conn.cursor()
    v2_cursor = v2_conn.cursor()
    
    # Get customers from v1
    v1_cursor.execute("""
        SELECT id, company_name, website, business_type, business_sector,
               employee_count_estimate, annual_revenue_estimate, contact_email, 
               contact_phone, status, lead_score, notes, created_at
        FROM customers
        WHERE is_deleted = 0
    """)
    
    customers = v1_cursor.fetchall()
    print(f"[INFO] Found {len(customers)} customers in v1")
    
    migrated = 0
    for customer in customers:
        try:
            v1_id = customer[0]
            
            # Insert into v2
            v2_cursor.execute("""
                INSERT INTO customers (
                    id, tenant_id, company_name, website, business_type, business_sector,
                    employee_count_estimate, annual_revenue_estimate, contact_email,
                    contact_phone, status, lead_score, notes, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (
                v1_id, tenant_id, customer[1], customer[2], customer[3], customer[4],
                customer[5], customer[6], customer[7], customer[8], customer[9],
                customer[10], customer[11], customer[12], datetime.utcnow()
            ))
            
            migrated += 1
            
        except Exception as e:
            print(f"[ERROR] Failed to migrate customer {customer[1]}: {e}")
    
    v2_conn.commit()
    print(f"[OK] Migrated {migrated}/{len(customers)} customers")
    
    v1_cursor.close()
    v2_cursor.close()


def migrate_contacts(v1_conn, v2_conn, tenant_id):
    """Migrate contacts from v1 to v2"""
    print("\n[MIGRATE] Contacts...")
    
    v1_cursor = v1_conn.cursor()
    v2_cursor = v2_conn.cursor()
    
    # Get contacts from v1
    v1_cursor.execute("""
        SELECT id, customer_id, first_name, last_name, job_title, role,
               email, phone, is_primary, notes, created_at
        FROM contacts
        WHERE is_deleted = 0
    """)
    
    contacts = v1_cursor.fetchall()
    print(f"[INFO] Found {len(contacts)} contacts in v1")
    
    migrated = 0
    for contact in contacts:
        try:
            v1_id = contact[0]
            
            # Insert into v2
            v2_cursor.execute("""
                INSERT INTO contacts (
                    id, tenant_id, customer_id, first_name, last_name, job_title,
                    role, email, phone, is_primary, notes, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (
                v1_id, tenant_id, contact[1], contact[2], contact[3], contact[4],
                contact[5], contact[6], contact[7], contact[8], contact[9],
                contact[10], datetime.utcnow()
            ))
            
            migrated += 1
            
        except Exception as e:
            print(f"[ERROR] Failed to migrate contact {contact[2]} {contact[3]}: {e}")
    
    v2_conn.commit()
    print(f"[OK] Migrated {migrated}/{len(contacts)} contacts")
    
    v1_cursor.close()
    v2_cursor.close()


def migrate_leads(v1_conn, v2_conn, tenant_id):
    """Migrate leads from v1 to v2"""
    print("\n[MIGRATE] Leads...")
    
    v1_cursor = v1_conn.cursor()
    v2_cursor = v2_conn.cursor()
    
    # Get leads from v1
    v1_cursor.execute("""
        SELECT id, campaign_id, company_name, website, contact_email, contact_phone,
               status, lead_score, source, business_sector, employee_count_estimate,
               annual_revenue_estimate, notes, created_at
        FROM leads
        WHERE is_deleted = 0
    """)
    
    leads = v1_cursor.fetchall()
    print(f"[INFO] Found {len(leads)} leads in v1")
    
    migrated = 0
    for lead in leads:
        try:
            v1_id = lead[0]
            
            # Insert into v2
            v2_cursor.execute("""
                INSERT INTO leads (
                    id, tenant_id, campaign_id, company_name, website, contact_email,
                    contact_phone, status, lead_score, source, business_sector,
                    employee_count_estimate, annual_revenue_estimate, notes,
                    created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (
                v1_id, tenant_id, lead[1], lead[2], lead[3], lead[4], lead[5],
                lead[6], lead[7], lead[8], lead[9], lead[10], lead[11], lead[12],
                lead[13], datetime.utcnow()
            ))
            
            migrated += 1
            
        except Exception as e:
            print(f"[ERROR] Failed to migrate lead {lead[2]}: {e}")
    
    v2_conn.commit()
    print(f"[OK] Migrated {migrated}/{len(leads)} leads")
    
    v1_cursor.close()
    v2_cursor.close()


def migrate_campaigns(v1_conn, v2_conn, tenant_id):
    """Migrate lead generation campaigns from v1 to v2"""
    print("\n[MIGRATE] Campaigns...")
    
    v1_cursor = v1_conn.cursor()
    v2_cursor = v2_conn.cursor()
    
    # Get campaigns from v1
    v1_cursor.execute("""
        SELECT id, name, description, prompt_type, postcode, distance_miles,
               max_results, custom_prompt, status, total_found, leads_created,
               duplicates_found, errors_count, started_at, completed_at, created_at
        FROM lead_generation_campaigns
        WHERE is_deleted = 0
    """)
    
    campaigns = v1_cursor.fetchall()
    print(f"[INFO] Found {len(campaigns)} campaigns in v1")
    
    migrated = 0
    for campaign in campaigns:
        try:
            v1_id = campaign[0]
            
            # Insert into v2
            v2_cursor.execute("""
                INSERT INTO lead_generation_campaigns (
                    id, tenant_id, name, description, prompt_type, postcode,
                    distance_miles, max_results, custom_prompt, status, total_found,
                    leads_created, duplicates_found, errors_count, started_at,
                    completed_at, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (
                v1_id, tenant_id, campaign[1], campaign[2], campaign[3], campaign[4],
                campaign[5], campaign[6], campaign[7], campaign[8], campaign[9],
                campaign[10], campaign[11], campaign[12], campaign[13], campaign[14],
                campaign[15], datetime.utcnow()
            ))
            
            migrated += 1
            
        except Exception as e:
            print(f"[ERROR] Failed to migrate campaign {campaign[1]}: {e}")
    
    v2_conn.commit()
    print(f"[OK] Migrated {migrated}/{len(campaigns)} campaigns")
    
    v1_cursor.close()
    v2_cursor.close()


def main():
    """Main migration function"""
    print("=" * 60)
    print("CCS Quote Tool - Data Migration v1 to v2")
    print("=" * 60)
    
    # Connect to databases
    v1_conn = connect_v1()
    if not v1_conn:
        print("[ERROR] Cannot connect to v1 database")
        return 1
    
    try:
        v2_conn = connect_v2()
    except Exception as e:
        print(f"[ERROR] Cannot connect to v2 database: {e}")
        v1_conn.close()
        return 1
    
    # Get default tenant ID
    tenant_id = get_default_tenant_id(v2_conn)
    if not tenant_id:
        v1_conn.close()
        v2_conn.close()
        return 1
    
    print(f"[OK] Using tenant ID: {tenant_id}")
    
    # Run migrations
    try:
        migrate_campaigns(v1_conn, v2_conn, tenant_id)
        migrate_customers(v1_conn, v2_conn, tenant_id)
        migrate_contacts(v1_conn, v2_conn, tenant_id)
        migrate_leads(v1_conn, v2_conn, tenant_id)
        
        print("\n" + "=" * 60)
        print("[SUCCESS] Migration completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        v1_conn.close()
        v2_conn.close()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

