import sqlite3
import jwt
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

SECRET_KEY = "edumerge_product_engineering_key"
ALGORITHM = "HS256"
DB_FILE = "smart_attendance.db"

app = FastAPI(title="Smart Attendance System API")
security = HTTPBearer()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            role TEXT CHECK(role IN ('ADMIN', 'FACULTY', 'STUDENT')) NOT NULL
        );
        CREATE TABLE IF NOT EXISTS sections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            usn TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            section_id INTEGER,
            qr_token TEXT UNIQUE NOT NULL
        );
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER,
            section_id INTEGER,
            faculty_id INTEGER,
            session_date TEXT,
            slot INTEGER,
            UNIQUE(subject_id, section_id, session_date, slot)
        );
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            student_id INTEGER,
            status TEXT CHECK(status IN ('PRESENT', 'ABSENT')),
            UNIQUE(session_id, student_id)
        );
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_id INTEGER,
            student_id INTEGER,
            requested_status TEXT,
            reason TEXT,
            status TEXT DEFAULT 'PENDING' CHECK(status IN ('PENDING', 'APPROVED', 'REJECTED')),
            reviewed_by INTEGER,
            review_remarks TEXT,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_id INTEGER,
            prev_status TEXT,
            new_status TEXT,
            changed_by INTEGER,
            ticket_id INTEGER,
            timestamp TEXT
        );
    ''')

    # Seed baseline mock data
    c.execute("INSERT OR IGNORE INTO users (id, username, role) VALUES (1, 'admin', 'ADMIN')")
    c.execute("INSERT OR IGNORE INTO users (id, username, role) VALUES (2, 'faculty1', 'FACULTY')")
    c.execute("INSERT OR IGNORE INTO users (id, username, role) VALUES (3, 'student1', 'STUDENT')")
    c.execute("INSERT OR IGNORE INTO sections (id, name) VALUES (1, 'CSE - Section A')")
    c.execute("INSERT OR IGNORE INTO subjects (id, code, name) VALUES (1, 'CS101', 'Data Structures')")
    c.execute("INSERT OR IGNORE INTO students (id, user_id, usn, name, section_id, qr_token) VALUES (1, 3, '1MS21CS001', 'Rahul Sharma', 1, 'QR_STU_1001')")
    conn.commit()
    conn.close()

init_db()

# --- Auth Helper ---
def create_token(user_id: int, username: str, role: str) -> str:
    payload = {
        "sub": username,
        "user_id": user_id,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=8)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        return jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization token")

# --- Schemas ---
class LoginRequest(BaseModel):
    username: str

class MarkAttendanceItem(BaseModel):
    student_id: int
    status: str

class SessionAttendanceRequest(BaseModel):
    subject_id: int
    section_id: int
    session_date: str
    slot: int
    records: List[MarkAttendanceItem]

class TicketCreateRequest(BaseModel):
    record_id: int
    requested_status: str
    reason: str

class TicketActionRequest(BaseModel):
    action: str  # APPROVED or REJECTED
    remarks: str

# --- Endpoints ---
@app.post("/api/auth/login")
def login(req: LoginRequest):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (req.username,)).fetchone()
    conn.close()
    if not user:
        raise HTTPException(status_code=404, detail="User account not found")
    return {"access_token": create_token(user["id"], user["username"], user["role"]), "role": user["role"], "user_id": user["id"]}

@app.post("/api/attendance/session")
def record_session_attendance(req: SessionAttendanceRequest, user=Depends(get_current_user)):
    if user["role"] not in ["FACULTY", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Faculty authorization required")
    
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute('''
            INSERT INTO sessions (subject_id, section_id, faculty_id, session_date, slot)
            VALUES (?, ?, ?, ?, ?)
        ''', (req.subject_id, req.section_id, user["user_id"], req.session_date, req.slot))
        session_id = cur.lastrowid

        for item in req.records:
            cur.execute('''
                INSERT INTO records (session_id, student_id, status)
                VALUES (?, ?, ?)
            ''', (session_id, item.student_id, item.status.upper()))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()
        raise HTTPException(status_code=400, detail="Attendance session already exists for this slot.")
    finally:
        conn.close()
    return {"message": "Attendance committed successfully", "session_id": session_id}

@app.post("/api/tickets/raise")
def raise_correction_ticket(req: TicketCreateRequest, user=Depends(get_current_user)):
    conn = get_db()
    cur = conn.cursor()
    student = cur.execute("SELECT id FROM students WHERE user_id = ?", (user["user_id"],)).fetchone()
    if not student:
        conn.close()
        raise HTTPException(status_code=403, detail="Only students can raise correction requests")

    cur.execute('''
        INSERT INTO tickets (record_id, student_id, requested_status, reason, created_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (req.record_id, student["id"], req.requested_status.upper(), req.reason, datetime.utcnow().isoformat()))
    
    conn.commit()
    ticket_id = cur.lastrowid
    conn.close()
    return {"message": "Correction ticket logged successfully", "ticket_id": ticket_id}

@app.post("/api/tickets/{ticket_id}/action")
def process_correction_ticket(ticket_id: int, req: TicketActionRequest, user=Depends(get_current_user)):
    if user["role"] not in ["ADMIN", "FACULTY"]:
        raise HTTPException(status_code=403, detail="Unauthorized approval permissions")

    conn = get_db()
    cur = conn.cursor()
    ticket = cur.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    
    if not ticket or ticket["status"] != "PENDING":
        conn.close()
        raise HTTPException(status_code=400, detail="Ticket is closed or non-existent")

    decision = req.action.upper()
    if decision not in ["APPROVED", "REJECTED"]:
        conn.close()
        raise HTTPException(status_code=400, detail="Invalid status decision")

    if decision == "APPROVED":
        record = cur.execute("SELECT * FROM records WHERE id = ?", (ticket["record_id"],)).fetchone()
        prev_status = record["status"]
        new_status = ticket["requested_status"]

        # Atomic state change + audit trail write
        cur.execute("UPDATE records SET status = ? WHERE id = ?", (new_status, record["id"]))
        cur.execute('''
            INSERT INTO audit_logs (record_id, prev_status, new_status, changed_by, ticket_id, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (record["id"], prev_status, new_status, user["user_id"], ticket_id, datetime.utcnow().isoformat()))

    cur.execute('''
        UPDATE tickets
        SET status = ?, reviewed_by = ?, review_remarks = ?
        WHERE id = ?
    ''', (decision, user["user_id"], req.remarks, ticket_id))

    conn.commit()
    conn.close()
    return {"message": f"Ticket {decision.lower()} successfully"}

@app.get("/api/reports/defaulters")
def get_defaulters(threshold: float = 75.0, user=Depends(get_current_user)):
    conn = get_db()
    query = '''
        SELECT 
            s.id AS student_id,
            s.usn,
            s.name,
            COUNT(r.id) AS total_classes,
            SUM(CASE WHEN r.status = 'PRESENT' THEN 1 ELSE 0 END) AS attended_classes,
            ROUND((SUM(CASE WHEN r.status = 'PRESENT' THEN 1.0 ELSE 0.0 END) / COUNT(r.id)) * 100, 2) AS percentage
        FROM students s
        LEFT JOIN records r ON s.id = r.student_id
        GROUP BY s.id
        HAVING total_classes > 0 AND percentage < ?
    '''
    rows = conn.execute(query, (threshold,)).fetchall()
    conn.close()
    return [dict(ix) for ix in rows]

@app.get("/api/tickets/pending")
def list_pending_tickets(user=Depends(get_current_user)):
    conn = get_db()
    rows = conn.execute("SELECT * FROM tickets WHERE status = 'PENDING'").fetchall()
    conn.close()
    return [dict(ix) for ix in rows]