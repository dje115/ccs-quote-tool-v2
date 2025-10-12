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
    "ActivityOutcome"
]

