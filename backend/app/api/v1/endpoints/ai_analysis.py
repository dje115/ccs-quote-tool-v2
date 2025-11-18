#!/usr/bin/env python3
"""
AI Analysis API endpoints for company analysis and lead generation
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from datetime import datetime

from app.core.dependencies import get_current_active_user, get_current_tenant, get_current_user
from app.core.database import get_async_db
from app.core.api_keys import get_api_keys
from app.models.tenant import User, Tenant
from app.models.crm import Customer
from app.services.ai_analysis_service import AIAnalysisService

router = APIRouter()


class CompanyAnalysisRequest(BaseModel):
    company_name: str
    company_number: Optional[str] = None


class LeadScoringRequest(BaseModel):
    company_data: Dict[str, Any]


class FinancialAnalysisRequest(BaseModel):
    company_number: str


class LeadStrategyRequest(BaseModel):
    company_data: Dict[str, Any]


@router.post("/analyze-company")
async def analyze_company(
    request: CompanyAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Comprehensive company analysis using AI, Companies House, and Google Maps
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        # Resolve API keys (tenant-specific with fallback to system keys) - use sync session
        from app.core.database import SessionLocal
        sync_db = SessionLocal()
        try:
            api_keys = get_api_keys(sync_db, current_tenant)
            
            # Initialize AI service with proper DB, tenant, and API keys
            ai_service = AIAnalysisService(
                openai_api_key=api_keys.openai,
                companies_house_api_key=api_keys.companies_house,
                google_maps_api_key=api_keys.google_maps,
                tenant_id=current_tenant.id,
                db=sync_db
            )
        finally:
            sync_db.close()
        
        # Perform analysis
        analysis_result = await ai_service.analyze_company(
            company_name=request.company_name,
            company_number=request.company_number
        )
        
        if not analysis_result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=analysis_result.get("error", "Analysis failed")
            )
        
        return {
            "success": True,
            "company_name": request.company_name,
            "analysis": analysis_result.get("analysis", {}),
            "source_data": analysis_result.get("source_data", {}),
            "analyzed_by": current_user.email,
            "analyzed_at": analysis_result.get("analyzed_at")
        }
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error analyzing company: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing company: {str(e)}"
        )


@router.post("/score-lead")
async def score_lead(
    request: LeadScoringRequest,
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Score lead quality using AI analysis
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        # Resolve API keys (tenant-specific with fallback to system keys) - use sync session
        from app.core.database import SessionLocal
        sync_db = SessionLocal()
        try:
            api_keys = get_api_keys(sync_db, current_tenant)
            
            # Initialize AI service with proper DB, tenant, and API keys
            ai_service = AIAnalysisService(
                openai_api_key=api_keys.openai,
                companies_house_api_key=api_keys.companies_house,
                google_maps_api_key=api_keys.google_maps,
                tenant_id=current_tenant.id,
                db=sync_db
            )
        finally:
            sync_db.close()
        
        # Perform lead scoring
        scoring_result = await ai_service.score_lead(request.company_data)
        
        if "error" in scoring_result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=scoring_result["error"]
            )
        
        return {
            "success": True,
            "scoring": scoring_result,
            "scored_by": current_user.email
        }
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error scoring lead: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error scoring lead: {str(e)}"
        )


@router.post("/analyze-financial")
async def analyze_financial_data(
    request: FinancialAnalysisRequest,
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Analyze financial data from Companies House
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        # Resolve API keys (tenant-specific with fallback to system keys) - use sync session
        from app.core.database import SessionLocal
        sync_db = SessionLocal()
        try:
            api_keys = get_api_keys(sync_db, current_tenant)
            
            # Initialize AI service with proper DB, tenant, and API keys
            ai_service = AIAnalysisService(
                openai_api_key=api_keys.openai,
                companies_house_api_key=api_keys.companies_house,
                google_maps_api_key=api_keys.google_maps,
                tenant_id=current_tenant.id,
                db=sync_db
            )
        finally:
            sync_db.close()
        
        # Perform financial analysis
        analysis_result = await ai_service.analyze_financial_data(request.company_number)
        
        if not analysis_result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=analysis_result.get("error", "Financial analysis failed")
            )
        
        return {
            "success": True,
            "company_number": request.company_number,
            "financial_data": analysis_result.get("financial_data", {}),
            "analysis": analysis_result.get("analysis", {}),
            "analyzed_by": current_user.email
        }
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error analyzing financial data: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing financial data: {str(e)}"
        )


@router.post("/generate-strategy")
async def generate_lead_strategy(
    request: LeadStrategyRequest,
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Generate lead engagement strategy
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        # Resolve API keys (tenant-specific with fallback to system keys) - use sync session
        from app.core.database import SessionLocal
        sync_db = SessionLocal()
        try:
            api_keys = get_api_keys(sync_db, current_tenant)
            
            # Initialize AI service with proper DB, tenant, and API keys
            ai_service = AIAnalysisService(
                openai_api_key=api_keys.openai,
                companies_house_api_key=api_keys.companies_house,
                google_maps_api_key=api_keys.google_maps,
                tenant_id=current_tenant.id,
                db=sync_db
            )
        finally:
            sync_db.close()
        
        # Generate strategy
        strategy_result = await ai_service.generate_lead_strategy(request.company_data)
        
        if "error" in strategy_result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=strategy_result["error"]
            )
        
        return {
            "success": True,
            "strategy": strategy_result,
            "generated_by": current_user.email
        }
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error generating strategy: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating strategy: {str(e)}"
        )


@router.get("/status")
async def get_ai_analysis_status(
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get status of running and queued AI analysis tasks for the current tenant.
    Returns a summary of customers with 'running' or 'queued' status.
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        from sqlalchemy import select
        
        # Query customers with running or queued AI analysis
        running_stmt = select(Customer).where(
            Customer.tenant_id == current_tenant.id,
            Customer.is_deleted == False,
            Customer.ai_analysis_status == 'running'
        )
        queued_stmt = select(Customer).where(
            Customer.tenant_id == current_tenant.id,
            Customer.is_deleted == False,
            Customer.ai_analysis_status == 'queued'
        )
        
        running_result = await db.execute(running_stmt)
        queued_result = await db.execute(queued_stmt)
        
        running_customers = running_result.scalars().all()
        queued_customers = queued_result.scalars().all()
        
        return {
            "running": [
                {
                    "customer_id": customer.id,
                    "company_name": customer.company_name,
                    "status": customer.ai_analysis_status or "running",
                    "task_id": customer.ai_analysis_task_id
                }
                for customer in running_customers
            ],
            "queued": [
                {
                    "customer_id": customer.id,
                    "company_name": customer.company_name,
                    "status": customer.ai_analysis_status or "queued",
                    "task_id": customer.ai_analysis_task_id
                }
                for customer in queued_customers
            ]
        }
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error fetching AI analysis status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching AI analysis status: {str(e)}"
        )


@router.get("/analysis-status")
async def get_analysis_status(
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get status of AI analysis services
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        # Resolve API keys (tenant-specific with fallback to system keys) - use sync session
        from app.core.database import SessionLocal
        sync_db = SessionLocal()
        try:
            api_keys = get_api_keys(sync_db, current_tenant)
        finally:
            sync_db.close()
        
        return {
            "success": True,
            "services": {
                "ai_analysis": bool(api_keys.openai),
                "companies_house": bool(api_keys.companies_house),
                "google_maps": bool(api_keys.google_maps)
            },
            "status": "operational" if api_keys.openai else "limited",
            "api_key_source": api_keys.source
        }
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error checking analysis status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking analysis status: {str(e)}"
        )


@router.get("/prompts")
async def get_ai_prompts(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get available AI prompts for analysis
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        # Return the available prompt types and their descriptions
        prompts = {
            "company_analysis": {
                "name": "Company Analysis",
                "description": "Comprehensive analysis of company data including financial health, growth potential, and IT infrastructure needs",
                "inputs": ["company_name", "company_number"],
                "outputs": ["analysis", "lead_score", "recommendations"]
            },
            "financial_analysis": {
                "name": "Financial Analysis", 
                "description": "AI-powered analysis of company financial data from Companies House",
                "inputs": ["company_number"],
                "outputs": ["financial_health", "growth_trends", "risk_assessment"]
            },
            "lead_scoring": {
                "name": "Lead Scoring",
                "description": "Score lead quality based on company data and characteristics",
                "inputs": ["company_data"],
                "outputs": ["lead_score", "score_breakdown", "recommendations"]
            },
            "engagement_strategy": {
                "name": "Engagement Strategy",
                "description": "Generate personalized engagement strategy for lead conversion",
                "inputs": ["company_data"],
                "outputs": ["strategy", "next_steps", "messaging"]
            }
        }
        
        return {
            "success": True,
            "prompts": prompts
        }
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting prompts: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting prompts: {str(e)}"
        )







