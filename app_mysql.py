"""
app_mysql.py — PulseHR with full MySQL / SQLAlchemy backend
Run: python app_mysql.py
"""
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from functools import wraps
import json
import os, csv
from datetime import datetime, date
import os, csv

from config import Config
from database.models import (
    db, User, Employee, Performance, Task,
    Attendance, Notification, WeeklyUpdate, LoginLog, Training, AIPrediction
)
from database.export_mysql_to_json import export as export_mysql_json

# ─── App Factory ──────────────────────────────────────────────────────────────
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)


# ─── Auth Decorator ──────────────────────────────────────────────────────────
def login_required(roles=None):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'user_id' not in session:
                if request.is_json:
                    return jsonify({'error': 'Unauthorized', 'redirect': '/login'}), 401
                return redirect(url_for('login'))
            if roles and session.get('role') not in roles:
                return jsonify({'error': 'Forbidden'}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator


# ─── Helper: sequential ID generation ───────────────────────────────────────
def _next_id(prefix: str, model_class) -> str:
    """
    Generate the next sequential padded ID, e.g. 'U0014', 'T0010'.
    Parses the numeric suffix explicitly to avoid VARCHAR sort issues.
    """
    rows = db.session.query(model_class.id).all()
    nums = []
    for (rid,) in rows:
        try:
            nums.append(int(str(rid)[len(prefix):]))
        except (ValueError, IndexError):
            pass
    next_num = max(nums, default=0) + 1
    return f"{prefix}{next_num:04d}"


# ═══════════════════════════════════════════════════════
#  AUTH ROUTES
# ═══════════════════════════════════════════════════════
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for(f'{session["role"]}_dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if 'user_id' in session:
            return redirect(url_for(f'{session["role"]}_dashboard'))
        return render_template('login.html')

    data     = request.get_json(silent=True) or {}
    email    = data.get('email', '').lower().strip()
    password = data.get('password', '').strip()

    if not email or not password:
        return jsonify({'success': False, 'message': 'Email and password are required'}), 400

    user = User.query.filter_by(email=email, status='Active').first()

    # NOTE: In production use bcrypt.check_password_hash(user.password_hash, password)
    if user and user.password_hash == password:
        session.permanent = True
        session['user_id'] = user.id
        session['role']    = user.role
        session['name']    = user.name
        session['email']   = user.email

        user.last_login = datetime.utcnow()
        log = LoginLog(
            user_id=user.id, name=user.name,
            role=user.role, ip_address=request.remote_addr or '127.0.0.1'
        )
        db.session.add(log)
        db.session.commit()
        return jsonify({'success': True, 'role': user.role,
                        'redirect': f'/{user.role}-dashboard'})

    return jsonify({'success': False, 'message': 'Invalid email or password'}), 401


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ─── Dashboard Pages ─────────────────────────────────────────────────────────
@app.route('/employee-dashboard')
@login_required(roles=['employee'])
def employee_dashboard():
    return render_template('employee_dashboard.html', user=session)

@app.route('/teamleader-dashboard')
@login_required(roles=['teamleader'])
def teamleader_dashboard():
    return render_template('teamleader_dashboard.html', user=dict(session))

@app.route('/hr-dashboard')
@login_required(roles=['hr'])
def hr_dashboard():
    return render_template('hr_dashboard.html', user=dict(session))

@app.route('/admin-dashboard')
@login_required(roles=['admin'])
def admin_dashboard():
    return render_template('admin_dashboard.html', user=dict(session))


# ═══════════════════════════════════════════════════════
#  UNIVERSAL NOTIFICATIONS (all roles)
# ═══════════════════════════════════════════════════════
@app.route('/api/notifications')
@login_required(roles=['employee', 'teamleader', 'hr', 'admin'])
def get_notifications():
    from database.models import Notification
    role = session.get('role', 'employee')
    uid  = session.get('user_id', '')
    
    # Filter for target: all, role, or specific user_id
    notifs = Notification.query.filter(
        Notification.target.in_(['all', role, uid])
    ).order_by(Notification.created_at.desc()).limit(10).all()
    
    results = []
    unread_count = 0
    for n in notifs:
        d = n.to_dict()
        read_list = json.loads(n.read_by) if n.read_by else []
        if uid not in read_list:
            unread_count += 1
        results.append(d)
        
    return jsonify({
        'notifications': results,
        'unread_count': unread_count
    })

@app.route('/api/notifications/mark-read', methods=['POST'])
@login_required(roles=['employee', 'teamleader', 'hr', 'admin'])
def mark_notifications_read():
    from database.models import Notification
    role = session.get('role', 'employee')
    uid = session.get('user_id', '')
    
    # Mark all notifications targetting this user or their role as read
    notifs = Notification.query.filter(
        Notification.target.in_(['all', role, uid])
    ).all()
    
    for n in notifs:
        read_list = json.loads(n.read_by) if n.read_by else []
        if uid not in read_list:
            read_list.append(uid)
            n.read_by = json.dumps(read_list)
            
    db.session.commit()
    return jsonify({'success': True})


# ═══════════════════════════════════════════════════════
#  EMPLOYEE APIs
# ═══════════════════════════════════════════════════════
@app.route('/api/employee/profile')
@login_required(roles=['employee'])
def get_employee_profile():
    emp = Employee.query.filter_by(user_id=session['user_id']).first()
    return jsonify(emp.to_dict() if emp else {})


@app.route('/api/employee/tasks')
@login_required(roles=['employee'])
def get_employee_tasks():
    tasks = Task.query.filter_by(assigned_to=session['user_id']).all()
    return jsonify([t.to_dict() for t in tasks])


@app.route('/api/employee/update-task', methods=['POST'])
@login_required(roles=['employee'])
def update_task_status():
    data = request.get_json(silent=True) or {}
    if not data.get('task_id'):
        return jsonify({'success': False, 'message': 'task_id required'}), 400

    task = Task.query.filter_by(id=data['task_id'], assigned_to=session['user_id']).first()
    if task:
        task.status   = data.get('status', task.status)
        task.progress = int(data.get('progress', task.progress))
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Task not found or not assigned to you'}), 404


@app.route('/api/employee/weekly-update', methods=['POST'])
@login_required(roles=['employee'])
def submit_weekly_update():
    data = request.get_json(silent=True) or {}
    wu   = WeeklyUpdate(
        user_id=session['user_id'],
        project_work=data.get('project_work', ''),
        tech_learned=data.get('tech_learned', ''),
        problems=data.get('problems', ''),
        task_completion_level=int(data.get('task_completion', 0)),
        week_date=date.today()
    )
    db.session.add(wu)
    db.session.commit()
    return jsonify({'success': True})


@app.route('/api/employee/training-update', methods=['POST'])
@login_required(roles=['employee'])
def submit_training_update():
    data = request.get_json(silent=True) or {}
    emp = Employee.query.filter_by(user_id=session['user_id']).first()
    if not emp:
        return jsonify({'success': False, 'message': 'Employee record not found'}), 404
        
    training = Training(
        user_id=session['user_id'],
        week_number=data.get('week', 1),
        hours_completed=float(data.get('hours', 0)),
        tech_learned=data.get('tech_learned', ''),
        problems=data.get('problems', ''),
        completion_pct=int(data.get('completion', 0))
    )
    db.session.add(training)
    db.session.commit()
    return jsonify({'success': True})


@app.route('/api/employee/performance')
@login_required(roles=['employee'])
def get_employee_performance():
    perf = Performance.query.filter_by(user_id=session['user_id']).first()
    return jsonify(perf.to_dict() if perf else {})


@app.route('/api/employee/notifications')
@login_required(roles=['employee'])
def get_employee_notifications():
    uid    = session['user_id']
    notifs = Notification.query.filter(
        Notification.target.in_(['all', 'employee', uid])
    ).order_by(Notification.created_at.desc()).limit(10).all()
    return jsonify([n.to_dict() for n in notifs])


@app.route('/api/employee/apply-leave', methods=['POST'])
@login_required(roles=['employee'])
def apply_leave():
    from database.models import LeaveRequest
    data = request.get_json(silent=True) or {}
    uid = _next_id('L', LeaveRequest)
    emp = Employee.query.filter_by(user_id=session['user_id']).first()
    
    dt_from = None
    dt_to = None
    try:
        dt_from = datetime.strptime(data.get('from_date'), '%Y-%m-%d').date()
        dt_to = datetime.strptime(data.get('to_date'), '%Y-%m-%d').date()
    except: pass
    
    days = (dt_to - dt_from).days + 1 if (dt_from and dt_to and dt_to >= dt_from) else 1
    
    lr = LeaveRequest(
        id=uid,
        user_id=session['user_id'],
        employee_name=emp.name if emp else session.get('name', ''),
        department=emp.department if emp else '',
        type=data.get('type', 'Annual Leave'),
        from_date=dt_from,
        to_date=dt_to,
        days=days,
        reason=data.get('reason', ''),
        is_emergency=data.get('is_emergency', False),
        status='Pending',
        applied_on=date.today()
    )
    db.session.add(lr)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/employee/my-leaves')
@login_required(roles=['employee'])
def my_leaves():
    from database.models import LeaveRequest
    leaves = LeaveRequest.query.filter_by(user_id=session['user_id']).order_by(LeaveRequest.applied_on.desc()).all()
    return jsonify([l.to_dict() for l in leaves])

@app.route('/api/employee/my-team')
@login_required(roles=['employee'])
def my_team():
    uid = session['user_id']
    emp = Employee.query.filter_by(user_id=uid).first()
    if not emp:
        return jsonify({'team_name': 'No Team Assigned', 'members': [], 'project_name': 'N/A', 'project_completion': 0})
    
    # Try to find team via team_id
    team_obj = None
    if emp.team_id:
        team_obj = Team.query.get(emp.team_id)
    
    # If not found via team_id, try to find by leader_id
    if not team_obj and emp.team_leader_id:
        team_obj = Team.query.filter_by(leader_id=emp.team_leader_id).first()
        
    if not team_obj:
        return jsonify({'team_name': 'No Team Assigned', 'members': [], 'project_name': 'N/A', 'project_completion': 0})
        
    members = Employee.query.filter_by(team_id=team_obj.id).all()
    # If members list is empty, use team_leader_id peers as fallback
    if not members and team_obj.leader_id:
        members = Employee.query.filter_by(team_leader_id=team_obj.leader_id).all()
        
    # Ensure leader is included if not in members
    leader_emp = Employee.query.filter_by(user_id=team_obj.leader_id).first()
    
    safe_members = []
    member_ids = set([m.user_id for m in members])
    
    if leader_emp and leader_emp.user_id not in member_ids:
        members.insert(0, leader_emp)
        
    for m in members:
        safe_members.append({
            'user_id': m.user_id,
            'name': m.name,
            'role': m.role,
            'department': m.department,
            'skills': m.skills or '',
            'is_me': m.user_id == uid,
            'is_tl': m.user_id == team_obj.leader_id
        })
        
    return jsonify({
        'team_name': team_obj.name or 'Unnamed Team',
        'project_name': team_obj.project_name or 'No Active Project',
        'project_completion': team_obj.project_completion or 0,
        'members': safe_members
    })


# ═══════════════════════════════════════════════════════
#  TEAM LEADER APIs
# ═══════════════════════════════════════════════════════
@app.route('/api/tl/team')
@login_required(roles=['teamleader'])
def get_tl_team():
    team = Employee.query.filter_by(team_leader_id=session['user_id']).all()
    result = []
    for e in team:
        d = e.to_dict()
        perf = Performance.query.filter_by(user_id=e.user_id).first()
        active_tasks = Task.query.filter_by(assigned_to=e.user_id).filter(Task.status != 'Completed').count()
        if perf:
            d['productivity_score'] = perf.productivity_score
            d['task_completion'] = perf.task_completion
        d['active_tasks'] = active_tasks
        result.append(d)
    return jsonify(result)


@app.route('/api/tl/create-task', methods=['POST'])
@login_required(roles=['teamleader'])
def create_task():
    data = request.get_json(silent=True) or {}
    if not data.get('title'):
        return jsonify({'success': False, 'message': 'title is required'}), 400

    task_id = _next_id('T', Task)
    deadline_val = None
    if data.get('deadline'):
        try:
            deadline_val = datetime.strptime(data['deadline'], '%Y-%m-%d').date()
        except ValueError:
            pass

    task = Task(
        id=task_id,
        title=data['title'],
        description=data.get('description', ''),
        priority=data.get('priority', 'Medium'),
        deadline=deadline_val,
        required_skills=json.dumps(data.get('required_skills', [])),
        assigned_to=data.get('assigned_to') or None,
        assigned_by=session['user_id'],
        status='Pending',
        progress=0
    )
    db.session.add(task)
    db.session.commit()
    return jsonify({'success': True, 'task_id': task_id})


@app.route('/api/tl/tasks')
@login_required(roles=['teamleader'])
def get_tl_tasks():
    tasks = Task.query.filter_by(assigned_by=session['user_id']).all()
    return jsonify([t.to_dict() for t in tasks])


@app.route('/api/tl/ai-suggest-employee', methods=['POST'])
@login_required(roles=['teamleader'])
def ai_suggest_employee():
    data            = request.get_json(silent=True) or {}
    required_skills = data.get('required_skills', [])
    team            = Employee.query.filter_by(team_leader_id=session['user_id']).all()

    suggestions = []
    for emp in team:
        emp_skills = [s.strip().lower() for s in (emp.skills or '').split(',')]
        matched    = sum(1 for s in required_skills
                        if any(s.lower() in es for es in emp_skills))
        skill_pct  = int((matched / max(len(required_skills), 1)) * 100)
        perf         = Performance.query.filter_by(user_id=emp.user_id).first()
        active_tasks = Task.query.filter_by(assigned_to=emp.user_id)\
                            .filter(Task.status != 'Completed').count()
        perf_score   = perf.productivity_score if perf else 75
        suggestions.append({
            'user_id':             emp.user_id,
            'name':                emp.name,
            'skill_match':         skill_pct,
            'current_workload':    active_tasks,
            'performance_score':   perf_score,
            'recommendation_score':(skill_pct * 0.5
                                    + max(0, (5 - active_tasks) * 5)
                                    + perf_score * 0.2)
        })

    suggestions.sort(key=lambda x: x['recommendation_score'], reverse=True)
    return jsonify(suggestions[:3])


@app.route('/api/tl/update-score', methods=['POST'])
@login_required(roles=['teamleader'])
def update_tl_score():
    data = request.get_json(silent=True) or {}
    if not data.get('user_id'):
        return jsonify({'success': False, 'message': 'user_id required'}), 400

    perf = Performance.query.filter_by(user_id=data['user_id']).first()
    if perf:
        perf.tl_score = max(0.0, min(10.0, float(data.get('score', 7))))
        db.session.commit()
    return jsonify({'success': True})

@app.route('/api/tl/leave-requests')
@login_required(roles=['teamleader'])
def get_tl_leaves():
    from database.models import LeaveRequest
    # Get employees in TL's team
    team_members = [e.user_id for e in Employee.query.filter_by(team_leader_id=session['user_id']).all()]
    if not team_members: return jsonify([])
    leaves = LeaveRequest.query.filter(LeaveRequest.user_id.in_(team_members)).order_by(LeaveRequest.applied_on.desc()).all()
    return jsonify([l.to_dict() for l in leaves])

@app.route('/api/tl/leave-approve', methods=['POST'])
@login_required(roles=['teamleader'])
def tl_leave_approve():
    from database.models import LeaveRequest
    data = request.get_json(silent=True) or {}
    lr = LeaveRequest.query.get(data.get('request_id'))
    if lr:
        lr.status = 'Approved (TL)'
        lr.reviewed_by = session.get('name')
        lr.reviewed_at = datetime.utcnow()
        db.session.commit()
    return jsonify({'success': True})

@app.route('/api/tl/leave-reject', methods=['POST'])
@login_required(roles=['teamleader'])
def tl_leave_reject():
    from database.models import LeaveRequest
    data = request.get_json(silent=True) or {}
    lr = LeaveRequest.query.get(data.get('request_id'))
    if lr:
        lr.status = 'Rejected (TL)'
        lr.reviewed_by = session.get('name')
        lr.reviewed_at = datetime.utcnow()
        db.session.commit()
    return jsonify({'success': True})


# ═══════════════════════════════════════════════════════
#  HR APIs
# ═══════════════════════════════════════════════════════
@app.route('/api/hr/teams')
@login_required(roles=['hr'])
def hr_get_teams():
    from database.models import Team
    teams = Team.query.all()
    result = []
    for t in teams:
        d = t.to_dict()
        ldr = User.query.get(t.leader_id) if t.leader_id else None
        d['leader_name'] = ldr.name if ldr else 'Unassigned'
        members = Employee.query.filter_by(team_id=t.id).all()
        d['member_ids'] = [m.user_id for m in members]
        d['team_members'] = [m.name for m in members]
        
        # calculate avg score
        if members:
            scores = []
            for m in members:
                p = Performance.query.filter_by(user_id=m.user_id).first()
                if p: scores.append(p.productivity_score)
            d['avg_member_score'] = sum(scores) // len(scores) if scores else 0
        else:
            d['avg_member_score'] = 0
            
        result.append(d)
    return jsonify(result)

@app.route('/api/hr/teams/create', methods=['POST'])
@login_required(roles=['hr'])
def hr_create_team():
    from database.models import Team
    data = request.get_json(silent=True) or {}
    tid = _next_id('TM', Team)
    leader_id = data.get('leader_id')
    t = Team(id=tid, name=data.get('name',''), description=data.get('description',''), leader_id=leader_id)
    db.session.add(t)
    db.session.commit()
    # Assign initial members if provided
    member_ids = data.get('member_ids') or data.get('members', [])
    if member_ids:
        Employee.query.filter(Employee.user_id.in_(member_ids)).update({
            'team_id': tid,
            'team_leader_id': leader_id or None
        })
        db.session.commit()
    return jsonify({'success': True, 'id': tid})

@app.route('/api/hr/teams/assign-members', methods=['POST'])
@login_required(roles=['hr'])
def hr_assign_team_members():
    from database.models import Team
    data = request.get_json(silent=True) or {}
    tid = data.get('team_id')
    # Support both 'members' and 'member_ids' from frontend
    member_ids = data.get('member_ids') or data.get('members', [])
    if not tid: return jsonify({'success': False})
    
    # Get team to find its leader
    t = Team.query.get(tid)
    lid = t.leader_id if t else None
    
    # Reset existing members
    Employee.query.filter_by(team_id=tid).update({'team_id': None})
    # Set new members
    if member_ids:
        Employee.query.filter(Employee.user_id.in_(member_ids)).update({
            'team_id': tid,
            'team_leader_id': lid # Maintain consistency
        })
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/hr/teams/assign-leader', methods=['POST'])
@login_required(roles=['hr'])
def hr_assign_team_leader():
    from database.models import Team
    data = request.get_json(silent=True) or {}
    tid = data.get('team_id')
    lid = data.get('leader_id')
    if not tid: return jsonify({'success': False})
    
    t = Team.query.get(tid)
    if t:
        t.leader_id = lid
        db.session.commit()
        # Also update team_leader_id on current members for consistency
        if lid:
            Employee.query.filter_by(team_id=tid).update({'team_leader_id': lid})
            db.session.commit()
    return jsonify({'success': True})

@app.route('/api/hr/unallocated-members')
@login_required(roles=['hr', 'admin'])
def get_unallocated_members():
    from database.models import Employee, Team
    # Get all allocated IDs from all teams
    allocated_ids = set()
    teams = Team.query.all()
    for t in teams:
        if t.leader_id: allocated_ids.add(t.leader_id)
        for m in t.members:
            allocated_ids.add(m.user_id)
            
    # Filter out active employees who are not in the allocated_ids set, and whose system role is NOT HR
    from database.models import User
    unallocated = Employee.query.join(User, Employee.user_id == User.id).filter(
        Employee.status == 'Active', 
        ~Employee.user_id.in_(list(allocated_ids) if allocated_ids else ['']),
        User.role != 'hr'
    ).all()
    return jsonify([e.to_dict() for e in unallocated])

@app.route('/api/hr/teams/delete', methods=['POST'])
@login_required(roles=['hr', 'admin'])
def delete_team_mysql():
    from database.models import Team, Employee, TeamPerformance, TeamProject
    data = request.get_json(silent=True) or {}
    tid = data.get('team_id')
    if not tid:
        return jsonify({'success': False, 'message': 'team_id required'}), 400
        
    t = Team.query.get(tid)
    if not t:
        return jsonify({'success': False, 'message': 'Team not found'}), 404
        
    # Reset members
    Employee.query.filter_by(team_id=tid).update({'team_id': None, 'team_leader_id': None})
    
    # Cleanup performance and projects
    TeamPerformance.query.filter_by(team_id=tid).delete()
    TeamProject.query.filter_by(team_id=tid).delete()
    
    db.session.delete(t)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/hr/teams/assign-project', methods=['POST'])
@login_required(roles=['hr'])
def hr_assign_team_project():
    from database.models import Team
    data = request.get_json(silent=True) or {}
    tid = data.get('team_id')
    name = data.get('project_name')
    status = data.get('project_status')
    pct = data.get('project_completion')
    
    query = Team.query if tid == 'all' else Team.query.filter_by(id=tid)
    for t in query.all():
        if name is not None: t.project_name = name
        if status is not None: t.project_status = status
        if pct is not None: t.project_completion = int(pct)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/hr/teams/set-score', methods=['POST'])
@login_required(roles=['hr'])
def hr_set_team_score():
    from database.models import Team
    data = request.get_json(silent=True) or {}
    tid = data.get('team_id')
    score = data.get('score')
    
    t = Team.query.get(tid)
    if t and score is not None:
        t.score = int(score)
        history = json.loads(t.monthly_scores) if t.monthly_scores else []
        history.append(int(score))
        if len(history) > 6: history.pop(0)
        t.monthly_scores = json.dumps(history)
        db.session.commit()
    return jsonify({'success': True})

@app.route('/api/hr/leave-requests')
@login_required(roles=['hr'])
def hr_get_leaves():
    from database.models import LeaveRequest
    leaves = LeaveRequest.query.order_by(LeaveRequest.applied_on.desc()).all()
    return jsonify([l.to_dict() for l in leaves])

@app.route('/api/hr/leave-approve', methods=['POST'])
@login_required(roles=['hr'])
def hr_leave_approve():
    from database.models import LeaveRequest
    data = request.get_json(silent=True) or {}
    lr = LeaveRequest.query.get(data.get('request_id'))
    if lr:
        lr.status = 'Approved (HR)'
        lr.reviewed_by = session.get('name')
        lr.reviewed_at = datetime.utcnow()
        db.session.commit()
    return jsonify({'success': True})

@app.route('/api/hr/leave-reject', methods=['POST'])
@login_required(roles=['hr'])
def hr_leave_reject():
    from database.models import LeaveRequest
    data = request.get_json(silent=True) or {}
    lr = LeaveRequest.query.get(data.get('request_id'))
    if lr:
        lr.status = 'Rejected (HR)'
        lr.reviewed_by = session.get('name')
        lr.reviewed_at = datetime.utcnow()
        db.session.commit()
    return jsonify({'success': True})

@app.route('/api/hr/employees')
@login_required(roles=['hr'])
def get_all_employees():
    employees = Employee.query.all()
    return jsonify([e.to_dict() for e in employees])


@app.route('/api/hr/attendance')
@login_required(roles=['hr'])
def get_attendance():
    from sqlalchemy import func
    rows = db.session.query(
        Attendance.user_id,
        func.sum(db.case((Attendance.status == 'Present', 1), else_=0)).label('present'),
        func.sum(db.case((Attendance.status == 'Absent',  1), else_=0)).label('absent'),
        func.sum(db.case((Attendance.status == 'Late',    1), else_=0)).label('late'),
        func.sum(Attendance.hours_worked).label('hours'),
        func.count().label('total')
    ).group_by(Attendance.user_id).all()

    return jsonify([{
        'user_id': r.user_id, 'month': 'January',
        'present': int(r.present or 0), 'absent': int(r.absent or 0),
        'late':    int(r.late or 0),    'total':  int(r.total or 0),
        'hours':   round(float(r.hours or 0), 1)
    } for r in rows])


@app.route('/api/hr/performance-all')
@login_required(roles=['hr'])
def get_all_performance():
    rows   = Performance.query.all()
    result = []
    for p in rows:
        d   = p.to_dict()
        emp = Employee.query.filter_by(user_id=p.user_id).first()
        if emp:
            d.update({'name': emp.name, 'department': emp.department, 'role': emp.role})
        result.append(d)
    return jsonify(result)


@app.route('/api/hr/stats')
@login_required(roles=['hr'])
def hr_stats():
    emps   = Employee.query.all()
    active = sum(1 for e in emps if e.status == 'Active')
    dept_dist: dict = {}
    for e in emps:
        dept_dist[e.department] = dept_dist.get(e.department, 0) + 1

    perfs = Performance.query.all()
    avg_p = round(sum(p.productivity_score for p in perfs) / max(len(perfs), 1), 1)
    return jsonify({
        'total_employees': len(emps), 'active': active,
        'inactive': len(emps) - active, 'departments': dept_dist,
        'avg_performance': avg_p
    })


@app.route('/api/hr/ai-predict-performance', methods=['POST'])
@login_required(roles=['hr'])
def predict_performance():
    from ml_models.predictor import predict_performance_score
    data   = request.get_json(silent=True) or {}
    result = predict_performance_score(data)
    _log_prediction('performance', data, result)
    return jsonify(result)


@app.route('/api/hr/ai-promotion', methods=['POST'])
@login_required(roles=['hr'])
def promotion_recommendation():
    from ml_models.predictor import recommend_promotion
    data   = request.get_json(silent=True) or {}
    result = recommend_promotion(data)
    _log_prediction('promotion', data, result)
    return jsonify(result)


@app.route('/api/hr/ai-attrition', methods=['POST'])
@login_required(roles=['hr'])
def attrition_risk():
    from ml_models.predictor import predict_attrition
    data   = request.get_json(silent=True) or {}
    result = predict_attrition(data)
    _log_prediction('attrition', data, result)
    return jsonify(result)


@app.route('/api/hr/skill-gap', methods=['POST'])
@login_required(roles=['hr'])
def skill_gap():
    from ml_models.predictor import analyze_skill_gap
    data   = request.get_json(silent=True) or {}
    result = analyze_skill_gap(data)
    return jsonify(result)


@app.route('/api/hr/ats-analyze', methods=['POST'])
@login_required(roles=['hr'])
def ats_analyze():
    from ml_models.predictor import analyze_ats
    data   = request.get_json(silent=True) or {}
    result = analyze_ats(data.get('resume_text', ''))
    return jsonify(result)


@app.route('/api/hr/send-notification', methods=['POST'])
@login_required(roles=['hr'])
def send_notification():
    data = request.get_json(silent=True) or {}
    if not data.get('message'):
        return jsonify({'success': False, 'message': 'message is required'}), 400

    notif = Notification(
        message=data['message'],
        type=data.get('type', 'info'),
        target=data.get('target', 'all'),
        sent_by=session['user_id'],
        read_by=json.dumps([])
    )
    db.session.add(notif)
    db.session.commit()
    return jsonify({'success': True})


@app.route('/api/hr/report/<report_type>')
@login_required(roles=['hr'])
def generate_report(report_type):
    allowed = {'performance', 'attendance', 'promotion', 'attrition', 'salary'}
    if report_type not in allowed:
        return jsonify({'error': 'Invalid report type'}), 400

    from utils.report_gen_mysql import generate_csv_report
    from io import BytesIO
    csv_data = generate_csv_report(report_type)
    output   = BytesIO(csv_data.encode('utf-8'))
    output.seek(0)
    return send_file(output, mimetype='text/csv', as_attachment=True,
                     download_name=f'{report_type}_report.csv')


def _log_prediction(pred_type: str, input_data: dict, result_data: dict):
    try:
        pred = AIPrediction(
            user_id=session.get('user_id'),
            prediction_type=pred_type,
            input_data=input_data,
            result_data=result_data,
            confidence=result_data.get('confidence', 0)
        )
        db.session.add(pred)
        db.session.commit()
    except Exception:
        db.session.rollback()


# ═══════════════════════════════════════════════════════
#  ADMIN APIs
# ═══════════════════════════════════════════════════════
@app.route('/api/admin/users')
@login_required(roles=['admin'])
def get_all_users():
    users = User.query.all()
    return jsonify([u.to_dict() for u in users])


@app.route('/api/admin/create-user', methods=['POST'])
@login_required(roles=['admin'])
def create_user():
    data = request.get_json(silent=True) or {}
    if not data.get('name') or not data.get('email'):
        return jsonify({'success': False, 'message': 'name and email are required'}), 400

    if User.query.filter_by(email=data['email'].lower()).first():
        return jsonify({'success': False, 'message': 'Email already exists'}), 409

    uid  = _next_id('U', User)
    user = User(
        id=uid, name=data['name'],
        email=data['email'].lower().strip(),
        password_hash=data.get('password', 'password123'),
        role=data.get('role', 'employee'), status='Active'
    )
    db.session.add(user)
    db.session.flush()

    if data.get('role', 'employee') != 'admin':
        # Determine employee_id format: TL### for teamleaders, EMP#### for others
        role = data.get('role', 'employee')
        emp_id = None
        if role == 'teamleader':
            existing = Employee.query.filter(Employee.employee_id.like('TL%')).all()
            nums = [int(e.employee_id[2:]) for e in existing if e.employee_id[2:].isdigit()]
            next_num = (max(nums) + 1) if nums else 1
            emp_id = f"TL{next_num:03d}"
        elif role == 'hr':
            existing = Employee.query.filter(Employee.employee_id.like('HR%')).all()
            nums = [int(e.employee_id[2:]) for e in existing if e.employee_id[2:].isdigit()]
            next_num = (max(nums) + 1) if nums else 1
            emp_id = f"HR{next_num:03d}"
        else:
            emp_id = f"EMP{uid[1:]}"
        emp = Employee(
            user_id=uid, employee_id=emp_id,
            name=data['name'],
            role=data.get('job_role', data.get('role', 'employee').capitalize()),
            department=data.get('department', 'Engineering'),
            skills=data.get('skills', ''),
            experience=int(data.get('experience', 0)),
            joining_date=date.today(),
            projects_completed=0, status='Active',
            team_leader_id=data.get('team_leader_id') or None,
            salary=float(data.get('salary', 0))
        )
        perf = Performance(
            user_id=uid, productivity_score=70, attendance_pct=90,
            task_completion=75, quality_rating=7, tl_score=7,
            satisfaction=75,
            monthly_trend=json.dumps([65, 68, 70, 72, 70]),
            month='January', year=date.today().year
        )
        db.session.add(emp)
        db.session.add(perf)

    db.session.commit()

    try:
        export_mysql_json()
    except Exception as e:
        print(f"WARN: seed snapshot export failed after create-user: {e}")

    # Append to CSV dataset for analytics/training (non-admin roles)
    if data.get('role', 'employee') != 'admin':
        csv_path = os.path.join(os.path.dirname(__file__), 'database', 'sample_dataset.csv')
        header = ['employee_id','name','department','role','experience_years','productivity_score','attendance_pct','task_completion','quality_rating','tl_score','projects_completed','satisfaction','salary','status']
        row = [
            emp_id,
            data['name'],
            data.get('department','Engineering'),
            data.get('job_role', role.capitalize()),
            int(data.get('experience',0)),
            70, 90, 75, 7, 7,
            0, 75,
            float(data.get('salary',0)),
            'Active'
        ]
        try:
            file_exists = os.path.exists(csv_path)
            # Ensure folder exists
            os.makedirs(os.path.dirname(csv_path), exist_ok=True)
            with open(csv_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(header)
                writer.writerow(row)
        except Exception as e:
            # Non-fatal: continue without blocking user creation
            print(f"WARN: Could not append to sample_dataset.csv: {e}")

    return jsonify({'success': True, 'user_id': uid})


@app.route('/api/admin/toggle-user', methods=['POST'])
@login_required(roles=['admin'])
def toggle_user():
    data = request.get_json(silent=True) or {}
    uid  = data.get('user_id')
    if not uid:
        return jsonify({'success': False, 'message': 'user_id required'}), 400

    user = User.query.get(uid)
    if user:
        user.status = 'Inactive' if user.status == 'Active' else 'Active'
        if user.employee:
            user.employee.status = user.status
        db.session.commit()
        try:
            export_mysql_json()
        except Exception as e:
            print(f"WARN: seed snapshot export failed after toggle-user: {e}")
    return jsonify({'success': True})


@app.route('/api/admin/delete-user', methods=['POST'])
@login_required(roles=['admin'])
def delete_user():
    data = request.get_json(silent=True) or {}
    uid  = data.get('user_id')
    if not uid:
        return jsonify({'success': False, 'message': 'user_id required'}), 400
    if uid == session.get('user_id'):
        return jsonify({'success': False, 'message': 'Cannot delete your own account'}), 403

    user = User.query.get(uid)
    if user:
        db.session.delete(user)
        db.session.commit()
        try:
            export_mysql_json()
        except Exception as e:
            print(f"WARN: seed snapshot export failed after delete-user: {e}")
    return jsonify({'success': True})


@app.route('/api/admin/reset-password', methods=['POST'])
@login_required(roles=['admin'])
def reset_password():
    data     = request.get_json(silent=True) or {}
    uid      = data.get('user_id')
    new_pass = data.get('new_password', '').strip()
    if not uid or not new_pass:
        return jsonify({'success': False, 'message': 'user_id and new_password required'}), 400
    if len(new_pass) < 6:
        return jsonify({'success': False, 'message': 'Password must be at least 6 characters'}), 400

    user = User.query.get(uid)
    if user:
        user.password_hash = new_pass
        db.session.commit()
        try:
            export_mysql_json()
        except Exception as e:
            print(f"WARN: seed snapshot export failed after reset-password: {e}")
    return jsonify({'success': True})


@app.route('/api/admin/login-logs')
@login_required(roles=['admin'])
def get_login_logs():
    logs = LoginLog.query.order_by(LoginLog.login_time.desc()).limit(50).all()
    return jsonify([l.to_dict() for l in logs])


@app.route('/api/admin/system-stats')
@login_required(roles=['admin'])
def system_stats():
    return jsonify({
        'total_users':      User.query.count(),
        'total_employees':  Employee.query.count(),
        'total_tasks':      Task.query.count(),
        'login_logs_count': LoginLog.query.count(),
        'server_status':    'Online',
        'db_engine':        'MySQL'
    })


# ─── New Team Performance & Rating Routes ───────────────────────────────────
@app.route('/api/tl/rate-employee', methods=['POST'])
@login_required(roles=['teamleader'])
def tl_rate_employee():
    from database.models import TLRating
    data = request.get_json(silent=True) or {}
    eid = data.get('employee_id')
    rating = data.get('rating', 0)
    feedback = data.get('feedback', '')
    
    if not eid:
        return jsonify({'success': False, 'message': 'employee_id required'}), 400
        
    rat = TLRating(
        employee_id=eid,
        tl_id=session['user_id'],
        rating=int(rating),
        feedback=feedback
    )
    db.session.add(rat)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/hr/team-performance')
@login_required(roles=['hr', 'admin'])
def get_all_team_performance():
    from database.models import TeamPerformance
    perfs = TeamPerformance.query.all()
    return jsonify([p.to_dict() for p in perfs])

@app.route('/api/hr/team-projects')
@login_required(roles=['hr', 'admin'])
def get_all_team_projects():
    from database.models import TeamProject
    projs = TeamProject.query.all()
    return jsonify([p.to_dict() for p in projs])


@app.route('/api/hr/teams-detailed')
@login_required(roles=['hr', 'admin'])
def get_teams_detailed():
    from database.models import Team, TeamPerformance, TeamProject, Performance
    teams = Team.query.all()
    results = []
    for t in teams:
        perf = TeamPerformance.query.filter_by(team_id=t.id).order_by(TeamPerformance.recorded_at.desc()).all()
        projs = TeamProject.query.filter_by(team_id=t.id).all()
        
        member_list = []
        for m in t.members:
            p = Performance.query.filter_by(user_id=m.user_id).first()
            member_list.append({
                'user_id': m.user_id,
                'name': m.name,
                'role': m.role,
                'productivity_score': p.productivity_score if p else 0,
                'quality_rating': p.quality_rating if p else 0
            })
            
        results.append({
            'id': t.id,
            'name': t.name,
            'description': t.description or '',
            'leader_id': t.leader_id,
            'member_ids': [m.user_id for m in t.members],
            'project_name': projs[0].project_name if projs else 'No Active Project',
            'project_status': projs[0].status if projs else 'N/A',
            'project_completion': projs[0].completion_pct if projs else 0,
            'score': t.score or 0,
            'leader_name': t.leader.name if t.leader else "Unassigned",
            'department': t.leader.department if t.leader else "N/A",
            'members': member_list,
            'performance_history': [p.productivity_score for p in perf[:6]],
            'projects': [{'name': p.project_name, 'status': p.status, 'completion': p.completion_pct} for p in projs],
            'latest_performance': perf[0].to_dict() if perf else None
        })
    return jsonify(results)

@app.route('/api/tl/team-task-stats')
@login_required(roles=['teamleader'])
def get_team_task_stats():
    from database.models import Team, TeamMemberTask, Employee
    t = Team.query.filter_by(leader_id=session['user_id']).first()
    if not t: return jsonify([])
    
    stats = db.session.query(TeamMemberTask, Employee.name).\
            join(Employee, TeamMemberTask.user_id == Employee.user_id).\
            filter(TeamMemberTask.team_id == t.id).all()
            
    results = []
    for s, name in stats:
        d = s.to_dict()
        d['name'] = name
        results.append(d)
    return jsonify(results)

# ─── Entry Point ─────────────────────────────────────────────────────────────
if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all()
            print("✅ DB connection OK")
        except Exception as e:
            print("❌ DB connection failed")
            print(f"URI: {Config.SQLALCHEMY_DATABASE_URI}")
            print(f"Host: {Config.MYSQL_HOST} Port: {Config.MYSQL_PORT}")
            print(f"User: {Config.MYSQL_USER} DB: {Config.MYSQL_DB}")
            print(f"Error: {e}")
            raise
    print("✅ PulseHR (MySQL) started — http://localhost:5000")
    app.run(debug=Config.DEBUG, host='0.0.0.0', port=5000)
