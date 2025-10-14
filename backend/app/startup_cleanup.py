"""
Startup cleanup script
Resets any stuck AI analysis tasks when the backend starts
"""
from app.core.database import SessionLocal
from app.models.crm import Customer
import logging

logger = logging.getLogger(__name__)

def cleanup_stuck_ai_tasks():
    """
    Reset any customers with 'running' or 'queued' AI analysis status
    This handles cases where the backend/celery restarts mid-task
    """
    db = SessionLocal()
    try:
        # Find all customers with active AI analysis tasks
        stuck_customers = db.query(Customer).filter(
            Customer.ai_analysis_status.in_(['running', 'queued'])
        ).all()
        
        if stuck_customers:
            logger.warning(f"Found {len(stuck_customers)} stuck AI analysis tasks, resetting...")
            
            for customer in stuck_customers:
                logger.info(f"Resetting AI analysis for: {customer.company_name} (was {customer.ai_analysis_status})")
                customer.ai_analysis_status = None
                customer.ai_analysis_task_id = None
            
            db.commit()
            logger.info(f"✓ Reset {len(stuck_customers)} stuck AI analysis tasks")
        else:
            logger.info("✓ No stuck AI analysis tasks found")
            
    except Exception as e:
        logger.error(f"Error cleaning up stuck AI tasks: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    # Allow running standalone for manual cleanup
    logging.basicConfig(level=logging.INFO)
    cleanup_stuck_ai_tasks()

