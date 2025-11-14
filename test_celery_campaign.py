#!/usr/bin/env python3
"""
Test script to verify Celery campaign execution
Tests the complete flow: create campaign -> start via API -> verify Celery executes
"""

import requests
import time
import sys

# Configuration
API_BASE = "http://localhost:8000/api/v1"
EMAIL = "admin@ccs.com"
PASSWORD = "admin123"

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")

def login():
    """Login and get auth token"""
    print_section("STEP 1: LOGIN")
    
    response = requests.post(
        f"{API_BASE}/auth/login",
        data={  # OAuth2 expects form data
            "username": EMAIL,
            "password": PASSWORD
        }
    )
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"✅ Login successful!")
        print(f"   Token: {token[:30]}...")
        return token
    else:
        print(f"❌ Login failed: {response.status_code}")
        print(f"   {response.text}")
        sys.exit(1)

def get_campaigns(token):
    """Get list of campaigns"""
    print_section("STEP 2: GET CAMPAIGNS")
    
    response = requests.get(
        f"{API_BASE}/campaigns",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        campaigns = response.json()
        print(f"✅ Found {len(campaigns)} campaigns")
        for c in campaigns:
            print(f"   - {c['name']} (ID: {c['id']}) - Status: {c['status']}")
        return campaigns
    else:
        print(f"❌ Failed to get campaigns: {response.status_code}")
        return []

def create_test_campaign(token):
    """Create a new test campaign"""
    print_section("STEP 3: CREATE TEST CAMPAIGN")
    
    campaign_data = {
        "name": f"Celery Test Campaign {int(time.time())}",
        "description": "Testing Celery background task execution",
        "prompt_type": "it_msp_expansion",
        "postcode": "LE17 5NJ",  # Market Harborough
        "distance_miles": 10,
        "max_results": 5,  # Keep it small for testing
        "exclude_duplicates": True,
        "include_existing_customers": False
    }
    
    response = requests.post(
        f"{API_BASE}/campaigns",
        headers={"Authorization": f"Bearer {token}"},
        json=campaign_data
    )
    
    if response.status_code == 201:
        campaign = response.json()
        print(f"✅ Campaign created successfully!")
        print(f"   ID: {campaign['id']}")
        print(f"   Name: {campaign['name']}")
        print(f"   Status: {campaign['status']}")
        return campaign
    else:
        print(f"❌ Failed to create campaign: {response.status_code}")
        print(f"   {response.text}")
        return None

def start_campaign(token, campaign_id):
    """Start the campaign via API (should queue to Celery)"""
    print_section("STEP 4: START CAMPAIGN (QUEUE TO CELERY)")
    
    response = requests.post(
        f"{API_BASE}/campaigns/{campaign_id}/start",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Campaign queued to Celery!")
        print(f"   Message: {result.get('message')}")
        print(f"   Task ID: {result.get('task_id')}")
        print(f"   Status: {result.get('status')}")
        return result.get('task_id')
    else:
        print(f"❌ Failed to start campaign: {response.status_code}")
        print(f"   {response.text}")
        return None

def poll_campaign_status(token, campaign_id, max_wait=300):
    """Poll campaign status until completion or timeout"""
    print_section("STEP 5: MONITOR CAMPAIGN EXECUTION")
    
    print(f"Polling campaign status (max {max_wait}s)...")
    print(f"Expected flow: DRAFT -> QUEUED -> RUNNING -> COMPLETED/FAILED\n")
    
    start_time = time.time()
    last_status = None
    
    while time.time() - start_time < max_wait:
        response = requests.get(
            f"{API_BASE}/campaigns/{campaign_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            campaign = response.json()
            status = campaign['status']
            
            if status != last_status:
                elapsed = int(time.time() - start_time)
                print(f"[{elapsed}s] Status: {status}")
                
                if status == 'QUEUED':
                    print(f"      ⏳ Campaign is queued in Celery, waiting for worker...")
                elif status == 'RUNNING':
                    print(f"      🚀 Campaign is executing in Celery worker!")
                    print(f"         - Searching for leads using OpenAI + web search")
                    print(f"         - This may take several minutes...")
                elif status == 'COMPLETED':
                    print(f"\n{'='*80}")
                    print(f"✅ CAMPAIGN COMPLETED SUCCESSFULLY!")
                    print(f"{'='*80}")
                    print(f"📊 Results:")
                    print(f"   - Total Found: {campaign.get('total_found', 0)}")
                    print(f"   - Leads Created: {campaign.get('leads_created', 0)}")
                    print(f"   - Duplicates: {campaign.get('duplicates_found', 0)}")
                    print(f"   - Started: {campaign.get('started_at', 'N/A')}")
                    print(f"   - Completed: {campaign.get('completed_at', 'N/A')}")
                    print(f"{'='*80}\n")
                    return True
                elif status == 'FAILED':
                    print(f"\n{'='*80}")
                    print(f"❌ CAMPAIGN FAILED")
                    print(f"{'='*80}")
                    print(f"   Error count: {campaign.get('errors_count', 0)}")
                    print(f"{'='*80}\n")
                    return False
                
                last_status = status
        
        time.sleep(5)  # Poll every 5 seconds
    
    print(f"\n⏰ Timeout reached after {max_wait}s")
    print(f"   Last status: {last_status}")
    return False

def main():
    """Run the complete test flow"""
    print("\n" + "="*80)
    print("  CELERY CAMPAIGN EXECUTION TEST")
    print("  Testing: FastAPI -> Celery -> Lead Generation -> Database")
    print("="*80)
    
    # Step 1: Login
    token = login()
    
    # Step 2: Get existing campaigns
    campaigns = get_campaigns(token)
    
    # Step 3: Create test campaign
    campaign = create_test_campaign(token)
    if not campaign:
        print("\n❌ TEST FAILED: Could not create campaign")
        sys.exit(1)
    
    campaign_id = campaign['id']
    
    # Step 4: Start campaign (queue to Celery)
    task_id = start_campaign(token, campaign_id)
    if not task_id:
        print("\n❌ TEST FAILED: Could not start campaign")
        sys.exit(1)
    
    # Step 5: Monitor execution
    success = poll_campaign_status(token, campaign_id, max_wait=300)
    
    # Final report
    print_section("TEST COMPLETE")
    if success:
        print("✅ Celery campaign execution is working correctly!")
        print("   - Campaign was queued to Celery")
        print("   - Celery worker picked up the task")
        print("   - Lead generation completed successfully")
        print("   - Results were saved to database")
        sys.exit(0)
    else:
        print("❌ Celery campaign execution test failed")
        print("   Check the Celery worker logs: docker logs ccs-celery-worker")
        print("   Check the backend logs: docker logs ccs-backend")
        sys.exit(1)

if __name__ == "__main__":
    main()






