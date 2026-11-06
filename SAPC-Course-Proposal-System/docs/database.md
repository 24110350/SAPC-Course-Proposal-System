# SAPC Course Proposal System — Database Architecture & Schema Specification

**Senate Academic Programme Committee (SAPC) — Project 13**  
**Indian Institute of Technology Gandhinagar**

---

## 1. Entity-Relationship Diagram

```mermaid
erDiagram
    proposals ||--o{ proposal_status_history : "tracks review changes"
    admin_users ||--o{ proposal_status_history : "records admin action"
    admin_users ||--o{ deadline_settings : "configures"

    proposals {
        serial id PK
        varchar proposal_id UK "SAPC-YYYY-XXXX"
        timestamptz submission_date "Default: NOW()"
        varchar status "Pending, Under Review, Approved, Rejected, Modification Required"
        varchar course_title "Title of the course"
        text potential_instructors "Instructors"
        varchar proposer_name "Proposer faculty"
        varchar faculty_email "Recipient notification email"
        varchar course_type "Discipline code: CS, EE, HS, etc."
        varchar course_type_other "Specified if Others"
        varchar course_level "1 to 6 (UG: 1-5, PG: 6)"
        varchar course_level_secondary "Optional dual level"
        varchar course_l_t_p_c "e.g. 3-0-2-4"
        numeric lecture_hours "L"
        numeric tutorial_hours "T"
        numeric practical_hours "P"
        numeric credits "C"
        varchar course_duration "1 Quad to 4 Quads"
        varchar expected_frequency "Each Semester, Each Year, etc."
        varchar elective_basket_btech "BS, HS, Mathematics, Science"
        varchar discipline_elective_btech "Discipline code"
        varchar discipline_basket_btech "Basket name"
        text minors "Comma-separated minor codes"
        varchar minor_basket_thematic_area "Thematic area"
        varchar discipline_elective_msc "MSc elective"
        varchar courses_discipline_mtech "MTech discipline"
        varchar mtech_sub_specialization "Sub-specialization"
        varchar discipline_elective_mdes "IDT"
        boolean is_modification "True if modification"
        varchar existing_course_code "Course code being modified"
        text prior_knowledge "Prerequisites"
        text course_contents "Syllabus separated by semicolons"
        text texts_and_references "APA / MLA references"
        text learning_outcomes "Course outcomes"
        text overlap_courses "Overlap details"
        text other_relevant_info "Applications / industrial relevance"
        varchar pdf_path "File path to generated PDF"
        varchar pdf_filename "Generated PDF filename"
        varchar email_notification_status "Pending, Sent, Failed"
        text email_error_log "Error detail if notification failed"
        timestamptz created_at
        timestamptz updated_at
    }

    deadline_settings {
        serial id PK
        timestamptz submission_start "Window opening date/time"
        timestamptz submission_deadline "Window closing date/time"
        boolean is_active "Admin override toggle"
        text announcement_message "Banner announcement"
        varchar updated_by "Admin user"
        timestamptz updated_at
    }

    admin_users {
        serial id PK
        varchar username UK
        varchar password_hash "PBKDF2 SHA256"
        varchar role "Academic Office"
        timestamptz created_at
    }

    proposal_status_history {
        serial id PK
        varchar proposal_id FK
        varchar previous_status
        varchar new_status
        text remarks
        varchar changed_by
        timestamptz changed_at
    }
```

---

## 2. Table Specifications

### 2.1 `proposals`
The core table storing course proposals submitted through Form **ACAD-SAPC-01**.

- **Primary Key**: `id` (Serial integer)
- **Unique Identifier**: `proposal_id` (`VARCHAR(50)`, format `SAPC-YYYY-XXXX`)
- **Status Constraints**: Values restricted to `'Pending'`, `'Under Review'`, `'Approved'`, `'Rejected'`, `'Modification Required'`.
- **Notification Tracking**: `email_notification_status` records whether automated email transmission succeeded (`'Sent'`), was logged locally (`'Sent'`), or failed (`'Failed'`).

### 2.2 `deadline_settings`
Maintains the submission window parameters configured by the Academic Office:
- `submission_start`: Starting timestamp in UTC.
- `submission_deadline`: Hard cutoff timestamp in UTC. Submissions attempted at `current_time > submission_deadline` are blocked on the server.
- `is_active`: Emergency administrative switch allowing instant opening or closing regardless of the calendar window.

### 2.3 `admin_users`
Stores Academic Office authorized accounts. Passwords are encrypted using salted PBKDF2 with SHA-256 (`generate_password_hash`).

### 2.4 `proposal_status_history`
Full audit log tracking state transitions for proposals as they move through the review pipeline:
- Links to `proposals.proposal_id` with `ON DELETE CASCADE`.
- Captures `previous_status`, `new_status`, administrative `remarks`, and `changed_by`.

---

## 3. Query Optimization and Indexes

To guarantee sub-millisecond query performance on dashboards with large proposal volumes, B-Tree indexes are applied to all queried attributes:

```sql
CREATE INDEX idx_proposals_proposal_id ON proposals(proposal_id);
CREATE INDEX idx_proposals_course_title ON proposals(course_title);
CREATE INDEX idx_proposals_proposer_name ON proposals(proposer_name);
CREATE INDEX idx_proposals_faculty_email ON proposals(faculty_email);
CREATE INDEX idx_proposals_status ON proposals(status);
CREATE INDEX idx_proposals_submission_date ON proposals(submission_date);
CREATE INDEX idx_proposals_course_type ON proposals(course_type);
CREATE INDEX idx_proposals_course_level ON proposals(course_level);
CREATE INDEX idx_proposals_is_modification ON proposals(is_modification);
```
