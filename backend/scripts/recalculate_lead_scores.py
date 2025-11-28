#!/usr/bin/env python3
"""
Script to recalculate lead scores for customers based on existing AI analysis data.
This is useful after updating the lead score calculation algorithm.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.crm import Customer
from app.services.ai_analysis_service import AIAnalysisService


def recalculate_lead_scores(tenant_id: str = None, customer_id: str = None):
    """
    Recalculate lead scores for customers based on existing AI analysis data.
    
    Args:
        tenant_id: Optional tenant ID to filter by
        customer_id: Optional customer ID to recalculate for a specific customer
    """
    db: Session = SessionLocal()
    
    try:
        # Build query
        query = db.query(Customer).filter(
            Customer.is_deleted == False,
            Customer.ai_analysis_raw.isnot(None)  # Only customers with AI analysis
        )
        
        if tenant_id:
            query = query.filter(Customer.tenant_id == tenant_id)
        
        if customer_id:
            query = query.filter(Customer.id == customer_id)
        
        customers = query.all()
        
        print(f"Found {len(customers)} customer(s) with AI analysis data")
        
        # Initialize AI service (we only need it for the calculation method)
        ai_service = AIAnalysisService(
            openai_api_key="",  # Not needed for recalculation
            companies_house_api_key="",
            google_maps_api_key="",
            tenant_id=tenant_id or "",
            db=db
        )
        
        updated_count = 0
        for customer in customers:
            try:
                if not customer.ai_analysis_raw:
                    continue
                
                # Recalculate lead score
                old_score = customer.lead_score
                new_score = ai_service._calculate_lead_score(customer.ai_analysis_raw)
                
                if old_score != new_score:
                    customer.lead_score = new_score
                    updated_count += 1
                    print(f"✓ {customer.company_name}: {old_score} → {new_score}")
                else:
                    print(f"  {customer.company_name}: {old_score} (no change)")
                    
            except Exception as e:
                print(f"✗ Error processing {customer.company_name}: {e}")
                continue
        
        # Commit changes
        if updated_count > 0:
            db.commit()
            print(f"\n✅ Updated {updated_count} customer(s)")
        else:
            print("\n✅ No changes needed")
            
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Recalculate lead scores for customers")
    parser.add_argument("--tenant-id", help="Tenant ID to filter by")
    parser.add_argument("--customer-id", help="Customer ID to recalculate for a specific customer")
    parser.add_argument("--company-name", help="Company name to search for (partial match)")
    
    args = parser.parse_args()
    
    if args.company_name:
        # Find customer by name
        db = SessionLocal()
        try:
            customer = db.query(Customer).filter(
                Customer.company_name.ilike(f"%{args.company_name}%"),
                Customer.is_deleted == False
            ).first()
            
            if customer:
                print(f"Found customer: {customer.company_name} (ID: {customer.id})")
                recalculate_lead_scores(customer_id=customer.id)
            else:
                print(f"❌ Customer not found: {args.company_name}")
        finally:
            db.close()
    else:
        recalculate_lead_scores(
            tenant_id=args.tenant_id,
            customer_id=args.customer_id
        )





