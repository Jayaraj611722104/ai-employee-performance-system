"""
utils/report_gen_mysql.py
CSV report generator that queries MySQL via SQLAlchemy.
"""
import csv
import io
import json
from database.models import db, Employee, Performance, Attendance, Task


def generate_csv_report(report_type: str) -> str:
    output = io.StringIO()

    if report_type == 'performance':
        writer = csv.writer(output)
        writer.writerow(['Employee Name','Department','Role','Productivity','Attendance %',
                         'Task Completion','Quality Rating','TL Score','Overall Score'])
        for p in Performance.query.all():
            emp = Employee.query.filter_by(user_id=p.user_id).first()
            if not emp:
                continue
            overall = round(p.productivity_score*0.3 + p.attendance_pct*0.2 +
                            p.task_completion*0.25 + p.quality_rating*10*0.15 +
                            p.tl_score*10*0.1, 1)
            writer.writerow([
                emp.name, emp.department, emp.role,
                p.productivity_score, p.attendance_pct,
                p.task_completion, p.quality_rating, p.tl_score, overall
            ])

    elif report_type == 'attendance':
        from sqlalchemy import func
        writer = csv.writer(output)
        writer.writerow(['Employee Name','Present Days','Absent Days','Late Days','Total Hours','Attendance %'])
        rows = db.session.query(
            Attendance.user_id,
            func.sum(db.case((Attendance.status=='Present',1),else_=0)).label('present'),
            func.sum(db.case((Attendance.status=='Absent', 1),else_=0)).label('absent'),
            func.sum(db.case((Attendance.status=='Late',   1),else_=0)).label('late'),
            func.sum(Attendance.hours_worked).label('hours'),
            func.count().label('total')
        ).group_by(Attendance.user_id).all()
        for r in rows:
            emp = Employee.query.filter_by(user_id=r.user_id).first()
            pct = round((r.present / r.total * 100), 1) if r.total else 0
            writer.writerow([
                emp.name if emp else '—',
                r.present, r.absent, r.late,
                round(r.hours or 0, 1), pct
            ])

    elif report_type == 'promotion':
        writer = csv.writer(output)
        writer.writerow(['Employee Name','Current Role','Experience (Years)',
                         'Performance Score','Eligibility %','Recommendation'])
        for p in Performance.query.all():
            emp = Employee.query.filter_by(user_id=p.user_id).first()
            if not emp:
                continue
            score = round(p.productivity_score*0.35 + p.attendance_pct*0.2 +
                          p.task_completion*0.25, 1)
            rec   = "Recommended" if score > 75 else "Not Yet Ready"
            writer.writerow([emp.name, emp.role, emp.experience, score, score, rec])

    elif report_type == 'attrition':
        writer = csv.writer(output)
        writer.writerow(['Employee Name','Department','Satisfaction Score',
                         'Attendance %','Performance Score','Risk Level'])
        for p in Performance.query.all():
            emp  = Employee.query.filter_by(user_id=p.user_id).first()
            if not emp:
                continue
            risk = ("High"   if (p.satisfaction or 75) < 50 else
                    "Medium" if (p.satisfaction or 75) < 65 else "Low")
            writer.writerow([emp.name, emp.department, p.satisfaction,
                             p.attendance_pct, p.productivity_score, risk])

    elif report_type == 'salary':
        writer = csv.writer(output)
        writer.writerow(['Employee Name','Department','Role','Experience (yrs)',
                         'Salary ($)','Performance Score'])
        for emp in Employee.query.all():
            p = Performance.query.filter_by(user_id=emp.user_id).first()
            writer.writerow([emp.name, emp.department, emp.role,
                             emp.experience, float(emp.salary or 0),
                             p.productivity_score if p else 'N/A'])

    else:
        writer = csv.writer(output)
        writer.writerow(['Report type not found'])

    return output.getvalue()
