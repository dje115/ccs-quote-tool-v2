#!/usr/bin/env python3
"""
SLA Compliance tracking models
"""

from sqlalchemy import Column, String, Boolean, Text, ForeignKey, DateTime, Integer, Numeric, Date, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from .base import Base, TimestampMixin


class SLAComplianceRecord(Base, TimestampMixin):
    """Tracks SLA compliance metrics for tickets and contracts"""
    __tablename__ = "sla_compliance_records"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    ticket_id = Column(String(36), ForeignKey("tickets.id", ondelete="CASCADE"), nullable=True, index=True)
    contract_id = Column(String(36), ForeignKey("support_contracts.id", ondelete="CASCADE"), nullable=True, index=True)
    sla_policy_id = Column(String(36), ForeignKey("sla_policies.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Metrics
    first_response_time_hours = Column(Numeric(10, 2), nullable=True)  # Actual time taken
    resolution_time_hours = Column(Numeric(10, 2), nullable=True)  # Actual time taken
    first_response_met = Column(Boolean, default=False, nullable=False)
    resolution_met = Column(Boolean, default=False, nullable=False)
    first_response_breached = Column(Boolean, default=False, nullable=False)
    resolution_breached = Column(Boolean, default=False, nullable=False)
    
    # Period tracking (for monthly/quarterly reports)
    period_start_date = Column(Date, nullable=False)
    period_end_date = Column(Date, nullable=False)
    
    # Relationships
    tenant = relationship("Tenant")
    ticket = relationship("Ticket")
    contract = relationship("SupportContract")
    sla_policy = relationship("SLAPolicy")
    
    def __repr__(self):
        return f"<SLAComplianceRecord {self.id} - {self.period_start_date} to {self.period_end_date}>"
    
    __table_args__ = (
        Index('idx_sla_compliance_tenant_period', 'tenant_id', 'period_start_date', 'period_end_date'),
        Index('idx_sla_compliance_ticket', 'ticket_id'),
        Index('idx_sla_compliance_contract', 'contract_id'),
        Index('idx_sla_compliance_policy', 'sla_policy_id'),
    )


class SLABreachAlert(Base, TimestampMixin):
    """Tracks SLA breach alerts and notifications"""
    __tablename__ = "sla_breach_alerts"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    ticket_id = Column(String(36), ForeignKey("tickets.id", ondelete="CASCADE"), nullable=True, index=True)
    contract_id = Column(String(36), ForeignKey("support_contracts.id", ondelete="CASCADE"), nullable=True, index=True)
    sla_policy_id = Column(String(36), ForeignKey("sla_policies.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Alert details
    breach_type = Column(String(50), nullable=False)  # 'first_response' or 'resolution'
    breach_percent = Column(Integer, nullable=False)  # How far over SLA (e.g., 105 = 5% over)
    alert_level = Column(String(20), nullable=False)  # 'warning' or 'critical'
    acknowledged = Column(Boolean, default=False, nullable=False, index=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    
    # Relationships
    tenant = relationship("Tenant")
    ticket = relationship("Ticket")
    contract = relationship("SupportContract")
    sla_policy = relationship("SLAPolicy")
    acknowledged_by_user = relationship("User", foreign_keys=[acknowledged_by])
    
    def __repr__(self):
        return f"<SLABreachAlert {self.breach_type} - {self.alert_level}>"
    
    __table_args__ = (
        Index('idx_sla_breach_tenant_unacknowledged', 'tenant_id', 'acknowledged', 'created_at'),
        Index('idx_sla_breach_ticket', 'ticket_id'),
        Index('idx_sla_breach_contract', 'contract_id'),
    )

