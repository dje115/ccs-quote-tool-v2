import httpx
import asyncio
from app.core.database import SessionLocal
from app.models.tenant import User, UserRole
from app.core.security import create_access_token

async def test_updated_api_status():
    # Get a regular user token
    db = SessionLocal()
    user = db.query(User).filter(User.role != UserRole.SUPER_ADMIN).first()
    if not user:
        print('No regular user found')
        return
    
    token = create_access_token(data={'sub': user.id, 'email': user.email, 'tenant_id': user.tenant_id})
    db.close()
    
    print(f'Testing updated API status for user: {user.email}')
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            'http://localhost:8000/api/v1/settings/api-status',
            headers={'Authorization': f'Bearer {token}'},
            timeout=10.0
        )
        
        if response.status_code == 200:
            result = response.json()
            print('Updated API Status Response:')
            for api, status in result.items():
                configured = status.get('configured', False)
                status_text = status.get('status', 'unknown')
                source = status.get('source', 'unknown')
                print(f'  {api}: configured={configured}, status={status_text}, source={source}')
        else:
            print(f'Error: {response.status_code}')
            print(response.text)

if __name__ == "__main__":
    asyncio.run(test_updated_api_status())
