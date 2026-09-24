from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

output_path = r"H:\Pre-Product assignment\Smart Attendance.pdf"
doc = SimpleDocTemplate(output_path, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
styles = getSampleStyleSheet()

title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=16, leading=20, textColor=colors.HexColor('#0F172A'))
sub_style = ParagraphStyle('Sub', parent=styles['Normal'], fontSize=8.5, leading=12, textColor=colors.HexColor('#475569'))
h2_style = ParagraphStyle('H2', parent=styles['Heading2'], fontSize=11, leading=15, textColor=colors.HexColor('#1E293B'), spaceBefore=8, spaceAfter=4)
body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=8, leading=11, textColor=colors.HexColor('#334155'))

elements = []

elements.append(Paragraph("Smart Attendance & Audit Management System", title_style))
elements.append(Paragraph("<b>Assignment Track:</b> Assignment 1 - Smart Attendance Management | <b>Company:</b> Edumerge Solutions<br/><b>Submission Deadline:</b> 9:00 AM, 25 September 2026 | <b>Author:</b> Harshitha", sub_style))
elements.append(Spacer(1, 8))

elements.append(Paragraph("1. Executive Summary & Problem Framing", h2_style))
elements.append(Paragraph("Institutional attendance management across 5,000 students and 200 faculty members is a compliance and retention challenge. This solution mitigates 4 core bottlenecks:<br/>"
                          "- <b>Instructional Overhead:</b> Rapid slot-based recording in under 90 seconds.<br/>"
                          "- <b>Data Tampering:</b> Immutable transaction logs replace editable spreadsheets.<br/>"
                          "- <b>Dispute Bottlenecks:</b> Formal dispute desk (PENDING -> APPROVED/REJECTED) with audit trail.<br/>"
                          "- <b>Early Defaulter Interventions:</b> Continuous aggregation identifying students below 75%.", body_style))
elements.append(Spacer(1, 6))

elements.append(Paragraph("2. Relational Schema & Integrity Constraints", h2_style))
schema_data = [
    ['Entity / Table', 'Key Schema Definition', 'Integrity Rule / Constraint'],
    ['sessions', 'id, subject_id, section_id, faculty_id, date, slot', 'UNIQUE(subject_id, section_id, date, slot) prevents duplicate lecture logs.'],
    ['records', 'id, session_id, student_id, status', 'UNIQUE(session_id, student_id) prevents double marking.'],
    ['tickets', 'id, record_id, student_id, reason, status, reviewed_by', 'State machine: PENDING -> APPROVED | REJECTED.'],
    ['audit_logs', 'id, record_id, prev_status, new_status, changed_by, ts', 'Append-only audit trail capturing all approved mutations.']
]
t = Table(schema_data, colWidths=[75, 215, 240])
t.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F1F5F9')),
    ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#0F172A')),
    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
    ('FONTSIZE', (0,0), (-1,-1), 7.5),
    ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ('TOPPADDING', (0,0), (-1,-1), 3),
    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
]))
elements.append(t)
elements.append(Spacer(1, 6))

elements.append(Paragraph("3. Edge Cases & Engineering Decisions", h2_style))
elements.append(Paragraph("- <b>Double Submission Prevention:</b> Database-level unique composite keys reject duplicate calls with HTTP 400.<br/>"
                          "- <b>Division-by-Zero Handling:</b> Aggregation query handles new cohorts via <i>HAVING total_classes > 0</i>.<br/>"
                          "- <b>Dispute Cut-off:</b> Enforces a strict 5-day correction window post-lecture.", body_style))
elements.append(Spacer(1, 6))

elements.append(Paragraph("4. Mandatory AI Usage Report", h2_style))
ai_data = [
    ['AI Tool Used', 'Gemini / Cursor'],
    ['Key Prompt', '"Design a relational database schema and API endpoints for a college attendance system with 5,000 students that handles attendance corrections through an approval workflow, keeping full audit logs without overwriting records directly."'],
    ['AI Generated Code', 'Baseline SQLite schema, FastAPI JWT routes, Tailwind CSS dashboard skeleton.'],
    ['Candidate Modifications', 'Wrapped updates in strict atomic database transactions; enforced role-based checks for dispute resolution.'],
    ['AI Error Rectification', 'AI wrote INNER JOIN query excluding students with 0 classes from defaulter lists. Identified via unit testing and corrected using LEFT JOIN with total_classes > 0 condition.']
]
t_ai = Table(ai_data, colWidths=[110, 420])
t_ai.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#F8FAFC')),
    ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
    ('FONTSIZE', (0,0), (-1,-1), 7.5),
    ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ('TOPPADDING', (0,0), (-1,-1), 3),
    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
]))
elements.append(t_ai)

doc.build(elements)
print("SUCCESS: Smart Attendance.pdf generated successfully!")
