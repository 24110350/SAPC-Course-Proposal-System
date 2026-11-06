# SAPC Course Proposal System — Testing Documentation

**Senate Academic Programme Committee (SAPC) — Project 13**  
**Indian Institute of Technology Gandhinagar | CS202**

---

## 1. Testing Summary & Test Pass Rate

| Test Category | Suite File | Total Tests | Passed | Failed | Pass Rate |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Backend Proposals & Validation** | `backend/tests/test_proposals.py` | 10 | 10 | 0 | 100% |
| **Deadline Boundary Enforcement** | `backend/tests/test_deadline_boundaries.py` | 9 | 9 | 0 | 100% |
| **Server-Side PDF Generation** | `backend/tests/test_pdf_generation.py` | 3 | 3 | 0 | 100% |
| **Automated Email Notification** | `backend/tests/test_email_notification.py` | 3 | 3 | 0 | 100% |
| **Excel & CSV Export** | `backend/tests/test_exports.py` | 3 | 3 | 0 | 100% |
| **Database & Auth Models** | `backend/tests/test_database.py` | 2 | 2 | 0 | 100% |
| **Frontend Form & Options** | `frontend/tests/formValidation.test.js` | 9 | 9 | 0 | 100% |
| **End-to-End Lifecycle Flow** | `tests/test_integration_flow.py` | 1 | 1 | 0 | 100% |
| **TOTAL** | — | **40** | **40** | **0** | **100%** |

---

## 2. Deadline Boundary Testing (Section 6 Requirement)

As mandated by the Project Instructor, boundary behavior was tested under exact edge conditions:

| Boundary Condition | Simulated Check Time vs Deadline | Expected Outcome | Actual Result |
| :--- | :--- | :--- | :--- |
| **Before Deadline** | 10 days before cutoff | Accepted | **PASSED** (`is_open = True`) |
| **Slightly Before Deadline** | 10 seconds before cutoff | Accepted | **PASSED** (`is_open = True`) |
| **Exactly At Deadline** | Timestamp == `submission_deadline` | Handled properly (inclusive) | **PASSED** (`is_open = True`) |
| **Immediately After Deadline** | 1 second after cutoff | Rejected with HTTP 403 | **PASSED** (`is_open = False`, HTTP 403 returned) |
| **Well After Deadline** | 5 days after cutoff | Rejected with HTTP 403 | **PASSED** (`is_open = False`, HTTP 403 returned) |
| **Admin Changes Deadline** | Admin extends deadline | New deadline takes effect immediately | **PASSED** (New timestamp respected by backend) |
| **Administrative Override** | `is_active = False` | Suspended immediately | **PASSED** (HTTP 403 returned) |

---

## 3. QA Defect Resolution (Traceability to Week 1 Report)

| Defect ID | Reported Issue from Week 1 Report | Solution Implemented in Phase 1 Release | Verification Status |
| :--- | :--- | :--- | :--- |
| **DEF-01** | *Email Notification Integration*: Field was present but not connected to outgoing service; notification trigger test failed. | Integrated `EmailService` supporting SMTP transmission and local outbox logging. Proposal is automatically associated with recipient, notification email is dispatched upon submission, failures are resiliently logged without rolling back proposal, and admin can retry sending from the dashboard. | **RESOLVED & VERIFIED** (Passes `test_email_service_notification_trigger` and `test_email_resilience_on_invalid_recipient`). |
| **DEF-02** | *Card-Based Submission Display*: Submissions presented in card layout rather than structured table requested by PI. | Built `AcademicDashboard` component featuring a database-backed table directly linked to PostgreSQL, multi-attribute filtering (Status, Discipline, Level, Nature), real-time search, sorting, pagination, and Excel/CSV export. | **RESOLVED & VERIFIED** (Verified via UI and API listing tests). |
| **DEF-03** | *Deadline Boundary Verification*: Boundary conditions at and immediately around deadline required systematic verification. | Implemented server-side deadline enforcement in `DeadlineSetting.is_currently_open()` and added dedicated test suite `test_deadline_boundaries.py` with 9 passing tests covering edge timestamps. | **RESOLVED & VERIFIED** (100% Boundary test pass rate). |

---

## 4. How to Execute Tests

### 4.1 Running Backend & Integration Test Suite
```bash
cd backend
python -m pytest -v
```

### 4.2 Running Full End-to-End Test Suite
```bash
# From project root
python -m pytest tests/test_integration_flow.py -v
```

### 4.3 Running Frontend Unit Tests
```bash
cd frontend
npm test
```
