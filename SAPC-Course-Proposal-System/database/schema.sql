-- ==============================================================================
-- SAPC Course Proposal System - PostgreSQL Relational Database Schema
-- Indian Institute of Technology Gandhinagar
-- Senate Academic Programme Committee (SAPC) - ACAD-SAPC-01
-- ==============================================================================

-- Drop tables if they already exist (cascade to handle dependencies)
DROP TABLE IF EXISTS proposal_status_history CASCADE;
DROP TABLE IF EXISTS deadline_settings CASCADE;
DROP TABLE IF EXISTS proposals CASCADE;
DROP TABLE IF EXISTS admin_users CASCADE;

-- ------------------------------------------------------------------------------
-- 1. Proposals Table
-- Captures every single field from ACAD-SAPC-01 + Phase 1 tracking attributes
-- ------------------------------------------------------------------------------
CREATE TABLE proposals (
    id SERIAL PRIMARY KEY,
    proposal_id VARCHAR(50) UNIQUE NOT NULL,
    submission_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'Pending',
    -- Status constraints: 'Pending', 'Under Review', 'Approved', 'Rejected', 'Modification Required'
    
    -- Course Identification & Proposer Information
    course_title VARCHAR(255) NOT NULL,
    potential_instructors TEXT NOT NULL,
    proposer_name VARCHAR(255) NOT NULL,
    faculty_email VARCHAR(255) NOT NULL,
    
    -- Course Classification & Structure
    course_type VARCHAR(50) NOT NULL,
    course_type_other VARCHAR(100),
    course_level VARCHAR(20) NOT NULL,
    course_level_secondary VARCHAR(20),
    course_l_t_p_c VARCHAR(50) NOT NULL,
    lecture_hours NUMERIC(4, 1) DEFAULT 0,
    tutorial_hours NUMERIC(4, 1) DEFAULT 0,
    practical_hours NUMERIC(4, 1) DEFAULT 0,
    credits NUMERIC(4, 1) DEFAULT 0,
    course_duration VARCHAR(50) NOT NULL,
    expected_frequency VARCHAR(50) NOT NULL,
    expected_frequency_other VARCHAR(100),
    
    -- Elective Baskets & Curricular Attributes
    elective_basket_btech VARCHAR(50),
    discipline_elective_btech VARCHAR(50),
    discipline_basket_btech VARCHAR(255),
    minors TEXT,
    minor_basket_thematic_area VARCHAR(255),
    discipline_elective_msc VARCHAR(50),
    courses_discipline_mtech VARCHAR(50),
    mtech_sub_specialization VARCHAR(255),
    discipline_elective_mdes VARCHAR(50),
    
    -- Course Nature
    is_modification BOOLEAN NOT NULL DEFAULT FALSE,
    existing_course_code VARCHAR(50),
    
    -- Detailed Academic Syllabus Information
    prior_knowledge TEXT,
    course_contents TEXT NOT NULL,
    texts_and_references TEXT NOT NULL,
    learning_outcomes TEXT NOT NULL,
    overlap_courses TEXT,
    other_relevant_info TEXT,
    
    -- Generated PDF Storage Reference
    pdf_path VARCHAR(500),
    pdf_filename VARCHAR(255),
    
    -- Notification Tracking
    email_notification_status VARCHAR(50) NOT NULL DEFAULT 'Pending',
    -- Status values: 'Pending', 'Sent', 'Failed'
    email_error_log TEXT,
    
    -- Reviewer Comments & Decision Tracking
    reviewer_comments TEXT,
    last_decision_notified VARCHAR(50),
    
    -- Audit Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Indexes for frequent queries, search, and filtering
CREATE INDEX idx_proposals_proposal_id ON proposals(proposal_id);
CREATE INDEX idx_proposals_course_title ON proposals(course_title);
CREATE INDEX idx_proposals_proposer_name ON proposals(proposer_name);
CREATE INDEX idx_proposals_faculty_email ON proposals(faculty_email);
CREATE INDEX idx_proposals_status ON proposals(status);
CREATE INDEX idx_proposals_submission_date ON proposals(submission_date);
CREATE INDEX idx_proposals_course_type ON proposals(course_type);
CREATE INDEX idx_proposals_course_level ON proposals(course_level);
CREATE INDEX idx_proposals_is_modification ON proposals(is_modification);

-- ------------------------------------------------------------------------------
-- 2. Deadline Settings Table
-- Configurable proposal submission window managed by Academic Office Admin
-- ------------------------------------------------------------------------------
CREATE TABLE deadline_settings (
    id SERIAL PRIMARY KEY,
    submission_start TIMESTAMP WITH TIME ZONE NOT NULL,
    submission_deadline TIMESTAMP WITH TIME ZONE NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    announcement_message TEXT,
    updated_by VARCHAR(100) DEFAULT 'Academic Office Admin',
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- ------------------------------------------------------------------------------
-- 3. Admin Users Table
-- Supports Academic Office administrative authentication
-- ------------------------------------------------------------------------------
CREATE TABLE admin_users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'Academic Office',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- ------------------------------------------------------------------------------
-- 4. Proposal Status History Table
-- Audit trail tracking review status changes made by Academic Office
-- ------------------------------------------------------------------------------
CREATE TABLE proposal_status_history (
    id SERIAL PRIMARY KEY,
    proposal_id VARCHAR(50) NOT NULL REFERENCES proposals(proposal_id) ON DELETE CASCADE,
    previous_status VARCHAR(50),
    new_status VARCHAR(50) NOT NULL,
    remarks TEXT,
    changed_by VARCHAR(100) NOT NULL,
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX idx_status_history_proposal_id ON proposal_status_history(proposal_id);

-- ------------------------------------------------------------------------------
-- 5. Proposal Additional Recipients Table (CC)
-- Tracks additional faculty members/colleagues who receive a proposal copy
-- ------------------------------------------------------------------------------
CREATE TABLE proposal_recipients (
    id SERIAL PRIMARY KEY,
    proposal_id VARCHAR(50) NOT NULL REFERENCES proposals(proposal_id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    delivery_status VARCHAR(50) NOT NULL DEFAULT 'Pending',
    error_message TEXT,
    sent_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX idx_proposal_recipients_proposal_id ON proposal_recipients(proposal_id);
CREATE INDEX idx_proposal_recipients_email ON proposal_recipients(email);
