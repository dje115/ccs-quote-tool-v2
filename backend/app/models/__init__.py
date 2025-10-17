"""
Database models for CCS Quote Tool v2
"""

from .base import Base
from .tenant import Tenant, User, TenantStatus, UserRole
from .crm import Customer, Contact, CustomerInteraction, CustomerStatus, BusinessSector, BusinessSize, ContactRole
from .leads import LeadGenerationCampaign, Lead, LeadInteraction, LeadGenerationPrompt, LeadGenerationStatus, LeadStatus, LeadSource
from .quotes import Quote, QuoteItem, QuoteTemplate, PricingItem, QuoteStatus
from .sales import SalesActivity, SalesNote, ActivityType, ActivityOutcome
from .sector import Sector

__all__ = [
    "Base",
    "Tenant", "User", "TenantStatus", "UserRole",
    "Customer", "Contact", "CustomerInteraction", "CustomerStatus", "BusinessSector", "BusinessSize", "ContactRole",
    "LeadGenerationCampaign", "Lead", "LeadInteraction", "LeadGenerationPrompt", "LeadGenerationStatus", "LeadStatus", "LeadSource",
    "Quote", "QuoteItem", "QuoteTemplate", "PricingItem", "QuoteStatus",
    "SalesActivity", "SalesNote", "ActivityType", "ActivityOutcome",
    "Sector"
]

