#!/usr/bin/env python3
"""
Pydantic schemas for sales activity tracking
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ActivityType(str, Enum):
    """Activity type enum"""
    CALL = "call"
    MEETING = "meeting"
    EMAIL = "email"
    NOTE = "note"
    TASK = "task"


class ActivityOutcome(str, Enum):
    """Activity outcome enum"""
    SUCCESSFUL = "successful"
    NO_ANSWER = "no_answer"
    VOICEMAIL = "voicemail"
    FOLLOW_UP_REQUIRED = "follow_up_required"
    NOT_INTERESTED = "not_interested"
    MEETING_SCHEDULED = "meeting_scheduled"
    QUOTE_REQUESTED = "quote_requested"
    WON = "won"
    LOST = "lost"


class SalesActivityBase(BaseModel):
    """Base sales activity schema"""
    customer_id: str
    contact_id: Optional[str] = None
    activity_type: ActivityType
    activity_date: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    subject: Optional[str] = None
    notes: str
    outcome: Optional[ActivityOutcome] = None
    follow_up_required: bool = False
    follow_up_date: Optional[datetime] = None
    follow_up_notes: Optional[str] = None
    ai_suggestions_used: List[str] = Field(default_factory=list)
    ai_context: Dict[str, Any] = Field(default_factory=dict)
    additional_data: Dict[str, Any] = Field(default_factory=dict)


class SalesActivityCreate(SalesActivityBase):
    """Schema for creating a sales activity"""
    pass


class SalesActivityUpdate(BaseModel):
    """Schema for updating a sales activity"""
    contact_id: Optional[str] = None
    activity_type: Optional[ActivityType] = None
    activity_date: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    subject: Optional[str] = None
    notes: Optional[str] = None
    outcome: Optional[ActivityOutcome] = None
    follow_up_required: Optional[bool] = None
    follow_up_date: Optional[datetime] = None
    follow_up_notes: Optional[str] = None
    ai_suggestions_used: Optional[List[str]] = None
    ai_context: Optional[Dict[str, Any]] = None
    additional_data: Optional[Dict[str, Any]] = None


class SalesActivityResponse(SalesActivityBase):
    """Schema for sales activity response"""
    id: str
    tenant_id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SalesNoteBase(BaseModel):
    """Base sales note schema"""
    customer_id: str
    note: str
    is_important: bool = False


class SalesNoteCreate(SalesNoteBase):
    """Schema for creating a sales note"""
    pass


class SalesNoteUpdate(BaseModel):
    """Schema for updating a sales note"""
    note: Optional[str] = None
    is_important: Optional[bool] = None


class SalesNoteResponse(SalesNoteBase):
    """Schema for sales note response"""
    id: str
    tenant_id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TenantProfileUpdate(BaseModel):
    """Schema for updating tenant company profile"""
    company_name: Optional[str] = None
    company_address: Optional[str] = None
    company_phone_numbers: Optional[List[str]] = None
    company_email_addresses: Optional[List[Dict[str, Any]]] = None  # [{"email": "...", "is_default": bool}]
    company_contact_names: Optional[List[Dict[str, Any]]] = None  # [{"name": "...", "is_default": bool}]
    company_description: Optional[str] = None
    company_websites: Optional[List[str]] = None
    products_services: Optional[List[str]] = None
    unique_selling_points: Optional[List[str]] = None
    target_markets: Optional[List[str]] = None
    sales_methodology: Optional[str] = None
    elevator_pitch: Optional[str] = None
    partnership_opportunities: Optional[str] = None
    logo_url: Optional[str] = None
    logo_text: Optional[str] = None
    use_text_logo: Optional[bool] = None
    
    class Config:
        extra = "ignore"  # Ignore extra fields like marketing_keywords (read-only)


class TenantProfileResponse(BaseModel):
    """Schema for tenant profile response"""
    company_name: Optional[str] = None
    company_address: Optional[str] = None
    company_phone_numbers: List[str] = Field(default_factory=list)
    company_email_addresses: List[Dict[str, Any]] = Field(default_factory=list)
    company_contact_names: List[Dict[str, Any]] = Field(default_factory=list)
    company_description: Optional[str] = None
    company_websites: List[str] = Field(default_factory=list)
    products_services: List[str] = Field(default_factory=list)
    unique_selling_points: List[str] = Field(default_factory=list)
    target_markets: List[str] = Field(default_factory=list)
    sales_methodology: Optional[str] = None
    elevator_pitch: Optional[str] = None
    logo_url: Optional[str] = None
    logo_text: Optional[str] = None
    use_text_logo: bool = False
    company_analysis: Dict[str, Any] = Field(default_factory=dict)
    company_analysis_date: Optional[datetime] = None
    website_keywords: Dict[str, List[str]] = Field(default_factory=dict)  # {"website_url": ["keyword1", "keyword2"]}

    class Config:
        from_attributes = True


class AISalesAssistantRequest(BaseModel):
    """Request schema for AI sales assistant"""
    customer_id: str
    query: str
    context: Optional[Dict[str, Any]] = None  # Additional context if needed


class AISalesAssistantResponse(BaseModel):
    """Response schema for AI sales assistant"""
    answer: str
    suggestions: List[str] = Field(default_factory=list)  # Follow-up suggestions
    relevant_data: Dict[str, Any] = Field(default_factory=dict)  # Relevant customer data used
    prompt_used: Optional[str] = None  # The prompt sent to AI (for transparency)

