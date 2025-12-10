#!/usr/bin/env python3
"""
Celery tasks for quote operations
All long-running quote operations should be executed as Celery tasks
"""
from app.core.async_bridge import run_async_safe
import json
import logging
from typing import Dict, Any, Optional, List
from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.core.api_keys import get_api_keys
from app.models.quotes import Quote
from app.models.tenant import Tenant
from app.services.quote_analysis_service import QuoteAnalysisService

logger = logging.getLogger(__name__)


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
        logger.info("Analyzing quote requirements (background task)", extra={
            'task_id': self.request.id,
            'quote_id': quote_id,
            'tenant_id': tenant_id
        })
        
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
                logger.info("Quote updated with analysis results", extra={'quote_id': quote_id})
                
                # Publish quote analysis completed event
                from app.core.events import get_event_publisher
                event_publisher = get_event_publisher()
                event_publisher.publish_quote_updated_sync(
                    tenant_id=tenant_id,
                    quote_id=quote_id,
                    quote_data={
                        'id': quote.id,
                        'quote_number': quote.quote_number,
                        'ai_analysis': analysis,
                        'status': quote.status.value if hasattr(quote.status, 'value') else str(quote.status)
                    }
                )
        
        return result
        
    except Exception as e:
        logger.error("Error in analyze_quote_requirements_task", extra={'quote_id': quote_id, 'error': str(e)}, exc_info=True)
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}
    finally:
        db.close()

