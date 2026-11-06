# SAPC Course Proposal System — REST API Documentation

**Senate Academic Programme Committee (SAPC) — Project 13**  
**Indian Institute of Technology Gandhinagar**

Base URL: `http://localhost:5000/api`

---

## 1. Course Proposals Endpoints

### 1.1 Submit Course Proposal
- **Route**: `POST /api/proposals`
- **Access**: Public (enforces active deadline server-side)
- **Content-Type**: `application/json`
- **Request Body**:
  ```json
  {
    "course_title": "Distributed Systems and Cloud Computing",
    "potential_instructors": "Dr. Vikram Sharma; Dr. Ananya Sen",
    "proposer_name": "Dr. Vikram Sharma",
    "faculty_email": "vikram.sharma@iitgn.ac.in",
    "course_type": "CS",
    "course_type_other": null,
    "course_level": "4",
    "course_level_secondary": "6",
    "course_l_t_p_c": "3-0-2-4",
    "lecture_hours": 3.0,
    "tutorial_hours": 0.0,
    "practical_hours": 2.0,
    "credits": 4.0,
    "course_duration": "4 Quads (Full Semester)",
    "expected_frequency": "Each Year",
    "expected_frequency_other": null,
    "elective_basket_btech": null,
    "discipline_elective_btech": "CS",
    "discipline_basket_btech": "Systems Basket",
    "minors": "CS, DA",
    "minor_basket_thematic_area": "HPC",
    "discipline_elective_msc": null,
    "courses_discipline_mtech": "CS",
    "mtech_sub_specialization": "Distributed Systems",
    "discipline_elective_mdes": null,
    "is_modification": false,
    "existing_course_code": null,
    "prior_knowledge": "Data structures and networks",
    "course_contents": "Models of distributed systems; RPC; vector clocks; Paxos; Raft; fault tolerance; replication.",
    "texts_and_references": "Coulouris et al. Distributed Systems (5th ed.).",
    "learning_outcomes": "Design resilient distributed services.",
    "overlap_courses": "None",
    "other_relevant_info": "Lab using Go and Kubernetes."
  }
  ```
- **Responses**:
  - `201 Created`: Proposal created, PDF generated, notification dispatched.
  - `400 Bad Request`: Validation failure (returns dictionary of field-specific errors).
  - `403 Forbidden`: Submissions closed due to deadline expiration or administrative suspension.
  - `409 Conflict`: Duplicate proposal detected (identical title & proposer).

---

### 1.2 List Course Proposals (Dashboard Query)
- **Route**: `GET /api/proposals`
- **Access**: Public / Academic Office
- **Query Parameters**:
  - `q` (string): Search query matching `proposal_id`, `course_title`, `proposer_name`, `faculty_email`, or `existing_course_code`.
  - `status` (string): Filter by status (`Pending`, `Under Review`, `Approved`, `Rejected`, `Modification Required`).
  - `course_type` (string): Filter by discipline (`CS`, `EE`, `ME`, `HS`, etc.).
  - `course_level` (string): Filter by level (`1` through `6`).
  - `nature` (string): `NEW` or `MODIFICATION`.
  - `sort_by` (string): Column to sort (`submission_date`, `course_title`, `proposal_id`, `status`).
  - `order` (string): `asc` or `desc` (default: `desc`).
  - `page` (int): Page number (default: 1).
  - `per_page` (int): Items per page (default: 20).
- **Response**: `200 OK`
  ```json
  {
    "success": true,
    "total": 4,
    "page": 1,
    "per_page": 20,
    "total_pages": 1,
    "proposals": [...],
    "stats": {
      "total": 4,
      "pending": 1,
      "under_review": 1,
      "approved": 1,
      "modification_required": 1,
      "rejected": 0
    }
  }
  ```

---

### 1.3 Get Proposal Details
- **Route**: `GET /api/proposals/<proposal_id>`
- **Access**: Public / Academic Office
- **Response**: `200 OK` (includes proposal fields and review audit history array `history: [...]`).

---

### 1.4 Update Proposal Status
- **Route**: `PATCH /api/proposals/<proposal_id>/status`
- **Access**: Admin only (`Authorization: Bearer <token>`)
- **Request Body**:
  ```json
  {
    "status": "Approved",
    "remarks": "Recommended by SAPC and approved by Chairman, Senate."
  }
  ```
- **Response**: `200 OK` (returns updated proposal and automatically re-generates official PDF with updated status stamp).

---

### 1.5 Download / View Generated PDF
- **Download**: `GET /api/proposals/<proposal_id>/pdf` (`Content-Disposition: attachment; filename="<id>.pdf"`)
- **Inline View**: `GET /api/proposals/<proposal_id>/pdf/view` (`Content-Disposition: inline`)

---

### 1.6 Resend Notification Email
- **Route**: `POST /api/proposals/<proposal_id>/resend-email`
- **Access**: Admin only (`Authorization: Bearer <token>`)
- **Response**: `200 OK` (retries dispatching notification email and updates status).

---

## 2. Submission Deadline Endpoints

### 2.1 Get Deadline Status
- **Route**: `GET /api/deadline`
- **Access**: Public
- **Response**: `200 OK`
  ```json
  {
    "success": true,
    "deadline": {
      "is_open": true,
      "submission_start": "2026-10-01T09:00:00Z",
      "submission_deadline": "2026-10-15T23:59:59Z",
      "time_remaining_seconds": 1253639,
      "status_message": "Submissions are currently open.",
      "is_active": true,
      "announcement_message": "Submissions for upcoming semester are open."
    }
  }
  ```

---

### 2.2 Update Deadline Settings
- **Route**: `PUT /api/deadline`
- **Access**: Admin only (`Authorization: Bearer <token>`)
- **Request Body**:
  ```json
  {
    "submission_start": "2026-10-01T09:00:00Z",
    "submission_deadline": "2026-10-25T23:59:59Z",
    "is_active": true,
    "announcement_message": "Deadline extended by 10 days."
  }
  ```

---

### 2.3 Boundary Check Evaluation
- **Route**: `POST /api/deadline/boundary-check`
- **Access**: Public / Testing
- **Request Body**:
  ```json
  { "check_time": "2026-10-15T23:59:59Z" }
  ```

---

## 3. Data Export Endpoints

### 3.1 Export Submissions
- **Route**: `GET /api/proposals/export?format=xlsx` or `?format=csv`
- **Access**: Admin only (`Authorization: Bearer <token>` or `?token=<token>`)
- **Response**:
  - `xlsx`: Streamed `.xlsx` workbook styled with openpyxl.
  - `csv`: UTF-8 comma-separated text file.

---

## 4. Authentication Endpoints

### 4.1 Admin Login
- **Route**: `POST /api/auth/login`
- **Request Body**:
  ```json
  { "username": "admin", "password": "Admin@IITGN2026" }
  ```
- **Response**: `200 OK` (returns signed token and user profile).

---

### 4.2 Email Outbox Audit
- **Route**: `GET /api/auth/outbox`
- **Access**: Admin only (`Authorization: Bearer <token>`)
- **Response**: `200 OK` (returns list of all automated notifications recorded by the system).
