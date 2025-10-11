import httpx
import asyncio
from app.core.database import SessionLocal
from app.models.tenant import User, UserRole, Tenant
from app.core.security import create_access_token

async def check_api_status():
    # Get a regular user token
    db = SessionLocal()
    user = db.query(User).filter(User.role != UserRole.SUPER_ADMIN).first()
    if not user:
        print('No regular user found')
        return
    
    token = create_access_token(data={'sub': user.id, 'email': user.email, 'tenant_id': user.tenant_id})
    
    print(f'User: {user.email}')
    print(f'Tenant ID: {user.tenant_id}')
    
    # Check tenant-specific keys
    tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
    if tenant:
        print('\nTenant-specific API keys:')
        print(f'  OpenAI: {"Configured" if tenant.openai_api_key else "Not configured"}')
        print(f'  Companies House: {"Configured" if tenant.companies_house_api_key else "Not configured"}')
        print(f'  Google Maps: {"Configured" if tenant.google_maps_api_key else "Not configured"}')
    
    db.close()
    
    # Test the API status endpoint
    async with httpx.AsyncClient() as client:
        response = await client.get(
            'http://localhost:8000/api/v1/settings/api-status',
            headers={'Authorization': f'Bearer {token}'},
            timeout=10.0
        )
        
        if response.status_code == 200:
            result = response.json()
            print('\nAPI Status Response:')
            for api, status in result.items():
                configured = status.get('configured', False)
                source = status.get('source', 'unknown')
                print(f'  {api}: configured={configured}, source={source}')
        else:
            print(f'\nError: {response.status_code}')

if __name__ == "__main__":
    asyncio.run(check_api_status())
