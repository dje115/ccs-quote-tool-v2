#!/usr/bin/env python3
"""
Simple script to start an existing queued campaign
"""
import requests
import sys

API_BASE = "http://localhost:8000/api/v1"
EMAIL = "admin@ccs.com"
PASSWORD = "admin123"

# Login
response = requests.post(
    f"{API_BASE}/auth/login",
    data={"username": EMAIL, "password": PASSWORD}
)

if response.status_code != 200:
    print(f"❌ Login failed: {response.status_code}")
    sys.exit(1)

token = response.json()["access_token"]
print(f"✅ Logged in")

# Get campaigns
response = requests.get(
    f"{API_BASE}/campaigns",
    headers={"Authorization": f"Bearer {token}"}
)

campaigns = response.json()
print(f"\n📋 Found {len(campaigns)} campaigns:")

for c in campaigns:
    print(f"  - {c['name']}")
    print(f"    ID: {c['id']}")
    print(f"    Status: {c['status']}")
    
    # If it's QUEUED, try to restart it (which will re-queue it)
    if c['status'].upper() in ['QUEUED', 'FAILED']:
        print(f"    🔄 Starting this campaign...")
        
        # Use restart for QUEUED/FAILED campaigns
        if c['status'].upper() == 'QUEUED':
            # Set it back to draft first
            print(f"    ⚠️  Campaign is QUEUED - it should be picked up by Celery worker")
            print(f"    📊 Check: docker logs ccs-celery-worker -f")
        else:
            restart_response = requests.post(
                f"{API_BASE}/campaigns/{c['id']}/restart",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if restart_response.status_code == 200:
                result = restart_response.json()
                print(f"    ✅ Restarted! Task ID: {result.get('task_id')}")
            else:
                print(f"    ❌ Failed: {restart_response.text}")
    
    elif c['status'].upper() == 'DRAFT':
        print(f"    🚀 Starting this DRAFT campaign...")
        
        start_response = requests.post(
            f"{API_BASE}/campaigns/{c['id']}/start",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if start_response.status_code == 200:
            result = start_response.json()
            print(f"    ✅ Started! Task ID: {result.get('task_id')}")
        else:
            print(f"    ❌ Failed: {start_response.text}")
    
    print()

print("\n🔍 To monitor Celery execution:")
print("   docker logs ccs-celery-worker -f")
print("\n🔍 To monitor backend:")
print("   docker logs ccs-backend -f")





