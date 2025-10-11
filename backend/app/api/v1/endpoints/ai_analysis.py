#!/usr/bin/env python3
"""
AI Analysis API endpoints for company analysis and lead generation
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from pydantic import BaseModel

from app.core.dependencies import get_db, get_current_active_user
from app.models.tenant import User
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
    db: Session = Depends(get_db)
):
    """Comprehensive company analysis using AI, Companies House, and Google Maps"""
    try:
        ai_service = AIAnalysisService()
        
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing company: {str(e)}"
        )


@router.post("/score-lead")
async def score_lead(
    request: LeadScoringRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Score lead quality using AI analysis"""
    try:
        ai_service = AIAnalysisService()
        
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error scoring lead: {str(e)}"
        )


@router.post("/analyze-financial")
async def analyze_financial_data(
    request: FinancialAnalysisRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Analyze financial data from Companies House"""
    try:
        ai_service = AIAnalysisService()
        
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing financial data: {str(e)}"
        )


@router.post("/generate-strategy")
async def generate_lead_strategy(
    request: LeadStrategyRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Generate lead engagement strategy"""
    try:
        ai_service = AIAnalysisService()
        
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating strategy: {str(e)}"
        )


@router.get("/analysis-status")
async def get_analysis_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get status of AI analysis services"""
    try:
        ai_service = AIAnalysisService()
        
        return {
            "success": True,
            "services": {
                "ai_analysis": ai_service.openai_client is not None,
                "companies_house": ai_service.companies_house_service.api_key is not None,
                "google_maps": ai_service.google_maps_service.api_key is not None
            },
            "status": "operational" if ai_service.openai_client else "limited"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking analysis status: {str(e)}"
        )


@router.get("/prompts")
async def get_ai_prompts(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get available AI prompts for analysis"""
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting prompts: {str(e)}"
        )


