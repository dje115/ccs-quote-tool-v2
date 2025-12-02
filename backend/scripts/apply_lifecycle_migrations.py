#!/usr/bin/env python3
"""
Apply lifecycle and opportunity migrations to the database
This script applies the SQL migrations for customer lifecycle fields and opportunities table
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from app.core.config import settings

def apply_migration(migration_file: str):
    """Apply a single migration file"""
    migration_path = Path(__file__).parent.parent / "migrations" / migration_file
    
    if not migration_path.exists():
        print(f"❌ Migration file not found: {migration_file}")
        return False
    
    print(f"📄 Applying migration: {migration_file}")
    
    try:
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            # Read migration SQL
            with open(migration_path, 'r') as f:
                migration_sql = f.read()
            
            # Execute migration
            conn.execute(text(migration_sql))
            conn.commit()
            
        print(f"✅ Successfully applied: {migration_file}")
        return True
    except Exception as e:
        print(f"❌ Error applying {migration_file}: {e}")
        return False
    finally:
        engine.dispose()

def main():
    """Apply all lifecycle-related migrations"""
    print("🚀 Applying lifecycle and opportunity migrations...\n")
    
    migrations = [
        "add_customer_lifecycle_fields.sql",
        "add_opportunities_table.sql"
    ]
    
    success_count = 0
    for migration in migrations:
        if apply_migration(migration):
            success_count += 1
        print()  # Blank line between migrations
    
    print(f"\n{'='*60}")
    if success_count == len(migrations):
        print(f"✅ All {success_count} migrations applied successfully!")
    else:
        print(f"⚠️  {success_count}/{len(migrations)} migrations applied successfully")
        print("Please check the errors above and fix any issues.")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()



