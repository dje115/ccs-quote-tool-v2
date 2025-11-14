#!/usr/bin/env python3
"""
Planning Application models for UK county-based planning data monitoring
"""

from sqlalchemy import Column, String, Boolean, Text, JSON, ForeignKey, Integer, Enum, DateTime, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
import uuid
from .base import Base, BaseModel


class PlanningApplicationStatus(enum.Enum):
    """Planning application status from the planning portal"""
    VALIDATED = "validated"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REFUSED = "refused"
    WITHDRAWN = "withdrawn"
    OTHER = "other"


class PlanningCampaignStatus(enum.Enum):
    """Planning campaign monitoring status"""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class ApplicationType(enum.Enum):
    """Type of planning application"""
    COMMERCIAL = "commercial"
    RESIDENTIAL = "residential"
    INDUSTRIAL = "industrial"
    MIXED_USE = "mixed_use"
    CHANGE_OF_USE = "change_of_use"
    MINOR = "minor"
    OTHER = "other"


class PlanningApplication(BaseModel):
    """Planning application model - stores individual planning applications"""
    __tablename__ = "planning_applications"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # External reference from planning portal
    reference = Column(String(100), nullable=False, index=True)  # Planning reference number
    external_id = Column(String(100), nullable=True, index=True)  # External system ID if available
    
    # Basic application details
    address = Column(Text, nullable=False)
    proposal = Column(Text, nullable=False)  # Description of what's being proposed
    application_type = Column(Enum(ApplicationType), nullable=True)
    status = Column(Enum(PlanningApplicationStatus), default=PlanningApplicationStatus.VALIDATED, nullable=False)
    
    # Dates
    date_validated = Column(DateTime(timezone=True), nullable=True)
    date_decided = Column(DateTime(timezone=True), nullable=True)
    
    # Location data
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    postcode = Column(String(20), nullable=True)
    
    # Source information
    county = Column(String(100), nullable=False, index=True)  # UK county (e.g., "Leicestershire")
    source_portal = Column(String(100), nullable=False)  # Which planning portal (e.g., "leicester_opendatasoft")
    
    # Classification and scoring (tenant-specific)
    tenant_classification = Column(String(50), nullable=True)  # How tenant classified this (commercial, residential, etc.)
    relevance_score = Column(Integer, nullable=True)  # 0-100 based on tenant's keywords/interests
    
    # AI Analysis (tenant-specific)
    ai_analysis = Column(JSON, nullable=True)  # Tenant-specific AI analysis
    ai_summary = Column(Text, nullable=True)  # Short AI-generated summary
    why_fit = Column(Text, nullable=True)  # Why this project might need tenant's services
    suggested_sales_approach = Column(Text, nullable=True)  # Recommended sales approach
    
    # Lead conversion tracking
    converted_to_lead_id = Column(String(36), nullable=True)
    converted_to_customer_id = Column(String(36), nullable=True)
    conversion_date = Column(DateTime(timezone=True), nullable=True)
    
    # Archive status (for deduplication but keeping records)
    is_archived = Column(Boolean, default=False, nullable=False, index=True)
    
    # Relationships (commented out to avoid import issues - can be added later)
    # lead = relationship("Lead", foreign_keys=[converted_to_lead_id])
    # customer = relationship("Customer", foreign_keys=[converted_to_customer_id])
    
    def __repr__(self):
        return f"<PlanningApplication {self.reference} - {self.address[:50]}>"


class PlanningApplicationCampaign(BaseModel):
    """Planning application campaign model - manages county monitoring per tenant"""
    __tablename__ = "planning_application_campaigns"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Campaign details
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # County configuration
    county = Column(String(100), nullable=False, index=True)  # UK county name
    source_portal = Column(String(100), nullable=False)  # Planning portal to monitor
    
    # Filtering settings (tenant-specific)
    application_types = Column(JSON, nullable=True)  # Array of ApplicationType enums
    include_residential = Column(Boolean, default=False, nullable=False)
    include_commercial = Column(Boolean, default=True, nullable=False)
    include_industrial = Column(Boolean, default=True, nullable=False)
    include_change_of_use = Column(Boolean, default=True, nullable=False)
    
    # Keyword filtering (tenant-specific)
    keyword_filters = Column(JSON, nullable=True)  # Array of keywords to include/exclude
    exclude_keywords = Column(JSON, nullable=True)  # Array of keywords to exclude
    
    # Geographic filtering
    center_postcode = Column(String(20), nullable=True)  # Center point for radius search
    radius_miles = Column(Integer, default=50, nullable=False)  # Search radius
    
    # Data retention settings
    days_to_monitor = Column(Integer, default=14, nullable=False)  # How many days back to fetch
    max_results_per_run = Column(Integer, default=300, nullable=False)
    
    # Scheduling configuration
    status = Column(Enum(PlanningCampaignStatus), default=PlanningCampaignStatus.DRAFT, nullable=False)
    is_scheduled = Column(Boolean, default=False, nullable=False)  # Enable/disable scheduling
    schedule_frequency_days = Column(Integer, default=14, nullable=False)  # Run every N days
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    next_run_at = Column(DateTime(timezone=True), nullable=True)
    
    # AI Analysis settings
    enable_ai_analysis = Column(Boolean, default=True, nullable=False)
    max_ai_analysis_per_run = Column(Integer, default=20, nullable=False)  # Limit AI analysis to top N
    
    # Results tracking
    total_applications_found = Column(Integer, default=0)
    new_applications_this_run = Column(Integer, default=0)
    ai_analysis_completed = Column(Integer, default=0)
    leads_generated = Column(Integer, default=0)
    
    # Error tracking
    last_error = Column(Text, nullable=True)
    consecutive_failures = Column(Integer, default=0)
    
    # Timestamps and user tracking
    created_by = Column(String(36), nullable=True)
    updated_by = Column(String(36), nullable=True)
    
    def __repr__(self):
        return f"<PlanningApplicationCampaign {self.name} - {self.county}>"


class PlanningApplicationKeyword(BaseModel):
    """Tenant-specific keywords for planning application classification"""
    __tablename__ = "planning_application_keywords"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Keyword details
    keyword = Column(String(200), nullable=False)
    keyword_type = Column(String(50), nullable=False)  # "commercial", "residential", "exclude", "include"
    weight = Column(Integer, default=10, nullable=False)  # Relevance weight 1-100
    
    # Category
    category = Column(String(100), nullable=True)  # e.g., "data_centre", "warehouse", "office_fit_out"
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    def __repr__(self):
        return f"<PlanningApplicationKeyword {self.keyword} ({self.keyword_type})>"
