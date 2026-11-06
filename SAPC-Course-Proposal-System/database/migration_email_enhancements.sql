-- ==============================================================================
-- SAPC Course Proposal System - Database Migration
-- Phase 1 Email Enhancements:
-- 1. Decision Notification Tracking (reviewer_comments, last_decision_notified)
-- 2. Additional Recipients (proposal_recipients table)
-- 
-- Compatible with PostgreSQL 12+ and safe to run on existing production database.
-- Does NOT delete or drop existing tables or records.
-- ==============================================================================

-- 1. Add reviewer comments and decision notification tracking to proposals table
ALTER TABLE proposals 
ADD COLUMN IF NOT EXISTS reviewer_comments TEXT;

ALTER TABLE proposals 
ADD COLUMN IF NOT EXISTS last_decision_notified VARCHAR(50);

-- 2. Create proposal_recipients table for tracking CC copies
CREATE TABLE IF NOT EXISTS proposal_recipients (
    id SERIAL PRIMARY KEY,
    proposal_id VARCHAR(50) NOT NULL REFERENCES proposals(proposal_id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    delivery_status VARCHAR(50) NOT NULL DEFAULT 'Pending',
    error_message TEXT,
    sent_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 3. Create indexes for performance on proposal_recipients
CREATE INDEX IF NOT EXISTS idx_proposal_recipients_proposal_id ON proposal_recipients(proposal_id);
CREATE INDEX IF NOT EXISTS idx_proposal_recipients_email ON proposal_recipients(email);

-- Verification Query (optional):
-- SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'proposals' AND column_name IN ('reviewer_comments', 'last_decision_notified');
-- SELECT table_name FROM information_schema.tables WHERE table_name = 'proposal_recipients';
