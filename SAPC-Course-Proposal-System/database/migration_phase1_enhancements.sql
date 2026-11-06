-- ==============================================================================
-- SAPC Course Proposal System - Database Migration
-- Phase 1 Enhancements:
-- 1. Professor Edit Authorization (edit_token)
-- 2. Minor Reason (minor_reason)
-- 3. SAPC Official Record & Approval Date (sapc_number, approval_date)
-- 4. Custom Form Fields JSON storage (custom_fields_data)
-- 5. Security Department Notification Tracking (security_email_status, security_email_error)
-- 6. Proposal Edit History Table (proposal_edit_history)
-- 7. Form Field Options Table (form_field_options)
-- 8. Custom Form Fields Configuration Table (custom_form_fields)
--
-- Compatible with PostgreSQL 12+ and safe to run on existing production database.
-- Does NOT delete or drop existing tables or records.
-- ==============================================================================

-- 1. Alter proposals table
ALTER TABLE proposals 
ADD COLUMN IF NOT EXISTS edit_token VARCHAR(100);

ALTER TABLE proposals 
ADD COLUMN IF NOT EXISTS minor_reason TEXT;

ALTER TABLE proposals 
ADD COLUMN IF NOT EXISTS sapc_number VARCHAR(100);

ALTER TABLE proposals 
ADD COLUMN IF NOT EXISTS approval_date TIMESTAMP WITH TIME ZONE;

ALTER TABLE proposals 
ADD COLUMN IF NOT EXISTS custom_fields_data TEXT;

ALTER TABLE proposals 
ADD COLUMN IF NOT EXISTS security_email_status VARCHAR(50) DEFAULT 'Pending';

ALTER TABLE proposals 
ADD COLUMN IF NOT EXISTS security_email_error TEXT;

CREATE INDEX IF NOT EXISTS idx_proposals_edit_token ON proposals(edit_token);
CREATE INDEX IF NOT EXISTS idx_proposals_sapc_number ON proposals(sapc_number);

-- 2. Create proposal_edit_history table
CREATE TABLE IF NOT EXISTS proposal_edit_history (
    id SERIAL PRIMARY KEY,
    proposal_id VARCHAR(50) NOT NULL REFERENCES proposals(proposal_id) ON DELETE CASCADE,
    edited_by VARCHAR(255) NOT NULL,
    edited_by_role VARCHAR(50) NOT NULL DEFAULT 'Professor',
    changes_summary TEXT,
    changes_json TEXT,
    edited_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_edit_history_proposal_id ON proposal_edit_history(proposal_id);

-- 3. Create form_field_options table
CREATE TABLE IF NOT EXISTS form_field_options (
    id SERIAL PRIMARY KEY,
    category VARCHAR(50) NOT NULL,
    value VARCHAR(100) NOT NULL,
    label VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    display_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_form_field_options_category ON form_field_options(category);

-- 4. Create custom_form_fields table
CREATE TABLE IF NOT EXISTS custom_form_fields (
    id SERIAL PRIMARY KEY,
    field_name VARCHAR(100) UNIQUE NOT NULL,
    field_label VARCHAR(255) NOT NULL,
    field_type VARCHAR(50) NOT NULL DEFAULT 'text',
    options_json TEXT,
    is_required BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    display_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
