#!/usr/bin/env python3
"""Add partnership_opportunities field to tenants table"""

from backend.app.core.database import engine
from sqlalchemy import text

# Add the column
with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE tenants ADD COLUMN partnership_opportunities TEXT"))
        conn.commit()
        print("✓ Added partnership_opportunities column to tenants table")
    except Exception as e:
        if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
            print("✓ Column partnership_opportunities already exists")
        else:
            print(f"✗ Error: {e}")



