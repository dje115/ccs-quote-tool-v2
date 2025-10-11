#!/usr/bin/env python3
"""
Add lead_score column to customers table
"""
from sqlalchemy import create_engine, text
import os

def add_lead_score_column():
    """Add lead_score column if it doesn't exist"""
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL', 'postgresql://ccsuser:ccspass@db:5432/ccsquote')
    
    # Create synchronous engine
    engine = create_engine(database_url)
    
    with engine.begin() as conn:
        # Check if column exists
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='customers' AND column_name='lead_score'
        """))
        
        exists = result.fetchone()
        
        if not exists:
            print("Adding lead_score column to customers table...")
            conn.execute(text("""
                ALTER TABLE customers 
                ADD COLUMN lead_score INTEGER
            """))
            print("✅ lead_score column added successfully!")
        else:
            print("✅ lead_score column already exists")

if __name__ == "__main__":
    add_lead_score_column()
