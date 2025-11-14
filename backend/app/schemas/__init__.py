"""
Pydantic schemas for API validation
"""

from .sales import (
    SalesActivityCreate,
    SalesActivityUpdate,
    SalesActivityResponse,
    SalesNoteCreate,
    SalesNoteUpdate,
    SalesNoteResponse,
    TenantProfileUpdate,
    TenantProfileResponse,
    AISalesAssistantRequest,
    AISalesAssistantResponse,
    ActivityType,
    ActivityOutcome
)

from .planning import (
    PlanningApplicationCreate,
    PlanningApplicationUpdate,
    PlanningApplicationResponse,
    PlanningApplicationCampaignCreate,
    PlanningApplicationCampaignUpdate,
    PlanningApplicationCampaignResponse,
    PlanningKeywordCreate,
    PlanningKeywordResponse,
    PlanningApplicationListResponse,
    PlanningApplicationStatus,
    PlanningCampaignStatus,
    ApplicationType
)

__all__ = [
    "SalesActivityCreate",
    "SalesActivityUpdate",
    "SalesActivityResponse",
    "SalesNoteCreate",
    "SalesNoteUpdate",
    "SalesNoteResponse",
    "TenantProfileUpdate",
    "TenantProfileResponse",
    "AISalesAssistantRequest",
    "AISalesAssistantResponse",
    "ActivityType",
    "ActivityOutcome",
    "PlanningApplicationCreate",
    "PlanningApplicationUpdate",
    "PlanningApplicationResponse",
    "PlanningApplicationCampaignCreate",
    "PlanningApplicationCampaignUpdate",
    "PlanningApplicationCampaignResponse",
    "PlanningKeywordCreate",
    "PlanningKeywordResponse",
    "PlanningApplicationListResponse",
    "PlanningApplicationStatus",
    "PlanningCampaignStatus",
    "ApplicationType"
]

