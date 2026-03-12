import os, json, csv, re
from datetime import datetime

DATA_DIR = os.path.dirname(__file__)
CSV_PATH = os.path.join(DATA_DIR, 'sample_dataset.csv')
JSON_PATH = os.path.join(DATA_DIR, 'data.json')

def slug_email(name):
    base = re.sub(r'[^a-z0-9]+', '.', name.strip().lower())
    base = re.sub(r'\.+', '.', base).strip('.')
    return f"{base or 'user'}@company.com"

def next_user_id(existing):
    ids = [int(u['id'][1:]) for u in existing if isinstance(u.get('id'), str) and u['id'].startswith('U') and u['id'][1:].isdigit()]
    n = (max(ids) + 1) if ids else 1
    return f"U{n:04d}"

def load_json():
    if os.path.exists(JSON_PATH):
        with open(JSON_PATH, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except Exception:
                pass
    # minimal structure
    return {
        "users": [],
        "employees": [],
        "performance": [],
        "tasks": [],
        "attendance": [],
        "notifications": [],
        "weekly_updates": [],
        "login_logs": [],
        "leave_requests": [],
        "teams": [],
        "training": [],
        "team_performance": [],
        "team_projects": [],
        "tl_ratings": [],
        "team_member_tasks": []
    }

def save_json(data):
    # backup
    try:
        if os.path.exists(JSON_PATH):
            os.replace(JSON_PATH, JSON_PATH + '.bak')
    except Exception:
        pass
    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def role_from_text(role_text):
    rt = (role_text or '').lower()
    if 'lead' in rt or 'leader' in rt or rt.startswith('tl'):
        return 'teamleader'
    if rt == 'hr' or 'human' in rt:
        return 'hr'
    return 'employee'

def build_ids(existing_emps, role, fallback_uid):
    # employee_id prefixes
    if role == 'teamleader':
        prefix = 'TL'
    elif role == 'hr':
        prefix = 'HR'
    else:
        prefix = 'EMP'
    if prefix == 'EMP':
        return f"EMP{fallback_uid[1:]}"
    nums = [int(e['employee_id'][2:]) for e in existing_emps
            if isinstance(e.get('employee_id'), str)
            and e['employee_id'].startswith(prefix)
            and e['employee_id'][2:].isdigit()]
    next_num = (max(nums) + 1) if nums else 1
    return f"{prefix}{next_num:03d}"

def convert():
    data = load_json()
    existing_users = data.get('users', [])
    existing_emps  = data.get('employees', [])
    existing_perf  = data.get('performance', [])
    # index sets for dedupe
    emp_ids = {e.get('employee_id') for e in existing_emps}
    user_emails = {u.get('email') for u in existing_users}

    if not os.path.exists(CSV_PATH):
        print(f"CSV not found at {CSV_PATH}")
        return

    added_emp = 0
    added_perf = 0
    added_user = 0

    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # read fields
            employee_id = row.get('employee_id') or ''
            name        = row.get('name') or 'Unknown'
            department  = row.get('department') or 'Engineering'
            role_text   = row.get('role') or ''
            role        = role_from_text(role_text)
            exp         = int(row.get('experience_years') or 0)
            prod        = int(row.get('productivity_score') or 0)
            attend      = int(row.get('attendance_pct') or 0)
            taskc       = int(row.get('task_completion') or 0)
            quality     = int(row.get('quality_rating') or 0)
            tls         = int(row.get('tl_score') or 0)
            projs       = int(row.get('projects_completed') or 0)
            satisfaction= int(row.get('satisfaction') or 75)
            salary      = float(row.get('salary') or 0)
            status      = row.get('status') or 'Active'

            # create user
            email = slug_email(name)
            if email in user_emails:
                uid = next(u['id'] for u in existing_users if u['email'] == email)
            else:
                uid = next_user_id(existing_users)
                user_emails.add(email)
                existing_users.append({
                    "id": uid,
                    "name": name,
                    "email": email,
                    "password": "password123",
                    "role": role,
                    "status": "Active",
                    "created_at": datetime.now().isoformat()
                })
                added_user += 1

            # employee_id
            if not employee_id or employee_id in emp_ids:
                employee_id = build_ids(existing_emps, role, uid)
            if employee_id in emp_ids:
                # skip duplicate employee entry
                continue
            emp_ids.add(employee_id)
            existing_emps.append({
                "user_id": uid,
                "name": name,
                "employee_id": employee_id,
                "role": role_text or (role.capitalize()),
                "department": department,
                "skills": "",
                "experience": exp,
                "joining_date": datetime.now().strftime('%Y-%m-%d'),
                "projects_completed": projs,
                "status": status,
                "team_leader_id": None,
                "salary": salary
            })
            added_emp += 1

            existing_perf.append({
                "user_id": uid,
                "name": name,
                "productivity_score": prod,
                "attendance_pct": attend,
                "task_completion": taskc,
                "quality_rating": quality,
                "tl_score": tls,
                "satisfaction": satisfaction,
                "monthly_trend": [prod] * 6
            })
            added_perf += 1

    data['users']      = existing_users
    data['employees']  = existing_emps
    data['performance']= existing_perf
    save_json(data)
    print(f"✅ Conversion completed: +users={added_user}, +employees={added_emp}, +performance={added_perf}")
    print(f"→ Wrote {JSON_PATH}")

if __name__ == '__main__':
    convert()
