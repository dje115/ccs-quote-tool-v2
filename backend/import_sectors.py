#!/usr/bin/env python3
"""
Import sector data from CSV file to database
"""

import csv
import sys
import os
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent))

from app.core.database import get_db
from app.models import Sector, Base
from app.core.config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def import_sectors():
    """Import sectors from CSV file to database"""
    
    # Create database engine
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Check if sectors already exist
        existing_sectors = db.query(Sector).count()
        if existing_sectors > 0:
            print(f"⚠️  {existing_sectors} sectors already exist in database")
            response = input("Do you want to clear existing sectors and re-import? (y/N): ")
            if response.lower() == 'y':
                db.query(Sector).delete()
                db.commit()
                print("✅ Cleared existing sectors")
            else:
                print("❌ Import cancelled")
                return
        
        # Read CSV file - try multiple possible paths
        possible_paths = [
            Path(__file__).parent / "sectors.csv",  # Local copy
            Path("/app/sectors.csv"),               # Docker container path
            Path("sectors.csv"),                    # Current directory
        ]
        
        csv_file = None
        for path in possible_paths:
            if path.exists():
                csv_file = path
                break
        
        if not csv_file:
            print(f"❌ CSV file not found. Tried paths:")
            for path in possible_paths:
                print(f"   - {path}")
            return
        
        
        print(f"📖 Reading sector data from: {csv_file}")
        
        imported_count = 0
        
        with open(csv_file, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            for row in csv_reader:
                try:
                    # Create sector object (excluding the dynamic columns)
                    sector = Sector(
                        sector_name=row['Sector Name'].strip(),
                        prompt_ready_replacement_line=row['Prompt-Ready Replacement Line'].strip(),
                        example_keywords=row['Example Keywords (for search queries)'].strip(),
                        example_companies=row['Example Companies (UK)'].strip() if row['Example Companies (UK)'].strip() else None
                    )
                    
                    db.add(sector)
                    imported_count += 1
                    
                    if imported_count % 10 == 0:
                        print(f"📊 Imported {imported_count} sectors...")
                        
                except Exception as e:
                    print(f"⚠️  Error importing sector '{row.get('Sector Name', 'Unknown')}': {e}")
                    continue
        
        # Commit all changes
        db.commit()
        print(f"✅ Successfully imported {imported_count} sectors to database")
        
        # Verify import
        total_sectors = db.query(Sector).count()
        print(f"📊 Total sectors in database: {total_sectors}")
        
    except Exception as e:
        print(f"❌ Error importing sectors: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    import_sectors()
