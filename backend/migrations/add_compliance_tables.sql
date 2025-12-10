-- Migration: Add compliance tables (GDPR and ISO)
-- Purpose: Support GDPR compliance, ISO 27001, and ISO 9001 management

-- GDPR Tables
CREATE TABLE IF NOT EXISTS data_collection_records (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    data_category VARCHAR(255) NOT NULL,
    data_type VARCHAR(100) NOT NULL,
    purpose VARCHAR(50) NOT NULL,
    legal_basis TEXT NOT NULL,
    retention_period_days VARCHAR(50),
    shared_with TEXT,
    source VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_data_collection_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS privacy_policies (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    version VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    generated_by_ai BOOLEAN NOT NULL DEFAULT FALSE,
    generation_prompt TEXT,
    effective_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_reviewed TIMESTAMP WITH TIME ZONE,
    next_review_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_privacy_policy_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS subject_access_requests (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    requestor_email VARCHAR(255) NOT NULL,
    requestor_name VARCHAR(255),
    requestor_id VARCHAR(36),
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    requested_data_types JSONB,
    request_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    due_date TIMESTAMP WITH TIME ZONE,
    completed_date TIMESTAMP WITH TIME ZONE,
    verification_token VARCHAR(255) UNIQUE,
    verified BOOLEAN NOT NULL DEFAULT FALSE,
    data_export_path VARCHAR(500),
    notes TEXT,
    processed_by VARCHAR(36),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_sar_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
    CONSTRAINT fk_sar_user FOREIGN KEY (requestor_id) REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT fk_sar_processor FOREIGN KEY (processed_by) REFERENCES users(id) ON DELETE SET NULL
);

-- ISO Tables
CREATE TABLE IF NOT EXISTS iso_controls (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    standard VARCHAR(50) NOT NULL,
    control_id VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_iso_control_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS iso_assessments (
    id VARCHAR(36) PRIMARY KEY,
    control_id VARCHAR(36) NOT NULL,
    tenant_id VARCHAR(36) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'not_started',
    compliance_percentage INTEGER,
    assessment_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    assessed_by VARCHAR(36),
    evidence TEXT,
    gaps TEXT,
    remediation_plan TEXT,
    notes TEXT,
    attachments JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_iso_assessment_control FOREIGN KEY (control_id) REFERENCES iso_controls(id) ON DELETE CASCADE,
    CONSTRAINT fk_iso_assessment_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
    CONSTRAINT fk_iso_assessment_assessor FOREIGN KEY (assessed_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS iso_audits (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    standard VARCHAR(50) NOT NULL,
    audit_type VARCHAR(50) NOT NULL,
    audit_date TIMESTAMP WITH TIME ZONE NOT NULL,
    auditor_name VARCHAR(255),
    auditor_organization VARCHAR(255),
    scope TEXT NOT NULL,
    findings TEXT,
    non_conformities TEXT,
    recommendations TEXT,
    result VARCHAR(50),
    certificate_number VARCHAR(255),
    certificate_expiry TIMESTAMP WITH TIME ZONE,
    report_path VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_iso_audit_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_data_collection_tenant ON data_collection_records(tenant_id);
CREATE INDEX IF NOT EXISTS idx_privacy_policy_tenant ON privacy_policies(tenant_id);
CREATE INDEX IF NOT EXISTS idx_privacy_policy_active ON privacy_policies(is_active);
CREATE INDEX IF NOT EXISTS idx_sar_tenant ON subject_access_requests(tenant_id);
CREATE INDEX IF NOT EXISTS idx_sar_email ON subject_access_requests(requestor_email);
CREATE INDEX IF NOT EXISTS idx_sar_status ON subject_access_requests(status);
CREATE INDEX IF NOT EXISTS idx_sar_token ON subject_access_requests(verification_token);
CREATE INDEX IF NOT EXISTS idx_iso_control_tenant ON iso_controls(tenant_id);
CREATE INDEX IF NOT EXISTS idx_iso_control_standard ON iso_controls(standard);
CREATE INDEX IF NOT EXISTS idx_iso_assessment_control ON iso_assessments(control_id);
CREATE INDEX IF NOT EXISTS idx_iso_assessment_tenant ON iso_assessments(tenant_id);
CREATE INDEX IF NOT EXISTS idx_iso_assessment_status ON iso_assessments(status);
CREATE INDEX IF NOT EXISTS idx_iso_audit_tenant ON iso_audits(tenant_id);
CREATE INDEX IF NOT EXISTS idx_iso_audit_standard ON iso_audits(standard);

COMMENT ON TABLE data_collection_records IS 'Records what personal data is collected and why (GDPR Article 13/14)';
COMMENT ON TABLE privacy_policies IS 'Stores generated or uploaded privacy policies';
COMMENT ON TABLE subject_access_requests IS 'Subject Access Requests (SAR) - GDPR Article 15';
COMMENT ON TABLE iso_controls IS 'ISO control/requirement (ISO 27001 controls, ISO 9001 requirements)';
COMMENT ON TABLE iso_assessments IS 'Assessment of compliance with a specific ISO control';
COMMENT ON TABLE iso_audits IS 'ISO audit records (internal or external audits)';

