import json
import os
from datetime import datetime, timedelta
import random
import time
import tempfile
from werkzeug.security import generate_password_hash

DB_FILE = os.path.join(os.path.dirname(__file__), 'data.json')
LOCK_FILE = os.path.join(os.path.dirname(__file__), 'data.lock')

DEMO_DATA = {
    "users": [
        {"id": "U0001", "name": "Admin User", "email": "admin@gmail.com", "password": "admin123", "role": "admin", "status": "Active"},
        {"id": "U0002", "name": "Sarah Mitchell", "email": "hr@gmail.com", "password": "hr123", "role": "hr", "status": "Active"},
        {"id": "U0003", "name": "David Chen", "email": "tl@gmail.com", "password": "tl123", "role": "teamleader", "status": "Active"},
        {"id": "U0004", "name": "Alice Johnson", "email": "alice@gmail.com", "password": "emp123", "role": "employee", "status": "Active"},
        {"id": "U0005", "name": "Bob Williams", "email": "bob@gmail.com", "password": "emp123", "role": "employee", "status": "Active"},
        {"id": "U0006", "name": "Carol Davis", "email": "carol@gmail.com", "password": "emp123", "role": "employee", "status": "Active"},
        {"id": "U0007", "name": "Eric Thompson", "email": "eric@gmail.com", "password": "emp123", "role": "employee", "status": "Active"},
        {"id": "U0008", "name": "Fiona Garcia", "email": "fiona@gmail.com", "password": "emp123", "role": "employee", "status": "Active"},
        {"id": "U0009", "name": "George Lee", "email": "george@gmail.com", "password": "emp123", "role": "employee", "status": "Active"},
        {"id": "U0010", "name": "Hannah Brown", "email": "hannah@gmail.com", "password": "emp123", "role": "employee", "status": "Active"},
        {"id": "U0011", "name": "Ivan Martinez", "email": "ivan@gmail.com", "password": "emp123", "role": "employee", "status": "Active"},
        {"id": "U0012", "name": "Julia Wilson", "email": "julia@gmail.com", "password": "emp123", "role": "employee", "status": "Active"},
        {"id": "U0013", "name": "Kevin Anderson", "email": "kevin@gmail.com", "password": "emp123", "role": "employee", "status": "Active"},
    ],
    "employees": [
        {"user_id": "U0003", "name": "David Chen", "employee_id": "TL001", "role": "Tech Lead", "department": "Engineering", "skills": "Python, React, Node.js, AWS, Leadership", "experience": 7, "joining_date": "2017-03-15", "projects_completed": 24, "status": "Active", "team_leader_id": None, "salary": 95000},
        {"user_id": "U0004", "name": "Alice Johnson", "employee_id": "EMP001", "role": "Senior Developer", "department": "Engineering", "skills": "Python, Django, React, PostgreSQL", "experience": 5, "joining_date": "2019-06-01", "projects_completed": 18, "status": "Active", "team_leader_id": "U0003", "salary": 82000},
        {"user_id": "U0005", "name": "Bob Williams", "employee_id": "EMP002", "role": "Software Engineer", "department": "Engineering", "skills": "Java, Spring Boot, MySQL, Docker", "experience": 4, "joining_date": "2020-01-10", "projects_completed": 12, "status": "Active", "team_leader_id": "U0003", "salary": 75000},
        {"user_id": "U0006", "name": "Carol Davis", "employee_id": "EMP003", "role": "QA Engineer", "department": "Quality", "skills": "Selenium, Python, Jest, TestNG", "experience": 3, "joining_date": "2021-03-22", "projects_completed": 9, "status": "Active", "team_leader_id": "U0003", "salary": 68000},
        {"user_id": "U0007", "name": "Eric Thompson", "employee_id": "EMP004", "role": "Data Analyst", "department": "Analytics", "skills": "Python, R, Tableau, SQL, Excel", "experience": 3, "joining_date": "2021-07-05", "projects_completed": 8, "status": "Active", "team_leader_id": "U0003", "salary": 72000},
        {"user_id": "U0008", "name": "Fiona Garcia", "employee_id": "EMP005", "role": "Junior Developer", "department": "Engineering", "skills": "JavaScript, HTML, CSS, Vue.js", "experience": 1, "joining_date": "2023-08-14", "projects_completed": 3, "status": "Active", "team_leader_id": "U0003", "salary": 55000},
        {"user_id": "U0009", "name": "George Lee", "employee_id": "EMP006", "role": "DevOps Engineer", "department": "Infrastructure", "skills": "Docker, Kubernetes, AWS, Terraform, Linux", "experience": 6, "joining_date": "2018-11-20", "projects_completed": 20, "status": "Active", "team_leader_id": "U0003", "salary": 88000},
        {"user_id": "U0010", "name": "Hannah Brown", "employee_id": "EMP007", "role": "Full Stack Developer", "department": "Engineering", "skills": "React, Node.js, MongoDB, GraphQL", "experience": 4, "joining_date": "2020-05-12", "projects_completed": 15, "status": "Active", "team_leader_id": "U0003", "salary": 78000},
        {"user_id": "U0011", "name": "Ivan Martinez", "employee_id": "EMP008", "role": "Junior Developer", "department": "Engineering", "skills": "Python, Django, HTML", "experience": 0, "joining_date": "2024-01-08", "projects_completed": 1, "status": "Active", "team_leader_id": "U0003", "salary": 50000},
        {"user_id": "U0012", "name": "Julia Wilson", "employee_id": "EMP009", "role": "Data Scientist", "department": "Analytics", "skills": "Python, ML, TensorFlow, Pandas, NumPy", "experience": 5, "joining_date": "2019-09-30", "projects_completed": 16, "status": "Active", "team_leader_id": "U0003", "salary": 90000},
        {"user_id": "U0013", "name": "Kevin Anderson", "employee_id": "EMP010", "role": "Web Developer", "department": "Engineering", "skills": "PHP, Laravel, MySQL, Bootstrap", "experience": 2, "joining_date": "2022-04-18", "projects_completed": 5, "status": "Inactive", "team_leader_id": "U0003", "salary": 60000},
    ],
    "performance": [
        {"user_id": "U0004", "productivity_score": 88, "attendance_pct": 96, "task_completion": 90, "quality_rating": 9, "tl_score": 9, "monthly_trend": [80, 83, 85, 87, 88, 88], "satisfaction": 85},
        {"user_id": "U0005", "productivity_score": 75, "attendance_pct": 89, "task_completion": 78, "quality_rating": 7, "tl_score": 7, "monthly_trend": [70, 71, 73, 75, 74, 75], "satisfaction": 72},
        {"user_id": "U0006", "productivity_score": 82, "attendance_pct": 94, "task_completion": 85, "quality_rating": 8, "tl_score": 8, "monthly_trend": [75, 77, 80, 82, 81, 82], "satisfaction": 80},
        {"user_id": "U0007", "productivity_score": 71, "attendance_pct": 87, "task_completion": 72, "quality_rating": 7, "tl_score": 6, "monthly_trend": [68, 69, 70, 71, 70, 71], "satisfaction": 65},
        {"user_id": "U0008", "productivity_score": 65, "attendance_pct": 91, "task_completion": 68, "quality_rating": 6, "tl_score": 6, "monthly_trend": [60, 62, 63, 65, 64, 65], "satisfaction": 70},
        {"user_id": "U0009", "productivity_score": 92, "attendance_pct": 98, "task_completion": 95, "quality_rating": 9, "tl_score": 10, "monthly_trend": [88, 89, 90, 91, 92, 92], "satisfaction": 90},
        {"user_id": "U0010", "productivity_score": 84, "attendance_pct": 93, "task_completion": 86, "quality_rating": 8, "tl_score": 8, "monthly_trend": [78, 80, 82, 83, 84, 84], "satisfaction": 82},
        {"user_id": "U0011", "productivity_score": 58, "attendance_pct": 85, "task_completion": 60, "quality_rating": 6, "tl_score": 5, "monthly_trend": [50, 52, 55, 57, 58, 58], "satisfaction": 60},
        {"user_id": "U0012", "productivity_score": 90, "attendance_pct": 97, "task_completion": 92, "quality_rating": 9, "tl_score": 9, "monthly_trend": [85, 87, 88, 89, 90, 90], "satisfaction": 88},
        {"user_id": "U0013", "productivity_score": 55, "attendance_pct": 72, "task_completion": 50, "quality_rating": 5, "tl_score": 4, "monthly_trend": [60, 58, 57, 55, 53, 55], "satisfaction": 40},
    ],
    "tasks": [
        {"id": "T0001", "title": "Build REST API for Auth Module", "description": "Implement JWT-based authentication with refresh tokens", "priority": "High", "deadline": (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d'), "required_skills": ["Python", "Flask", "JWT"], "assigned_to": "U0004", "assigned_by": "U0003", "status": "In Progress", "progress": 60, "created_at": datetime.now().isoformat()},
        {"id": "T0002", "title": "Unit Testing for Payment Service", "description": "Write comprehensive unit tests for payment module", "priority": "Medium", "deadline": (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'), "required_skills": ["Java", "JUnit", "Mockito"], "assigned_to": "U0005", "assigned_by": "U0003", "status": "In Progress", "progress": 40, "created_at": datetime.now().isoformat()},
        {"id": "T0003", "title": "Selenium Test Suite for Dashboard", "description": "Automate regression testing for HR dashboard", "priority": "High", "deadline": (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d'), "required_skills": ["Selenium", "Python"], "assigned_to": "U0006", "assigned_by": "U0003", "status": "Pending", "progress": 0, "created_at": datetime.now().isoformat()},
        {"id": "T0004", "title": "Weekly Data Analysis Report", "description": "Generate analytics report for Q4 performance", "priority": "Low", "deadline": (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d'), "required_skills": ["Python", "Pandas", "SQL"], "assigned_to": "U0007", "assigned_by": "U0003", "status": "Pending", "progress": 20, "created_at": datetime.now().isoformat()},
        {"id": "T0005", "title": "Landing Page Redesign", "description": "Redesign company homepage with new brand guidelines", "priority": "Medium", "deadline": (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d'), "required_skills": ["HTML", "CSS", "JavaScript", "Vue.js"], "assigned_to": "U0008", "assigned_by": "U0003", "status": "In Progress", "progress": 30, "created_at": datetime.now().isoformat()},
        {"id": "T0006", "title": "CI/CD Pipeline Setup", "description": "Configure GitHub Actions for automated deployment", "priority": "High", "deadline": (datetime.now() + timedelta(days=4)).strftime('%Y-%m-%d'), "required_skills": ["Docker", "Kubernetes", "AWS"], "assigned_to": "U0009", "assigned_by": "U0003", "status": "Completed", "progress": 100, "created_at": datetime.now().isoformat()},
        {"id": "T0007", "title": "GraphQL API Integration", "description": "Migrate REST endpoints to GraphQL", "priority": "Medium", "deadline": (datetime.now() + timedelta(days=8)).strftime('%Y-%m-%d'), "required_skills": ["React", "GraphQL", "Node.js"], "assigned_to": "U0010", "assigned_by": "U0003", "status": "In Progress", "progress": 55, "created_at": datetime.now().isoformat()},
        {"id": "T0008", "title": "Fresher Training: Python Basics", "description": "Complete Python fundamentals module and submit exercises", "priority": "Medium", "deadline": (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'), "required_skills": ["Python"], "assigned_to": "U0011", "assigned_by": "U0003", "status": "In Progress", "progress": 25, "created_at": datetime.now().isoformat()},
        {"id": "T0009", "title": "ML Model for Customer Churn", "description": "Build and deploy customer churn prediction model", "priority": "High", "deadline": (datetime.now() + timedelta(days=12)).strftime('%Y-%m-%d'), "required_skills": ["Python", "ML", "TensorFlow"], "assigned_to": "U0012", "assigned_by": "U0003", "status": "In Progress", "progress": 70, "created_at": datetime.now().isoformat()},
    ],
    "attendance": [
        {"user_id": "U0004", "month": "January", "present": 22, "absent": 1, "late": 1, "total": 24, "hours": 176},
        {"user_id": "U0005", "month": "January", "present": 20, "absent": 3, "late": 1, "total": 24, "hours": 160},
        {"user_id": "U0006", "month": "January", "present": 23, "absent": 1, "late": 0, "total": 24, "hours": 184},
        {"user_id": "U0007", "month": "January", "present": 19, "absent": 4, "late": 1, "total": 24, "hours": 152},
        {"user_id": "U0008", "month": "January", "present": 21, "absent": 2, "late": 1, "total": 24, "hours": 168},
        {"user_id": "U0009", "month": "January", "present": 24, "absent": 0, "late": 0, "total": 24, "hours": 192},
        {"user_id": "U0010", "month": "January", "present": 22, "absent": 2, "late": 0, "total": 24, "hours": 176},
        {"user_id": "U0011", "month": "January", "present": 20, "absent": 3, "late": 1, "total": 24, "hours": 160},
        {"user_id": "U0012", "month": "January", "present": 23, "absent": 1, "late": 0, "total": 24, "hours": 184},
        {"user_id": "U0013", "month": "January", "present": 17, "absent": 7, "late": 0, "total": 24, "hours": 136},
    ],
    "notifications": [
        {"id": 1, "message": "Q4 Performance Reviews due next Friday", "type": "warning", "target": "all", "from": "HR Team", "time": datetime.now().isoformat()},
        {"id": 2, "message": "Team standup at 10 AM tomorrow", "type": "info", "target": "employee", "from": "David Chen", "time": datetime.now().isoformat()},
        {"id": 3, "message": "Alice Johnson is eligible for promotion!", "type": "success", "target": "hr", "from": "AI System", "time": datetime.now().isoformat()},
        {"id": 4, "message": "Kevin Anderson has high attrition risk", "type": "danger", "target": "hr", "from": "AI System", "time": datetime.now().isoformat()},
        {"id": 5, "message": "New training program: Advanced React - Register now", "type": "info", "target": "all", "from": "HR Team", "time": datetime.now().isoformat()},
    ],
    "weekly_updates": [],
    "login_logs": [],
    "system_activities": [],
    "leave_requests": [
        {"id": "LR001", "user_id": "U0004", "employee_name": "Alice Johnson", "department": "Engineering", "type": "Casual Leave", "from_date": "2026-03-12", "to_date": "2026-03-13", "days": 2, "reason": "Family function to attend — wedding of close relative.", "status": "Pending", "applied_on": "2026-03-07"},
        {"id": "LR002", "user_id": "U0005", "employee_name": "Bob Williams", "department": "Engineering", "type": "Sick Leave", "from_date": "2026-03-09", "to_date": "2026-03-09", "days": 1, "reason": "Severe headache and fever, visiting doctor.", "status": "Pending", "applied_on": "2026-03-08"},
        {"id": "LR003", "user_id": "U0007", "employee_name": "Eric Thompson", "department": "Analytics", "type": "Annual Leave", "from_date": "2026-03-18", "to_date": "2026-03-22", "days": 5, "reason": "Pre-planned vacation with family. Tickets already booked.", "status": "Approved", "applied_on": "2026-03-01"},
        {"id": "LR004", "user_id": "U0008", "employee_name": "Fiona Garcia", "department": "Engineering", "type": "Work From Home", "from_date": "2026-03-10", "to_date": "2026-03-10", "days": 1, "reason": "Home internet technician visit, need to be present at home.", "status": "Pending", "applied_on": "2026-03-08"},
        {"id": "LR005", "user_id": "U0010", "employee_name": "Hannah Brown", "department": "Engineering", "type": "Emergency Leave", "from_date": "2026-03-08", "to_date": "2026-03-09", "days": 2, "reason": "Medical emergency — parent hospitalised.", "status": "Approved", "applied_on": "2026-03-08"},
        {"id": "LR006", "user_id": "U0013", "employee_name": "Kevin Anderson", "department": "Engineering", "type": "Casual Leave", "from_date": "2026-03-15", "to_date": "2026-03-15", "days": 1, "reason": "Personal errand that cannot be rescheduled.", "status": "Rejected", "applied_on": "2026-03-05"}
    ],
    "teams": [
        {"id": "TM001", "name": "Alpha Squad", "description": "Core product engineering team", "leader_id": "U0003", "member_ids": ["U0004", "U0005", "U0010"], "project_name": "Customer Portal v2", "project_status": "In Progress", "project_completion": 68, "score": 87, "monthly_scores": [70, 74, 78, 82, 85, 87]},
        {"id": "TM002", "name": "Data Wizards", "description": "Analytics and data science team", "leader_id": "U0003", "member_ids": ["U0007", "U0012"], "project_name": "ML Churn Prediction", "project_status": "In Progress", "project_completion": 72, "score": 91, "monthly_scores": [80, 82, 85, 87, 89, 91]},
        {"id": "TM003", "name": "QA Ninjas", "description": "Quality assurance and testing team", "leader_id": "U0003", "member_ids": ["U0006"], "project_name": "Test Automation Suite", "project_status": "In Progress", "project_completion": 45, "score": 48, "monthly_scores": [60, 58, 55, 52, 50, 48]},
        {"id": "TM004", "name": "DevOps Heroes", "description": "Infrastructure and DevOps team", "leader_id": "U0003", "member_ids": ["U0009", "U0011"], "project_name": "CI/CD Pipeline Setup", "project_status": "At Risk", "project_completion": 22, "score": 42, "monthly_scores": [65, 60, 55, 50, 46, 42]}
    ],
    "training": [
        {"user_id": "U0008", "name": "Fiona Garcia", "week": 1, "hours": 8, "tech_learned": "Vue.js Composition API", "problems": "State management complexity", "completion": 85},
        {"user_id": "U0011", "name": "Ivan Martinez", "week": 1, "hours": 6, "tech_learned": "Python OOP concepts", "problems": "Understanding decorators", "completion": 60},
    ],
    "team_performance": [
        {"team_id": "TM001", "productivity_score": 85, "quality_score": 9, "completion_pct": 70, "recorded_at": (datetime.now() - timedelta(days=21)).isoformat()},
        {"team_id": "TM001", "productivity_score": 87, "quality_score": 8, "completion_pct": 75, "recorded_at": (datetime.now() - timedelta(days=14)).isoformat()},
        {"team_id": "TM001", "productivity_score": 88, "quality_score": 9, "completion_pct": 82, "recorded_at": datetime.now().isoformat()},
        {"team_id": "TM002", "productivity_score": 90, "quality_score": 9, "completion_pct": 85, "recorded_at": (datetime.now() - timedelta(days=14)).isoformat()},
        {"team_id": "TM002", "productivity_score": 92, "quality_score": 10, "completion_pct": 91, "recorded_at": datetime.now().isoformat()},
    ],
    "team_projects": [
        {"team_id": "TM001", "project_name": "Customer Portal v2", "status": "In Progress", "completion_pct": 68},
        {"team_id": "TM001", "project_name": "Internal Dashboard", "status": "In Progress", "completion_pct": 45},
        {"team_id": "TM002", "project_name": "ML Churn Prediction", "status": "In Progress", "completion_pct": 72},
    ],
    "tl_ratings": [
        {"employee_id": "U0004", "rating": 5, "feedback": "Excellent work on the Auth module, very secure implementation.", "rated_by": "U0003", "created_at": datetime.now().isoformat()},
        {"employee_id": "U0005", "rating": 4, "feedback": "Good progress on payment service unit tests.", "rated_by": "U0003", "created_at": datetime.now().isoformat()},
    ],
    "team_member_tasks": [
        {"team_id": "TM001", "user_id": "U0004", "tasks_completed": 12, "tasks_pending": 2},
        {"team_id": "TM001", "user_id": "U0005", "tasks_completed": 8, "tasks_pending": 3},
        {"team_id": "TM001", "user_id": "U0010", "tasks_completed": 15, "tasks_pending": 1},
    ],
    "integrations": {
        "email": {
            "enabled": False,
            "smtp_host": "",
            "smtp_port": 587,
            "smtp_user": "",
            "smtp_password": "",
            "from_email": "",
            "from_name": "",
            "use_tls": True
        },
        "slack": {
            "enabled": False,
            "webhook_url": "",
            "channel": "",
            "bot_name": ""
        },
        "calendar": {
            "enabled": False,
            "provider": "google",
            "api_key": "",
            "calendar_id": "",
            "ics_url": ""
        }
    }
}

def _ensure_integrations(db):
    if 'integrations' not in db:
        db['integrations'] = DEMO_DATA['integrations']
    return db['integrations']

def init_db(force=False):
    if os.path.exists(DB_FILE) and not force:
        print(f"ℹ️ Database already exists at {DB_FILE}. Skipping initialization.")
        return
        
    print(f"🚀 Initializing new database at {DB_FILE}...")
    
    # Hash passwords for DEMO_DATA users
    for user in DEMO_DATA['users']:
        if not user['password'].startswith('pbkdf2:sha256:'):
            user['password'] = generate_password_hash(user['password'])
        # Add 2FA fields
        user['two_factor_enabled'] = False
        user['two_factor_secret'] = None
        
    _atomic_write_json(DB_FILE, DEMO_DATA)
    print("✅ Database initialized with demo data")

def _atomic_write_json(path, data):
    backup = path + '.bak'
    try:
        if os.path.exists(path):
            try:
                os.replace(path, backup)
            except Exception:
                pass
        fd, tmp_path = tempfile.mkstemp(dir=os.path.dirname(path), prefix='data_', suffix='.tmp')
        try:
            with os.fdopen(fd, 'w') as tmpf:
                json.dump(data, tmpf, indent=2)
            os.replace(tmp_path, path)
        finally:
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass
    except Exception:
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

def _with_lock():
    start = time.time()
    while True:
        try:
            fd = os.open(LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_RDWR)
            return fd
        except (FileExistsError, PermissionError):
            if time.time() - start > 2.0:
                break
            time.sleep(0.05)
    # best effort: proceed without lock if contention persists
    return None

def _release_lock(fd):
    try:
        if fd is not None:
            os.close(fd)
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
    except Exception:
        pass


def get_db_data():
    if not os.path.exists(DB_FILE):
        init_db()
    fd = _with_lock()
    try:
        # retry read a few times in case a writer is replacing the file
        for _ in range(3):
            try:
                with open(DB_FILE, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                time.sleep(0.05)
        # fallback to backup if primary is corrupted
        backup = DB_FILE + '.bak'
        if os.path.exists(backup):
            with open(backup, 'r') as bf:
                return json.load(bf)
        # final fallback: reinitialize
        _atomic_write_json(DB_FILE, DEMO_DATA)
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    finally:
        _release_lock(fd)


def save_db_data(data):
    fd = _with_lock()
    try:
        _atomic_write_json(DB_FILE, data)
    finally:
        _release_lock(fd)

if __name__ == "__main__":
    init_db()
