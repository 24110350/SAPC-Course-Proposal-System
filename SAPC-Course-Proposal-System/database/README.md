# SAPC Course Proposal System — Database Documentation

This directory contains the relational database definition and sample seed datasets for the **SAPC Course Proposal System (Project 13)** at IIT Gandhinagar.

---

## 1. Files in this Directory

| File | Description |
| :--- | :--- |
| `schema.sql` | PostgreSQL DDL script creating all tables (`proposals`, `deadline_settings`, `admin_users`, `proposal_status_history`), foreign keys, constraints, and indexes. |
| `seed.sql` | Demonstration seed script inserting pre-configured admin credentials, default deadline window, and 4 sample course proposals clearly labeled `DEMO / SAMPLE DATA`. |
| `README.md` | This technical guide. |

---

## 2. PostgreSQL Setup Instructions

### Prerequisites
- PostgreSQL 14+ installed and running.
- `psql` command-line utility available or pgAdmin / DBeaver client.

### Step-by-Step Database Initialization

1. **Connect to PostgreSQL as superuser**:
   ```bash
   psql -U postgres
   ```

2. **Create the Database and Dedicated User**:
   ```sql
   CREATE DATABASE sapc_db;
   CREATE USER sapc_admin WITH ENCRYPTED PASSWORD 'postgres';
   GRANT ALL PRIVILEGES ON DATABASE sapc_db TO sapc_admin;
   \c sapc_db
   GRANT ALL ON SCHEMA public TO sapc_admin;
   ```

3. **Execute Schema and Seed Scripts**:
   ```bash
   # Run schema migration
   psql -U postgres -d sapc_db -f schema.sql

   # Run demonstration seeds
   psql -U postgres -d sapc_db -f seed.sql
   ```

4. **Verify Database Content**:
   ```sql
   SELECT proposal_id, course_title, proposer_name, status FROM proposals;
   ```

---

## 3. Database Architecture & Schema Specification

### 3.1 `proposals` Table
Captures the complete structure of the official **ACAD-SAPC-01** form:

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | SERIAL | PRIMARY KEY | Internal auto-increment ID |
| `proposal_id` | VARCHAR(50) | UNIQUE, NOT NULL | Standardized ID (e.g. `SAPC-2026-0001`) |
| `submission_date` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW | Submission timestamp |
| `status` | VARCHAR(50) | NOT NULL, DEFAULT 'Pending' | `Pending`, `Under Review`, `Approved`, `Rejected`, `Modification Required` |
| `course_title` | VARCHAR(255) | NOT NULL | Title of proposed course |
| `potential_instructors`| TEXT | NOT NULL | Name(s) of potential instructors |
| `proposer_name` | VARCHAR(255) | NOT NULL | Name of faculty member proposing |
| `faculty_email` | VARCHAR(255) | NOT NULL | Validated email address for notifications |
| `course_type` | VARCHAR(50) | NOT NULL | Discipline code (e.g. `CS`, `EE`, `HS`, `ME`, `Others`) |
| `course_type_other` | VARCHAR(100) | | Specified description if `Others` is chosen |
| `course_level` | VARCHAR(20) | NOT NULL | Levels `1` through `6` |
| `course_level_secondary` | VARCHAR(20) | | Optional secondary level (e.g. Level 3 and 6) |
| `course_l_t_p_c` | VARCHAR(50) | NOT NULL | L-T-P-C string (e.g. `3-0-2-4`) |
| `lecture_hours` | NUMERIC(4,1) | DEFAULT 0 | Lecture contact hours |
| `tutorial_hours` | NUMERIC(4,1) | DEFAULT 0 | Tutorial contact hours |
| `practical_hours`| NUMERIC(4,1) | DEFAULT 0 | Practical / Lab contact hours |
| `credits` | NUMERIC(4,1) | DEFAULT 0 | Total academic credits |
| `course_duration` | VARCHAR(50) | NOT NULL | `1 Quad`, `2 Quads`, `3 Quads`, `4 Quads (Full Semester)` |
| `expected_frequency`| VARCHAR(50) | NOT NULL | `Each Semester`, `Each Year`, `Once in Two Years`, `Others` |
| `elective_basket_btech` | VARCHAR(50) | | `BS`, `HS`, `Mathematics`, `Science`, or `None` |
| `discipline_elective_btech` | VARCHAR(50) | | AI, CL, CE, CS, EE, ICDT, MSE, ME |
| `minors` | TEXT | | Comma-separated list of selected minor disciplines |
| `is_modification` | BOOLEAN | NOT NULL, DEFAULT FALSE | Whether this modifies an existing course |
| `existing_course_code` | VARCHAR(50) | | Course code if modification (e.g. `EE-302`) |
| `course_contents` | TEXT | NOT NULL | Detailed syllabus paragraph separated by semicolons |
| `texts_and_references` | TEXT | NOT NULL | APA / MLA formatted references |
| `learning_outcomes` | TEXT | NOT NULL | Formal course outcomes |
| `pdf_path` | VARCHAR(500) | | Relative storage path to generated PDF |
| `pdf_filename` | VARCHAR(255) | | Generated PDF filename |
| `email_notification_status` | VARCHAR(50) | NOT NULL, DEFAULT 'Pending' | `Pending`, `Sent`, `Failed` |

### 3.2 Indexes
Indexed for sub-millisecond retrieval during dashboard searches and filters:
- `idx_proposals_proposal_id`
- `idx_proposals_course_title`
- `idx_proposals_proposer_name`
- `idx_proposals_faculty_email`
- `idx_proposals_status`
- `idx_proposals_submission_date`
- `idx_proposals_course_type`
- `idx_proposals_course_level`
- `idx_proposals_is_modification`

---

## 4. Development Flexibility (Dual DB Engine)

While `schema.sql` and `seed.sql` are written for PostgreSQL, the Flask backend uses an intelligent ORM / DB abstraction layer (`backend/app/models`):
- When `DATABASE_URL` starts with `postgresql://`, it connects directly to PostgreSQL using `psycopg2`.
- In zero-dependency development or environments without a running PostgreSQL daemon, it falls back seamlessly to SQLite (`sqlite:///sapc_course_proposals.db`) so evaluators can run the entire system instantly without database configuration.
