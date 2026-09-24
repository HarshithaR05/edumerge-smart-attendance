Set-Content -Path "H:\Pre-Product assignment\README.md" -Value (Get-Clipboard)
Set-Content -Path "H:\Pre-Product assignment\README.md" -Value @'
# Smart Attendance & Audit Management System

**Assignment Track:** Assignment 1 – Smart Attendance Management  
**Company:** Edumerge Solutions Pre-Drive Product Engineering Drive  
**Author:** Candidate Submission  

---

## 1. Problem Statement & Product Vision
In higher education institutions with thousands of students and hundreds of faculty, manual roll calls and fragmented spreadsheets create severe operational drag:
- **Lost instructional time:** ~5–10 minutes wasted per class on attendance.
- **Data corruption & proxy attendance:** Paper sheets get lost, damaged, or marked fraudulently.
- **Untracked disputes:** No audit trail when an accidental absence mark occurs (e.g., student at college sports or administrative duty).
- **Delayed academic intervention:** Defaulters (<75%) are identified only at the end of the term, preventing proactive intervention.

### Strategic Solution
A centralized attendance engine providing:
1. **<90-Second Bulk Submission:** Fast roll-call submission per class session.
2. **Immutable Audit Trail:** Direct record mutation is prohibited; all updates require approved tickets and log previous/new states.
3. **Continuous Defaulter Engine:** Real-time percentage tracking alerting staff to students below 75%.
4. **Structured Dispute Desk:** Transparent review lifecycle (PENDING -> APPROVED / REJECTED) for student corrections.

---

## 2. Personas & Core User Journeys

| Role | Job-to-be-Done (JTBD) | Key Workflows |
| :--- | :--- | :--- |
| **Faculty** | "Record lecture attendance quickly without disrupting instruction." | Select Subject/Section, record session, review, submit. |
| **Student** | "Monitor attendance % and fix misrecorded absences." | View subject records, submit correction tickets with reasons. |
| **Admin / HOD** | "Enforce academic compliance and audit corrections." | Review and approve/reject dispute tickets, monitor defaulters (<75%). |

---

## 3. System Architecture & Relational Schema

+---------------------------------------+
                 |    Client: Vanilla JS + Tailwind      |
                 |  (Role-based UI: Admin, Faculty, Stu) |
                 +-------------------+-------------------+
                                     | REST / JSON
                                     v
                 +---------------------------------------+
                 |    Backend Engine: FastAPI (Python)   |
                 |   (JWT Validation, Domain Workflows)  |
                 +-------------------+-------------------+
                                     |
                                     v
                 +---------------------------------------+
                 |   Database: SQLite / PostgreSQL       |
                 |  (Composite Constraints, Audit Trail) |
                 +---------------------------------------+

### Relational Schema & Constraints
- `users`: `(id, username, role [ADMIN, FACULTY, STUDENT])`
- `sections`: `(id, name)`
- `subjects`: `(id, code, name)`
- `students`: `(id, user_id, usn, name, section_id, qr_token)`
- `sessions`: `(id, subject_id, section_id, faculty_id, session_date, slot)`
  - **Constraint:** `UNIQUE(subject_id, section_id, session_date, slot)` blocks duplicate session entries.
- `records`: `(id, session_id, student_id, status [PRESENT, ABSENT])`
  - **Constraint:** `UNIQUE(session_id, student_id)` prevents duplicate student records per session.
- `tickets`: `(id, record_id, student_id, requested_status, reason, status [PENDING, APPROVED, REJECTED], reviewed_by, review_remarks, created_at)`
- `audit_logs`: `(id, record_id, prev_status, new_status, changed_by, ticket_id, timestamp)`

---

## 4. Key Edge Cases & Assumptions Handled
1. **Double Submission Prevention:** Database-level composite unique keys prevent duplicate submissions even during network retries or simultaneous requests.
2. **Compliance & Audit Logging:** Corrections never directly overwrite values; they record an atomic update along with an immutable log entry in `audit_logs`.
3. **Dispute Cut-off Window:** Dispute tickets must be filed within institutional policy windows (e.g., 5 business days).
4. **Division-by-Zero Handling:** Defaulter aggregation accounts for newly created sections with zero sessions using explicit `HAVING total_classes > 0` checks.

---

 5. Local Setup & Execution Guide

  Prerequisites
- Python 3.9+ installed
 
 Step 1: Install Dependencies
```bash
pip install fastapi uvicorn pydantic pyjwt passlib
Step 2: Run Backend Server
Bash
cd Backend
python -m uvicorn app:app --reload --port 8000
Interactive API documentation available at: http://localhost:8000/docs

Step 3: Run Frontend Dashboard
Open Frontend/index.html directly in any web browser.

6. Mandatory AI Usage Report
AI Tool Used: Gemini / Cursor

What I asked AI to do:

Scaffold database schema with composite unique constraints to avoid double-marking periods.

Implement dispute state machine and append-only audit trail.

Construct SQL query for dynamic defaulter calculation (<75%).

Most Useful Prompt: "Design a relational database schema and API endpoints for a college attendance system with 5,000 students that handles attendance corrections through an approval workflow, keeping full audit logs without overwriting historical records directly."

Code Generated by AI: Baseline SQLite tables, FastAPI route skeleton, and Tailwind CSS single-page layout.

Code I Modified: Wrapped session submissions and ticket updates in atomic database transactions; added role-based verification for ticket approvals.

AI Output That Was Wrong: Initial SQL defaulter query used an INNER JOIN that excluded registered students with zero sessions.

How I Identified & Fixed It: Tested edge cases with a fresh section; resolved by switching to LEFT JOIN with HAVING total_classes > 0.
'@ -Encoding utf8

