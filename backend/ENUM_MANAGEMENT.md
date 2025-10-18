# PostgreSQL Enum Management Guide

## Overview
This document explains how to manage PostgreSQL enum types in this application, particularly the `customerstatus` enum used in the CRM module.

## Important Rules

### 1. Case Sensitivity
PostgreSQL enums are **case-sensitive**. This application uses **UPPERCASE** values for consistency.

**DO:**
```python
class CustomerStatus(enum.Enum):
    LEAD = "LEAD"
    PROSPECT = "PROSPECT"
```

**DON'T:**
```python
class CustomerStatus(enum.Enum):
    LEAD = "lead"  # ❌ Won't match database
    PROSPECT = "Prospect"  # ❌ Mixed case causes errors
```

### 2. Python Enum vs Database Enum
- **Python enum name** (left side): Used in code, e.g., `CustomerStatus.LEAD`
- **Python enum value** (right side): Stored in database, e.g., `"LEAD"`
- These values MUST match the PostgreSQL enum exactly

### 3. Current CustomerStatus Values

#### Active Values (Use These)
```
LEAD          - New potential customer
PROSPECT      - Qualified lead, actively engaging
CUSTOMER      - Active paying customer
COLD_LEAD     - Lead that went cold
INACTIVE      - Customer no longer active
LOST          - Lost to competitor or decided not to buy
```

#### Legacy Values (Do Not Use)
```
ACTIVE        - Old status, replaced by CUSTOMER
CHURNED       - Old status, replaced by INACTIVE/LOST
customer      - Lowercase duplicate (migration artifact)
cold_lead     - Lowercase duplicate (migration artifact)
lost          - Lowercase duplicate (migration artifact)
```

## How to Add a New Status Value

### Step 1: Add to Python Enum
Edit `backend/app/models/crm.py`:
```python
class CustomerStatus(enum.Enum):
    LEAD = "LEAD"
    PROSPECT = "PROSPECT"
    # ... existing values ...
    NEW_STATUS = "NEW_STATUS"  # Add your new status
```

### Step 2: Add to Database
Create a migration script (e.g., `add_new_status.py`):
```python
from app.core.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TYPE customerstatus ADD VALUE IF NOT EXISTS 'NEW_STATUS';"))
        conn.commit()
        print("✅ Added 'NEW_STATUS'")
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
```

Run it:
```bash
docker-compose exec backend python add_new_status.py
```

### Step 3: Restart Backend
```bash
docker-compose restart backend
```

## Troubleshooting

### Error: "invalid input value for enum"
**Problem:** Python enum value doesn't match database enum value.

**Solution:**
1. Check database values:
```python
from app.core.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text(
        "SELECT enumlabel FROM pg_enum WHERE enumtypid = "
        "(SELECT oid FROM pg_type WHERE typname = 'customerstatus')"
    ))
    for row in result:
        print(row[0])
```

2. Ensure Python enum values match exactly (case-sensitive)

### Cannot Remove Enum Value
PostgreSQL does **NOT** support removing enum values directly. Options:
1. Leave unused values in the database (safe, recommended)
2. Recreate the entire enum type (complex, requires downtime)

## Best Practices

### 1. Always Document Changes
When adding/modifying enums, update:
- This documentation file
- Python enum docstring in `models/crm.py`
- Any related API documentation

### 2. Use Uppercase Convention
All status values should be UPPERCASE for consistency:
- Easy to read
- Clear distinction from regular strings
- Matches SQL conventions

### 3. Test After Changes
After modifying enums, test:
```bash
# 1. Check database has the value
docker-compose exec backend python -c "from app.core.database import engine; from sqlalchemy import text; print(list(engine.connect().execute(text('SELECT enumlabel FROM pg_enum WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = \'customerstatus\')')))"

# 2. Test in code
docker-compose exec backend python -c "from app.models.crm import CustomerStatus; print([s.value for s in CustomerStatus])"

# 3. Test API endpoint
curl http://localhost:8000/api/v1/dashboard/
```

### 4. Migration Strategy
When changing enum values:
1. Add new values to database first
2. Update code to use new values
3. Migrate existing data if needed
4. Leave old values in database (don't delete)

## History

### 2025-10-12: Enum Case Standardization
- **Issue:** Mixed case enum values (LEAD, customer, cold_lead)
- **Fix:** Standardized to all UPPERCASE
- **Added:** CUSTOMER, COLD_LEAD, LOST (uppercase versions)
- **Reason:** PostgreSQL enum comparison was failing due to case mismatch

## Reference Files

- Python Enum: `backend/app/models/crm.py` - `CustomerStatus` class
- Database Schema: Check with `docker-compose exec db psql -U postgres -d ccs_crm -c "\dT+ customerstatus"`
- Migration Examples: See scripts like `add_uppercase_enums.py`, `fix_all_enum_values.py`





