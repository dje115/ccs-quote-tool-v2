from app.core.database import SessionLocal
from app.models.crm import Customer

db = SessionLocal()
c = db.query(Customer).filter(Customer.company_name == 'Central Technology Ltd').first()

if c:
    print(f'AI Status: {c.ai_analysis_status}')
    print(f'Task ID: {c.ai_analysis_task_id}')
    print(f'Started: {c.ai_analysis_started_at}')
    print(f'Completed: {c.ai_analysis_completed_at}')
    
    if c.ai_analysis_status in ['running', 'queued']:
        print('\n❌ Button is DISABLED - Task appears to be running')
    else:
        print('\n✅ Button should be ENABLED')
else:
    print('Customer not found')

db.close()



