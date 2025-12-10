#!/usr/bin/env python3
"""
GDPR Compliance Models

SECURITY & COMPLIANCE: Models for GDPR compliance including data collection tracking,
privacy policies, and Subject Access Requests (SAR).
"""

from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from .base import Base, TimestampMixin


class DataCollectionPurpose(enum.Enum):
    """Purpose for data collection (GDPR Article 6)"""
    CONTRACT = "contract"  # Performance of a contract
    LEGAL_OBLIGATION = "legal_obligation"  # Legal obligation
    VITAL_INTERESTS = "vital_interests"  # Protection of vital interests
    PUBLIC_TASK = "public_task"  # Public task
    LEGITIMATE_INTERESTS = "legitimate_interests"  # Legitimate interests
    CONSENT = "consent"  # Consent


class SARStatus(enum.Enum):
    """Subject Access Request status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"
    EXPIRED = "expired"


class DataCollectionRecord(Base, TimestampMixin):
    """
    Records what data is collected and why (GDPR Article 13/14 requirement)
    """
    __tablename__ = "data_collection_records"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    
    data_category = Column(String(255), nullable=False)  # e.g., "customer_name", "email", "phone"
    data_type = Column(String(100), nullable=False)  # e.g., "personal_data", "sensitive_data", "technical_data"
    purpose = Column(String(50), nullable=False)  # DataCollectionPurpose enum value
    legal_basis = Column(Text, nullable=False)  # Description of legal basis
    retention_period_days = Column(String(50), nullable=True)  # How long data is kept
    shared_with = Column(Text, nullable=True)  # Who data is shared with
    source = Column(String(255), nullable=True)  # Where data comes from
    
    # Relationships
    tenant = relationship("Tenant", backref="data_collection_records")
    
    def __repr__(self):
        return f"<DataCollectionRecord category={self.data_category} purpose={self.purpose}>"


class PrivacyPolicy(Base, TimestampMixin):
    """
    Stores generated or uploaded privacy policies
    """
    __tablename__ = "privacy_policies"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    
    version = Column(String(50), nullable=False)  # e.g., "1.0", "2.1"
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)  # Full policy text
    is_active = Column(Boolean, default=True, nullable=False)
    generated_by_ai = Column(Boolean, default=False, nullable=False)
    generation_prompt = Column(Text, nullable=True)  # Prompt used if AI-generated
    
    effective_date = Column(DateTime(timezone=True), nullable=False, default=func.now())
    last_reviewed = Column(DateTime(timezone=True), nullable=True)
    next_review_date = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    tenant = relationship("Tenant", backref="privacy_policies")
    
    def __repr__(self):
        return f"<PrivacyPolicy version={self.version} tenant_id={self.tenant_id}>"


class SubjectAccessRequest(Base, TimestampMixin):
    """
    Subject Access Request (SAR) - GDPR Article 15
    """
    __tablename__ = "subject_access_requests"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    
    requestor_email = Column(String(255), nullable=False, index=True)
    requestor_name = Column(String(255), nullable=True)
    requestor_id = Column(String(36), nullable=True)  # If requestor is a user in the system
    
    status = Column(String(50), nullable=False, default=SARStatus.PENDING.value, index=True)
    requested_data_types = Column(JSON, nullable=True)  # Array of data types requested
    
    request_date = Column(DateTime(timezone=True), nullable=False, default=func.now())
    due_date = Column(DateTime(timezone=True), nullable=True)  # GDPR: 30 days from request
    completed_date = Column(DateTime(timezone=True), nullable=True)
    
    verification_token = Column(String(255), nullable=True, unique=True, index=True)  # For email verification
    verified = Column(Boolean, default=False, nullable=False)
    
    data_export_path = Column(String(500), nullable=True)  # Path to exported data file
    notes = Column(Text, nullable=True)  # Internal notes
    
    processed_by = Column(String(36), ForeignKey("users.id"), nullable=True)  # User who processed the request
    
    # Relationships
    tenant = relationship("Tenant", backref="subject_access_requests")
    processor = relationship("User", foreign_keys=[processed_by], backref="processed_sars")
    
    def __repr__(self):
        return f"<SubjectAccessRequest id={self.id} status={self.status.value if isinstance(self.status, enum.Enum) else self.status}>"

