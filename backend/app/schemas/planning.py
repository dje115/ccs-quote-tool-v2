"""
Planning Application schemas for API requests and responses
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.planning import PlanningApplicationStatus, PlanningCampaignStatus, ApplicationType


class PlanningApplicationBase(BaseModel):
    """Base planning application schema"""
    reference: str = Field(..., description="Planning application reference number")
    address: str = Field(..., description="Application address")
    proposal: str = Field(..., description="Description of the proposed development")
    application_type: Optional[ApplicationType] = Field(None, description="Type of application")
    status: PlanningApplicationStatus = Field(PlanningApplicationStatus.VALIDATED, description="Application status")
    date_validated: Optional[datetime] = Field(None, description="Date application was validated")
    date_decided: Optional[datetime] = Field(None, description="Date decision was made")
    latitude: Optional[float] = Field(None, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, description="Longitude coordinate")
    postcode: Optional[str] = Field(None, description="UK postcode")
    county: str = Field(..., description="UK county name")
    source_portal: str = Field(..., description="Planning portal source")


class PlanningApplicationCreate(PlanningApplicationBase):
    """Schema for creating a new planning application"""
    pass


class PlanningApplicationUpdate(BaseModel):
    """Schema for updating a planning application"""
    tenant_classification: Optional[str] = Field(None, description="Tenant-specific classification")
    relevance_score: Optional[int] = Field(None, ge=0, le=100, description="Relevance score 0-100")
    ai_analysis: Optional[Dict[str, Any]] = Field(None, description="AI analysis data")
    ai_summary: Optional[str] = Field(None, description="AI-generated summary")
    why_fit: Optional[str] = Field(None, description="Why this project fits tenant services")
    suggested_sales_approach: Optional[str] = Field(None, description="Suggested sales approach")


class PlanningApplicationResponse(PlanningApplicationBase):
    """Schema for planning application API responses"""
    id: str
    tenant_classification: Optional[str] = None
    relevance_score: Optional[int] = None
    ai_analysis: Optional[Dict[str, Any]] = None
    ai_summary: Optional[str] = None
    why_fit: Optional[str] = None
    suggested_sales_approach: Optional[str] = None
    converted_to_lead_id: Optional[str] = None
    converted_to_customer_id: Optional[str] = None
    conversion_date: Optional[datetime] = None
    is_archived: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PlanningApplicationCampaignBase(BaseModel):
    """Base planning campaign schema"""
    name: str = Field(..., description="Campaign name")
    description: Optional[str] = Field(None, description="Campaign description")
    county: str = Field(..., description="UK county to monitor")
    source_portal: str = Field(..., description="Planning portal to monitor")
    
    # Filtering settings
    application_types: Optional[List[ApplicationType]] = Field(None, description="Types of applications to include")
    include_residential: bool = Field(False, description="Include residential applications")
    include_commercial: bool = Field(True, description="Include commercial applications")
    include_industrial: bool = Field(True, description="Include industrial applications")
    include_change_of_use: bool = Field(True, description="Include change of use applications")
    
    # Keyword filtering
    keyword_filters: Optional[List[str]] = Field(None, description="Keywords to include")
    exclude_keywords: Optional[List[str]] = Field(None, description="Keywords to exclude")
    
    # Geographic filtering
    center_postcode: Optional[str] = Field(None, description="Center postcode for radius search")
    radius_miles: int = Field(50, ge=1, le=200, description="Search radius in miles")
    
    # Data settings
    days_to_monitor: int = Field(14, ge=1, le=90, description="Days back to monitor")
    max_results_per_run: int = Field(300, ge=10, le=1000, description="Max results per run")
    
    # Scheduling
    is_scheduled: bool = Field(False, description="Enable scheduling")
    schedule_frequency_days: int = Field(14, ge=1, le=365, description="Run frequency in days")
    
    # AI Analysis
    enable_ai_analysis: bool = Field(True, description="Enable AI analysis")
    max_ai_analysis_per_run: int = Field(20, ge=1, le=100, description="Max AI analysis per run")


class PlanningApplicationCampaignCreate(PlanningApplicationCampaignBase):
    """Schema for creating a planning campaign"""
    pass


class PlanningApplicationCampaignUpdate(BaseModel):
    """Schema for updating a planning campaign"""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[PlanningCampaignStatus] = None
    
    # Filtering settings
    application_types: Optional[List[ApplicationType]] = None
    include_residential: Optional[bool] = None
    include_commercial: Optional[bool] = None
    include_industrial: Optional[bool] = None
    include_change_of_use: Optional[bool] = None
    
    # Keyword filtering
    keyword_filters: Optional[List[str]] = None
    exclude_keywords: Optional[List[str]] = None
    
    # Geographic filtering
    center_postcode: Optional[str] = None
    radius_miles: Optional[int] = Field(None, ge=1, le=200)
    
    # Data settings
    days_to_monitor: Optional[int] = Field(None, ge=1, le=90)
    max_results_per_run: Optional[int] = Field(None, ge=10, le=1000)
    
    # Scheduling
    is_scheduled: Optional[bool] = None
    schedule_frequency_days: Optional[int] = Field(None, ge=1, le=365)
    
    # AI Analysis
    enable_ai_analysis: Optional[bool] = None
    max_ai_analysis_per_run: Optional[int] = Field(None, ge=1, le=100)


class PlanningApplicationCampaignResponse(PlanningApplicationCampaignBase):
    """Schema for planning campaign API responses"""
    id: str
    tenant_id: str
    status: PlanningCampaignStatus
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    
    # Results tracking
    total_applications_found: int = 0
    new_applications_this_run: int = 0
    ai_analysis_completed: int = 0
    leads_generated: int = 0
    
    # Error tracking
    last_error: Optional[str] = None
    consecutive_failures: int = 0
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    model_config = {"from_attributes": True}


class PlanningKeywordCreate(BaseModel):
    """Schema for creating planning keywords"""
    keyword: str = Field(..., description="Keyword text")
    keyword_type: str = Field(..., description="Type: commercial, residential, exclude, include")
    weight: int = Field(10, ge=1, le=100, description="Relevance weight")
    category: Optional[str] = Field(None, description="Category like data_centre, warehouse, etc.")


class PlanningKeywordResponse(BaseModel):
    """Schema for planning keyword responses"""
    id: str
    tenant_id: str
    keyword: str
    keyword_type: str
    weight: int
    category: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PlanningApplicationListResponse(BaseModel):
    """Schema for listing planning applications with filters"""
    applications: List[PlanningApplicationResponse]
    total: int
    page: int = 1
    per_page: int = 50
    total_pages: int


class PlanningApplicationArchiveRequest(BaseModel):
    """Schema for archiving planning applications"""
    application_ids: List[str] = Field(..., description="List of application IDs to archive/unarchive")
    archived: bool = Field(True, description="True to archive, False to unarchive")
