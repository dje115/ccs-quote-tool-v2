#!/usr/bin/env python3
"""Fix admin.py and add reset endpoint"""

# Read the file
with open('/app/app/api/v1/endpoints/admin.py', 'r') as f:
    content = f.read()

# Find the last valid function (test_google_maps_api)
# Remove everything after it
marker = '    except Exception as e:\n        return {"success": False, "message": f"Connection failed: {str(e)}"}'
if marker in content:
    # Keep everything up to and including the marker
    clean_content = content[:content.rfind(marker) + len(marker)]
    
    # Add the new endpoint
    new_endpoint = '''


@router.post("/reset-stuck-tasks")
async def reset_stuck_ai_tasks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Reset any stuck AI analysis tasks
    Admin only - manually trigger cleanup of running/queued tasks
    """
    # Only allow admin users
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Find all customers with active AI analysis tasks
        stuck_customers = db.query(Customer).filter(
            Customer.ai_analysis_status.in_(['running', 'queued'])
        ).all()
        
        if not stuck_customers:
            return {
                "success": True,
                "message": "No stuck AI analysis tasks found",
                "reset_count": 0,
                "customers": []
            }
        
        reset_list = []
        for customer in stuck_customers:
            reset_list.append({
                "id": str(customer.id),
                "company_name": customer.company_name,
                "status": customer.ai_analysis_status,
                "task_id": customer.ai_analysis_task_id
            })
            
            customer.ai_analysis_status = None
            customer.ai_analysis_task_id = None
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Successfully reset {len(stuck_customers)} stuck AI analysis task(s)",
            "reset_count": len(stuck_customers),
            "customers": reset_list
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to reset tasks: {str(e)}")
'''
    
    final_content = clean_content + new_endpoint
    
    # Write back
    with open('/app/app/api/v1/endpoints/admin.py', 'w') as f:
        f.write(final_content)
    
    print("✅ File fixed and endpoint added")
else:
    print("❌ Could not find marker in file")





