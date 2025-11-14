#!/usr/bin/env python3
"""
Add missing columns to quotes table
"""
import os
import sys
from sqlalchemy import create_engine, text

# Get database URL from environment
database_url = os.getenv(
    'DATABASE_URL',
    'postgresql://postgres:postgres_password_2025@localhost:5432/ccs_quote_tool'
)

engine = create_engine(database_url)

migrations = [
    "ALTER TABLE quotes ADD COLUMN IF NOT EXISTS project_title VARCHAR(200)",
    "ALTER TABLE quotes ADD COLUMN IF NOT EXISTS project_description TEXT",
    "ALTER TABLE quotes ADD COLUMN IF NOT EXISTS site_address TEXT",
    "ALTER TABLE quotes ADD COLUMN IF NOT EXISTS building_type VARCHAR(100)",
    "ALTER TABLE quotes ADD COLUMN IF NOT EXISTS building_size FLOAT",
    "ALTER TABLE quotes ADD COLUMN IF NOT EXISTS number_of_floors INTEGER DEFAULT 1",
    "ALTER TABLE quotes ADD COLUMN IF NOT EXISTS number_of_rooms INTEGER DEFAULT 1",
    "ALTER TABLE quotes ADD COLUMN IF NOT EXISTS cabling_type VARCHAR(50)",
    "ALTER TABLE quotes ADD COLUMN IF NOT EXISTS wifi_requirements BOOLEAN DEFAULT FALSE",
    "ALTER TABLE quotes ADD COLUMN IF NOT EXISTS cctv_requirements BOOLEAN DEFAULT FALSE",
    "ALTER TABLE quotes ADD COLUMN IF NOT EXISTS door_entry_requirements BOOLEAN DEFAULT FALSE",
    "ALTER TABLE quotes ADD COLUMN IF NOT EXISTS special_requirements TEXT",
    "ALTER TABLE quotes ADD COLUMN IF NOT EXISTS travel_distance_km FLOAT",
    "ALTER TABLE quotes ADD COLUMN IF NOT EXISTS travel_time_minutes FLOAT",
    "ALTER TABLE quotes ADD COLUMN IF NOT EXISTS travel_cost NUMERIC(10,2)",
    "ALTER TABLE quotes ADD COLUMN IF NOT EXISTS ai_analysis JSON",
    "ALTER TABLE quotes ADD COLUMN IF NOT EXISTS recommended_products JSON",
    "ALTER TABLE quotes ADD COLUMN IF NOT EXISTS labour_breakdown JSON",
    "ALTER TABLE quotes ADD COLUMN IF NOT EXISTS quotation_details JSON",
    "ALTER TABLE quotes ADD COLUMN IF NOT EXISTS clarifications_log JSON",
    "ALTER TABLE quotes ADD COLUMN IF NOT EXISTS ai_raw_response TEXT",
    "ALTER TABLE quotes ADD COLUMN IF NOT EXISTS estimated_time INTEGER",
    "ALTER TABLE quotes ADD COLUMN IF NOT EXISTS estimated_cost NUMERIC(10,2)",
]

with engine.connect() as conn:
    for migration in migrations:
        try:
            conn.execute(text(migration))
            print(f"✓ {migration.split('ADD COLUMN')[1].strip()}")
        except Exception as e:
            print(f"✗ Error: {e}")
    conn.commit()

print("\n✅ Migration completed!")


