# SAPC Course Proposal System — Phase 1 (with Email Enhancements)
### Course Proposal and Curriculum Platform for the Academic Office
**Indian Institute of Technology Gandhinagar (IITGN)**  
**Course:** CS202 — Project 13 (Group 11)  
**Form Code:** ACAD-SAPC-01 (Senate Academic Programme Committee)

---

## 1. Project Overview

The **SAPC Course Proposal System** is an institutional software platform engineered for the Academic Office at IIT Gandhinagar. It completely digitizes the submission, review, tracking, and archival of proposals for new courses and modifications to existing courses.

This release delivers the core Phase 1 foundation, the email enhancements, and the complete **Phase 1 Enhancement Requirements (8 Feature Groups)**:
1. **Professor PDF Download**: Submitters can immediately download their official ACAD-SAPC-01 PDF from the submission confirmation screen, with copyable direct download and preview URLs. Admin downloads remain fully preserved.
2. **Secure Proposal Editing & Audit Trail**: Professors can securely edit their submitted proposals using proposal-specific, unguessable URL-safe authorization tokens (`edit_token`) while the submission window is open. Administrators can edit any proposal at any time with JWT authentication. Edits regenerate the official PDF and create a complete audit history (`proposal_edit_history`).
3. **Manual Email Composition & Dispatch**: Professors and administrators can compose and send custom emails regarding any proposal with the official PDF attached, complete with To, CC, editable subject, and message. Outbox logs and automatic notification emails are fully preserved.
4. **Reason for Adding Course as Minor**: Form Section 3, proposal details modal, editing views, Excel/CSV exports, and the official ReportLab PDF include the multiline `minor_reason` field.
5. **Database-Backed Dynamic Form Configuration**: Authorized administrators can add, edit, sort, and deactivate options for course types, levels, durations, frequencies, elective baskets, and minors via `/api/form-config`. Admins can also configure custom form fields. The professor form dynamically loads active options while preserving historical proposals.
6. **Security Department PDF Notification**: Submitted proposal PDFs are automatically routed to the configurable Security Department email (`SECURITY_DEPT_EMAIL`, default: `security@iitgn.ac.in`). Dispatch failures are isolated so submissions never fail, with status logging and admin retry capabilities.
7. **Linked Course Modification History**: Course modification proposals are linked to previous proposals sharing the same `existing_course_code` or title. Admins can view a chronological version history, previous approved versions, details, and download previous PDFs without overwriting old records.
8. **Excel Batch Import & SAPC Number / Approval Date Tracking**: Admins can upload an Excel workbook (.xlsx) to bulk update proposals with official SAPC Numbers (`sapc_number`) and Approval Dates (`approval_date`), complete with a row-by-row validation preview, error summaries, downloadable template, and updated export.

---

## 2. Technology Stack

- **Frontend**:
  - React.js 18 (Vite build engine)
  - Responsive Component-Based Architecture
  - Institutional IIT Gandhinagar Design System (Navy `#002147`, Gold `#c29b38`, crisp slate tables)
  - Lucide Icons
- **Backend**:
  - Python 3.12 / Flask 3.1 REST API
  - SQLAlchemy 2.0 ORM & Schema Engine
  - ReportLab Platypus Engine (Server-side PDF generation)
  - OpenPyXL (Professional Excel workbook generation)
  - Python smtplib / Email Outbox Logging Service
  - HMAC-SHA256 Token Authentication
- **Database**:
  - PostgreSQL 14+ Relational Database (Primary)
  - Dual-mode automatic SQLite fallback for zero-dependency local evaluation
- **Testing**:
  - Pytest (Backend, Database, Boundary, Email, PDF, and Export testing)
  - Node.js Test Runner (Frontend form validation & options testing)

---

## 3. Project Directory Structure

```
SAPC-Course-Proposal-System/
│
├── frontend/                     # React.js SPA (Vite)
│   ├── src/
│   │   ├── components/
│   │   │   ├── Navbar.jsx               # Header with view switcher and auth pill
│   │   │   ├── CourseProposalForm.jsx   # ACAD-SAPC-01 Digital Proposal Form
│   │   │   ├── AcademicDashboard.jsx    # Structured Database-Backed Table
│   │   │   ├── DeadlineBanner.jsx       # Real-time submission window countdown
│   │   │   ├── DeadlineManagerModal.jsx # Admin deadline configuration modal
│   │   │   ├── ProposalDetailModal.jsx  # Full proposal view & status audit history
│   │   │   ├── AdminLoginModal.jsx      # Admin login with demo auto-fill
│   │   │   └── OutboxModal.jsx          # Email dispatch audit modal
│   │   ├── constants/
│   │   │   └── sapcOptions.js           # Disciplines, levels, and abbreviations
│   │   ├── services/
│   │   │   └── api.js                   # REST API client
│   │   ├── App.jsx                      # Root container & routing
│   │   ├── main.jsx                     # DOM mount
│   │   └── index.css                    # Institutional stylesheet
│   ├── tests/
│   │   └── formValidation.test.js       # Frontend unit test suite
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
│
├── backend/                      # Flask REST API
│   ├── app/
│   │   ├── models/                      # SQLAlchemy Relational Models
│   │   │   ├── proposal.py              # ACAD-SAPC-01 Proposal Model
│   │   │   ├── deadline.py              # Configurable Deadline Model
│   │   │   ├── user.py                  # AdminUser & StatusHistory Models
│   │   │   └── __init__.py              # Database engine & session factory
│   │   ├── routes/                      # REST API Endpoints
│   │   │   ├── proposals.py             # Submission, listing, PDF serving
│   │   │   ├── deadline.py              # Deadline query & management
│   │   │   ├── export.py                # Excel (.xlsx) and CSV export
│   │   │   └── auth.py                  # Login & outbox inspection
│   │   ├── services/
│   │   │   ├── pdf_service.py           # ReportLab ACAD-SAPC-01 PDF Generator
│   │   │   ├── email_service.py         # Notification service (SMTP + Local outbox)
│   │   │   └── export_service.py        # OpenPyXL & CSV export generator
│   │   ├── utils/
│   │   │   ├── validators.py            # Independent server-side validation
│   │   │   └── auth_helper.py           # Token authentication & admin decorator
│   │   ├── config.py                    # Environment and configuration
│   │   └── __init__.py                  # Application factory
│   ├── tests/                           # Pytest Test Suite
│   │   ├── conftest.py                  # Test fixtures & mock payloads
│   │   ├── test_proposals.py            # Proposal submission & listing tests
│   │   ├── test_deadline_boundaries.py  # Comprehensive deadline edge tests
│   │   ├── test_pdf_generation.py       # PDF creation and download tests
│   │   ├── test_email_notification.py   # Email dispatch & resilience tests
│   │   ├── test_exports.py              # Excel & CSV export tests
│   │   └── test_database.py             # Database CRUD & hashing tests
│   ├── requirements.txt
│   └── run.py                           # Backend server entry point
│
├── database/                     # PostgreSQL Database Scripts
│   ├── schema.sql                       # Full DDL (tables, constraints, indexes)
│   ├── seed.sql                         # Demo dataset (labeled DEMO / SAMPLE DATA)
│   └── README.md                        # Database installation & query manual
│
├── generated_pdfs/               # Server-side generated PDF repository
│   └── .gitkeep
│
├── tests/                        # Root-level integration test suite
│   └── test_integration_flow.py        # End-to-end full lifecycle test
│
├── docs/                         # Detailed Technical Documentation
│   ├── architecture.md                  # Three-tier architecture & Mermaid diagrams
│   ├── database.md                      # Schema specification & ER diagram
│   ├── api.md                           # REST API reference manual
│   └── testing.md                       # Test results & QA defect verification
│
├── .env.example                  # Environment variable configuration template
├── .gitignore                    # Git ignore file
└── README.md                     # This documentation file
```

---

## 4. Quick Start: How to Run Locally

### Prerequisites
- **Python**: Version 3.10, 3.11, or 3.12 installed.
- **Node.js**: Version 18+ installed (tested on Node v22.17).
- **PostgreSQL** (optional, recommended for production; system defaults to SQLite if PostgreSQL is not active).

---

### Step 1: Backend Setup and Launch

Open a terminal in the project directory:

```bash
cd backend

# (Optional) Create and activate a Python virtual environment:
# On Windows:
python -m venv venv
.\venv\Scripts\activate
# On Linux/macOS:
# python3 -m venv venv
# source venv/bin/activate

# Install dependencies:
pip install -r requirements.txt

# Run the Flask backend server:
python run.py
```

*The backend starts at `http://localhost:5000`. On first start, it automatically initializes database tables, seeds demonstration course proposals, and pre-renders their initial PDFs in `generated_pdfs/`.*

---

### Step 2: Frontend Setup and Launch

Open a second terminal in the project directory:

```bash
cd frontend

# Install npm dependencies:
npm install

# Start the Vite development server:
npm run dev
```

*Open your browser and navigate to `http://localhost:5173`.*

---

## 5. PostgreSQL Database Setup (Production)

If you wish to run against a dedicated PostgreSQL database instead of the built-in development database:

1. **Create the Database in PostgreSQL**:
   ```sql
   CREATE DATABASE sapc_db;
   CREATE USER sapc_admin WITH ENCRYPTED PASSWORD 'postgres';
   GRANT ALL PRIVILEGES ON DATABASE sapc_db TO sapc_admin;
   ```

2. **Execute Schema and Seed SQL Scripts**:
   ```bash
   cd database
   psql -U postgres -d sapc_db -f schema.sql
   psql -U postgres -d sapc_db -f seed.sql
   ```

3. **Configure Backend Environment**:
   Copy `.env.example` to `.env` in the project root or backend folder and set:
   ```env
   DATABASE_URL=postgresql://sapc_admin:postgres@localhost:5432/sapc_db
   ```

---

## 6. Default Administrative Credentials

The Academic Office dashboard provides administrative privileges (adjusting submission deadlines, changing proposal status, retrying notification emails, and exporting spreadsheets):

- **Username**: `admin`
- **Password**: `Admin@IITGN2026`
- **Role**: `Academic Office`

*(In the web UI, click **Admin Login** in the top navigation bar. An **"Auto-fill demo credentials"** button is provided for convenient evaluation.)*

---

## 7. How to Test Core Features

### 7.1 Testing the Course Proposal Form
1. Click **Course Proposal Form** in the top navigation bar.
2. Fill out the form fields. Notice:
   - Required validation checks (Title, Instructors, Proposer, Valid Email, Course Type, Level, Contents).
   - Dynamic credit calculation from L-T-P-C inputs.
   - Conditional **Existing Course Code** field appearing only when "Yes (Modification)" is selected.
   - Multi-select Minor chips with the complete 26-discipline legend from ACAD-SAPC-01.
3. Click **Submit Course Proposal**.
4. Upon successful submission, a confirmation screen appears showing:
   - Generated Proposal ID (e.g. `SAPC-2026-0005`).
   - Notification email status.
   - Direct buttons to **Download Official PDF** and **View PDF in New Tab**.

---

### 7.2 Testing Server-Side PDF Generation and Download
1. Navigate to the **Academic Office Dashboard**.
2. Locate any proposal row in the structured table.
3. Click the **Download PDF** icon in the "Official PDF" column to save the PDF.
4. Click the **External Link** icon to view the PDF rendered directly in your browser.
5. The generated PDF includes:
   - Official IIT Gandhinagar heading and ACAD-SAPC-01 document code.
   - Structured tabular layout for course metadata and curricular baskets.
   - Word-wrapped course contents and reference lists.
   - Official footer routing instructions (`ar.ug@iitgn.ac.in`, `doaa@iitgn.ac.in`).

---

### 7.3 Testing the Configurable Submission Deadline
1. Log in as Admin using the credentials above.
2. Click **Configure Deadline** in the dashboard toolbar.
3. **Test Open Window**: Ensure the deadline is set in the future. Submit a proposal from the form — the server accepts it.
4. **Test Closed Window**: Change the deadline to a past date/time, or uncheck "Enable Proposal Submissions". Click **Save Configuration**.
5. Observe the red **"Submissions Closed"** banner on the frontend.
6. Try submitting a proposal — the Flask backend intercepts the request and rejects it with `HTTP 403 Forbidden` (`SUBMISSION_CLOSED`).
7. Reset the deadline to a future date to re-enable submissions.

---

### 7.4 Testing the Academic Office Dashboard & Decision Notifications
1. Click **Academic Office Dashboard** in the navigation bar.
2. **Search**: Type a keyword (e.g., `Distributed`, `Sharma`, `EE`, `Ethics`) into the search bar. The table updates in real time.
3. **Filter**: Filter by Status (`Approved`, `Pending`, etc.), Discipline (`CS`, `EE`), Level (`Level 3`, `Level 4`), or Nature (`New Course`, `Modification`).
4. **Sort**: Click any column header (`Proposal ID`, `Course Title`, `Submitted`, `Status`) to sort ascending or descending.
5. **View Details**: Click the **Eye icon** to inspect the full ACAD-SAPC-01 submission details, reviewer remarks, additional CC recipients, and status review audit history.
6. **Change Status & Trigger Decision Emails**:
   - As an authorized Admin, open the proposal detail or change status from the table.
   - When status is changed to **Approved**, an official decision email with subject `SAPC Course Proposal Approved — [Course Title] — [Proposal ID]` is dispatched to the submitter's address (`faculty_email`).
   - When status is changed to **Rejected**, an email with subject `SAPC Course Proposal Rejected — [Course Title] — [Proposal ID]` is dispatched to the submitter, including the reviewer's rejection comments and appeal instructions.
   - When status is changed to **Modification Required**, an email with subject `Modifications Required — [Course Title] — [Proposal ID]` is dispatched including specific requested changes.
   - **Pending** and **Under Review** statuses do not trigger decision emails.
   - Saving the same status repeatedly avoids duplicate notifications.
   - Changing between decisions (e.g. from Rejected to Approved) generates a fresh decision notification.

---

### 7.5 Testing Additional Recipients (CC) for Proposal Copy
1. On the **Course Proposal Form**, locate the optional field: **Additional Recipients (CC)** placed below the Faculty Email input.
2. Enter one or multiple comma-separated email addresses (e.g. `hod.cse@iitgn.ac.in, colleague@iitgn.ac.in`).
3. Fill out the course proposal and click **Submit Course Proposal**.
4. The system validates the addresses (format, duplicate handling, max 10 recipients, whitespace trimming).
5. The proposal is safely persisted in the database, its PDF is generated, and copy emails are sent individually to each CC recipient with the PDF attached and `Reply-To` set to the proposer's email.
6. Submitter's own email is automatically omitted from CC to prevent unintended duplicates.
7. Recipient delivery statuses (`Sent`, `Failed`, `Pending`) are stored persistently in the `proposal_recipients` database table and can be inspected in the proposal detail view.

---

### 7.6 Testing Excel (.xlsx) and CSV (.csv) Export
1. In the **Academic Office Dashboard**, click **Export Excel** or **Export CSV**.
2. The browser automatically downloads a formatted spreadsheet:
   - **Excel**: Professionally styled `.xlsx` file generated with OpenPyXL, including navy header row, borders, zebra shading, and auto-fitted column widths.
   - **CSV**: Standard comma-separated format compatible with any spreadsheet tool.

---

### 7.7 Testing Automated Email Notifications & Outbox Audit
- In development/local evaluation mode (`MAIL_BACKEND=local`), all outgoing emails (submission confirmations, CC copies, decision notifications) are recorded in `backend/outbox_emails.json` and logged to stdout.
- To inspect dispatched emails: Log in as Admin and click **Email Outbox** in the dashboard toolbar to view the exact dispatched message, recipient, subject, email type, and timestamp.
- **Production SMTP Configuration**:
  To route emails through live SMTP (e.g. Gmail, IITGN mail gateway):
  Configure in your `.env` file:
  ```env
  MAIL_BACKEND=smtp
  MAIL_HOST=smtp.gmail.com
  MAIL_PORT=587
  MAIL_USE_TLS=True
  MAIL_USE_SSL=False
  MAIL_USERNAME=your_account@iitgn.ac.in
  MAIL_PASSWORD=your_secure_app_password
  MAIL_FROM=sapc-academic@iitgn.ac.in
  MAIL_SENDER_NAME=SAPC Academic Office, IIT Gandhinagar
  ```
- **Resilience**: An email dispatch failure never rolls back or loses a saved proposal or status update; failures are recorded on the proposal record for administrator audit and retry.

---

### 7.8 Phase 1 Enhancements Testing & Workflows

#### 1. Professor PDF Download Workflow (Requirement 1)
- Upon submitting a proposal via `CourseProposalForm`, the success screen immediately displays:
  - **Download Official ACAD-SAPC-01 PDF** button
  - **View PDF in New Tab** button
  - Direct copyable PDF link
- Professors can download the official document directly without waiting or logging in.
- Admin PDF download endpoints (`/api/proposals/<id>/pdf` and inline `/view`) remain fully functional and protected.

#### 2. Professor & Admin Proposal Editing Workflow (Requirement 2)
- **Professor Editing**:
  - The submitter receives a unique, unguessable URL-safe authorization token (`edit_token`, 32+ cryptographically random bytes) on submission and via email.
  - The edit link format is: `http://localhost:5173/?edit_token=<edit_token>`.
  - Accessing this link loads the submitted proposal into `CourseProposalForm` in **Edit Mode**.
  - Submitters can edit form details **only while the submission window is open** (`is_open = True`). Once the deadline passes, edits are blocked server-side (HTTP 403).
  - Submitters cannot access or edit other submitters' proposals.
- **Admin Editing**:
  - Authenticated administrators (JWT bearer token) can edit any proposal at any time, even after the deadline has passed.
  - Admins can initiate edits directly from the Academic Dashboard table via the row **Edit** button (`Edit3`) or from the Proposal Detail Modal.
- **Audit Trail & Regeneration**:
  - Each edit regenerates the official ACAD-SAPC-01 PDF immediately.
  - An immutable record is appended to `proposal_edit_history` recording the editor (`Professor` or `Admin`), editor email, edit timestamp, and field-level delta summary (`changes_summary`).
  - Edit history is viewable by admins in the Proposal Detail Modal under **Proposal Edit History**.

#### 3. Manual Email Composition with PDF Attachment (Requirement 3)
- In the Proposal Detail Modal (or confirmation screen), click **Compose Email**.
- The `EmailComposeModal` opens with:
  - **To**: Pre-populated with submitter/reviewer email (editable).
  - **CC**: Optional comma-separated additional recipients.
  - **Subject**: Editable (pre-filled with proposal ID and course title).
  - **Message**: Custom body text with institutional footer.
  - **Attach Official PDF**: Checkbox (default checked).
- Click **Send Email**. The backend compiles and attaches the latest generated ACAD-SAPC-01 PDF, dispatches the email via SMTP/local outbox, logs the event to the email outbox table, and confirms delivery.

#### 4. 'Reason for Adding Course as Minor' Field (Requirement 4)
- Located in **Section 3: Curriculum Basket & Programme Applicability** directly under the Minors multi-select checklist.
- The multiline textarea captures the academic justification for offering the course as part of a minor programme.
- Value is stored in the `minor_reason` database column.
- Rendered in Section 3 of the official ReportLab ACAD-SAPC-01 PDF, in the Proposal Detail Modal, in the edit form, and included in Excel (`.xlsx`) and CSV (`.csv`) export columns.

#### 5. Dynamic Form Configuration Workflow (Requirement 5)
- Log in as Admin on the Academic Dashboard and click **Form Config** in the toolbar.
- The `FormConfigModal` provides management tabs:
  - **Options Management**: Select category (`course_type`, `course_level`, `course_duration`, `expected_frequency`, `minors`, `btech_elective_basket`), view all current options, add new options, and toggle options between **Active** and **Inactive**.
  - **Custom Fields Management**: Add dynamic custom fields (text, number, textarea, select, checkbox) specifying field label, field key, category, and whether the field is required.
- The professor proposal form dynamically queries `/api/form-config` on load and merges active database-configured options with standard constants.
- Deactivating an option prevents future proposals from selecting it while perfectly preserving existing historical proposals with that value.

#### 6. Security Department PDF Notification (Requirement 6)
- Configured via `SECURITY_DEPT_EMAIL` environment variable (default: `security@iitgn.ac.in`).
- Upon proposal submission, the backend automatically dispatches a notification email with the ACAD-SAPC-01 PDF attached to the Security Department.
- **Failure Resilience**: If security dispatch encounters an error (e.g. SMTP unavailable), proposal submission succeeds completely. The error is logged to `security_email_status = 'Failed'` and `security_email_error`.
- Admins can view the Security Email status in the Proposal Detail Modal and trigger a one-click retry via **Retry Security Notification**.

#### 7. Linked Course Modification History (Requirement 7)
- When a proposal is marked as a modification (`is_modification = True`) with an `existing_course_code`, or shares a title with previous proposals, the system links them chronologically.
- In the Proposal Detail Modal, the **Course Modification & Version History** panel displays:
  - All proposals linked by course code/title sorted chronologically.
  - Previous proposal IDs, version badges, submission dates, and approval statuses.
  - Quick action to view past proposal details and directly download previous approved PDFs.
  - Existing/historical proposals are never overwritten or modified when a new modification proposal is submitted.

#### 8. Excel Import with SAPC Number & Approval Date (Requirement 8)
- In the Academic Dashboard, click **Import Excel**.
- The `ExcelImportModal` provides:
  - **Download Import Template**: Pre-formatted `.xlsx` template with columns (`Proposal ID`, `SAPC Number`, `Approval Date`, `Status`, `Remarks`).
  - **File Upload & Validation Preview**: Upload the updated spreadsheet. The backend validates rows without committing changes and returns a preview table categorizing rows as **Valid** or **Invalid** with specific error diagnostics.
  - **Confirmation**: Click **Confirm & Import Changes** to batch-apply SAPC numbers and approval dates to matched proposals.
  - **Export Updated**: The exported Excel and CSV files now include `SAPC Number`, `Approval Date`, `Reason for Minor`, and `Security Notification Status`.

---

## 8. Database Migrations

### Automatic Migration (SQLite & PostgreSQL)
On application startup, `init_db()` automatically runs a non-destructive schema inspection and adds missing columns (`edit_token`, `minor_reason`, `sapc_number`, `approval_date`, `custom_fields_data`, `security_email_status`, `security_email_error`, `reviewer_comments`, `last_decision_notified`) and creates `proposal_edit_history`, `form_field_options`, `custom_form_fields`, and `proposal_recipients` tables if not already present. It also auto-seeds default form option categories.

### Manual SQL Migration (Production PostgreSQL)
For production database administration, execute the Phase 1 enhancement migration script:
```bash
psql -U postgres -d sapc_db -f database/migration_phase1_enhancements.sql
```
This script safely creates new tables and indexes, and adds the required tracking columns without altering or deleting existing proposal data.

---

## 9. Running Automated Test Suites

### 9.1 Backend Test Suite (Pytest — 60 Tests)
```bash
cd backend
python -m pytest -v
```
*Executes all 60 automated tests covering:*
- *Feature 1: Professor ACAD-SAPC-01 PDF download and unauthenticated public token access.*
- *Feature 2: Professor secure token-based editing, admin editing, edit history audit trail, deadline lockout, and unauthorized access rejection.*
- *Feature 3: Manual email composition with PDF attachment, recipient CC, custom subjects, and delivery logging.*
- *Feature 4: Minor reason field persistence, display, and ReportLab PDF layout rendering.*
- *Feature 5: Dynamic form options and custom fields CRUD, active/inactive filtering, and historical proposal preservation.*
- *Feature 6: Security Department PDF email dispatch, error resilience, and retry endpoint.*
- *Feature 7: Course modification version linking, chronological history, and previous PDF downloads.*
- *Feature 8: Excel batch import validation preview, SAPC number and approval date updates, duplicate safety, and updated exports.*
- *Regressions: Additional recipients (CC), decision notifications, deadline boundaries, database CRUD, and proposal search/filtering.*

### 9.2 Frontend Unit Tests (Node.js Test Runner — 13 Tests)
```bash
cd frontend
npm test
```
*Executes 13 unit tests validating form fields, minor reason validation, edit token regex, SAPC number/approval date validation, CC parsing, duplicate handling, email regex, and ACAD-SAPC-01 constants.*

### 9.3 Frontend Production Build Verification
```bash
cd frontend
npm run build
```
*Runs Vite production build and verifies bundle compilation (built in ~7s, 0 errors).*

---

## 10. Startup Commands

### Backend Server (Flask REST API)
```bash
cd backend
python run.py
```
*Runs on `http://127.0.0.1:5000` (dual PostgreSQL / SQLite support).*

### Frontend Development Server (Vite)
```bash
cd frontend
npm run dev
```
*Runs on `http://localhost:5173` with automatic API proxying to `http://127.0.0.1:5000`.*

---

## 11. Troubleshooting & Common Questions

1. **Port 5000 is already in use**:
   Set `PORT=5001` in your environment or run `python run.py --port 5001`. In `frontend/vite.config.js`, update the proxy target to match.
2. **PostgreSQL connection fails**:
   The backend automatically falls back to local SQLite (`sapc_course_proposals.db`) so the system remains fully functional without a running PostgreSQL daemon.
3. **Where are generated PDFs stored?**:
   PDF files are stored in `generated_pdfs/` in the project root and are accessible via the `/api/proposals/<id>/pdf` endpoints.

---

## 12. Project Team

**Project Group 11 — CS202, IIT Gandhinagar**
- Killada Eswara Valli (24110165)
- Somireddy Bhavitha (24110350)
- Rishitha Gugulothu (25110123)
- Madas Tanvi Raj (25110181)
- Gurudayal Meena (231101125)
