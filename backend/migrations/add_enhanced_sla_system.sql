-- Enhanced SLA System Migration
-- Adds comprehensive SLA tracking, policies, and reporting

-- Enhance SLA Policies table
ALTER TABLE sla_policies 
ADD COLUMN IF NOT EXISTS sla_level VARCHAR(50),
ADD COLUMN IF NOT EXISTS first_response_hours_urgent INTEGER,
ADD COLUMN IF NOT EXISTS first_response_hours_high INTEGER,
ADD COLUMN IF NOT EXISTS first_response_hours_medium INTEGER,
ADD COLUMN IF NOT EXISTS first_response_hours_low INTEGER,
ADD COLUMN IF NOT EXISTS resolution_hours_urgent INTEGER,
ADD COLUMN IF NOT EXISTS resolution_hours_high INTEGER,
ADD COLUMN IF NOT EXISTS resolution_hours_medium INTEGER,
ADD COLUMN IF NOT EXISTS resolution_hours_low INTEGER,
ADD COLUMN IF NOT EXISTS uptime_target INTEGER,
ADD COLUMN IF NOT EXISTS availability_hours VARCHAR(50),
ADD COLUMN IF NOT EXISTS business_hours_start VARCHAR(10),
ADD COLUMN IF NOT EXISTS business_hours_end VARCHAR(10),
ADD COLUMN IF NOT EXISTS business_days JSONB,
ADD COLUMN IF NOT EXISTS timezone VARCHAR(50) DEFAULT 'Europe/London' NOT NULL,
ADD COLUMN IF NOT EXISTS escalation_warning_percent INTEGER DEFAULT 80 NOT NULL,
ADD COLUMN IF NOT EXISTS escalation_critical_percent INTEGER DEFAULT 95 NOT NULL,
ADD COLUMN IF NOT EXISTS auto_escalate_on_breach BOOLEAN DEFAULT TRUE NOT NULL,
ADD COLUMN IF NOT EXISTS contract_type VARCHAR(50),
ADD COLUMN IF NOT EXISTS is_default BOOLEAN DEFAULT FALSE NOT NULL;

-- Add indexes for SLA policies
CREATE INDEX IF NOT EXISTS idx_sla_tenant_active ON sla_policies(tenant_id, is_active);
CREATE INDEX IF NOT EXISTS idx_sla_default ON sla_policies(tenant_id, is_default);

-- Link SLA policies to support contracts
ALTER TABLE support_contracts
ADD COLUMN IF NOT EXISTS sla_policy_id VARCHAR(36) REFERENCES sla_policies(id);

CREATE INDEX IF NOT EXISTS idx_contract_sla_policy ON support_contracts(sla_policy_id);

-- Enhance tickets table with SLA tracking
ALTER TABLE tickets
ADD COLUMN IF NOT EXISTS sla_policy_id VARCHAR(36) REFERENCES sla_policies(id),
ADD COLUMN IF NOT EXISTS sla_first_response_hours INTEGER,
ADD COLUMN IF NOT EXISTS sla_first_response_breached BOOLEAN DEFAULT FALSE NOT NULL,
ADD COLUMN IF NOT EXISTS sla_resolution_breached BOOLEAN DEFAULT FALSE NOT NULL,
ADD COLUMN IF NOT EXISTS sla_first_response_breached_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS sla_resolution_breached_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS sla_first_response_met_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS sla_resolution_met_at TIMESTAMP WITH TIME ZONE;

CREATE INDEX IF NOT EXISTS idx_ticket_sla_policy ON tickets(sla_policy_id);
CREATE INDEX IF NOT EXISTS idx_ticket_sla_breached ON tickets(tenant_id, sla_resolution_breached, status);

-- Create SLA compliance tracking table
CREATE TABLE IF NOT EXISTS sla_compliance_records (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    ticket_id VARCHAR(36) REFERENCES tickets(id) ON DELETE CASCADE,
    contract_id VARCHAR(36) REFERENCES support_contracts(id) ON DELETE CASCADE,
    sla_policy_id VARCHAR(36) NOT NULL REFERENCES sla_policies(id) ON DELETE CASCADE,
    
    -- Metrics
    first_response_time_hours DECIMAL(10, 2),
    resolution_time_hours DECIMAL(10, 2),
    first_response_met BOOLEAN DEFAULT FALSE NOT NULL,
    resolution_met BOOLEAN DEFAULT FALSE NOT NULL,
    first_response_breached BOOLEAN DEFAULT FALSE NOT NULL,
    resolution_breached BOOLEAN DEFAULT FALSE NOT NULL,
    
    -- Timestamps
    period_start_date DATE NOT NULL,
    period_end_date DATE NOT NULL,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sla_compliance_tenant_period ON sla_compliance_records(tenant_id, period_start_date, period_end_date);
CREATE INDEX IF NOT EXISTS idx_sla_compliance_ticket ON sla_compliance_records(ticket_id);
CREATE INDEX IF NOT EXISTS idx_sla_compliance_contract ON sla_compliance_records(contract_id);
CREATE INDEX IF NOT EXISTS idx_sla_compliance_policy ON sla_compliance_records(sla_policy_id);

-- Create SLA breach alerts table
CREATE TABLE IF NOT EXISTS sla_breach_alerts (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    ticket_id VARCHAR(36) REFERENCES tickets(id) ON DELETE CASCADE,
    contract_id VARCHAR(36) REFERENCES support_contracts(id) ON DELETE CASCADE,
    sla_policy_id VARCHAR(36) NOT NULL REFERENCES sla_policies(id) ON DELETE CASCADE,
    
    -- Alert details
    breach_type VARCHAR(50) NOT NULL,  -- 'first_response' or 'resolution'
    breach_percent INTEGER NOT NULL,  -- How far over SLA (e.g., 105 = 5% over)
    alert_level VARCHAR(20) NOT NULL,  -- 'warning' or 'critical'
    acknowledged BOOLEAN DEFAULT FALSE NOT NULL,
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    acknowledged_by VARCHAR(36) REFERENCES users(id),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sla_breach_tenant_unacknowledged ON sla_breach_alerts(tenant_id, acknowledged, created_at);
CREATE INDEX IF NOT EXISTS idx_sla_breach_ticket ON sla_breach_alerts(ticket_id);
CREATE INDEX IF NOT EXISTS idx_sla_breach_contract ON sla_breach_alerts(contract_id);

