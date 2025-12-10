"""
Database models for CCS Quote Tool v2
"""

from .base import Base
from .tenant import Tenant, User, TenantStatus, UserRole
from .crm import Customer, Contact, CustomerInteraction, CustomerStatus, BusinessSector, BusinessSize, ContactRole
from .leads import LeadGenerationCampaign, Lead, LeadInteraction, LeadGenerationPrompt, LeadGenerationStatus, LeadStatus, LeadSource
from .quotes import (
    Quote,
    QuoteItem,
    QuoteTemplate,
    PricingItem,
    QuoteStatus,
    QuoteApprovalState,
    QuoteWorkflowLog,
    CustomerOrder,
    SupplierPurchaseOrder,
    OrderStatus,
    PurchaseOrderStatus,
)
from .quote_documents import QuoteDocument, QuoteDocumentVersion, DocumentType
from .quote_prompt_history import QuotePromptHistory
from .product import Product, PricingRule, QuoteVersion
from .supplier import Supplier, SupplierCategory, SupplierPricing, ProductContentHistory, PricingVerificationQueue
from .sales import SalesActivity, SalesNote, ActivityType, ActivityOutcome
from .sector import Sector
from .planning import PlanningApplication, PlanningApplicationCampaign, PlanningApplicationKeyword, PlanningApplicationStatus, PlanningCampaignStatus, ApplicationType
from .ai_prompt import AIPrompt, AIPromptVersion, PromptCategory
from .ai_provider import AIProvider, ProviderAPIKey, ProviderType
from .pricing_config import TenantPricingConfig, PricingBundleItem, PricingConfigType, BundleType
from .support_contract import SupportContract, ContractRenewal, ContractTemplate as SupportContractTemplate, ContractType as SupportContractType, ContractStatus as SupportContractStatus, RenewalFrequency
from .contracts import Contract, EnhancedContractTemplate, ContractTemplateVersion, ContractType, ContractStatus
from .opportunities import Opportunity, OpportunityStage
from .helpdesk import Ticket, TicketComment, TicketAttachment, TicketHistory, TicketAgentChat, NPAHistory, SLAPolicy, TicketTemplate, QuickReplyTemplate, TicketMacro, TicketLink, TicketTimeEntry, TicketStatus, TicketPriority, TicketType
from .auth import RefreshToken
from .knowledge_base import KnowledgeBaseArticle
from .sla_compliance import SLAComplianceRecord, SLABreachAlert
from .password_history import PasswordHistory
from .account_lockout import AccountLockout
from .passwordless_login import PasswordlessLoginToken
from .user_2fa import User2FA
from .security_event import SecurityEvent, SecurityEventType, SecurityEventSeverity

__all__ = [
    "Base",
    "Tenant", "User", "TenantStatus", "UserRole",
    "Customer", "Contact", "CustomerInteraction", "CustomerStatus", "BusinessSector", "BusinessSize", "ContactRole",
    "LeadGenerationCampaign", "Lead", "LeadInteraction", "LeadGenerationPrompt", "LeadGenerationStatus", "LeadStatus", "LeadSource",
    "Quote", "QuoteItem", "QuoteTemplate", "PricingItem", "QuoteStatus", "QuoteApprovalState",
    "QuoteWorkflowLog", "CustomerOrder", "SupplierPurchaseOrder", "OrderStatus", "PurchaseOrderStatus",
    "QuoteDocument", "QuoteDocumentVersion", "DocumentType",
    "QuotePromptHistory",
    "Product", "PricingRule", "QuoteVersion",
           "Supplier", "SupplierCategory", "SupplierPricing", "ProductContentHistory", "PricingVerificationQueue",
    "SalesActivity", "SalesNote", "ActivityType", "ActivityOutcome",
    "Sector",
    "PlanningApplication", "PlanningApplicationCampaign", "PlanningApplicationKeyword", "PlanningApplicationStatus", "PlanningCampaignStatus", "ApplicationType",
    "AIPrompt", "AIPromptVersion", "PromptCategory",
    "AIProvider", "ProviderAPIKey", "ProviderType",
    "TenantPricingConfig", "PricingBundleItem", "PricingConfigType", "BundleType",
    "SupportContract", "ContractRenewal", "SupportContractTemplate", "SupportContractType", "SupportContractStatus", "RenewalFrequency",
    "Contract", "EnhancedContractTemplate", "ContractTemplateVersion", "ContractType", "ContractStatus",
    "Opportunity", "OpportunityStage",
    "Ticket", "TicketComment", "TicketAttachment", "TicketHistory", "TicketAgentChat", "NPAHistory", "SLAPolicy", "TicketTemplate", "QuickReplyTemplate", "TicketMacro", "TicketLink", "TicketTimeEntry",
    "TicketStatus", "TicketPriority", "TicketType",
    "SLAComplianceRecord", "SLABreachAlert",
    "KnowledgeBaseArticle",
    "RefreshToken",
    "PasswordHistory",
    "AccountLockout",
    "PasswordlessLoginToken",
    "User2FA",
    "SecurityEvent",
    "SecurityEventType",
    "SecurityEventSeverity"
]

