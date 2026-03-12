import csv
import io
from datetime import datetime


def generate_csv_report(report_type: str, db: dict) -> str:
    output = io.StringIO()

    if report_type == 'performance':
        writer = csv.writer(output)
        writer.writerow(['Employee Name', 'Department', 'Role', 'Productivity', 'Attendance %', 'Task Completion', 'Quality Rating', 'TL Score'])
        for p in db['performance']:
            emp = next((e for e in db['employees'] if e['user_id'] == p['user_id']), {})
            writer.writerow([emp.get('name', ''), emp.get('department', ''), emp.get('role', ''),
                             p.get('productivity_score', ''), p.get('attendance_pct', ''),
                             p.get('task_completion', ''), p.get('quality_rating', ''), p.get('tl_score', '')])

    elif report_type == 'attendance':
        writer = csv.writer(output)
        writer.writerow(['Employee Name', 'Month', 'Present Days', 'Absent Days', 'Late Days', 'Total Days', 'Hours Worked'])
        for a in db['attendance']:
            emp = next((e for e in db['employees'] if e['user_id'] == a['user_id']), {})
            writer.writerow([emp.get('name', ''), a.get('month', ''), a.get('present', ''),
                             a.get('absent', ''), a.get('late', ''), a.get('total', ''), a.get('hours', '')])

    elif report_type == 'promotion':
        writer = csv.writer(output)
        writer.writerow(['Employee Name', 'Current Role', 'Experience (Years)', 'Performance Score', 'Eligibility %', 'Recommendation'])
        for p in db['performance']:
            emp = next((e for e in db['employees'] if e['user_id'] == p['user_id']), {})
            score = round(p.get('productivity_score', 0) * 0.35 + p.get('attendance_pct', 0) * 0.2 + p.get('task_completion', 0) * 0.25, 1)
            rec = "Recommended" if score > 75 else "Not Yet Ready"
            writer.writerow([emp.get('name', ''), emp.get('role', ''), emp.get('experience', ''), score, score, rec])

    elif report_type == 'attrition':
        writer = csv.writer(output)
        writer.writerow(['Employee Name', 'Department', 'Satisfaction Score', 'Attendance %', 'Performance', 'Risk Level'])
        for p in db['performance']:
            emp = next((e for e in db['employees'] if e['user_id'] == p['user_id']), {})
            sat = p.get('satisfaction', 75)
            risk = "High" if sat < 50 else "Medium" if sat < 65 else "Low"
            writer.writerow([emp.get('name', ''), emp.get('department', ''), sat, p.get('attendance_pct', ''), p.get('productivity_score', ''), risk])

    elif report_type == 'salary':
        writer = csv.writer(output)
        writer.writerow(['Employee Name', 'Department', 'Role', 'Experience', 'Salary', 'Performance Score'])
        for emp in db['employees']:
            p = next((p for p in db['performance'] if p['user_id'] == emp['user_id']), {})
            writer.writerow([emp.get('name', ''), emp.get('department', ''), emp.get('role', ''),
                             emp.get('experience', ''), emp.get('salary', 'N/A'), p.get('productivity_score', '')])

    else:
        writer = csv.writer(output)
        writer.writerow(['Report Type Not Found'])

    return output.getvalue()
