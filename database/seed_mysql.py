"""
database/seed_mysql.py
Run ONCE after tables are created to insert all demo data into MySQL.

    python database/seed_mysql.py
"""
import sys, os, json
from datetime import date, timedelta, datetime
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app_mysql import app
from database.models import (
    db, User, Employee, Performance, Task,
    Attendance, Notification, Training, Team, LeaveRequest,
    TeamPerformance, TeamProject, TLRating, TeamMemberTask
)

# ── Seed Data ──
SEED_USERS = [
    {"id":"U0001","name":"Admin User",       "email":"admin@company.com",    "password":"admin123",  "role":"admin"},
    {"id":"U0002","name":"Sarah Mitchell",   "email":"hr@company.com",       "password":"hr123",     "role":"hr"},
    {"id":"U0003","name":"David Chen",       "email":"tl@company.com",       "password":"tl123",     "role":"teamleader"},
    {"id":"U0004","name":"Alice Johnson",    "email":"employee@gmail.com",   "password":"emp123",    "role":"employee"},
    {"id":"U0005","name":"Bob Williams",     "email":"bob@company.com",      "password":"emp123",    "role":"employee"},
    {"id":"U0006","name":"Carol Davis",      "email":"carol@company.com",    "password":"emp123",    "role":"employee"},
    {"id":"U0007","name":"Eric Thompson",    "email":"eric@company.com",     "password":"emp123",    "role":"employee"},
    {"id":"U0008","name":"Fiona Garcia",     "email":"fiona@company.com",    "password":"emp123",    "role":"employee"},
    {"id":"U0009","name":"George Lee",       "email":"george@company.com",   "password":"emp123",    "role":"employee"},
    {"id":"U0010","name":"Hannah Brown",     "email":"hannah@company.com",   "password":"emp123",    "role":"employee"},
    {"id":"U0011","name":"Ivan Martinez",    "email":"ivan@company.com",     "password":"emp123",    "role":"employee"},
    {"id":"U0012","name":"Julia Wilson",     "email":"julia@company.com",    "password":"emp123",    "role":"employee"},
    {"id":"U0013","name":"Kevin Anderson",   "email":"kevin@company.com",    "password":"emp123",    "role":"employee"},
]

SEED_EMPLOYEES = [
    {"user_id":"U0003","employee_id":"TL001","name":"David Chen",      "role":"Tech Lead",            "department":"Engineering",    "skills":"Python, React, Node.js, AWS, Leadership","experience":7, "joining_date":date(2017,3,15),  "projects_completed":24,"status":"Active","team_leader_id":None,    "salary":95000},
    {"user_id":"U0004","employee_id":"EMP001","name":"Alice Johnson",  "role":"Senior Developer",     "department":"Engineering",    "skills":"Python, Django, React, PostgreSQL",       "experience":5, "joining_date":date(2019,6,1),   "projects_completed":18,"status":"Active","team_leader_id":"U0003","salary":82000},
    {"user_id":"U0005","employee_id":"EMP002","name":"Bob Williams",   "role":"Software Engineer",    "department":"Engineering",    "skills":"Java, Spring Boot, MySQL, Docker",        "experience":4, "joining_date":date(2020,1,10),  "projects_completed":12,"status":"Active","team_leader_id":"U0003","salary":75000},
    {"user_id":"U0006","employee_id":"EMP003","name":"Carol Davis",    "role":"QA Engineer",          "department":"Quality",        "skills":"Selenium, Python, Jest, TestNG",          "experience":3, "joining_date":date(2021,3,22),  "projects_completed":9, "status":"Active","team_leader_id":"U0003","salary":68000},
    {"user_id":"U0007","employee_id":"EMP004","name":"Eric Thompson",  "role":"Data Analyst",         "department":"Analytics",      "skills":"Python, R, Tableau, SQL, Excel",          "experience":3, "joining_date":date(2021,7,5),   "projects_completed":8, "status":"Active","team_leader_id":"U0003","salary":72000},
    {"user_id":"U0008","employee_id":"EMP005","name":"Fiona Garcia",   "role":"Junior Developer",     "department":"Engineering",    "skills":"JavaScript, HTML, CSS, Vue.js",           "experience":1, "joining_date":date(2023,8,14),  "projects_completed":3, "status":"Active","team_leader_id":"U0003","salary":55000},
    {"user_id":"U0009","employee_id":"EMP006","name":"George Lee",     "role":"DevOps Engineer",      "department":"Infrastructure", "skills":"Docker, Kubernetes, AWS, Terraform, Linux","experience":6, "joining_date":date(2018,11,20), "projects_completed":20,"status":"Active","team_leader_id":"U0003","salary":88000},
    {"user_id":"U0010","employee_id":"EMP007","name":"Hannah Brown",   "role":"Full Stack Developer", "department":"Engineering",    "skills":"React, Node.js, MongoDB, GraphQL",        "experience":4, "joining_date":date(2020,5,12),  "projects_completed":15,"status":"Active","team_leader_id":"U0003","salary":78000},
    {"user_id":"U0011","employee_id":"EMP008","name":"Ivan Martinez",  "role":"Junior Developer",     "department":"Engineering",    "skills":"Python, Django, HTML",                    "experience":0, "joining_date":date(2024,1,8),   "projects_completed":1, "status":"Active","team_leader_id":"U0003","salary":50000},
    {"user_id":"U0012","employee_id":"EMP009","name":"Julia Wilson",   "role":"Data Scientist",       "department":"Analytics",      "skills":"Python, ML, TensorFlow, Pandas, NumPy",   "experience":5, "joining_date":date(2019,9,30),  "projects_completed":16,"status":"Active","team_leader_id":"U0003","salary":90000},
    {"user_id":"U0013","employee_id":"EMP010","name":"Kevin Anderson", "role":"Web Developer",        "department":"Engineering",    "skills":"PHP, Laravel, MySQL, Bootstrap",          "experience":2, "joining_date":date(2022,4,18),  "projects_completed":5, "status":"Inactive","team_leader_id":"U0003","salary":60000},
]

SEED_PERFORMANCE = [
    {"user_id":"U0004","productivity_score":88,"attendance_pct":96,"task_completion":90,"quality_rating":9,"tl_score":9,"satisfaction":85,"monthly_trend":[80,83,85,87,88,88]},
    {"user_id":"U0005","productivity_score":75,"attendance_pct":89,"task_completion":78,"quality_rating":7,"tl_score":7,"satisfaction":72,"monthly_trend":[70,71,73,75,74,75]},
    {"user_id":"U0006","productivity_score":82,"attendance_pct":94,"task_completion":85,"quality_rating":8,"tl_score":8,"satisfaction":80,"monthly_trend":[75,77,80,82,81,82]},
    {"user_id":"U0007","productivity_score":71,"attendance_pct":87,"task_completion":72,"quality_rating":7,"tl_score":6,"satisfaction":65,"monthly_trend":[68,69,70,71,70,71]},
    {"user_id":"U0008","productivity_score":65,"attendance_pct":91,"task_completion":68,"quality_rating":6,"tl_score":6,"satisfaction":70,"monthly_trend":[60,62,63,65,64,65]},
    {"user_id":"U0009","productivity_score":92,"attendance_pct":98,"task_completion":95,"quality_rating":9,"tl_score":10,"satisfaction":90,"monthly_trend":[88,89,90,91,92,92]},
    {"user_id":"U0010","productivity_score":84,"attendance_pct":93,"task_completion":86,"quality_rating":8,"tl_score":8,"satisfaction":82,"monthly_trend":[78,80,82,83,84,84]},
    {"user_id":"U0011","productivity_score":58,"attendance_pct":85,"task_completion":60,"quality_rating":6,"tl_score":5,"satisfaction":60,"monthly_trend":[50,52,55,57,58,58]},
    {"user_id":"U0012","productivity_score":90,"attendance_pct":97,"task_completion":92,"quality_rating":9,"tl_score":9,"satisfaction":88,"monthly_trend":[85,87,88,89,90,90]},
    {"user_id":"U0013","productivity_score":55,"attendance_pct":72,"task_completion":50,"quality_rating":5,"tl_score":4,"satisfaction":40,"monthly_trend":[60,58,57,55,53,55]},
]

SEED_TASKS = [
    {"id":"T0001","title":"Build REST API for Auth Module",    "description":"Implement JWT-based authentication",      "priority":"High",  "deadline":date.today()+timedelta(days=5),  "required_skills":["Python","Flask","JWT"],         "assigned_to":"U0004","assigned_by":"U0003","status":"In Progress","progress":60},
    {"id":"T0002","title":"Unit Testing for Payment Service",  "description":"Write unit tests for payment module",     "priority":"Medium","deadline":date.today()+timedelta(days=7),  "required_skills":["Java","JUnit","Mockito"],       "assigned_to":"U0005","assigned_by":"U0003","status":"In Progress","progress":40},
    {"id":"T0003","title":"Selenium Test Suite for Dashboard", "description":"Automate regression testing HR dashboard","priority":"High",  "deadline":date.today()+timedelta(days=3),  "required_skills":["Selenium","Python"],            "assigned_to":"U0006","assigned_by":"U0003","status":"Pending",     "progress":0},
]

SEED_ATTENDANCE = [
    {"user_id":"U0004","present":22,"absent":1,"late":1,"total":24,"hours":176},
    {"user_id":"U0005","present":20,"absent":3,"late":1,"total":24,"hours":160},
]

SEED_TEAMS = [
    {"id":"TM001", "name":"Alpha Squad", "description":"Core backend engineering", "leader_id":"U0003", "project_name":"PulseHR API V2", "project_status":"In Progress", "project_completion":65, "score":88, "monthly_scores":json.dumps([80,82,85,86,88])},
    {"id":"TM002", "name":"Beta Force", "description":"Frontend redesign and UX", "leader_id":None, "project_name":"Employee Dashboard UI", "project_status":"In Progress", "project_completion":40, "score":72, "monthly_scores":json.dumps([70,72,71,73,72])},
    {"id":"TM003", "name":"Gamma Data", "description":"Analytics and reporting", "leader_id":None, "project_name":"Performance AI Models", "project_status":"Not Started", "project_completion":0, "score":45, "monthly_scores":json.dumps([55,50,48,46,45])}
]

SEED_LEAVE_REQUESTS = [
    {"id":"L0001", "user_id":"U0004", "employee_name":"Alice Johnson", "department":"Engineering", "type":"Medical Leave", "from_date":date.today()+timedelta(days=2), "to_date":date.today()+timedelta(days=4), "days":3, "reason":"Scheduled minor surgery.", "is_emergency":False, "status":"Pending", "applied_on":date.today()-timedelta(days=1)},
    {"id":"L0002", "user_id":"U0005", "employee_name":"Bob Williams", "department":"Engineering", "type":"Casual Leave", "from_date":date.today()+timedelta(days=10), "to_date":date.today()+timedelta(days=11), "days":2, "reason":"Family trip out of town.", "is_emergency":False, "status":"Approved (HR)", "applied_on":date.today()-timedelta(days=3), "reviewed_by":"Sarah Mitchell", "reviewed_at":datetime.utcnow()},
    {"id":"L0003", "user_id":"U0008", "employee_name":"Fiona Garcia", "department":"Engineering", "type":"Sick Leave", "from_date":date.today(), "to_date":date.today()+timedelta(days=1), "days":2, "reason":"Severe fever and flu.", "is_emergency":True, "status":"Pending", "applied_on":date.today()}
]

SEED_TEAM_PERFORMANCE = [
    {"team_id":"TM001", "productivity_score":85.5, "project_completion":70.0, "quality_rating":8.5},
    {"team_id":"TM002", "productivity_score":72.0, "project_completion":45.0, "quality_rating":7.2},
    {"team_id":"TM003", "productivity_score":45.0, "project_completion":10.0, "quality_rating":5.5},
]

SEED_TEAM_PROJECTS = [
    {"team_id":"TM001", "project_name":"PulseHR API V2", "status":"In Progress", "completion_pct":70},
    {"team_id":"TM002", "project_name":"Employee Dashboard UI", "status":"In Progress", "completion_pct":45},
    {"team_id":"TM003", "project_name":"Performance AI Models", "status":"Not Started", "completion_pct":0},
]

SEED_TL_RATINGS = [
    {"employee_id":"U0004", "tl_id":"U0003", "rating":5, "feedback":"Alice is performing exceptionally well in the API redesign. Great leadership skills."},
    {"employee_id":"U0005", "tl_id":"U0003", "rating":4, "feedback":"Bob is doing great, but needs to focus more on documentation."},
    {"employee_id":"U0010", "tl_id":"U0003", "rating":5, "feedback":"Hannah is a great asset with fast delivery."},
]

SEED_TEAM_MEMBER_TASKS = [
    {"team_id":"TM001", "user_id":"U0004", "tasks_completed":12, "tasks_pending":2},
    {"team_id":"TM001", "user_id":"U0005", "tasks_completed":8,  "tasks_pending":3},
    {"team_id":"TM001", "user_id":"U0010", "tasks_completed":15, "tasks_pending":1},
]

# ── Seed Function ──
def seed():
    with app.app_context():
        print("🚀 Starting database seed...")

        # Create tables if not present; do NOT drop existing data
        db.create_all()
        print("✅ Tables ensured")
        # If users already exist, skip seeding to preserve existing records
        if User.query.count() > 0:
            print("ℹ️ Data already exists — skipping seed to preserve existing users and records")
            return

        # ── Users ──
        for u in SEED_USERS:
            user = User(
                id=u['id'], name=u['name'], email=u['email'],
                password_hash=u['password'], role=u['role'], status='Active'
            )
            db.session.add(user)
        db.session.commit()
        print(f"✅ {len(SEED_USERS)} users inserted")

        # ── Teams ──
        for t in SEED_TEAMS:
            team = Team(
                id=t['id'], name=t['name'], description=t['description'],
                leader_id=t['leader_id'], project_name=t['project_name'],
                project_status=t['project_status'], project_completion=t['project_completion'],
                score=t['score'], monthly_scores=t['monthly_scores']
            )
            db.session.add(team)
        db.session.commit()
        print(f"✅ {len(SEED_TEAMS)} teams inserted")

        # ── Employees ──
        for e in SEED_EMPLOYEES:
            emp = Employee(
                employee_id=e['employee_id'],
                name=e['name'],
                role=e['role'],
                department=e['department'],
                skills=e['skills'],
                experience=e['experience'],
                joining_date=e['joining_date'],
                projects_completed=e['projects_completed'],
                status=e['status'],
                salary=e['salary'],
                user_id=e['user_id'],
                team_leader_id=e['team_leader_id'],
                team_id='TM001' if e['team_leader_id'] == 'U0003' else None # automatically attach some employees to Alpha Squad for demo
            )
            db.session.add(emp)
        db.session.commit()
        print(f"✅ {len(SEED_EMPLOYEES)} employees inserted")

        # ── Performance ──
        for p in SEED_PERFORMANCE:
            row = Performance(
                user_id=p['user_id'],
                productivity_score=p['productivity_score'],
                attendance_pct=p['attendance_pct'],
                task_completion=p['task_completion'],
                quality_rating=p['quality_rating'],
                tl_score=p['tl_score'],
                satisfaction=p['satisfaction'],
                monthly_trend=json.dumps(p['monthly_trend']),
                month='January', year=2025
            )
            db.session.add(row)
        db.session.commit()
        print(f"✅ {len(SEED_PERFORMANCE)} performance records inserted")

        # ── Tasks ──
        for t in SEED_TASKS:
            task = Task(
                id=t['id'], title=t['title'], description=t['description'],
                priority=t['priority'], deadline=t['deadline'],
                required_skills=json.dumps(t['required_skills']),
                assigned_to=t['assigned_to'], assigned_by=t['assigned_by'],
                status=t['status'], progress=t['progress']
            )
            db.session.add(task)
        db.session.commit()
        print(f"✅ {len(SEED_TASKS)} tasks inserted")

        # ── Attendance ──
        for a in SEED_ATTENDANCE:
            for day_offset in range(a['present']):
                att = Attendance(
                    user_id=a['user_id'],
                    date=date(2025, 1, day_offset + 1),
                    status='Present',
                    hours_worked=round(a['hours'] / a['present'], 1)
                )
                db.session.add(att)
        db.session.commit()
        print(f"✅ Attendance records inserted")

        # ── Leave Requests ──
        for l in SEED_LEAVE_REQUESTS:
            lr = LeaveRequest(
                id=l['id'], user_id=l['user_id'], employee_name=l['employee_name'],
                department=l['department'], type=l['type'], from_date=l['from_date'],
                to_date=l['to_date'], days=l['days'], reason=l['reason'],
                is_emergency=l['is_emergency'], status=l['status'],
                applied_on=l['applied_on'], reviewed_by=l.get('reviewed_by'),
                reviewed_at=l.get('reviewed_at')
            )
            db.session.add(lr)
        db.session.commit()
        print(f"✅ {len(SEED_LEAVE_REQUESTS)} leave requests inserted")

        # ── Notifications ──
        notifs = [
            Notification(message="Q4 Performance Reviews due next Friday", type="warning", target="all", sent_by="U0002"),
            Notification(message="Team standup at 10 AM tomorrow", type="info", target="employee", sent_by="U0003"),
            Notification(message="Alice Johnson is eligible for promotion!", type="success", target="all", sent_by="U0002"),
            Notification(message="New training program: Advanced React", type="info", target="all", sent_by="U0002"),
        ]
        for n in notifs:
            db.session.add(n)
        db.session.commit()
        print("✅ Notifications inserted")

        # ── Team Performance ──
        for tp in SEED_TEAM_PERFORMANCE:
            tp_row = TeamPerformance(**tp)
            db.session.add(tp_row)
        db.session.commit()
        print(f"✅ {len(SEED_TEAM_PERFORMANCE)} team performance records inserted")

        # ── Team Projects ──
        for tpj in SEED_TEAM_PROJECTS:
            tpj_row = TeamProject(**tpj)
            db.session.add(tpj_row)
        db.session.commit()
        print(f"✅ {len(SEED_TEAM_PROJECTS)} team projects inserted")

        # ── TL Ratings ──
        for tr in SEED_TL_RATINGS:
            tr_row = TLRating(**tr)
            db.session.add(tr_row)
        db.session.commit()
        print(f"✅ {len(SEED_TL_RATINGS)} TL ratings inserted")

        # ── Team Member Tasks ──
        for tmt in SEED_TEAM_MEMBER_TASKS:
            tmt_row = TeamMemberTask(**tmt)
            db.session.add(tmt_row)
        db.session.commit()
        print(f"✅ {len(SEED_TEAM_MEMBER_TASKS)} team member tasks inserted")

        print("\n🎉 Database seeded successfully!")
        print("─" * 40)
        print("Login credentials:")
        print("  Admin    →  admin@company.com    / admin123")
        print("  HR       →  hr@company.com       / hr123")
        print("  TL       →  tl@company.com       / tl123")
        print("  Employee →  employee@gmail.com   / emp123")


if __name__ == '__main__':
    seed()
