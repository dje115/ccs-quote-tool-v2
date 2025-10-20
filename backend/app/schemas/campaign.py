from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models import LeadGenerationStatus

class CampaignCreate(BaseModel):
    name: str = Field(..., description="Campaign name")
    description: Optional[str] = Field(None, description="Campaign description")
    sector_name: str = Field("General Business", description="Target sector name")  # Made optional with default
    postcode: Optional[str] = Field(None, description="UK postcode for location-based search")  # Made optional for company_list
    distance_miles: int = Field(50, ge=5, le=200, description="Search radius in miles")
    max_results: int = Field(20, ge=5, le=100, description="Maximum number of leads to generate")
    prompt_type: str = Field("sector_search", description="Type of search prompt")
    custom_prompt: Optional[str] = Field(None, description="Custom search prompt for custom_search type")
    company_size_category: Optional[str] = Field(None, description="Company size filter: Micro, Small, Medium, Large")
    
    # Company list campaign fields
    company_names: Optional[List[str]] = Field(None, description="List of company names for company_list campaigns")
    exclude_duplicates: Optional[bool] = Field(True, description="Whether to exclude duplicate companies")
    include_existing_customers: Optional[bool] = Field(False, description="Whether to include existing customers in analysis")

class CampaignResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    sector_name: str = Field(..., description="First business sector from business_sectors")
    postcode: Optional[str] = Field(None, description="UK postcode - optional for company_list campaigns")
    distance_miles: int
    max_results: int
    prompt_type: str
    custom_prompt: Optional[str]
    company_size_category: Optional[str]
    status: LeadGenerationStatus
    tenant_id: str
    created_by: str
    created_at: datetime
    completed_at: Optional[datetime]
    total_leads: int = Field(0, description="Number of leads created (leads_created)")
    ai_analysis_summary: Optional[str]
    
    # Company list campaign fields
    company_names: Optional[List[str]] = Field(None, description="List of company names for company_list campaigns")
    exclude_duplicates: Optional[bool] = Field(True, description="Whether to exclude duplicate companies")
    include_existing_customers: Optional[bool] = Field(False, description="Whether to include existing customers in analysis")

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
            "postcode": obj.postcode if obj.postcode else None,
            "distance_miles": obj.distance_miles,
            "max_results": obj.max_results,
            "prompt_type": obj.prompt_type,
            "custom_prompt": obj.custom_prompt,
            "company_size_category": obj.company_size_category,
            "status": obj.status,
            "tenant_id": obj.tenant_id,
            "created_by": obj.created_by,
            "created_at": obj.created_at,
            "completed_at": obj.completed_at,
            "total_leads": obj.leads_created,
            "ai_analysis_summary": obj.ai_analysis_summary,
            # Company list campaign fields
            "company_names": obj.company_names if obj.company_names else None,
            "exclude_duplicates": obj.exclude_duplicates if obj.exclude_duplicates is not None else True,
            "include_existing_customers": obj.include_existing_customers if obj.include_existing_customers is not None else False
        }
        return cls(**data)
