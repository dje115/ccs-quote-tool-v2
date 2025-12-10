#!/usr/bin/env python3
"""
ISO 27001 and ISO 9001 Compliance Models

COMPLIANCE: Models for ISO 27001 (Information Security) and ISO 9001 (Quality Management) compliance.
"""

from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Boolean, Integer, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from .base import Base, TimestampMixin


class ISOStandard(enum.Enum):
    """ISO standard types"""
    ISO_27001 = "iso_27001"  # Information Security Management
    ISO_9001 = "iso_9001"    # Quality Management


class ComplianceStatus(enum.Enum):
    """Compliance status"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    UNDER_REVIEW = "under_review"


class ISOControl(Base, TimestampMixin):
    """
    ISO control/requirement (e.g., ISO 27001 controls, ISO 9001 requirements)
    """
    __tablename__ = "iso_controls"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    
    standard = Column(String(50), nullable=False, index=True)  # ISOStandard enum value
    control_id = Column(String(50), nullable=False)  # e.g., "A.5.1.1" for ISO 27001
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=True)  # e.g., "Access Control", "Risk Management"
    
    # Relationships
    tenant = relationship("Tenant", backref="iso_controls")
    assessments = relationship("ISOAssessment", back_populates="control", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ISOControl standard={self.standard} control_id={self.control_id}>"


class ISOAssessment(Base, TimestampMixin):
    """
    Assessment of compliance with a specific ISO control
    """
    __tablename__ = "iso_assessments"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    control_id = Column(String(36), ForeignKey("iso_controls.id"), nullable=False, index=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    
    status = Column(String(50), nullable=False, default=ComplianceStatus.NOT_STARTED.value, index=True)
    compliance_percentage = Column(Integer, nullable=True)  # 0-100
    
    assessment_date = Column(DateTime(timezone=True), nullable=False, default=func.now())
    assessed_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    
    evidence = Column(Text, nullable=True)  # Evidence of compliance
    gaps = Column(Text, nullable=True)  # Identified gaps
    remediation_plan = Column(Text, nullable=True)  # Plan to address gaps
    notes = Column(Text, nullable=True)
    
    attachments = Column(JSON, nullable=True)  # Array of file paths/URLs
    
    # Relationships
    control = relationship("ISOControl", back_populates="assessments")
    tenant = relationship("Tenant", backref="iso_assessments")
    assessor = relationship("User", foreign_keys=[assessed_by], backref="iso_assessments")
    
    def __repr__(self):
        return f"<ISOAssessment control_id={self.control_id} status={self.status}>"


class ISOAudit(Base, TimestampMixin):
    """
    ISO audit records (internal or external audits)
    """
    __tablename__ = "iso_audits"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    
    standard = Column(String(50), nullable=False, index=True)  # ISOStandard enum value
    audit_type = Column(String(50), nullable=False)  # "internal", "external", "surveillance"
    
    audit_date = Column(DateTime(timezone=True), nullable=False)
    auditor_name = Column(String(255), nullable=True)
    auditor_organization = Column(String(255), nullable=True)
    
    scope = Column(Text, nullable=False)  # Scope of audit
    findings = Column(Text, nullable=True)  # Audit findings
    non_conformities = Column(Text, nullable=True)  # Non-conformities identified
    recommendations = Column(Text, nullable=True)
    
    result = Column(String(50), nullable=True)  # "passed", "failed", "conditional"
    certificate_number = Column(String(255), nullable=True)
    certificate_expiry = Column(DateTime(timezone=True), nullable=True)
    
    report_path = Column(String(500), nullable=True)  # Path to audit report
    
    # Relationships
    tenant = relationship("Tenant", backref="iso_audits")
    
    def __repr__(self):
        return f"<ISOAudit standard={self.standard} audit_type={self.audit_type} audit_date={self.audit_date}>"

