#!/usr/bin/env python3
"""
Celery tasks for quote operations
All long-running quote operations should be executed as Celery tasks
"""
import asyncio
import json
from typing import Dict, Any, Optional, List
from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.core.api_keys import get_api_keys
from app.models.quotes import Quote
from app.models.tenant import Tenant
from app.services.quote_analysis_service import QuoteAnalysisService


@celery_app.task(name='analyze_quote_requirements', bind=True)
def analyze_quote_requirements_task(
    self,
    quote_id: Optional[str],
    tenant_id: str,
    quote_data: Dict[str, Any],
    clarification_answers: Optional[List[Dict[str, str]]] = None,
    questions_only: bool = False
) -> Dict[str, Any]:
    """
    Background task to analyze quote requirements using AI
    
    Args:
        quote_id: Optional quote ID (if analyzing existing quote)
        tenant_id: Tenant ID
        quote_data: Quote data dictionary
        clarification_answers: Optional clarification answers
        questions_only: Whether to only return questions
    
    Returns:
        Dict with analysis results
    """
    db = SessionLocal()
    
    try:
        print(f"\n{'='*80}")
        print(f"🤖 ANALYZING QUOTE REQUIREMENTS (Background Task)")
        print(f"Task ID: {self.request.id}")
        print(f"Quote ID: {quote_id}")
        print(f"Tenant ID: {tenant_id}")
        print(f"{'='*80}\n")
        
        # Get tenant
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            return {'success': False, 'error': 'Tenant not found'}
        
        # Get API keys
        api_keys = get_api_keys(db, tenant)
        if not api_keys.openai:
            return {'success': False, 'error': 'OpenAI API key not configured'}
        
        # Initialize analysis service
        analysis_service = QuoteAnalysisService(
            db=db,
            tenant_id=tenant_id,
            openai_api_key=api_keys.openai
        )
        
        # Run async analysis
        result = asyncio.run(
            analysis_service.analyze_requirements(
                quote_data=quote_data,
                clarification_answers=clarification_answers,
                questions_only=questions_only
            )
        )
        
        # Update quote if it exists and not questions_only
        if quote_id and not questions_only and result.get('success') and result.get('analysis'):
            quote = db.query(Quote).filter(
                Quote.id == quote_id,
                Quote.tenant_id == tenant_id
            ).first()
            
            if quote:
                analysis = result['analysis']
                quote.ai_analysis = analysis
                quote.recommended_products = json.dumps(analysis.get('recommended_products', [])) if isinstance(analysis.get('recommended_products'), list) else analysis.get('recommended_products')
                quote.labour_breakdown = json.dumps(analysis.get('labour_breakdown', [])) if isinstance(analysis.get('labour_breakdown'), list) else analysis.get('labour_breakdown')
                quote.estimated_time = analysis.get('estimated_time')
                quote.estimated_cost = analysis.get('estimated_cost')
                quote.quotation_details = json.dumps(analysis.get('quotation', {})) if isinstance(analysis.get('quotation'), dict) else analysis.get('quotation')
                
                # Update travel costs if provided
                if 'travel_distance_km' in analysis:
                    quote.travel_distance_km = analysis.get('travel_distance_km')
                    quote.travel_time_minutes = analysis.get('travel_time_minutes')
                    quote.travel_cost = analysis.get('travel_cost')
                
                if result.get('raw_response'):
                    quote.ai_raw_response = result['raw_response']
                
                db.commit()
                print(f"✅ Quote {quote_id} updated with analysis results")
        
        return result
        
    except Exception as e:
        print(f"❌ Error in analyze_quote_requirements_task: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}
    finally:
        db.close()

