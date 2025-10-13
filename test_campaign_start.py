#!/usr/bin/env python3
"""
Quick test script to start a campaign and monitor execution
"""
import requests
import time

# Configuration
API_BASE = "http://localhost:8000/api/v1"
EMAIL = "admin@ccs.com"
PASSWORD = "admin123"
CAMPAIGN_ID = "d7be75e0-484b-4841-9fef-5588563aa361"

def main():
    print("🔐 Step 1: Logging in...")
    
    # Login
    login_response = requests.post(
        f"{API_BASE}/auth/login",
        data={"username": EMAIL, "password": PASSWORD}
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        print(login_response.text)
        return
    
    token = login_response.json()["access_token"]
    print(f"✅ Logged in successfully")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Check campaign status
    print(f"\n📊 Step 2: Checking campaign status...")
    campaign_response = requests.get(
        f"{API_BASE}/campaigns/{CAMPAIGN_ID}",
        headers=headers
    )
    
    if campaign_response.status_code != 200:
        print(f"❌ Failed to get campaign: {campaign_response.status_code}")
        return
    
    campaign = campaign_response.json()
    print(f"✅ Campaign: {campaign['name']}")
    print(f"   Status: {campaign['status']}")
    print(f"   Max Results: {campaign['max_results']}")
    
    # Start campaign
    print(f"\n🚀 Step 3: Starting campaign...")
    start_response = requests.post(
        f"{API_BASE}/campaigns/{CAMPAIGN_ID}/start",
        headers=headers
    )
    
    if start_response.status_code != 200:
        print(f"❌ Failed to start campaign: {start_response.status_code}")
        print(start_response.text)
        return
    
    print(f"✅ Campaign start request sent!")
    print(f"   Response: {start_response.json()}")
    
    # Monitor campaign status
    print(f"\n👀 Step 4: Monitoring campaign (will check every 5 seconds)...")
    print(f"   Watch backend logs in another terminal:")
    print(f"   docker logs ccs-backend -f")
    print()
    
    for i in range(24):  # Monitor for up to 2 minutes
        time.sleep(5)
        
        status_response = requests.get(
            f"{API_BASE}/campaigns/{CAMPAIGN_ID}",
            headers=headers
        )
        
        if status_response.status_code == 200:
            campaign = status_response.json()
            status = campaign['status']
            leads = campaign['leads_created']
            total = campaign['total_found']
            
            print(f"   [{i*5:>3}s] Status: {status:<12} | Leads: {leads:>3} | Total Found: {total:>3}")
            
            if status in ['COMPLETED', 'FAILED', 'CANCELLED']:
                print(f"\n{'='*60}")
                print(f"🏁 Campaign finished with status: {status}")
                print(f"   Total Found: {total}")
                print(f"   Leads Created: {leads}")
                print(f"   Duplicates: {campaign.get('duplicates_found', 0)}")
                print(f"   Errors: {campaign.get('errors_count', 0)}")
                print(f"{'='*60}")
                break
        else:
            print(f"   [{i*5:>3}s] Failed to check status")
    else:
        print(f"\n⏰ Monitoring timeout (2 minutes). Campaign may still be running.")
        print(f"   Check final status manually or view backend logs.")

if __name__ == "__main__":
    main()

