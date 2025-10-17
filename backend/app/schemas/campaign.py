from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models import LeadGenerationStatus

class CampaignCreate(BaseModel):
    name: str = Field(..., description="Campaign name")
    description: Optional[str] = Field(None, description="Campaign description")
    sector_name: str = Field(..., description="Target sector name")
    postcode: str = Field(..., description="UK postcode for location-based search")
    distance_miles: int = Field(50, ge=5, le=200, description="Search radius in miles")
    max_results: int = Field(20, ge=5, le=100, description="Maximum number of leads to generate")
    prompt_type: str = Field("sector_search", description="Type of search prompt")
    custom_prompt: Optional[str] = Field(None, description="Custom search prompt for custom_search type")

class CampaignResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    sector_name: str = Field(..., description="First business sector from business_sectors")
    postcode: str
    distance_miles: int
    max_results: int
    prompt_type: str
    custom_prompt: Optional[str]
    status: LeadGenerationStatus
    tenant_id: str
    created_by: str
    created_at: datetime
    completed_at: Optional[datetime]
    total_leads: int = Field(0, description="Number of leads created (leads_created)")
    ai_analysis_summary: Optional[str]

    class Config:
        from_attributes = True
        
    @classmethod
    def from_orm(cls, obj):
        """Custom from_orm method to handle field mapping"""
        data = {
            "id": obj.id,
            "name": obj.name,
            "description": obj.description,
            "sector_name": obj.business_sectors[0] if obj.business_sectors else "General Business",
            "postcode": obj.postcode,
            "distance_miles": obj.distance_miles,
            "max_results": obj.max_results,
            "prompt_type": obj.prompt_type,
            "custom_prompt": obj.custom_prompt,
            "status": obj.status,
            "tenant_id": obj.tenant_id,
            "created_by": obj.created_by,
            "created_at": obj.created_at,
            "completed_at": obj.completed_at,
            "total_leads": obj.leads_created,
            "ai_analysis_summary": obj.ai_analysis_summary
        }
        return cls(**data)
