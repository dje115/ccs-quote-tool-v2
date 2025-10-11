import httpx
import asyncio
from app.core.database import SessionLocal
from app.models.tenant import User, UserRole
from app.core.security import create_access_token

async def test_tenant_apis():
    print('🔍 Testing Tenant API Endpoints...')
    
    # Get a regular user token (not admin)
    db = SessionLocal()
    user = db.query(User).filter(User.role != UserRole.SUPER_ADMIN).first()
    if not user:
        print('❌ No regular user found')
        return
    
    token = create_access_token(data={'sub': user.id, 'email': user.email, 'tenant_id': user.tenant_id})
    db.close()
    
    # Test OpenAI API
    print('\n1. Testing Tenant OpenAI API...')
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                'http://localhost:8000/api/v1/settings/test-openai',
                headers={'Authorization': f'Bearer {token}'},
                timeout=30.0
            )
            result = response.json()
            if result.get('success'):
                print(f'   ✅ Success: {result.get("message")}')
            else:
                print(f'   ❌ Failed: {result.get("message")}')
    except Exception as e:
        print(f'   ❌ Error: {e}')
    
    # Test Companies House API
    print('\n2. Testing Tenant Companies House API...')
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                'http://localhost:8000/api/v1/settings/test-companies-house',
                headers={'Authorization': f'Bearer {token}'},
                timeout=30.0
            )
            result = response.json()
            if result.get('success'):
                print(f'   ✅ Success: {result.get("message")}')
            else:
                print(f'   ❌ Failed: {result.get("message")}')
    except Exception as e:
        print(f'   ❌ Error: {e}')
    
    # Test Google Maps API
    print('\n3. Testing Tenant Google Maps API...')
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                'http://localhost:8000/api/v1/settings/test-google-maps',
                headers={'Authorization': f'Bearer {token}'},
                timeout=30.0
            )
            result = response.json()
            if result.get('success'):
                print(f'   ✅ Success: {result.get("message")}')
            else:
                print(f'   ❌ Failed: {result.get("message")}')
    except Exception as e:
        print(f'   ❌ Error: {e}')
    
    print('\n📋 Tenant API Testing Complete!')

if __name__ == "__main__":
    asyncio.run(test_tenant_apis())
