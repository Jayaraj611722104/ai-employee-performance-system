import os, json
from datetime import date, datetime

from app_mysql import app
from database.models import (
    db, User, Employee, Team, Task, Performance, Attendance,
    Notification, WeeklyUpdate, LoginLog, Training, AIPrediction, LeaveRequest,
    TeamPerformance, TeamProject, TLRating, TeamMemberTask
)

OUT_PATH = os.path.join(os.path.dirname(__file__), 'data.json')

def to_dict_row(row):
    d = {}
    for c in row.__table__.columns:
        val = getattr(row, c.name)
        if isinstance(val, datetime):
            val = val.isoformat()
        elif isinstance(val, date):
            val = str(val)
        d[c.name] = val
    return d

def export():
    with app.app_context():
        data = {}
        # Users: map password_hash -> password for JSON mode compatibility
        users = []
        for u in User.query.all():
            d = to_dict_row(u)
            d['password'] = d.pop('password_hash', 'password123')
            users.append(d)
        data['users'] = users

        # Employees
        data['employees'] = [to_dict_row(e) for e in Employee.query.all()]

        # Performance: ensure monthly_trend is list
        perf_rows = []
        for p in Performance.query.all():
            d = to_dict_row(p)
            # monthly_trend may be JSON string; normalize to list
            mt = d.get('monthly_trend')
            if isinstance(mt, str):
                try:
                    d['monthly_trend'] = json.loads(mt)
                except Exception:
                    d['monthly_trend'] = []
            perf_rows.append(d)
        data['performance'] = perf_rows

        # Tasks: required_skills could be JSON string; keep as-is
        data['tasks'] = [to_dict_row(t) for t in Task.query.all()]

        # Attendance
        data['attendance'] = [to_dict_row(a) for a in Attendance.query.all()]

        # Notifications
        data['notifications'] = [to_dict_row(n) for n in Notification.query.all()]

        # Weekly Updates
        data['weekly_updates'] = [to_dict_row(w) for w in WeeklyUpdate.query.all()]

        # Login Logs
        data['login_logs'] = [to_dict_row(l) for l in LoginLog.query.all()]

        # Training
        data['training'] = [to_dict_row(t) for t in Training.query.all()]

        # AI Predictions
        data['ai_predictions'] = [to_dict_row(a) for a in AIPrediction.query.all()]

        # Leave Requests
        data['leave_requests'] = [to_dict_row(l) for l in LeaveRequest.query.all()]

        # Teams: normalize monthly_scores
        teams = []
        for t in Team.query.all():
            d = to_dict_row(t)
            ms = d.get('monthly_scores')
            if isinstance(ms, str):
                try:
                    d['monthly_scores'] = json.loads(ms)
                except Exception:
                    d['monthly_scores'] = []
            teams.append(d)
        data['teams'] = teams

        # Team Performance
        data['team_performance'] = [to_dict_row(tp) for tp in TeamPerformance.query.all()]

        # Team Projects
        data['team_projects'] = [to_dict_row(tp) for tp in TeamProject.query.all()]

        # TL Ratings
        data['tl_ratings'] = [to_dict_row(tr) for tr in TLRating.query.all()]

        # Team Member Tasks
        data['team_member_tasks'] = [to_dict_row(tmt) for tmt in TeamMemberTask.query.all()]

        # Write JSON with backup
        try:
            if os.path.exists(OUT_PATH):
                os.replace(OUT_PATH, OUT_PATH + '.bak')
        except Exception:
            pass
        with open(OUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"✅ Exported MySQL database to {OUT_PATH}")

if __name__ == '__main__':
    export()
