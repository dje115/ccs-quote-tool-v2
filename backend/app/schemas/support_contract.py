#!/usr/bin/env python3
"""
Pydantic schemas for Support Contracts API
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from enum import Enum


class ContractTypeEnum(str, Enum):
    managed_services = "managed_services"
    maintenance = "maintenance"
    saas_subscription = "saas_subscription"
    support_hours = "support_hours"
    warranty = "warranty"
    consulting = "consulting"


class ContractStatusEnum(str, Enum):
    draft = "draft"
    active = "active"
    pending_renewal = "pending_renewal"
    expired = "expired"
    cancelled = "cancelled"
    suspended = "suspended"


class RenewalFrequencyEnum(str, Enum):
    monthly = "monthly"
    quarterly = "quarterly"
    semi_annual = "semi_annual"
    annual = "annual"
    biennial = "biennial"
    triennial = "triennial"
    one_time = "one_time"


# Request schemas
class SupportContractCreate(BaseModel):
    customer_id: str
    contract_name: str
    description: Optional[str] = None
    contract_type: ContractTypeEnum
    start_date: date
    end_date: Optional[date] = None
    renewal_frequency: Optional[RenewalFrequencyEnum] = None
    auto_renew: bool = True
    monthly_value: Optional[float] = None
    annual_value: Optional[float] = None
    setup_fee: float = 0.0
    currency: str = "GBP"
    terms: Optional[str] = None
    sla_level: Optional[str] = None
    included_services: Optional[List[str]] = None
    excluded_services: Optional[List[str]] = None
    support_hours_included: Optional[int] = None
    renewal_notice_days: int = 90
    cancellation_notice_days: int = 30
    quote_id: Optional[str] = None
    opportunity_id: Optional[str] = None
    notes: Optional[str] = None
    contract_metadata: Optional[Dict[str, Any]] = None


class SupportContractUpdate(BaseModel):
    contract_name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ContractStatusEnum] = None
    end_date: Optional[date] = None
    renewal_date: Optional[date] = None
    renewal_frequency: Optional[RenewalFrequencyEnum] = None
    auto_renew: Optional[bool] = None
    monthly_value: Optional[float] = None
    annual_value: Optional[float] = None
    setup_fee: Optional[float] = None
    currency: Optional[str] = None
    terms: Optional[str] = None
    sla_level: Optional[str] = None
    included_services: Optional[List[str]] = None
    excluded_services: Optional[List[str]] = None
    support_hours_included: Optional[int] = None
    support_hours_used: Optional[int] = None
    renewal_notice_days: Optional[int] = None
    cancellation_notice_days: Optional[int] = None
    notes: Optional[str] = None
    contract_metadata: Optional[Dict[str, Any]] = None


# Response schemas
class SupportContractResponse(BaseModel):
    id: str
    tenant_id: str
    customer_id: str
    contract_number: str
    contract_name: str
    description: Optional[str]
    contract_type: str
    status: str
    start_date: date
    end_date: Optional[date]
    renewal_date: Optional[date]
    renewal_frequency: Optional[str]
    auto_renew: bool
    monthly_value: Optional[float]
    annual_value: Optional[float]
    setup_fee: float
    currency: str
    terms: Optional[str]
    sla_level: Optional[str]
    included_services: Optional[List[str]]
    excluded_services: Optional[List[str]]
    support_hours_included: Optional[int]
    support_hours_used: int
    renewal_notice_days: int
    cancellation_notice_days: int
    cancellation_reason: Optional[str]
    cancelled_at: Optional[datetime]
    cancelled_by: Optional[str]
    quote_id: Optional[str]
    opportunity_id: Optional[str]
    notes: Optional[str]
    contract_metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    
    # Computed fields
    days_until_renewal: Optional[int] = None
    is_expiring_soon: bool = False
    total_value: Optional[float] = None
    
    class Config:
        from_attributes = True


class ContractRenewalCreate(BaseModel):
    renewal_date: date
    new_end_date: Optional[date] = None
    new_monthly_value: Optional[float] = None
    new_annual_value: Optional[float] = None
    renewal_type: Optional[str] = None
    notes: Optional[str] = None


class ContractRenewalResponse(BaseModel):
    id: str
    contract_id: str
    tenant_id: str
    renewal_date: date
    previous_end_date: Optional[date]
    new_end_date: Optional[date]
    previous_monthly_value: Optional[float]
    new_monthly_value: Optional[float]
    previous_annual_value: Optional[float]
    new_annual_value: Optional[float]
    status: str
    renewal_type: Optional[str]
    reminder_sent_at: Optional[datetime]
    reminder_sent_to: Optional[str]
    approved_at: Optional[datetime]
    approved_by: Optional[str]
    completed_at: Optional[datetime]
    declined_at: Optional[datetime]
    declined_reason: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ContractTemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    contract_type: ContractTypeEnum
    terms_template: Optional[str] = None
    included_services_template: Optional[List[str]] = None
    sla_level: Optional[str] = None
    default_renewal_frequency: Optional[RenewalFrequencyEnum] = None
    default_renewal_notice_days: int = 90
    default_cancellation_notice_days: int = 30
    default_monthly_value: Optional[float] = None
    default_annual_value: Optional[float] = None


class ContractTemplateResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    description: Optional[str]
    contract_type: str
    terms_template: Optional[str]
    included_services_template: Optional[List[str]]
    sla_level: Optional[str]
    default_renewal_frequency: Optional[str]
    default_renewal_notice_days: int
    default_cancellation_notice_days: int
    default_monthly_value: Optional[float]
    default_annual_value: Optional[float]
    is_active: bool
    is_system: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

