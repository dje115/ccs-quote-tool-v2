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
    
    # Run each seed script in its own session to avoid transaction issues
    try:
        # 1. Seed AI Providers (must be first - other scripts may depend on providers)
        db1 = SessionLocal()
        try:
            await seed_ai_providers(db1)
        except Exception as e:
            logger.warning(f"⚠️  Error seeding AI providers: {e}")
            db1.rollback()
        finally:
            db1.close()
        
        # 2. Seed AI Prompts (depends on providers)
        db2 = SessionLocal()
        try:
            await seed_ai_prompts(db2)
        except Exception as e:
            logger.warning(f"⚠️  Error seeding AI prompts: {e}")
            db2.rollback()
        finally:
            db2.close()
        
        # 3. Seed Quote Type Prompts (depends on prompts)
        db3 = SessionLocal()
        try:
            await seed_quote_type_prompts(db3)
        except Exception as e:
            logger.warning(f"⚠️  Error seeding quote type prompts: {e}")
            db3.rollback()
        finally:
            db3.close()
        
        logger.info("✅ All seed scripts completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Error running seed scripts: {e}", exc_info=True)
        # Don't fail startup - log error and continue
        # This allows the application to start even if seed scripts fail
        # (they can be run manually later if needed)


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
        
        from seed_ai_prompts import seed_prompts_async
        logger.info("Seeding AI prompts...")
        await seed_prompts_async(db)
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

