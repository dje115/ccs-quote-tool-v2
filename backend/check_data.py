from app.core.database import SessionLocal
from app.models.tenant import Tenant, User

db = SessionLocal()

print("=== TENANTS ===")
tenants = db.query(Tenant).all()
print(f"Total: {len(tenants)}")
for t in tenants:
    print(f"  - {t.name} | Status: {t.status} | ID: {t.id}")

print("\n=== USERS ===")
users = db.query(User).all()
print(f"Total: {len(users)}")
for u in users:
    role_str = u.role.value if hasattr(u.role, 'value') else str(u.role)
    print(f"  - {u.email} | Role: {role_str} | Tenant: {u.tenant_id}")

db.close()

