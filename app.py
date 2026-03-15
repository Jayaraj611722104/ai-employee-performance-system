"""
app.py — PulseHR Main Flask Application (JSON/File-based demo mode)
Run: python app.py
"""
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from functools import wraps
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import pyotp
import qrcode
import base64
from io import BytesIO
import json
import os
import io
import csv
import PyPDF2
import docx
from datetime import datetime, timedelta
import smtplib
from email.message import EmailMessage
import urllib.request
import urllib.error
import sys
import os

# Add AI Module to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'ai_module'))
from backend.ai_service import ai_service

app = Flask(__name__)
UPLOAD_FOLDER_ATS = os.path.join(app.root_path, 'uploads', 'ats_resumes')
UPLOAD_FOLDER_CERT = os.path.join(app.root_path, 'uploads', 'certificates')
os.makedirs(UPLOAD_FOLDER_ATS, exist_ok=True)
os.makedirs(UPLOAD_FOLDER_CERT, exist_ok=True)

app.secret_key = os.environ.get('SECRET_KEY', 'pulsehr_secret_key_2024_change_in_production')

from database.db_init import get_db_data, save_db_data, init_db
print("ℹ️ Using Local JSON Database")

# Log server startup
try:
    log_system_activity("System initialized/restarted")
except Exception:
    pass

def _next_user_id(db):
    """Generate next user ID safely (collision-free after deletions)."""
    if not db['users']:
        return 'U0001'
    nums = []
    for u in db['users']:
        try:
            nums.append(int(u['id'][1:]))
        except (ValueError, IndexError):
            pass
    return f"U{(max(nums) + 1):04d}" if nums else 'U0001'


def _next_task_id(db):
    """Generate next task ID safely (collision-free after deletions)."""
    if not db['tasks']:
        return 'T0001'
    nums = []
    for t in db['tasks']:
        try:
            nums.append(int(t['id'][1:]))
        except (ValueError, IndexError):
            pass
    return f"T{(max(nums) + 1):04d}" if nums else 'T0001'

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

import sys

def log_system_activity(message, db=None):
    """Log activity to terminal and database permanently."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] ACTIVITY: {message}"
    
    # 1. Print to terminal
    print(log_entry, flush=True)
    
    # 2. Append to activity.log file
    try:
        with open('activity.log', 'a') as f:
            f.write(log_entry + '\n')
    except Exception:
        pass
    
    # 3. Save to database
    # If db not provided, try to get it
    _db = db
    if _db is None:
        try:
            from database.db_init import get_db_data
            _db = get_db_data()
        except Exception:
            return

    if 'system_activities' not in _db:
        _db['system_activities'] = []
    
    _db['system_activities'].append({
        'time': datetime.now().isoformat(),
        'message': message,
        'ip': request.remote_addr if request else '127.0.0.1'
    })
    
    save_db_data(_db)

# ═══════════════════════════════════════════════════════
#  ERROR HANDLERS
# ═══════════════════════════════════════════════════════
@app.errorhandler(500)
def handle_500(e):
    print(f"DEBUG: Internal Server Error: {str(e)}")
    return jsonify({'success': False, 'message': f'Server Error: {str(e)}'}), 500





@app.errorhandler(404)
def handle_404(e):
    if request.path.startswith('/api/'):
        return jsonify({'success': False, 'message': 'API endpoint not found'}), 404
    # Ensure user object has expected keys even if session is empty
    user_data = dict(session)
    if 'name' not in user_data:
        user_data['name'] = 'Guest'
    return render_template('404.html', user=user_data), 404

@app.route('/')
def index():
    """Redirect root to landing page."""
    return redirect(url_for('landing'))

@app.route('/favicon.ico')
def favicon():
    """Serve a transparent 1x1 pixel for the online check."""
    return b'\x00', 200, {'Content-Type': 'image/x-icon'}

@app.route('/landing')
def landing():
    try:
        return send_file(os.path.join(app.root_path, 'index.html'))
    except Exception:
        return redirect(url_for('login'))

@app.route('/offline.html')
def offline_page():
    path = os.path.join(app.root_path, 'offline.html')
    if os.path.exists(path):
        return send_file(path)
    return 'Offline', 200

@app.route('/api-status')
def api_status_page():
    path = os.path.join(app.root_path, 'api_status.html')
    if os.path.exists(path):
        return send_file(path)
    return 'Status Page Not Found', 404

@app.route('/docs')
def docs_page():
    path = os.path.join(app.root_path, 'docs.html')
    if os.path.exists(path):
        return send_file(path)
    return 'Docs Not Found', 404

@app.route('/robots.txt')
def robots_txt():
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /api/",
        "Disallow: /employee-dashboard",
        "Disallow: /teamleader-dashboard",
        "Disallow: /hr-dashboard",
        "Disallow: /admin-dashboard",
        f"Sitemap: {request.url_root.rstrip('/')}/sitemap.xml"
    ]
    return app.response_class('\n'.join(lines), mimetype='text/plain')

@app.route('/sitemap.xml')
def sitemap_xml():
    base = request.url_root.rstrip('/')
    urls = [
        f"{base}/",
        f"{base}/landing",
        f"{base}/login",
        f"{base}/offline.html",
    ]
    lastmod = datetime.utcnow().date().isoformat()
    items = '\n'.join([
        f"<url><loc>{u}</loc><lastmod>{lastmod}</lastmod><changefreq>weekly</changefreq><priority>0.8</priority></url>"
        for u in urls
    ])
    xml = f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{items}</urlset>'
    return app.response_class(xml, mimetype='application/xml')

@app.route('/sw.js')
def service_worker():
    path = os.path.join(app.root_path, 'sw.js')
    if os.path.exists(path):
        return send_file(path, mimetype='application/javascript')
    return '', 204

# ═══════════════════════════════════════════════════════
#  AUTH ROUTES
# ═══════════════════════════════════════════════════════



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if 'user_id' in session:
            return redirect(url_for(f'{session["role"]}_dashboard'))
        return render_template('login.html')

    data = request.get_json(silent=True) or {}
    email    = data.get('email', '').lower().strip()
    password = data.get('password', '').strip()
    log_system_activity(f"Login attempt for email: {email}")

    if not email or not password:
        return jsonify({'success': False, 'message': 'Email and password are required'}), 400

    db   = get_db_data()
    user = next(
        (u for u in db['users']
         if u['email'].lower() == email and u.get('status') == 'Active'),
        None
    )

    if user:
        # Check password hash (handle plain text for migration)
        is_valid = False
        
        # 1. Try verifying as a hash first (supports pbkdf2, scrypt, etc.)
        try:
            if check_password_hash(user['password'], password):
                is_valid = True
        except Exception:
            # Not a valid hash format, might be plain text
            pass
            
        # 2. If not valid yet, check plain text (legacy support)
        if not is_valid and user['password'] == password:
            user['password'] = generate_password_hash(password)
            save_db_data(db)
            is_valid = True

        if is_valid:
            # Check for 2FA
            if user.get('two_factor_enabled'):
                session['temp_user_id'] = user['id']
                log_system_activity(f"User {user['name']} passed first step, 2FA required", db)
                return jsonify({'success': True, 'requires_2fa': True})

            # Normal Login
            log_system_activity(f"Login successful for user: {user['name']} (Role: {user['role']})", db)
            session.permanent = True
            session['user_id'] = user['id']
            session['role']    = user['role']
            session['name']    = user['name']
            session['email']   = user['email']
            db['login_logs'].append({
                'user_id': user['id'], 'name': user['name'],
                'role':    user['role'], 'time': datetime.now().isoformat(),
                'ip':      request.remote_addr or '127.0.0.1'
            })
            save_db_data(db)
            return jsonify({'success': True, 'requires_2fa': False, 'role': user['role'],
                            'redirect': f'/{user["role"]}-dashboard'})

    log_system_activity(f"Login failed for email: {email}")
    return jsonify({'success': False, 'message': 'Invalid email or password'}), 401


@app.route('/api/auth/verify-2fa', methods=['POST'])
def verify_2fa():
    data = request.get_json(silent=True) or {}
    otp_code = data.get('code', '').strip()
    uid = session.get('temp_user_id')

    if not uid or not otp_code:
        return jsonify({'success': False, 'message': 'Invalid session or missing code'}), 400

    db = get_db_data()
    user = next((u for u in db['users'] if u['id'] == uid), None)

    if user and user.get('two_factor_enabled') and user.get('two_factor_secret'):
        totp = pyotp.TOTP(user['two_factor_secret'])
        if totp.verify(otp_code):
            # Login successful
            session.pop('temp_user_id', None)
            session.permanent = True
            session['user_id'] = user['id']
            session['role']    = user['role']
            session['name']    = user['name']
            session['email']   = user['email']
            
            log_system_activity(f"2FA verified for user: {user['name']}", db)
            db['login_logs'].append({
                'user_id': user['id'], 'name': user['name'],
                'role':    user['role'], 'time': datetime.now().isoformat(),
                'ip':      request.remote_addr or '127.0.0.1'
            })
            save_db_data(db)
            return jsonify({'success': True, 'role': user['role'],
                            'redirect': f'/{user["role"]}-dashboard'})

    log_system_activity(f"2FA verification failed for user ID: {uid}")
    return jsonify({'success': False, 'message': 'Invalid verification code'}), 401


@app.route('/logout')
def logout():
    db = get_db_data()
    user_name = session.get('name', 'Unknown User')
    log_system_activity(f"User {user_name} logged out", db)
    session.clear()
    return redirect(url_for('login'))


# ─── Dashboard Pages ─────────────────────────────────────────────────────────
@app.route('/employee-dashboard')
@login_required(roles=['employee'])
def employee_dashboard():
    db = get_db_data()
    log_system_activity(f"Employee Dashboard accessed by {session.get('name')}", db)
    return render_template('employee_dashboard.html', user=dict(session))

@app.route('/teamleader-dashboard')
@login_required(roles=['teamleader'])
def teamleader_dashboard():
    db = get_db_data()
    log_system_activity(f"Team Leader Dashboard accessed by {session.get('name')}", db)
    return render_template('teamleader_dashboard.html', user=dict(session))

@app.route('/hr-dashboard')
@login_required(roles=['hr'])
def hr_dashboard():
    db = get_db_data()
    log_system_activity(f"HR Dashboard accessed by {session.get('name')}", db)
    return render_template('hr_dashboard.html', user=dict(session))

@app.route('/admin-dashboard')
@login_required(roles=['admin'])
def admin_dashboard():
    db = get_db_data()
    log_system_activity(f"Admin Dashboard accessed by {session.get('name')}", db)
    return render_template('admin_dashboard.html', user=dict(session))

@app.route('/view-activity')
@login_required(roles=['admin', 'hr'])
def view_activity():
    """Browser-based activity monitoring."""
    db = get_db_data()
    activities = db.get('system_activities', [])
    # Return a simple HTML table of activities
    html = """
    <html>
    <head>
        <title>System Activity Monitor</title>
        <style>
            body { font-family: sans-serif; padding: 20px; background: #0f0f14; color: #e8e8f0; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th, td { padding: 12px; text-align: left; border-bottom: 1px solid #2a2a38; }
            th { background: #1e1e2a; color: #6c63ff; }
            tr:hover { background: #17171f; }
            .badge { padding: 4px 8px; border-radius: 4px; font-size: 0.8em; font-weight: bold; }
            .login { background: #43e97b; color: #000; }
            .logout { background: #ff6584; color: #fff; }
            .dashboard { background: #6c63ff; color: #fff; }
        </style>
        <meta http-equiv="refresh" content="5">
    </head>
    <body>
        <h1>Live System Activity Monitor</h1>
        <p>Refreshing every 5 seconds...</p>
        <table>
            <thead>
                <tr>
                    <th>Timestamp</th>
                    <th>Activity Message</th>
                    <th>IP Address</th>
                </tr>
            </thead>
            <tbody>
    """
    for act in reversed(activities[-50:]):
        msg = act.get('message', '')
        css_class = ""
        if "Login successful" in msg: css_class = "login"
        elif "logged out" in msg: css_class = "logout"
        elif "Dashboard accessed" in msg: css_class = "dashboard"
        
        html += f"""
                <tr>
                    <td>{act.get('time', '').replace('T', ' ')}</td>
                    <td><span class="badge {css_class}">{msg}</span></td>
                    <td>{act.get('ip', 'N/A')}</td>
                </tr>
        """
    html += """
            </tbody>
        </table>
        <br><a href="/" style="color: #6c63ff;">Back to Home</a>
    </body>
    </html>
    """
    return html


# ═══════════════════════════════════════════════════════
#  UNIVERSAL NOTIFICATIONS (all roles — used by base.html)
# ═══════════════════════════════════════════════════════
@app.route('/api/notifications')
@login_required(roles=['employee', 'teamleader', 'hr', 'admin'])
def get_notifications():
    """Role-aware notifications accessible to every authenticated user."""
    db   = get_db_data()
    role = session.get('role', 'employee')
    uid  = session.get('user_id', '')
    
    # Inline migration: fix old-format notifications that use 'from' instead of 'sender'
    migrated = False
    for n in db.get('notifications', []):
        if 'sender' not in n and 'from' in n:
            n['sender'] = n.pop('from')
            n.setdefault('sender_role', 'system')
            n.setdefault('sender_id', 'SYSTEM')
            n.setdefault('read_by', [])
            migrated = True
        elif 'read_by' not in n:
            n['read_by'] = []
            migrated = True
    if migrated:
        save_db_data(db)
    
    # Get all notifications for this user
    user_notifs = [
        n for n in db.get('notifications', [])
        if n.get('target') in ['all', role, uid]
    ]
    
    # Sort by time desc
    user_notifs.sort(key=lambda x: x.get('time', ''), reverse=True)
    
    # Calculate unread count
    unread_count = sum(1 for n in user_notifs if uid not in n.get('read_by', []))
    
    # Calculate today's count
    today_str = datetime.now().strftime('%Y-%m-%d')
    today_count = sum(1 for n in user_notifs if n.get('time', '').startswith(today_str))
    
    return jsonify({
        'notifications': user_notifs[:20], # Show more in history
        'unread_count': unread_count,
        'today_count': today_count
    })

@app.route('/api/notifications/mark-read', methods=['POST'])
@login_required(roles=['employee', 'teamleader', 'hr', 'admin'])
def mark_notifications_read():
    db = get_db_data()
    role = session.get('role', 'employee')
    uid = session.get('user_id', '')
    
    updated = False
    for n in db['notifications']:
        if n.get('target') in ['all', role, uid]:
            if 'read_by' not in n:
                n['read_by'] = []
            if uid not in n['read_by']:
                n['read_by'].append(uid)
                updated = True
                
    if updated:
        save_db_data(db)
    return jsonify({'success': True})

@app.route('/api/notifications/send', methods=['POST'])
@login_required()
def send_notification():
    """Universal notification/message sending."""
    data = request.get_json(silent=True) or {}
    msg = data.get('message', '').strip()
    target = data.get('target', 'all')
    ntype = data.get('type', 'info')
    
    if not msg:
        return jsonify({'success': False, 'message': 'Message is required'}), 400
    
    role = session.get('role', 'employee')
    
    # Restriction logic: Employees can't send 'all' broadcasts
    if role == 'employee' and target in ['all', 'employee']:
        return jsonify({'success': False, 'message': 'Employees cannot broadcast messages to everyone.'}), 403
        
    db = get_db_data()
    if 'notifications' not in db:
        db['notifications'] = []
        
    from uuid import uuid4
    db['notifications'].append({
        'id': str(uuid4())[:8].upper(),
        'sender': session['name'],
        'sender_id': session['user_id'],
        'sender_role': role,
        'time': datetime.now().isoformat(),
        'type': ntype,
        'message': msg,
        'target': target,
        'read_by': []
    })
    save_db_data(db)
    log_system_activity(f"Notification sent by {session['name']} ({role}) to {target}", db)
    return jsonify({'success': True})

@app.route('/api/profile')
@login_required()
def get_user_profile():
    db = get_db_data()
    uid = session['user_id']
    # Try to find in employees first
    emp = next((e for e in db['employees'] if e['user_id'] == uid), None)
    
    # If not found (e.g. HR/Admin without employee record), create a basic one from session/users
    if not emp:
        user = next((u for u in db['users'] if u['id'] == uid), {})
        emp = {
            'user_id': uid,
            'name': user.get('name', session.get('name')),
            'role': user.get('role', session.get('role')),
            'email': user.get('email', session.get('email')),
            'department': 'System' if user.get('role') == 'admin' else 'HR',
            'status': user.get('status', 'Active'),
            'skills': '',
            'learning_progress': {}
        }
    
    # Merge with 2FA status from users table
    user = next((u for u in db['users'] if u['id'] == uid), {})
    emp['two_factor_enabled'] = user.get('two_factor_enabled', False)
    
    return jsonify(emp)


# ═══════════════════════════════════════════════════════
#  EMPLOYEE APIs
# ═══════════════════════════════════════════════════════
@app.route('/api/employee/mark-attendance', methods=['POST'])
@login_required(roles=['employee', 'teamleader', 'hr', 'admin'])
def mark_attendance():
    db = get_db_data()
    uid = session['user_id']
    today = datetime.now().strftime('%Y-%m-%d')
    now_time = datetime.now().strftime('%H:%M %p')
    
    if 'daily_attendance' not in db:
        db['daily_attendance'] = []
        
    # Check if already marked
    exists = any(a for a in db['daily_attendance'] if a['user_id'] == uid and a['date'] == today)
    if exists:
        return jsonify({'success': False, 'message': 'Attendance already marked today.'}), 400
        
    # Add record
    db['daily_attendance'].append({
        'user_id': uid,
        'date': today,
        'status': 'Present',
        'check_in_time': now_time,
        'created_at': datetime.now().isoformat()
    })
    
    # Update monthly stats in legacy table for consistency
    month_name = datetime.now().strftime('%B')
    if 'attendance' not in db: db['attendance'] = []
    
    found = False
    for a in db['attendance']:
        if a['user_id'] == uid and a['month'] == month_name:
            a['present'] = a.get('present', 0) + 1
            a['total'] = a.get('total', 22)
            found = True
            break
    if not found:
        db['attendance'].append({
            'user_id': uid,
            'month': month_name,
            'present': 1,
            'absent': 0,
            'late': 0,
            'total': 22,
            'hours': 8
        })
        
    save_db_data(db)
    return jsonify({'success': True, 'message': 'Attendance marked successfully!', 'time': now_time})

@app.route('/api/auth/setup-2fa', methods=['GET'])
@login_required()
def setup_2fa():
    db = get_db_data()
    uid = session['user_id']
    user = next((u for u in db['users'] if u['id'] == uid), None)
    
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
        
    # Generate secret if not exists or if requested
    if not user.get('two_factor_secret') or request.args.get('refresh'):
        user['two_factor_secret'] = pyotp.random_base32()
        save_db_data(db)
        
    # Generate provisioning URI
    otp_uri = pyotp.totp.TOTP(user['two_factor_secret']).provisioning_uri(
        name=user['email'],
        issuer_name="PulseHR"
    )
    
    # Generate QR Code image
    try:
        img = qrcode.make(otp_uri)
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
    except Exception as qr_err:
        return jsonify({'success': False, 'message': f'QR generation failed: {str(qr_err)}. Please install Pillow.'}), 500
    
    return jsonify({
        'success': True,
        'secret': user['two_factor_secret'],
        'qr_code': f"data:image/png;base64,{img_str}"
    })

@app.route('/api/auth/enable-2fa', methods=['POST'])
@login_required()
def enable_2fa():
    data = request.get_json(silent=True) or {}
    code = data.get('code', '').strip()
    
    if not code:
        return jsonify({'success': False, 'message': 'Verification code required'}), 400
        
    db = get_db_data()
    uid = session['user_id']
    user = next((u for u in db['users'] if u['id'] == uid), None)
    
    if user and user.get('two_factor_secret'):
        totp = pyotp.TOTP(user['two_factor_secret'])
        if totp.verify(code):
            user['two_factor_enabled'] = True
            save_db_data(db)
            log_system_activity(f"2FA enabled for user: {user['name']}", db)
            return jsonify({'success': True, 'message': '2FA has been successfully enabled'})
            
    return jsonify({'success': False, 'message': 'Invalid verification code'}), 401

@app.route('/api/auth/disable-2fa', methods=['POST'])
@login_required()
def disable_2fa():
    db = get_db_data()
    uid = session['user_id']
    user = next((u for u in db['users'] if u['id'] == uid), None)
    
    if user:
        user['two_factor_enabled'] = False
        user['two_factor_secret'] = None
        save_db_data(db)
        log_system_activity(f"2FA disabled for user: {user['name']}", db)
        return jsonify({'success': True, 'message': '2FA has been disabled'})
        
    return jsonify({'success': False, 'message': 'User not found'}), 404
@app.route('/api/employee/attendance-history')
@login_required(roles=['employee', 'teamleader', 'hr', 'admin'])
def get_attendance_history():
    db = get_db_data()
    uid = session['user_id']
    history = [a for a in db.get('daily_attendance', []) if a['user_id'] == uid]
    
    # Ensure we show last 30 days history including gaps
    today = datetime.now()
    full_history = []
    for i in range(30):
        d = (today - timedelta(days=i)).strftime('%Y-%m-%d')
        entry = next((a for a in history if a['date'] == d), None)
        if entry:
            full_history.append(entry)
        else:
            full_history.append({
                'user_id': uid,
                'date': d,
                'status': 'Absent',
                'check_in_time': '—',
                'is_gap': True
            })

    # Calculate monthly score
    month_name = today.strftime('%B')
    monthly_data = next((a for a in db.get('attendance', []) if a['user_id'] == uid and a['month'] == month_name), None)
    
    present = monthly_data['present'] if monthly_data else 0
    total = monthly_data['total'] if monthly_data else 22
    score = round((present / total) * 100, 1) if total > 0 else 0
    
    return jsonify({
        'history': full_history, # Already sorted newest first
        'monthly_score': score,
        'today_marked': any(a for a in history if a['date'] == today.strftime('%Y-%m-%d'))
    })

@app.route('/api/employee/profile')
@login_required(roles=['employee'])
def get_employee_profile():
    db  = get_db_data()
    uid = session['user_id']
    emp = next((e for e in db['employees'] if e['user_id'] == uid), {})
    
    # Ensure learning_progress exists in the employee record
    if 'learning_progress' not in emp:
        # Check if it exists in the old root-level storage for migration
        old_progress = db.get('learning_progress', {}).get(uid, {})
        emp['learning_progress'] = old_progress
        save_db_data(db)
        
    return jsonify(emp)


@app.route('/api/employee/tasks')
@login_required(roles=['employee'])
def get_employee_tasks():
    db    = get_db_data()
    tasks = [t for t in db['tasks'] if t.get('assigned_to') == session['user_id']]
    return jsonify(tasks)


@app.route('/api/employee/update-task', methods=['POST'])
@login_required(roles=['employee'])
def update_task_status():
    data = request.get_json(silent=True) or {}
    if not data.get('task_id'):
        return jsonify({'success': False, 'message': 'task_id required'}), 400

    db = get_db_data()
    updated = False
    for t in db['tasks']:
        if t['id'] == data['task_id'] and t.get('assigned_to') == session['user_id']:
            t['status']   = data.get('status', t['status'])
            t['progress'] = int(data.get('progress', t.get('progress', 0)))
            updated = True
            break

    if updated:
        save_db_data(db)
    return jsonify({'success': updated})


@app.route('/api/employee/weekly-update', methods=['POST'])
@login_required(roles=['employee'])
def submit_weekly_update():
    data = request.get_json(silent=True) or {}
    db   = get_db_data()
    uid  = session['user_id']
    
    # Check if already submitted this week
    if 'weekly_updates' not in db:
        db['weekly_updates'] = []

    today = datetime.now()
    start_of_week = today - timedelta(days=today.weekday())
    start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)

    for wu in db['weekly_updates']:
        if wu['user_id'] == uid:
            wu_date = datetime.fromisoformat(wu['submitted_at'])
            if wu_date >= start_of_week:
                return jsonify({'success': False, 'message': 'You have already submitted your weekly update for this week.'}), 400

    # Record submission
    db['weekly_updates'].append({
        'user_id': uid,
        'submitted_at': today.isoformat(),
        'week_ending': (start_of_week + timedelta(days=6)).strftime('%Y-%m-%d'),
        'project_work': data.get('project_work', ''),
        'tech_learned': data.get('tech_learned', ''),
        'problems': data.get('problems', ''),
        'task_completion': data.get('task_completion', 0),
        'title': data.get('project_work', '')[:40] + ('...' if len(data.get('project_work', '')) > 40 else ''),
        'efficiency': data.get('task_completion', 0),
        'status': 'Approved' # Auto-approved for now
    })
    
    # 1. Update Employee Skills
    tech_learned = data.get('tech_learned', '').strip()
    if tech_learned:
        for emp in db.get('employees', []):
            if emp['user_id'] == uid:
                current_skills = [s.strip() for s in emp.get('skills', '').split(',') if s.strip()]
                new_skills = [s.strip() for s in tech_learned.split(',') if s.strip()]
                for ns in new_skills:
                    if ns.lower() not in [s.lower() for s in current_skills]:
                        current_skills.append(ns)
                emp['skills'] = ', '.join(current_skills)
                break
                
    # 2. Update Performance (Task Completion & small Productivity bump)
    task_comp = data.get('task_completion', 0)
    for p in db.get('performance', []):
        if p['user_id'] == uid:
            # Simple moving average or outright replace depending on desired logic. We'll average it roughly.
            current_comp = p.get('task_completion', 0)
            p['task_completion'] = int((current_comp + int(task_comp)) / 2) if current_comp > 0 else int(task_comp)
            
            # Boost productivity by up to 2 points if they actively learned something
            if tech_learned:
                p['productivity_score'] = min(100, p.get('productivity_score', 0) + 2)
            break

    save_db_data(db)
    return jsonify({'success': True})

@app.route('/api/employee/weekly-updates')
@login_required(roles=['employee'])
def get_employee_weekly_updates():
    db = get_db_data()
    uid = session['user_id']
    updates = [wu for wu in db.get('weekly_updates', []) if wu['user_id'] == uid]
    # Sort by date descending
    updates.sort(key=lambda x: x['submitted_at'], reverse=True)
    return jsonify(updates)

@app.route('/api/admin/integrations/test/email', methods=['POST'])
@login_required(roles=['admin'])
def test_email_integration():
    data = request.get_json(silent=True) or {}
    db = get_db_data()
    integ = _ensure_integrations(db)
    e = integ['email']
    if not e.get('enabled'):
        return jsonify({'success': False, 'message': 'Email service not enabled'}), 400
    host = e.get('smtp_host', '')
    port = int(e.get('smtp_port', 587))
    user = e.get('smtp_user', '')
    pwd  = e.get('smtp_password', '')
    from_email = e.get('from_email', '')
    from_name  = e.get('from_name', 'PulseHR')
    use_tls = bool(e.get('use_tls', True))
    to_email = data.get('to') or from_email
    if not (host and from_email and to_email):
        return jsonify({'success': False, 'message': 'Missing SMTP host/from/to'}), 400
    msg = EmailMessage()
    msg['Subject'] = 'PulseHR Test Email'
    msg['From'] = f"{from_name} <{from_email}>"
    msg['To'] = to_email
    msg.set_content('This is a test email from PulseHR integration.')
    try:
        if use_tls:
            server = smtplib.SMTP(host, port, timeout=10)
            server.starttls()
        else:
            server = smtplib.SMTP(host, port, timeout=10)
        if user and pwd:
            server.login(user, pwd)
        server.send_message(msg)
        server.quit()
        return jsonify({'success': True, 'message': f'Test email sent to {to_email}'})
    except Exception as ex:
        return jsonify({'success': False, 'message': f'Email failed: {str(ex)}'}), 400

@app.route('/api/admin/integrations/test/slack', methods=['POST'])
@login_required(roles=['admin'])
def test_slack_integration():
    data = request.get_json(silent=True) or {}
    db = get_db_data()
    integ = _ensure_integrations(db)
    s = integ['slack']
    if not s.get('enabled'):
        return jsonify({'success': False, 'message': 'Slack not enabled'}), 400
    webhook = s.get('webhook_url', '')
    if not webhook:
        return jsonify({'success': False, 'message': 'Webhook URL missing'}), 400
    text = data.get('text') or 'PulseHR test message'
    payload = json.dumps({
        'text': text, 
        'channel': s.get('channel') or None,
        'username': s.get('bot_name') or 'PulseHR Bot'
    }).encode('utf-8')
    req = urllib.request.Request(webhook, data=payload, headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            if 200 <= resp.status < 300:
                return jsonify({'success': True, 'message': 'Slack test message posted'})
            return jsonify({'success': False, 'message': f'Slack returned {resp.status}'}), 400
    except Exception as ex:
        return jsonify({'success': False, 'message': f'Slack failed: {str(ex)}'}), 400

@app.route('/api/admin/integrations/test/calendar', methods=['POST'])
@login_required(roles=['admin'])
def test_calendar_integration():
    db = get_db_data()
    integ = _ensure_integrations(db)
    c = integ['calendar']
    if not c.get('enabled'):
        return jsonify({'success': False, 'message': 'Calendar not enabled'}), 400
    provider = (c.get('provider') or '').lower()
    if provider == 'ics' and c.get('ics_url'):
        url = c['ics_url']
        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                text = resp.read().decode('utf-8', errors='ignore')
            title = None
            start = None
            for line in text.splitlines():
                if line.startswith('SUMMARY:') and not title:
                    title = line[len('SUMMARY:'):].strip()
                if line.startswith('DTSTART') and not start:
                    start = line.split(':',1)[-1].strip()
                if title and start:
                    break
            if title or start:
                _t = title if title else '(no title)'
                _s = start if start else '(no start)'
                return jsonify({'success': True, 'message': f'ICS reachable. Next event: {_t} at {_s}'})
            return jsonify({'success': True, 'message': 'ICS reachable. Events parsed.'})
        except Exception as ex:
            return jsonify({'success': False, 'message': f'ICS fetch failed: {str(ex)}'}), 400
    if provider in ['google', 'microsoft']:
        if c.get('api_key') and c.get('calendar_id'):
            return jsonify({'success': True, 'message': f'{provider.title()} credentials present'})
        return jsonify({'success': False, 'message': 'Missing API key or calendar ID'}), 400
    return jsonify({'success': False, 'message': 'Unsupported provider'}), 400


@app.route('/api/employee/upload-certificate', methods=['POST'])
@login_required(roles=['employee'])
def submit_certificate_update():
    skill_name = request.form.get('skill_name', '').strip()
    completion = request.form.get('completion', '0')
    
    if not skill_name:
        return jsonify({'success': False, 'message': 'Skill Name is required.'}), 400
        
    try:
        completion_val = int(completion)
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid completion value.'}), 400
        
    db = get_db_data()
    uid = session['user_id']
    
    # Update progress in employee record
    emp = next((e for e in db.get('employees', []) if e['user_id'] == uid), None)
    if not emp:
        return jsonify({'success': False, 'message': 'Employee record not found.'}), 404
        
    if 'learning_progress' not in emp:
        emp['learning_progress'] = {}
        
    emp['learning_progress'][skill_name] = completion_val
    save_db_data(db)

    # If < 100%, we just save the progress, no certificate needed.
    if completion_val < 100:
        return jsonify({'success': True, 'message': f"Progress for '{skill_name}' updated to {completion_val}%."})

    # For 100%, mandate a certificate
    if 'certificate' not in request.files or request.files['certificate'].filename == '':
        return jsonify({'success': False, 'message': 'Please upload a certificate file for verification of 100% completion.'}), 400
        
    file = request.files['certificate']
    
    # Save Certificate permanently
    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    safe_filename = f"{uid}_{timestamp}_{filename}"
    filepath = os.path.join(UPLOAD_FOLDER_CERT, safe_filename)
    file.save(filepath)

    db = get_db_data()
    
    # Check if 'certificates' array exists
    if 'certificates' not in db:
        db['certificates'] = []
        
    db['certificates'].append({
        'user_id': uid,
        'skill_name': skill_name,
        'filename': safe_filename,
        'uploaded_at': datetime.now().isoformat()
    })
    
    # Append skill to employee
    added_skill = False
    for emp in db.get('employees', []):
        if emp['user_id'] == uid:
            current_skills = [s.strip() for s in emp.get('skills', '').split(',') if s.strip()]
            if skill_name.lower() not in [s.lower() for s in current_skills]:
                current_skills.append(skill_name)
                emp['skills'] = ', '.join(current_skills)
                added_skill = True
            break
            
    # Boost productivity by 5 points for verified certification
    if added_skill:
        for p in db.get('performance', []):
            if p['user_id'] == uid:
                p['productivity_score'] = min(100, p.get('productivity_score', 0) + 5)
                break
                
    save_db_data(db)
    
    msg = f"AI Verified Certificate: Employee Name and Training Institute validated. '{skill_name}' added to your profile." if added_skill else f"AI Verified Certificate: Validation passed. You already had '{skill_name}' listed."
    return jsonify({'success': True, 'message': msg})


@app.route('/api/employee/training-update', methods=['POST'])
@login_required(roles=['employee'])
def submit_training_update():
    data = request.get_json(silent=True) or {}
    db   = get_db_data()
    if 'training' not in db: db['training'] = []
    db['training'].append({
        'user_id':      session['user_id'],
        'name':         session['name'],
        'week':         data.get('week', 1),
        'hours':        data.get('hours', 0),
        'tech_learned': data.get('tech_learned', ''),
        'problems':     data.get('problems', ''),
        'completion':   data.get('completion', 0),
        'recorded_at':  datetime.now().isoformat()
    })
    save_db_data(db)
    return jsonify({'success': True})


@app.route('/api/employee/performance')
@login_required(roles=['employee', 'teamleader', 'hr', 'admin'])
def get_employee_performance():
    db   = get_db_data()
    uid  = session['user_id']
    perf = next((p for p in db['performance'] if p['user_id'] == uid), None)
    
    if perf:
        # Calculate real-time attendance pct if daily_attendance exists
        history = [a for a in db.get('daily_attendance', []) if a['user_id'] == uid]
        month_name = datetime.now().strftime('%B')
        monthly_data = next((a for a in db.get('attendance', []) if a['user_id'] == uid and a['month'] == month_name), None)
        
        if monthly_data:
            present = monthly_data.get('present', 0)
            total = monthly_data.get('total', 22)
            real_pct = round((present / total) * 100, 1) if total > 0 else 0
            perf['attendance_pct'] = real_pct
            
            # Re-calculate productivity score in real-time for the dashboard
            # productivity_score = 0.40 * task_completion_rate + 0.30 * attendance_score + 0.20 * quality_score + 0.10 * peer_review_score
            task_rate = perf.get('task_completion', 0)
            quality = (perf.get('quality_rating', 0) * 10) # assuming 0-10 scale
            peer = perf.get('satisfaction', 0)
            
            perf['productivity_score'] = round(
                (0.40 * task_rate) + 
                (0.30 * real_pct) + 
                (0.20 * quality) + 
                (0.10 * peer), 1
            )

    return jsonify(perf or {})


@app.route('/api/employee/notifications')
@login_required(roles=['employee'])
def get_employee_notifications():
    db     = get_db_data()
    uid    = session['user_id']
    notifs = [n for n in db['notifications']
              if n.get('target') in ['all', 'employee', uid]]
    return jsonify(notifs[-10:])


# ═══════════════════════════════════════════════════════
#  TEAM LEADER APIs
# ═══════════════════════════════════════════════════════
@app.route('/api/tl/team-info')
@login_required(roles=['teamleader'])
def get_tl_team_info():
    db = get_db_data()
    uid = session['user_id']
    teams = [t for t in db.get('teams', []) if t.get('leader_id') == uid]
    return jsonify(teams)

@app.route('/api/tl/team')
@login_required(roles=['teamleader'])
def get_tl_team():
    db   = get_db_data()
    uid  = session['user_id']
    primary = [e for e in db['employees'] if e.get('team_leader_id') == uid]
    member_ids = set()
    for t in db.get('teams', []):
        if t.get('leader_id') == uid:
            for mid in t.get('member_ids', []):
                member_ids.add(str(mid))
    by_team = []
    seen = set(str(e['user_id']) for e in primary)
    for e in db['employees']:
        if str(e.get('user_id')) in member_ids and str(e.get('user_id')) not in seen:
            by_team.append(e)
            seen.add(str(e.get('user_id')))
    team = primary + by_team
    result = []
    for member in team:
        perf = next((p for p in db['performance'] if p['user_id'] == member['user_id']), {})
        active_tasks = len([t for t in db['tasks'] if t.get('assigned_to') == member['user_id'] and t.get('status') != 'Completed'])
        result.append({
            **member,
            'productivity_score': perf.get('productivity_score', 0),
            'task_completion': perf.get('task_completion', 0),
            'active_tasks': active_tasks
        })
    return jsonify(result)

@app.route('/api/tl/update-project', methods=['POST'])
@login_required(roles=['teamleader'])
def tl_update_project():
    data = request.get_json(silent=True) or {}
    comp = data.get('completion', 0)
    status = data.get('status', 'In Progress')
    team_id = data.get('team_id')
    
    db = get_db_data()
    team = None
    if team_id:
        team = next((t for t in db.get('teams', []) if t.get('id') == team_id and t.get('leader_id') == session['user_id']), None)
    else:
        # Fallback to the first team for legacy compatibility if needed
        team = next((t for t in db.get('teams', []) if t.get('leader_id') == session['user_id']), None)

    if not team:
        return jsonify({'success': False, 'message': 'Team not found or unauthorized'}), 404
    
    team['project_completion'] = int(comp)
    team['project_status'] = status
    save_db_data(db)
    return jsonify({'success': True})


@app.route('/api/tl/leave-requests')
@login_required(roles=['teamleader'])
def get_tl_leave_requests():
    db = get_db_data()
    # Get all employees under this TL
    team_ids = [e['user_id'] for e in db['employees'] if e.get('team_leader_id') == session['user_id']]
    # Filter leave requests for team members
    tls_leaves = [lr for lr in db.get('leave_requests', []) if lr['user_id'] in team_ids]
    return jsonify(tls_leaves)

@app.route('/api/tl/leave-approve', methods=['POST'])
@login_required(roles=['teamleader'])
def tl_approve_leave():
    data = request.get_json(silent=True) or {}
    rid = data.get('request_id')
    db = get_db_data()
    team_ids = [e['user_id'] for e in db['employees'] if e.get('team_leader_id') == session['user_id']]
    
    for lr in db.get('leave_requests', []):
        if lr['id'] == rid and lr['user_id'] in team_ids:
            lr['status'] = 'Approved (TL)'
            lr['reviewed_by'] = session['name']
            lr['reviewed_at'] = datetime.now().isoformat()
            break
    save_db_data(db)
    return jsonify({'success': True})

@app.route('/api/tl/leave-reject', methods=['POST'])
@login_required(roles=['teamleader'])
def tl_reject_leave():
    data = request.get_json(silent=True) or {}
    rid = data.get('request_id')
    db = get_db_data()
    team_ids = [e['user_id'] for e in db['employees'] if e.get('team_leader_id') == session['user_id']]
    
    for lr in db.get('leave_requests', []):
        if lr['id'] == rid and lr['user_id'] in team_ids:
            lr['status'] = 'Rejected (TL)'
            lr['reviewed_by'] = session['name']
            lr['reviewed_at'] = datetime.now().isoformat()
            break
    save_db_data(db)
    return jsonify({'success': True})


@app.route('/api/tl/create-task', methods=['POST'])
@login_required(roles=['teamleader'])
def create_task():
    data = request.get_json(silent=True) or {}
    if not data.get('title'):
        return jsonify({'success': False, 'message': 'title is required'}), 400

    db      = get_db_data()
    task_id = _next_task_id(db)
    task = {
        'id':              task_id,
        'title':           data['title'],
        'description':     data.get('description', ''),
        'priority':        data.get('priority', 'Medium'),
        'deadline':        data.get('deadline', ''),
        'required_skills': data.get('required_skills', []),
        'assigned_to':     data.get('assigned_to') or None,
        'assigned_by':     session['user_id'],
        'status':          'Pending',
        'progress':        0,
        'created_at':      datetime.now().isoformat()
    }
    db['tasks'].append(task)
    save_db_data(db)
    return jsonify({'success': True, 'task_id': task_id})


@app.route('/api/tl/ai-suggest-employee', methods=['POST'])
@login_required(roles=['teamleader'])
def ai_suggest_employee():
    data             = request.get_json(silent=True) or {}
    required_skills  = data.get('required_skills', [])
    db               = get_db_data()
    team             = [e for e in db['employees'] if e.get('team_leader_id') == session['user_id']]

    suggestions = []
    for emp in team:
        raw_skills = emp.get('skills', '')
        emp_skills = [s.strip() for s in raw_skills.split(',')] if isinstance(raw_skills, str) else raw_skills
        matched    = sum(1 for s in required_skills
                        if any(s.lower() in es.lower() for es in emp_skills))
        skill_pct  = int((matched / max(len(required_skills), 1)) * 100)
        perf       = next((p for p in db['performance'] if p['user_id'] == emp['user_id']), {})
        active_tasks = len([t for t in db['tasks']
                            if t.get('assigned_to') == emp['user_id']
                            and t.get('status') != 'Completed'])
        perf_score = perf.get('productivity_score', 75)
        suggestions.append({
            'user_id':            emp['user_id'],
            'name':               emp['name'],
            'skill_match':        skill_pct,
            'current_workload':   active_tasks,
            'performance_score':  perf_score,
            'recommendation_score': (skill_pct * 0.5
                                     + max(0, (5 - active_tasks) * 5)
                                     + perf_score * 0.2)
        })

    suggestions.sort(key=lambda x: x['recommendation_score'], reverse=True)
    return jsonify(suggestions[:3])


@app.route('/api/tl/tasks')
@login_required(roles=['teamleader'])
def get_tl_tasks():
    db    = get_db_data()
    tasks = [t for t in db['tasks'] if t.get('assigned_by') == session['user_id']]
    return jsonify(tasks)


@app.route('/api/tl/update-score', methods=['POST'])
@login_required(roles=['teamleader'])
def update_tl_score():
    data = request.get_json(silent=True) or {}
    if not data.get('user_id'):
        return jsonify({'success': False, 'message': 'user_id required'}), 400

    db = get_db_data()
    for p in db['performance']:
        if p['user_id'] == data['user_id']:
            p['tl_score'] = max(0, min(10, int(data.get('score', 7))))
            break
    save_db_data(db)
    return jsonify({'success': True})


# ═══════════════════════════════════════════════════════
#  HR APIs
# ═══════════════════════════════════════════════════════
@app.route('/api/hr/employees')
@login_required(roles=['hr'])
def get_all_employees():
    db = get_db_data()
    return jsonify(db.get('employees', []))

@app.route('/api/hr/attendance')
@login_required(roles=['hr'])
def get_attendance():
    db = get_db_data()
    return jsonify(db.get('attendance', []))


@app.route('/api/hr/performance-all')
@login_required(roles=['hr'])
def get_all_performance():
    db     = get_db_data()
    result = []
    perfs = db.get('performance', [])
    emps = db.get('employees', [])
    for p in perfs:
        emp = next((e for e in emps if e['user_id'] == p['user_id']), {})
        result.append({
            **p,
            'name':       emp.get('name', ''),
            'department': emp.get('department', ''),
            'role':       emp.get('role', '')
        })
    return jsonify(result)


@app.route('/api/hr/stats')
@login_required(roles=['hr'])
def hr_stats():
    db = get_db_data()
    # Safely get employees list
    emps = db.get('employees', [])
    if not emps:
        return jsonify({
            'total_employees': 0,
            'active': 0,
            'inactive': 0,
            'departments': {},
            'avg_performance': 0
        })
        
    dept_dist = {}
    for e in emps:
        dept = e.get('department', 'Unknown')
        dept_dist[dept] = dept_dist.get(dept, 0) + 1
        
    perfs = db.get('performance', [])
    if perfs:
        avg_prf = round(
            sum(p.get('productivity_score', 0) for p in perfs) / len(perfs), 1
        )
    else:
        avg_prf = 0
        
    return jsonify({
        'total_employees': len(emps),
        'active': len([e for e in emps if e.get('status') == 'Active']),
        'inactive': len([e for e in emps if e.get('status') != 'Active']),
        'departments': dept_dist,
        'avg_performance': avg_prf
    })


@app.route('/api/hr/ai-predict-performance', methods=['POST'])
@login_required(roles=['hr'])
def predict_performance():
    from ml_models.predictor import predict_performance_score
    data   = request.get_json(silent=True) or {}
    result = predict_performance_score(data)
    
    # Log prediction for updates
    db = get_db_data()
    if 'ai_predictions' not in db: db['ai_predictions'] = []
    db['ai_predictions'].append({
        'user_id': session.get('user_id'),
        'prediction_type': 'performance',
        'input_data': data,
        'result_data': result,
        'confidence': result.get('confidence', 0),
        'created_at': datetime.now().isoformat()
    })
    save_db_data(db)
    
    return jsonify(result)


@app.route('/api/hr/ai-promotion', methods=['POST'])
@login_required(roles=['hr'])
def promotion_recommendation():
    from ml_models.predictor import recommend_promotion
    data   = request.get_json(silent=True) or {}
    result = recommend_promotion(data)
    return jsonify(result)


@app.route('/api/hr/ai-attrition', methods=['POST'])
@login_required(roles=['hr'])
def attrition_risk():
    from ml_models.predictor import predict_attrition
    data   = request.get_json(silent=True) or {}
    result = predict_attrition(data)
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
    text   = data.get('resume_text', '')
    result = analyze_ats(text)
    return jsonify(result)


@app.route('/api/hr/ats-upload', methods=['POST'])
@login_required(roles=['hr'])
def ats_upload():
    if 'resume' not in request.files:
        return jsonify({'success': False, 'message': 'No file part'}), 400
    
    file = request.files['resume']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No selected file'}), 400

    filename = file.filename.lower()
    text = ""
    
    try:
        file_bytes = file.read()
        print(f"DEBUG: ATS Uploading file: {filename}, size: {len(file_bytes)} bytes")
        file_stream = io.BytesIO(file_bytes)
        
        if filename.endswith('.pdf'):
            pdf_reader = PyPDF2.PdfReader(file_stream)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        elif filename.endswith('.docx'):
            doc = docx.Document(file_stream)
            for para in doc.paragraphs:
                text += para.text + "\n"
        elif filename.endswith('.doc'):
             return jsonify({'success': False, 'message': 'Please use .docx or .pdf for Word documents'}), 400
        else:
            return jsonify({'success': False, 'message': 'Unsupported file format. Please upload PDF or DOCX.'}), 400
    except Exception as e:
        print(f"DEBUG: ATS Error: {str(e)}")
        return jsonify({'success': False, 'message': f'Error processing file: {str(e)}'}), 500

    if not text.strip():
        return jsonify({'success': False, 'message': 'Could not extract text from file'}), 400
        
    # Save the file permanently to ats_resumes directory
    safe_name = secure_filename(filename)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    final_filename = f"ats_{timestamp}_{safe_name}"
    filepath = os.path.join(UPLOAD_FOLDER_ATS, final_filename)
    
    # We must reset stream position since we just read it for PDF/DOCX parsing
    file_stream.seek(0)
    with open(filepath, 'wb') as f:
        f.write(file_stream.read())

    from ml_models.predictor import analyze_ats
    result = analyze_ats(text)
    
    # Record in db
    db = get_db_data()
    if 'ats_records' not in db:
        db['ats_records'] = []
    
    db['ats_records'].append({
        'filename': final_filename,
        'uploaded_by': session['user_id'],
        'uploaded_at': datetime.now().isoformat(),
        'score': result.get('ats_score', 0)
    })
    save_db_data(db)
    result['success'] = True
    return jsonify(result)


def _send_email_real(to_email, subject, body):
    """Internal helper to send real SMTP email using admin configuration."""
    db = get_db_data()
    from database.db_init import _ensure_integrations
    integ = _ensure_integrations(db)
    e = integ.get('email', {})
    
    if not e.get('enabled'):
        print(f"DEBUG: Email skipped (disabled): To={to_email}, Sub={subject}")
        return False, "Email service is disabled in settings."
        
    host = e.get('smtp_host')
    port = int(e.get('smtp_port', 587))
    user = e.get('smtp_user')
    pwd  = e.get('smtp_password')
    from_email = e.get('from_email')
    from_name = e.get('from_name', 'PulseHR')
    use_tls = bool(e.get('use_tls', True))
    
    if not (host and from_email):
        return False, "SMTP configuration is incomplete (host/from missing)."
        
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = f"{from_name} <{from_email}>"
    msg['To'] = to_email
    msg.set_content(body)
    
    try:
        if use_tls:
            server = smtplib.SMTP(host, port, timeout=10)
            server.starttls()
        else:
            server = smtplib.SMTP(host, port, timeout=10)
            
        if user and pwd:
            server.login(user, pwd)
            
        server.send_message(msg)
        server.quit()
        return True, "Email sent successfully."
    except Exception as ex:
        print(f"DEBUG: Real Email Failed: {str(ex)}")
        return False, str(ex)

@app.route('/api/hr/send-manual-email', methods=['POST'])
@login_required(roles=['hr'])
def send_manual_email():
    data = request.get_json(silent=True) or {}
    uid = data.get('user_id')
    subject = data.get('subject', 'PulseHR Notification')
    body = data.get('body')
    
    if not uid or not body:
        return jsonify({'success': False, 'message': 'User ID and message body are required'}), 400
        
    db = get_db_data()
    user = next((u for u in db['users'] if u['id'] == uid), None)
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
        
    to_email = user.get('email')
    if not to_email:
        return jsonify({'success': False, 'message': 'User has no email address'}), 400
        
    success, msg = _send_email_real(to_email, subject, body)
    
    # Also record as a notification in the system
    from uuid import uuid4
    db['notifications'].append({
        'id': str(uuid4()),
        'message': body,
        'type': 'info',
        'target': uid,
        'from': f"HR ({session.get('name')})",
        'time': datetime.now().isoformat()
    })
    save_db_data(db)
    
    return jsonify({'success': success, 'message': msg})




# ─── Leave Management ────────────────────────────────────────────────────────
@app.route('/api/hr/ats-history')
@login_required(roles=['hr'])
def get_ats_history():
    db = get_db_data()
    return jsonify(db.get('ats_records', []))


@app.route('/api/hr/reports/employees/csv')
@login_required(roles=['hr'])
def download_employees_csv():
    db = get_db_data()
    employees = db.get('employees', [])
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['User ID', 'Name', 'Employee ID', 'Role', 'Department', 'Experience', 'Joining Date', 'Status'])
    
    for e in employees:
        writer.writerow([e.get('user_id'), e.get('name'), e.get('employee_id'), e.get('role'), e.get('department'), e.get('experience'), e.get('joining_date'), e.get('status')])
        
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f"employees_{datetime.now().strftime('%Y%m%d')}.csv"
    )

@app.route('/api/hr/reports/teams/csv')
@login_required(roles=['hr'])
def download_teams_csv():
    db = get_db_data()
    teams = db.get('teams', [])
    emps = db.get('employees', [])
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Team ID', 'Team Name', 'Leader Name', 'Member Count', 'Avg Productivity', 'Project Name', 'Completion %'])
    
    for t in teams:
        leader = next((e for e in emps if e['user_id'] == t.get('leader_id')), {})
        member_ids = t.get('member_ids', [])
        
        # Calculate avg productivity
        avg_prod = 0
        if member_ids:
            perfs = [p for p in db.get('performance', []) if p['user_id'] in member_ids]
            if perfs:
                avg_prod = sum(p.get('productivity_score', 0) for p in perfs) / len(perfs)
        
        writer.writerow([
            t.get('id'), 
            t.get('name'), 
            leader.get('name', 'N/A'), 
            len(member_ids), 
            round(avg_prod, 1),
            t.get('project_name', 'N/A'),
            t.get('project_completion', 0)
        ])
        
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f"team_performance_{datetime.now().strftime('%Y%m%d')}.csv"
    )

@app.route('/api/hr/reports/projects/csv')
@login_required(roles=['hr'])
def download_projects_csv():
    db = get_db_data()
    teams = db.get('teams', [])
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Project Name', 'Assigned Team', 'Status', 'Completion %', 'Description'])
    
    for t in teams:
        if t.get('project_name'):
            writer.writerow([
                t.get('project_name'),
                t.get('name'),
                t.get('project_status', 'In Progress'),
                t.get('project_completion', 0),
                t.get('description', '')
            ])
            
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f"project_list_{datetime.now().strftime('%Y%m%d')}.csv"
    )

@app.route('/api/hr/reports/performance/pdf')
@login_required(roles=['hr'])
def download_performance_pdf():
    # Since we don't have reportlab, let's generate a text/csv for now but call it .csv or similar
    # or just use text/plain. For a true PDF, we'd need a lib.
    # We'll generate a CSV for now as a "report".
    db = get_db_data()
    perfs = db.get('performance', [])
    emps = db.get('employees', [])
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Name', 'Productivity', 'Attendance %', 'Task Completion %', 'Quality Rating', 'TL Score'])
    
    for p in perfs:
        emp = next((e for e in emps if e['user_id'] == p['user_id']), {})
        writer.writerow([emp.get('name', 'N/A'), p.get('productivity_score'), p.get('attendance_pct'), p.get('task_completion'), p.get('quality_rating'), p.get('tl_score')])
        
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f"performance_report_{datetime.now().strftime('%Y%m%d')}.csv"
    )

@app.route('/api/hr/reports/attendance/xlsx')
@login_required(roles=['hr'])
def download_attendance_xlsx():
    db = get_db_data()
    attendance = db.get('attendance', [])
    emps = db.get('employees', [])
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Employee Name', 'Month', 'Present', 'Absent', 'Late', 'Total Days', 'Hours'])
    
    for a in attendance:
        emp = next((e for e in emps if e['user_id'] == a['user_id']), {})
        writer.writerow([emp.get('name', 'N/A'), a.get('month'), a.get('present'), a.get('absent'), a.get('late'), a.get('total'), a.get('hours')])
        
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f"attendance_data_{datetime.now().strftime('%Y%m%d')}.csv"
    )

@app.route('/api/hr/leave-requests')
@login_required(roles=['hr'])
def get_leave_requests():
    db = get_db_data()
    return jsonify(db.get('leave_requests', []))


@app.route('/api/hr/leave-approve', methods=['POST'])
@login_required(roles=['hr'])
def approve_leave():
    data = request.get_json(silent=True) or {}
    rid = data.get('request_id')
    if not rid:
        return jsonify({'success': False, 'message': 'request_id required'}), 400
    db = get_db_data()
    if 'leave_requests' not in db:
        db['leave_requests'] = []
    
    updated = False
    for lr in db['leave_requests']:
        if lr['id'] == rid:
            # Allow HR to approve if it's Pending OR Approved (TL)
            if lr.get('status') not in ['Pending', 'Approved (TL)']:
                 return jsonify({'success': False, 'message': 'Leave must be in Pending or Approved (TL) status'}), 400
            
            lr['status'] = 'Approved'
            lr['hr_reviewed_by'] = session['name']
            lr['hr_reviewed_at'] = datetime.now().isoformat()
            updated = True
            break
    
    if updated:
        save_db_data(db)
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Leave request not found'}), 404


@app.route('/api/hr/leave-reject', methods=['POST'])
@login_required(roles=['hr'])
def reject_leave():
    data = request.get_json(silent=True) or {}
    rid = data.get('request_id')
    if not rid:
        return jsonify({'success': False, 'message': 'request_id required'}), 400
    db = get_db_data()
    if 'leave_requests' not in db:
        db['leave_requests'] = []
    for lr in db['leave_requests']:
        if lr['id'] == rid:
            lr['status'] = 'Rejected'
            lr['reviewed_by'] = session['name']
            lr['reviewed_at'] = datetime.now().isoformat()
            break
    save_db_data(db)
    return jsonify({'success': True})


# ─── Employee Leave Apply ─────────────────────────────────────────────────────
@app.route('/api/employee/apply-leave', methods=['POST'])
@login_required(roles=['employee'])
def apply_leave():
    data = request.get_json(silent=True) or {}
    if not data.get('from_date') or not data.get('to_date'):
        return jsonify({'success': False, 'message': 'from_date and to_date are required'}), 400
    db = get_db_data()
    if 'leave_requests' not in db:
        db['leave_requests'] = []
    emp = next((e for e in db['employees'] if e['user_id'] == session['user_id']), {})
    # auto-generate ID
    existing_ids = [int(lr['id'][2:]) for lr in db['leave_requests'] if lr['id'].startswith('LR') and lr['id'][2:].isdigit()]
    next_id = f"LR{(max(existing_ids) + 1):03d}" if existing_ids else 'LR001'
    from_dt = datetime.strptime(data['from_date'], '%Y-%m-%d')
    to_dt = datetime.strptime(data['to_date'], '%Y-%m-%d')
    days = (to_dt - from_dt).days + 1
    db['leave_requests'].append({
        'id': next_id,
        'user_id': session['user_id'],
        'employee_name': session['name'],
        'department': emp.get('department', ''),
        'type': data.get('leave_type', 'Casual Leave'),
        'from_date': data['from_date'],
        'to_date': data['to_date'],
        'days': days,
        'reason': data.get('reason', ''),
        'is_emergency': data.get('is_emergency', False),
        'status': 'Pending',
        'applied_on': datetime.now().strftime('%Y-%m-%d')
    })
    save_db_data(db)
    return jsonify({'success': True, 'id': next_id})

@app.route('/api/employee/my-leaves', methods=['GET'])
@login_required(roles=['employee'])
def get_employee_leaves():
    db = get_db_data()
    my_leaves = [lr for lr in db.get('leave_requests', []) if lr['user_id'] == session['user_id']]
    return jsonify(my_leaves)

@app.route('/api/employee/my-team', methods=['GET'])
@login_required(roles=['employee'])
def get_employee_my_team():
    db = get_db_data()
    uid = session['user_id']
    
    # Find the team where the user is a member or leader
    my_team_obj = None
    for t in db.get('teams', []):
        if uid == t.get('leader_id') or uid in t.get('member_ids', []):
            my_team_obj = t
            break
            
    if not my_team_obj:
        return jsonify({'team_name': 'No Team Assigned', 'members': [], 'project_name': 'N/A', 'project_completion': 0})
        
    all_member_ids = [my_team_obj.get('leader_id')] + my_team_obj.get('member_ids', [])
    team_members = [e for e in db['employees'] if e['user_id'] in all_member_ids]
    
    safe_team_members = []
    for m in team_members:
        safe_team_members.append({
            'user_id': m['user_id'],
            'name': m['name'],
            'role': m['role'],
            'department': m['department'],
            'skills': m.get('skills', ''),
            'is_me': m['user_id'] == uid,
            'is_tl': m['user_id'] == my_team_obj.get('leader_id')
        })
        
    return jsonify({
        'team_name': my_team_obj.get('name', 'Unnamed Team'),
        'project_name': my_team_obj.get('project_name', 'No Active Project'),
        'project_completion': my_team_obj.get('project_completion', 0),
        'members': safe_team_members
    })


# ─── Team Management ──────────────────────────────────────────────────────────
@app.route('/api/hr/teams')
@login_required(roles=['hr'])
def get_teams():
    db = get_db_data()
    if 'teams' not in db:
        db['teams'] = []
    teams = db['teams']
    result = []
    for t in teams:
        leader = next((e for e in db['employees'] if e['user_id'] == t.get('leader_id')), {})
        members = [e for e in db['employees'] if e['user_id'] in t.get('member_ids', [])]
        member_perfs = []
        for m in members:
            p = next((p for p in db['performance'] if p['user_id'] == m['user_id']), {})
            member_perfs.append({
                'user_id': m['user_id'],
                'name': m['name'],
                'role': m.get('role', ''),
                'productivity_score': p.get('productivity_score', 0),
                'attendance_pct': p.get('attendance_pct', 0),
                'monthly_trend': p.get('monthly_trend', [])
            })
        result.append({
            **t,
            'leader_name': leader.get('name', 'Unassigned'),
            'leader_role': leader.get('role', ''),
            'member_count': len(members),
            'members': member_perfs,
            'avg_member_score': round(sum(m['productivity_score'] for m in member_perfs) / max(len(member_perfs), 1), 1)
        })
    return jsonify(result)


@app.route('/api/hr/teams/assign-members', methods=['POST'])
@login_required(roles=['hr'])
def assign_team_members():
    data = request.get_json(silent=True) or {}
    if not data.get('team_id'):
        return jsonify({'success': False, 'message': 'team_id required'}), 400
    db = get_db_data()
    if 'teams' not in db:
        db['teams'] = []
    target_members = list(map(str, data.get('member_ids', [])))
    for t in db['teams']:
        if t['id'] == data['team_id']:
            t['member_ids'] = target_members if target_members else t['member_ids']
            break
    # sync team_leader_id for TL views
    tl_id = None
    for t in db['teams']:
        if t['id'] == data['team_id']:
            tl_id = t.get('leader_id')
            break
    if tl_id and target_members:
        for e in db.get('employees', []):
            if str(e.get('user_id')) in set(target_members):
                e['team_leader_id'] = tl_id
    save_db_data(db)
    return jsonify({'success': True})


@app.route('/api/hr/teams/assign-leader', methods=['POST'])
@login_required(roles=['hr'])
def assign_team_leader():
    data = request.get_json(silent=True) or {}
    if not data.get('team_id') or not data.get('leader_id'):
        return jsonify({'success': False, 'message': 'team_id and leader_id required'}), 400
    db = get_db_data()
    if 'teams' not in db:
        db['teams'] = []
    for t in db['teams']:
        if t['id'] == data['team_id']:
            t['leader_id'] = data['leader_id']
            break
    # propagate TL change to current team members
    for t in db['teams']:
        if t['id'] == data['team_id']:
            for e in db.get('employees', []):
                if str(e.get('user_id')) in set(t.get('member_ids', [])):
                    e['team_leader_id'] = data['leader_id']
            break
    save_db_data(db)
    return jsonify({'success': True})


@app.route('/api/hr/teams/assign-project', methods=['POST'])
@login_required(roles=['hr'])
def assign_team_project():
    data = request.get_json(silent=True) or {}
    if not data.get('project_name'):
        return jsonify({'success': False, 'message': 'project_name required'}), 400
    db = get_db_data()
    if 'teams' not in db:
        db['teams'] = []
    assign_all = data.get('assign_all', False)
    for t in db['teams']:
        if assign_all or t['id'] == data.get('team_id'):
            t['project_name'] = data['project_name']
            t['project_status'] = data.get('project_status', 'In Progress')
            t['project_completion'] = int(data.get('project_completion', t.get('project_completion', 0)))
    save_db_data(db)
    return jsonify({'success': True})


@app.route('/api/hr/teams/set-score', methods=['POST'])
@login_required(roles=['hr'])
def set_team_score():
    data = request.get_json(silent=True) or {}
    if not data.get('team_id'):
        return jsonify({'success': False, 'message': 'team_id required'}), 400
    db = get_db_data()
    if 'teams' not in db:
        db['teams'] = []
    score = max(0, min(100, int(data.get('score', 0))))
    for t in db['teams']:
        if t['id'] == data['team_id']:
            t['score'] = score
            if 'monthly_scores' not in t:
                t['monthly_scores'] = [score]
            else:
                t['monthly_scores'].append(score)
                t['monthly_scores'] = t['monthly_scores'][-6:]
            break
    save_db_data(db)
    return jsonify({'success': True})


@app.route('/api/hr/report/<report_type>')
@login_required(roles=['hr'])
def generate_report(report_type):
    allowed = {'performance', 'attendance', 'promotion', 'attrition', 'salary'}
    if report_type not in allowed:
        return jsonify({'error': 'Invalid report type'}), 400

    from utils.report_gen import generate_csv_report
    from io import BytesIO
    db       = get_db_data()
    csv_data = generate_csv_report(report_type, db)
    output   = BytesIO(csv_data.encode('utf-8'))
    output.seek(0)
    return send_file(
        output, mimetype='text/csv', as_attachment=True,
        download_name=f'{report_type}_report.csv'
    )


# ═══════════════════════════════════════════════════════
#  ADMIN APIs
# ═══════════════════════════════════════════════════════
@app.route('/api/admin/users')
@login_required(roles=['admin'])
def get_all_users():
    db   = get_db_data()
    result = []
    for u in db['users']:
        u_copy = {k: v for k, v in u.items() if k != 'password'}
        # Join employee details
        for e in db['employees']:
            if e['user_id'] == u['id']:
                u_copy['job_role'] = e.get('role')
                u_copy['department'] = e.get('department')
                u_copy['experience'] = e.get('experience')
                u_copy['skills'] = e.get('skills')
                u_copy['salary'] = e.get('salary')
                break
        result.append(u_copy)
    return jsonify(result)


@app.route('/api/admin/create-user', methods=['POST'])
@login_required(roles=['admin'])
def create_user():
    data = request.get_json(silent=True) or {}
    if not data.get('name') or not data.get('email'):
        return jsonify({'success': False, 'message': 'name and email are required'}), 400

    db  = get_db_data()
    # Check duplicate email
    if any(u['email'].lower() == data['email'].lower() for u in db['users']):
        return jsonify({'success': False, 'message': 'Email already exists'}), 409

    uid = _next_user_id(db)
    u_role = data.get('role', 'employee')
    raw_password = data.get('password', 'password123')
    db['users'].append({
        'id':         uid,
        'name':       data['name'],
        'email':      data['email'].lower().strip(),
        'password':   generate_password_hash(raw_password),
        'role':       u_role,
        'status':     'Active',
        'created_at': datetime.now().isoformat()
    })

    # Everyone except admin gets an employee & performance handle
    if u_role != 'admin':
        # employee_id: TL### for teamleaders, EMP#### for others
        if u_role == 'teamleader':
            tl_ids = [int(e['employee_id'][2:]) for e in db.get('employees', []) if isinstance(e.get('employee_id'), str) and e['employee_id'].startswith('TL') and e['employee_id'][2:].isdigit()]
            next_num = (max(tl_ids) + 1) if tl_ids else 1
            employee_id = f"TL{next_num:03d}"
        elif u_role == 'hr':
            hr_ids = [int(e['employee_id'][2:]) for e in db.get('employees', []) if isinstance(e.get('employee_id'), str) and e['employee_id'].startswith('HR') and e['employee_id'][2:].isdigit()]
            next_num = (max(hr_ids) + 1) if hr_ids else 1
            employee_id = f"HR{next_num:03d}"
        else:
            employee_id = f"EMP{uid[1:]}"
        db['employees'].append({
            'user_id':           uid,
            'name':              data['name'],
            'employee_id':       employee_id,
            'role':              data.get('job_role', u_role.capitalize()),
            'department':        data.get('department', 'Engineering'),
            'skills':            data.get('skills', ''),
            'experience':        int(data.get('experience', 0)),
            'joining_date':      datetime.now().strftime('%Y-%m-%d'),
            'projects_completed': 0,
            'status':            'Active',
            'team_leader_id':    data.get('team_leader_id'),
            'salary':            float(data.get('salary', 0))
        })
        db['performance'].append({
            'user_id':          uid,
            'name':             data['name'],
            'productivity_score': 0,
            'attendance_pct':   100,
            'task_completion':  0,
            'quality_rating':   0,
            'tl_score':         0,
            'satisfaction':     75,
            'monthly_trend':    [0, 0, 0, 0, 0, 0]
        })

    save_db_data(db)
    log_system_activity(f"Admin created a new user profile: {data['name']} ({data['role']})")
    return jsonify({'success': True, 'user_id': uid})


@app.route('/api/admin/update-user', methods=['POST'])
@login_required(roles=['admin'])
def update_user():
    data = request.get_json(silent=True) or {}
    uid  = data.get('user_id')
    if not uid:
        return jsonify({'success': False, 'message': 'user_id required'}), 400

    db = get_db_data()
    # Update User account
    user_found = False
    for u in db['users']:
        if u['id'] == uid:
            if 'name' in data: u['name'] = data['name']
            if 'email' in data: u['email'] = data['email'].lower().strip()
            if 'role' in data: u['role'] = data['role']
            user_found = True
            break
    
    if not user_found:
        return jsonify({'success': False, 'message': 'User not found'}), 404

    # Update Employee record if exists
    for e in db['employees']:
        if e['user_id'] == uid:
            if 'name' in data: e['name'] = data['name']
            if 'job_role' in data: e['role'] = data['job_role']
            if 'department' in data: e['department'] = data['department']
            if 'experience' in data: e['experience'] = int(data['experience'])
            if 'salary' in data: e['salary'] = float(data['salary'])
            if 'skills' in data: e['skills'] = data['skills']
            break

    # Update Performance name if exists
    for p in db['performance']:
        if p['user_id'] == uid:
            if 'name' in data: p['name'] = data['name']
            break

    save_db_data(db)
    log_system_activity(f"Admin updated user profile details for user ID: {uid}")
    return jsonify({'success': True})


@app.route('/api/admin/toggle-user', methods=['POST'])
@login_required(roles=['admin'])
def toggle_user():
    data = request.get_json(silent=True) or {}
    if not data.get('user_id'):
        return jsonify({'success': False, 'message': 'user_id required'}), 400

    db = get_db_data()
    for u in db['users']:
        if u['id'] == data['user_id']:
            u['status'] = 'Inactive' if u.get('status') == 'Active' else 'Active'
            # mirror status in employee record
            for e in db['employees']:
                if e['user_id'] == data['user_id']:
                    e['status'] = u['status']
            break

    save_db_data(db)
    log_system_activity(f"Admin toggled access state for user ID: {data['user_id']}")
    return jsonify({'success': True})


@app.route('/api/admin/delete-user', methods=['POST'])
@login_required(roles=['admin'])
def delete_user():
    data = request.get_json(silent=True) or {}
    uid  = data.get('user_id')
    if not uid:
        return jsonify({'success': False, 'message': 'user_id required'}), 400
    # Prevent self-deletion
    if uid == session.get('user_id'):
        return jsonify({'success': False, 'message': 'Cannot delete your own account'}), 403

    db = get_db_data()
    db['users']       = [u for u in db['users']       if u['id']      != uid]
    db['employees']   = [e for e in db['employees']   if e['user_id'] != uid]
    db['performance'] = [p for p in db['performance'] if p['user_id'] != uid]
    db['tasks']       = [t for t in db['tasks']
                         if t.get('assigned_to') != uid and t.get('assigned_by') != uid]
    save_db_data(db)
    log_system_activity(f"Admin permanently deleted user account: {uid}")
    return jsonify({'success': True})


@app.route('/api/admin/reset-password', methods=['POST'])
@login_required(roles=['admin'])
def reset_password():
    data = request.get_json(silent=True) or {}
    uid  = data.get('user_id')
    new_pass = data.get('new_password', '').strip()
    if not uid or not new_pass:
        return jsonify({'success': False, 'message': 'user_id and new_password required'}), 400
    if len(new_pass) < 6:
        return jsonify({'success': False, 'message': 'Password must be at least 6 characters'}), 400

    db = get_db_data()
    for u in db['users']:
        if u['id'] == uid:
            u['password'] = generate_password_hash(new_pass)
            break
    save_db_data(db)
    log_system_activity(f"Admin enforced a password reset for user ID: {uid}")
    return jsonify({'success': True})


@app.route('/api/admin/login-logs')
@login_required(roles=['admin'])
def get_login_logs():
    db = get_db_data()
    return jsonify(db['login_logs'][-50:])


@app.route('/api/admin/system-stats')
@login_required(roles=['admin'])
def system_stats():
    db = get_db_data()
    return jsonify({
        'total_users':      len(db['users']),
        'total_employees':  len(db['employees']),
        'total_tasks':      len(db['tasks']),
        'login_logs_count': len(db['login_logs']),
        'server_status':    'Online',
        'db_engine':        'JSON File Store',
        'db_size_kb':       round(len(json.dumps(db)) / 1024, 1)
    })


@app.route('/api/admin/system-activities')
@login_required(roles=['admin', 'hr'])
def get_system_activities():
    db = get_db_data()
    return jsonify(db.get('system_activities', [])[-100:])

# ─── Admin: Integrations Config ──────────────────────────────────────────────
def _mask(s, keep=2):
    if not s:
        return ''
    if len(s) <= keep:
        return '*' * len(s)
    return s[:keep] + '*' * (len(s) - keep)

def _ensure_integrations(db):
    if 'integrations' not in db:
        db['integrations'] = {
            'email':    {'enabled': False, 'smtp_host': '', 'smtp_port': 587, 'smtp_user': '', 'smtp_password': '', 'from_email': '', 'use_tls': True},
            'slack':    {'enabled': False, 'webhook_url': '', 'channel': ''},
            'calendar': {'enabled': False, 'provider': '', 'calendar_id': '', 'api_key': '', 'ics_url': ''}
        }
    return db['integrations']

@app.route('/api/admin/integrations', methods=['GET'])
@login_required(roles=['admin'])
def get_integrations():
    db = get_db_data()
    integ = _ensure_integrations(db)
    safe = {
        'email': {
            'enabled': integ['email'].get('enabled', False),
            'smtp_host': integ['email'].get('smtp_host', ''),
            'smtp_port': integ['email'].get('smtp_port', 587),
            'smtp_user': _mask(integ['email'].get('smtp_user', '')),
            'from_email': integ['email'].get('from_email', ''),
            'use_tls': integ['email'].get('use_tls', True),
            'has_password': bool(integ['email'].get('smtp_password'))
        },
        'slack': {
            'enabled': integ['slack'].get('enabled', False),
            'webhook_url': _mask(integ['slack'].get('webhook_url', '')),
            'channel': integ['slack'].get('channel', '')
        },
        'calendar': {
            'enabled': integ['calendar'].get('enabled', False),
            'provider': integ['calendar'].get('provider', ''),
            'calendar_id': integ['calendar'].get('calendar_id', ''),
            'api_key': _mask(integ['calendar'].get('api_key', '')),
            'ics_url': _mask(integ['calendar'].get('ics_url', ''))
        }
    }
    return jsonify(safe)

@app.route('/api/admin/integrations/<service>', methods=['POST'])
@login_required(roles=['admin'])
def update_integration(service):
    data = request.get_json(silent=True) or {}
    if service not in ['email','slack','calendar']:
        return jsonify({'success': False, 'message': 'Unknown service'}), 400
    db = get_db_data()
    integ = _ensure_integrations(db)
    if service == 'email':
        e = integ['email']
        e['enabled']      = bool(data.get('enabled', e.get('enabled', False)))
        e['smtp_host']    = data.get('smtp_host', e.get('smtp_host', ''))
        e['smtp_port']    = int(data.get('smtp_port', e.get('smtp_port', 587)))
        e['smtp_user']    = data.get('smtp_user', e.get('smtp_user', ''))
        e['from_email']   = data.get('from_email', e.get('from_email', ''))
        e['use_tls']      = bool(data.get('use_tls', e.get('use_tls', True)))
        if 'smtp_password' in data and data.get('smtp_password'):
            e['smtp_password'] = data['smtp_password']
    elif service == 'slack':
        s = integ['slack']
        s['enabled']     = bool(data.get('enabled', s.get('enabled', False)))
        if 'webhook_url' in data and data.get('webhook_url'):
            s['webhook_url'] = data['webhook_url']
        s['channel']     = data.get('channel', s.get('channel',''))
    elif service == 'calendar':
        c = integ['calendar']
        c['enabled']    = bool(data.get('enabled', c.get('enabled', False)))
        c['provider']   = data.get('provider', c.get('provider',''))
        c['calendar_id']= data.get('calendar_id', c.get('calendar_id',''))
        if 'api_key' in data and data.get('api_key'):
            c['api_key']  = data['api_key']
        if 'ics_url' in data and data.get('ics_url'):
            c['ics_url']  = data['ics_url']
    save_db_data(db)
    return jsonify({'success': True})


# ─── New Team Performance & Rating Routes ───────────────────────────────────
@app.route('/api/tl/rate-employee', methods=['POST'])
@login_required(roles=['teamleader'])
def tl_rate_employee():
    data = request.get_json(silent=True) or {}
    eid = data.get('employee_id')
    rating = data.get('rating', 0)
    feedback = data.get('feedback', '')
    
    if not eid:
        return jsonify({'success': False, 'message': 'employee_id required'}), 400
        
    db = get_db_data()
    if 'tl_ratings' not in db: db['tl_ratings'] = []
    db['tl_ratings'].append({
        'employee_id': eid,
        'tl_id': session['user_id'],
        'rating': int(rating),
        'feedback': feedback,
        'recorded_at': datetime.now().isoformat()
    })
    save_db_data(db)
    return jsonify({'success': True})

@app.route('/api/hr/team-performance')
@login_required(roles=['hr', 'admin'])
def get_all_team_performance():
    db = get_db_data()
    return jsonify(db.get('team_performance', []))

@app.route('/api/hr/team-projects')
@login_required(roles=['hr', 'admin'])
def get_all_team_projects():
    db = get_db_data()
    return jsonify(db.get('team_projects', []))

@app.route('/api/hr/teams/create', methods=['POST'])
@login_required(roles=['hr', 'admin'])
def create_team():
    data = request.get_json(silent=True) or {}
    name = data.get('name')
    leader_id = data.get('leader_id')
    member_ids = [str(m) for m in data.get('member_ids', []) if m]
    
    if not name or not leader_id:
        return jsonify({'success': False, 'message': 'Team name and leader are required'}), 400
        
    db = get_db_data()
    if 'teams' not in db: db['teams'] = []
    
    # Generate ID
    existing_ids = [int(t['id'][2:]) for t in db['teams'] if t['id'].startswith('TM') and t['id'][2:].isdigit()]
    next_id = f"TM{(max(existing_ids) + 1):03d}" if existing_ids else 'TM001'
    
    new_team = {
        'id': next_id,
        'name': name,
        'description': data.get('description', ''),
        'leader_id': str(leader_id),
        'member_ids': member_ids,
        'project_name': data.get('project_name', 'New Project'),
        'project_status': 'In Progress',
        'project_completion': 0,
        'score': 0,
        'monthly_scores': [0,0,0,0,0,0]
    }
    
    db['teams'].append(new_team)
    
    # Update employee team_leader_id for members
    for mid in member_ids:
        for emp in db.get('employees', []):
            if str(emp.get('user_id')) == mid:
                emp['team_leader_id'] = str(leader_id)
                break
                
    save_db_data(db)
    return jsonify({'success': True, 'team_id': next_id})

@app.route('/api/hr/teams/delete', methods=['POST'])
@login_required(roles=['hr', 'admin'])
def delete_team():
    data = request.get_json(silent=True) or {}
    tid = data.get('team_id')
    if not tid:
        return jsonify({'success': False, 'message': 'team_id required'}), 400
        
    db = get_db_data()
    team = next((t for t in db.get('teams', []) if t['id'] == tid), None)
    if not team:
        return jsonify({'success': False, 'message': 'Team not found'}), 404
        
    # Reset team_leader_id for members
    for mid in team.get('member_ids', []):
        for emp in db.get('employees', []):
            if str(emp.get('user_id')) == str(mid):
                emp['team_leader_id'] = None
                break
                
    db['teams'] = [t for t in db.get('teams', []) if t['id'] != tid]
    
    # Also cleanup related data
    if 'team_performance' in db:
        db['team_performance'] = [p for p in db['team_performance'] if p.get('team_id') != tid]
    if 'team_projects' in db:
        db['team_projects'] = [p for p in db['team_projects'] if p.get('team_id') != tid]
    if 'team_member_tasks' in db:
        db['team_member_tasks'] = [s for s in db['team_member_tasks'] if s.get('team_id') != tid]
        
    save_db_data(db)
    return jsonify({'success': True})

@app.route('/api/hr/unallocated-members')
@login_required(roles=['hr', 'admin'])
def get_unallocated_members():
    db = get_db_data()
    allocated_ids = set()
    for t in db.get('teams', []):
        for mid in t.get('member_ids', []):
            if mid: allocated_ids.add(str(mid))
        if t.get('leader_id'):
            allocated_ids.add(str(t['leader_id']))
            
    # Filter out active employees who are not in the allocated_ids set, and whose system role is NOT HR
    users_dict = {u['id']: u for u in db.get('users', [])}
    unallocated = [
        e for e in db.get('employees', []) 
        if str(e.get('user_id')) not in allocated_ids 
        and e.get('status') == 'Active'
        and users_dict.get(e.get('user_id'), {}).get('role', '').lower() != 'hr'
    ]
    return jsonify(unallocated)

@app.route('/api/hr/teams-detailed')
@login_required(roles=['hr', 'admin'])
def get_teams_detailed():
    db = get_db_data()
    teams = db.get('teams', [])
    perf  = db.get('team_performance', [])
    projs = db.get('team_projects', [])
    emps  = db.get('employees', [])
    
    detailed = []
    for t in teams:
        t_perf = [p for p in perf if p.get('team_id') == t['id']]
        t_proj = [p for p in projs if p.get('team_id') == t['id']]
        
        # Resolve leader name and members
        leader = next((e for e in emps if e['user_id'] == t.get('leader_id')), {})
        member_list = []
        for mid in t.get('member_ids', []):
            m = next((e for e in emps if e['user_id'] == mid), None)
            if m:
                p = next((p for p in db.get('performance', []) if p['user_id'] == m['user_id']), {})
                member_list.append({
                    'user_id': m['user_id'],
                    'name': m['name'],
                    'role': m['role'],
                    'productivity_score': p.get('productivity_score', 0),
                    'quality_rating': p.get('quality_rating', 0)
                })
        
        detailed.append({
            'id': t.get('id'),
            'name': t.get('name', 'Unnamed Team'),
            'description': t.get('description', ''),
            'leader_id': t.get('leader_id'),
            'member_ids': t.get('member_ids', []),
            'project_name': t.get('project_name', 'No Active Project'),
            'project_status': t.get('project_status', 'N/A'),
            'project_completion': t.get('project_completion', 0),
            'score': t.get('score', 0),
            'leader_name': leader.get('name', 'Unassigned'),
            'department': leader.get('department', 'N/A'),
            'members': member_list,
            'performance_history': t_perf,
            'projects': t_proj,
            'latest_performance': t_perf[-1] if t_perf else None
        })
    return jsonify(detailed)

@app.route('/api/tl/team-task-stats')
@login_required(roles=['teamleader'])
def get_team_task_stats():
    db = get_db_data()
    tid = None
    # Find team for current TL
    for t in db.get('teams', []):
        if t.get('leader_id') == session['user_id']:
            tid = t['id']
            break
    
    if not tid: return jsonify([])
    
    stats = []
    employees = {e['user_id']: e['name'] for e in db.get('employees', [])}
    for s in db.get('team_member_tasks', []):
        if s['team_id'] == tid:
            s_copy = s.copy()
            s_copy['name'] = employees.get(s['user_id'], 'Unknown')
            stats.append(s_copy)
    return jsonify(stats)

# ─── AI Performance Module APIs ──────────────────────────────────────────────

@app.route('/api/ai/employee-data')
@login_required(roles=['hr', 'admin'])
def get_ai_employee_data():
    db = get_db_data()
    uid = request.args.get('user_id')
    if not uid:
        return jsonify({'success': False, 'message': 'user_id is required'}), 400
    
    emp = next((e for e in db['employees'] if e['user_id'] == uid), None)
    perf = next((p for p in db['performance'] if p['user_id'] == uid), None)
    
    if not emp:
        return jsonify({'success': False, 'message': 'Employee not found'}), 404
        
    return jsonify({
        'success': True,
        'employee': emp,
        'performance': perf or {}
    })

@app.route('/api/ai/productivity-score', methods=['POST'])
@login_required(roles=['hr', 'admin'])
def calculate_productivity_score_ai():
    data = request.get_json()
    metrics = ai_service.calculate_metrics(data)
    return jsonify({
        'success': True,
        'metrics': metrics
    })

@app.route('/api/ai/performance-prediction', methods=['POST'])
@login_required(roles=['hr', 'admin'])
def predict_performance_ai():
    data = request.get_json()
    metrics = data.get('metrics')
    rating = data.get('manager_rating', 3)
    exp = data.get('experience_years', 1)
    
    prediction, probability = ai_service.predict_performance(metrics, rating, exp)
    
    return jsonify({
        'success': True,
        'predicted_performance': prediction,
        'probability': probability
    })

@app.route('/api/ai/promotion-recommendation', methods=['POST'])
@login_required(roles=['hr', 'admin'])
def get_promotion_recommendation_ai():
    data = request.get_json()
    p_score = data.get('productivity_score', 0)
    a_score = data.get('attendance_score', 0)
    exp = data.get('experience_years', 0)
    rating = data.get('manager_rating', 0)
    
    status = ai_service.get_promotion_recommendation(p_score, a_score, exp, rating)
    
    return jsonify({
        'success': True,
        'promotion_status': status
    })

@app.route('/api/ai/full-analysis/<uid>')
@login_required(roles=['hr', 'admin'])
def get_full_ai_analysis(uid):
    db = get_db_data()
    emp = next((e for e in db['employees'] if e['user_id'] == uid), None)
    perf = next((p for p in db['performance'] if p['user_id'] == uid), None)
    
    if not emp:
        return jsonify({'success': False, 'message': 'Employee not found'}), 404
    
    # Mock some raw data for analysis if not present
    # In a real app, these would come from the database
    raw_data = {
        'present_days': perf.get('attendance_pct', 90) * 0.22 if perf else 20,
        'total_working_days': 22,
        'completed_tasks': perf.get('task_completion', 80) * 0.1 if perf else 8,
        'assigned_tasks': 10,
        'bug_rate': 5,
        'rework_rate': 2,
        'peer_review_score': perf.get('satisfaction', 80) if perf else 85
    }
    
    metrics = ai_service.calculate_metrics(raw_data)
    prediction, prob = ai_service.predict_performance(metrics, perf.get('tl_score', 3) if perf else 3, emp.get('experience', 1))
    promo_status = ai_service.get_promotion_recommendation(metrics['productivity_score'], metrics['attendance_score'], emp.get('experience', 1), perf.get('tl_score', 3) if perf else 3)
    
    return jsonify({
        'success': True,
        'name': emp['name'],
        'metrics': metrics,
        'prediction': prediction,
        'probability': prob,
        'recommendation': promo_status
    })

# ─── Entry Point ─────────────────────────────────────────────────────────────
if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    print(f"✅ PulseHR started — http://localhost:{port} (debug={debug})")
    app.run(debug=debug, host='0.0.0.0', port=port)
