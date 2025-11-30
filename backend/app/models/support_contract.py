#!/usr/bin/env python3
"""
Support Contracts models for managing service contracts, maintenance agreements, and SaaS subscriptions
"""

from sqlalchemy import Column, String, Boolean, Text, JSON, ForeignKey, Integer, Enum, DateTime, Numeric, Date, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
import uuid
from .base import Base, TimestampMixin


class ContractType(enum.Enum):
    """Type of support contract"""
    MANAGED_SERVICES = "managed_services"  # Ongoing managed IT services
    MAINTENANCE = "maintenance"  # Hardware/software maintenance
    SAAS_SUBSCRIPTION = "saas_subscription"  # Software as a Service subscription
    SUPPORT_HOURS = "support_hours"  # Pre-paid support hours
    WARRANTY = "warranty"  # Warranty coverage
    CONSULTING = "consulting"  # Consulting retainer


class ContractStatus(enum.Enum):
    """Status of the contract"""
    DRAFT = "draft"  # Contract being drafted
    ACTIVE = "active"  # Contract is active and in effect
    PENDING_RENEWAL = "pending_renewal"  # Contract is up for renewal
    EXPIRED = "expired"  # Contract has expired
    CANCELLED = "cancelled"  # Contract was cancelled
    SUSPENDED = "suspended"  # Contract temporarily suspended


class RenewalFrequency(enum.Enum):
    """How often the contract renews"""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    SEMI_ANNUAL = "semi_annual"  # Every 6 months
    ANNUAL = "annual"
    BIENNIAL = "biennial"  # Every 2 years
    TRIENNIAL = "triennial"  # Every 3 years
    ONE_TIME = "one_time"  # No renewal


class SupportContract(Base, TimestampMixin):
    """
    Support Contract model for managing service contracts, maintenance, and subscriptions
    """
    __tablename__ = "support_contracts"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False, index=True)
    
    # Contract identification
    contract_number = Column(String(100), unique=True, nullable=False, index=True)
    contract_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Contract type and status
    contract_type = Column(Enum(ContractType), nullable=False, index=True)
    status = Column(Enum(ContractStatus), default=ContractStatus.DRAFT, nullable=False, index=True)
    
    # Dates
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=True, index=True)  # Null for ongoing contracts
    renewal_date = Column(Date, nullable=True, index=True)  # Next renewal date
    renewal_frequency = Column(Enum(RenewalFrequency), nullable=True)
    auto_renew = Column(Boolean, default=True, nullable=False)
    
    # Financials
    monthly_value = Column(Numeric(12, 2), nullable=True)  # Monthly recurring value
    annual_value = Column(Numeric(12, 2), nullable=True)  # Annual value
    setup_fee = Column(Numeric(12, 2), default=0, nullable=False)
    currency = Column(String(3), default="GBP", nullable=False)
    
    # Contract details
    terms = Column(Text, nullable=True)  # Contract terms and conditions
    sla_level = Column(String(50), nullable=True)  # Service Level Agreement (e.g., "24/7", "Business Hours", "Next Business Day")
    sla_policy_id = Column(String(36), ForeignKey("sla_policies.id"), nullable=True, index=True)  # Link to SLA policy
    included_services = Column(JSON, nullable=True)  # List of services included
    excluded_services = Column(JSON, nullable=True)  # List of services excluded
    support_hours_included = Column(Integer, nullable=True)  # Pre-paid support hours
    support_hours_used = Column(Integer, default=0, nullable=False)
    
    # Renewal and cancellation
    renewal_notice_days = Column(Integer, default=90, nullable=False)  # Days before renewal to send notice
    cancellation_notice_days = Column(Integer, default=30, nullable=False)  # Days notice required for cancellation
    cancellation_reason = Column(Text, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    cancelled_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    
    # Related quote/opportunity
    quote_id = Column(String(36), ForeignKey("quotes.id"), nullable=True, index=True)
    opportunity_id = Column(String(36), nullable=True)  # Related sales opportunity
    
    # Notes and metadata
    notes = Column(Text, nullable=True)
    contract_metadata = Column(JSON, nullable=True)  # Additional contract-specific data (renamed from 'metadata' to avoid SQLAlchemy conflict)
    
    # Relationships
    tenant = relationship("Tenant", backref="support_contracts")
    customer = relationship("Customer", backref="support_contracts")
    quote = relationship("Quote", backref="support_contracts")
    cancelled_by_user = relationship("User", foreign_keys=[cancelled_by], backref="cancelled_contracts")
    sla_policy = relationship("SLAPolicy", foreign_keys=[sla_policy_id])
    
    def __repr__(self):
        return f"<SupportContract {self.contract_number} ({self.contract_type.value})>"
    
    __table_args__ = (
        Index('idx_contract_tenant_customer', 'tenant_id', 'customer_id'),
        Index('idx_contract_renewal_date', 'renewal_date'),
        Index('idx_contract_status_type', 'status', 'contract_type'),
    )


class ContractRenewal(Base, TimestampMixin):
    """
    Tracks contract renewal history and upcoming renewals
    """
    __tablename__ = "contract_renewals"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    contract_id = Column(String(36), ForeignKey("support_contracts.id"), nullable=False, index=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Renewal details
    renewal_date = Column(Date, nullable=False, index=True)
    previous_end_date = Column(Date, nullable=True)
    new_end_date = Column(Date, nullable=True)
    
    # Financial changes
    previous_monthly_value = Column(Numeric(12, 2), nullable=True)
    new_monthly_value = Column(Numeric(12, 2), nullable=True)
    previous_annual_value = Column(Numeric(12, 2), nullable=True)
    new_annual_value = Column(Numeric(12, 2), nullable=True)
    
    # Status
    status = Column(String(50), default="pending", nullable=False, index=True)  # pending, approved, completed, declined
    renewal_type = Column(String(50), nullable=True)  # auto, manual, upgrade, downgrade
    
    # Actions
    reminder_sent_at = Column(DateTime, nullable=True)
    reminder_sent_to = Column(String(36), ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    approved_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    completed_at = Column(DateTime, nullable=True)
    declined_at = Column(DateTime, nullable=True)
    declined_reason = Column(Text, nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Relationships
    contract = relationship("SupportContract", backref="renewals")
    tenant = relationship("Tenant", backref="contract_renewals")
    reminder_user = relationship("User", foreign_keys=[reminder_sent_to], backref="renewal_reminders_sent")
    approver = relationship("User", foreign_keys=[approved_by], backref="renewals_approved")
    
    def __repr__(self):
        return f"<ContractRenewal {self.id} for contract {self.contract_id}>"
    
    __table_args__ = (
        Index('idx_renewal_contract_date', 'contract_id', 'renewal_date'),
        Index('idx_renewal_status', 'status'),
    )


class ContractTemplate(Base, TimestampMixin):
    """
    Reusable contract templates for different contract types
    """
    __tablename__ = "contract_templates"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Template details
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    contract_type = Column(Enum(ContractType), nullable=False, index=True)
    
    # Template content
    terms_template = Column(Text, nullable=True)  # Template for contract terms
    included_services_template = Column(JSON, nullable=True)  # Template for included services
    sla_level = Column(String(50), nullable=True)
    
    # Default values
    default_renewal_frequency = Column(Enum(RenewalFrequency), nullable=True)
    default_renewal_notice_days = Column(Integer, default=90, nullable=False)
    default_cancellation_notice_days = Column(Integer, default=30, nullable=False)
    default_monthly_value = Column(Numeric(12, 2), nullable=True)
    default_annual_value = Column(Numeric(12, 2), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_system = Column(Boolean, default=False, nullable=False)  # System template vs tenant-specific
    
    # Relationships
    tenant = relationship("Tenant", backref="contract_templates")
    
    def __repr__(self):
        return f"<ContractTemplate {self.name} ({self.contract_type.value})>"

