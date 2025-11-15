#!/usr/bin/env python3
"""
Script to create version 1 history for all existing prompts that don't have version history
This ensures all prompts have proper versioning
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.ai_prompt import AIPrompt, AIPromptVersion
from datetime import datetime, timezone
import uuid


def create_missing_versions(db: Session):
    """Create version 1 for all prompts that don't have version history"""
    print("🔍 Checking for prompts without version history...")
    
    # Get all prompts
    prompts = db.query(AIPrompt).all()
    print(f"📋 Found {len(prompts)} total prompts")
    
    created_count = 0
    skipped_count = 0
    
    for prompt in prompts:
        # Check if version 1 already exists
        existing_version = db.query(AIPromptVersion).filter(
            AIPromptVersion.prompt_id == prompt.id,
            AIPromptVersion.version == 1
        ).first()
        
        if existing_version:
            skipped_count += 1
            continue
        
        # Create version 1 snapshot
        version = AIPromptVersion(
            id=str(uuid.uuid4()),
            prompt_id=prompt.id,
            version=1,
            note="Initial version (migrated)",
            system_prompt=prompt.system_prompt,
            user_prompt_template=prompt.user_prompt_template,
            variables=prompt.variables,
            model=prompt.model,
            temperature=prompt.temperature,
            max_tokens=prompt.max_tokens,
            created_by=prompt.created_by
        )
        
        db.add(version)
        created_count += 1
        print(f"✅ Created version 1 for: {prompt.name} ({prompt.category})")
    
    db.commit()
    print(f"\n📊 Summary:")
    print(f"   Created: {created_count} version records")
    print(f"   Skipped: {skipped_count} (already had version 1)")
    print(f"✅ Version history migration complete!")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        create_missing_versions(db)
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating versions: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

