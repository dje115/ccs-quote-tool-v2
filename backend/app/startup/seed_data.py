#!/usr/bin/env python3
"""
Startup seed data initialization
Runs all database seed scripts automatically on application startup
"""

import asyncio
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.logging import get_logger

logger = get_logger(__name__)


async def run_seed_scripts():
    """
    Run all database seed scripts during application startup.
    This ensures the database is properly initialized with default data.
    
    All seed scripts are idempotent - they can be run multiple times safely.
    """
    logger.info("🌱 Running database seed scripts...")
    
    db = SessionLocal()
    try:
        # Run seed scripts in order
        # 1. Seed AI Providers (must be first - other scripts may depend on providers)
        await seed_ai_providers(db)
        
        # 2. Seed AI Prompts (depends on providers)
        await seed_ai_prompts(db)
        
        # 3. Seed Quote Type Prompts (depends on prompts)
        await seed_quote_type_prompts(db)
        
        logger.info("✅ All seed scripts completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Error running seed scripts: {e}", exc_info=True)
        # Don't fail startup - log error and continue
        # This allows the application to start even if seed scripts fail
        # (they can be run manually later if needed)
    finally:
        db.close()


def _get_scripts_path():
    """Get absolute path to scripts directory"""
    import os
    # Get backend directory (parent of app directory)
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
    scripts_path = os.path.join(backend_dir, 'scripts')
    return scripts_path


async def seed_ai_providers(db: Session):
    """Seed AI providers"""
    try:
        import sys
        scripts_path = _get_scripts_path()
        if scripts_path not in sys.path:
            sys.path.insert(0, scripts_path)
        
        from seed_ai_providers import seed_providers
        logger.info("Seeding AI providers...")
        seed_providers(db)
        logger.info("✅ AI providers seeded")
    except Exception as e:
        logger.warning(f"⚠️  Error seeding AI providers: {e}")
        # Continue with other seeds even if this fails


async def seed_ai_prompts(db: Session):
    """Seed AI prompts"""
    try:
        import sys
        scripts_path = _get_scripts_path()
        if scripts_path not in sys.path:
            sys.path.insert(0, scripts_path)
        
        from seed_ai_prompts import seed_prompts
        logger.info("Seeding AI prompts...")
        seed_prompts(db)
        logger.info("✅ AI prompts seeded")
    except Exception as e:
        logger.warning(f"⚠️  Error seeding AI prompts: {e}")
        # Continue with other seeds even if this fails


async def seed_quote_type_prompts(db: Session):
    """Seed quote type-specific prompts"""
    try:
        import sys
        scripts_path = _get_scripts_path()
        if scripts_path not in sys.path:
            sys.path.insert(0, scripts_path)
        
        from seed_quote_type_prompts import seed_quote_type_prompts_async
        logger.info("Seeding quote type prompts...")
        await seed_quote_type_prompts_async(db)
        logger.info("✅ Quote type prompts seeded")
    except ImportError as e:
        # Script might not exist yet - that's okay
        logger.debug(f"Quote type prompts script not found - skipping: {e}")
    except Exception as e:
        logger.warning(f"⚠️  Error seeding quote type prompts: {e}")
        # Continue even if this fails


if __name__ == "__main__":
    # Allow running directly for testing
    asyncio.run(run_seed_scripts())

