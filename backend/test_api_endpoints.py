import httpx
import asyncio
from app.core.database import SessionLocal
from app.models.tenant import User, UserRole
from app.core.security import create_access_token

async def test_api_endpoints():
    print("🔍 Testing API Endpoints...")
    
    # Get admin user token
    db = SessionLocal()
    admin_user = db.query(User).filter(User.role == UserRole.SUPER_ADMIN).first()
    if not admin_user:
        print("❌ Admin user not found")
        return
    
    token = create_access_token(data={'sub': admin_user.id, 'email': admin_user.email, 'tenant_id': admin_user.tenant_id})
    db.close()
    
    # Test OpenAI API
    print("\n1. Testing OpenAI API...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                'http://localhost:8000/api/v1/admin/test-openai',
                headers={'Authorization': f'Bearer {token}'},
                timeout=30.0
            )
            result = response.json()
            if result.get("success"):
                print(f"   ✅ Success: {result.get('message')}")
            else:
                print(f"   ❌ Failed: {result.get('message')}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test Companies House API
    print("\n2. Testing Companies House API...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                'http://localhost:8000/api/v1/admin/test-companies_house',
                headers={'Authorization': f'Bearer {token}'},
                timeout=30.0
            )
            result = response.json()
            if result.get("success"):
                print(f"   ✅ Success: {result.get('message')}")
            else:
                print(f"   ❌ Failed: {result.get('message')}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test Google Maps API
    print("\n3. Testing Google Maps API...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                'http://localhost:8000/api/v1/admin/test-google_maps',
                headers={'Authorization': f'Bearer {token}'},
                timeout=30.0
            )
            result = response.json()
            if result.get("success"):
                print(f"   ✅ Success: {result.get('message')}")
            else:
                print(f"   ❌ Failed: {result.get('message')}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n📋 API Testing Complete!")

if __name__ == "__main__":
    asyncio.run(test_api_endpoints())
