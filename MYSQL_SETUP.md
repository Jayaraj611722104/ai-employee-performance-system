# PulseHR — MySQL Setup Guide

## ⚡ Quick Start (3 Steps)

### Step 1 — Install dependencies
```bash
pip install -r requirements_mysql.txt
```

### Step 2 — Configure database
Open `config.py` and set your MySQL credentials:
```python
MYSQL_HOST     = 'localhost'
MYSQL_PORT     = 3306
MYSQL_USER     = 'root'
MYSQL_PASSWORD = 'your_password'   # ← change this
MYSQL_DB       = 'pulsehr'
```
Or use environment variables:
```bash
export MYSQL_PASSWORD=your_password
export MYSQL_USER=root
export MYSQL_DB=pulsehr
```

### Step 3 — Create database + seed data
```sql
-- In MySQL console:
CREATE DATABASE pulsehr CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```
Then run the seeder:
```bash
python database/seed_mysql.py
```

### Step 4 — Run the application
```bash
python app_mysql.py
```
Open: **http://localhost:5000**

---

## 🔐 Demo Login Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@company.com | admin123 |
| HR Manager | hr@company.com | hr123 |
| Team Leader | tl@company.com | tl123 |
| Employee | employee@gmail.com | emp123 |

---

## 📁 MySQL File Structure

```
hr_system/
├── app_mysql.py              ← Main Flask app (MySQL version)
├── config.py                 ← Database config & credentials
├── requirements_mysql.txt    ← All Python dependencies
│
├── database/
│   ├── models.py             ← SQLAlchemy ORM models (all 9 tables)
│   ├── seed_mysql.py         ← Seed script (inserts demo data)
│   ├── schema.sql            ← Raw MySQL DDL (for reference)
│   └── sample_dataset.csv    ← Sample data CSV
│
├── ml_models/
│   └── predictor.py          ← AI modules (Random Forest)
│
├── utils/
│   ├── report_gen.py         ← CSV reports (JSON version)
│   └── report_gen_mysql.py   ← CSV reports (MySQL version)
│
└── templates/                ← All HTML dashboards (same for both versions)
    ├── login.html
    ├── base.html
    ├── employee_dashboard.html
    ├── teamleader_dashboard.html
    ├── hr_dashboard.html
    └── admin_dashboard.html
```

---

## 🗄️ Database Schema (9 Tables)

| Table | Description |
|-------|-------------|
| `users` | Authentication — id, email, password_hash, role, status |
| `employees` | Employee profiles — department, role, skills, salary |
| `performance` | Performance metrics — productivity, attendance, quality |
| `tasks` | Task management — priority, deadline, status, progress |
| `attendance` | Daily attendance records |
| `notifications` | System & HR notifications |
| `weekly_updates` | Employee weekly self-reports |
| `login_logs` | Login activity tracking |
| `training` | Fresher training records |
| `ai_predictions` | Log of all AI predictions made |

---

## 🔗 MySQL Connection String Format

```python
# Standard
mysql+pymysql://username:password@host:port/database

# With SSL (production)
mysql+pymysql://user:pass@host/db?ssl_ca=/path/to/ca.pem&ssl_verify_cert=true

# Remote server
mysql+pymysql://admin:mypass@db.myserver.com:3306/pulsehr
```

---

## 🌐 All API Endpoints

### Auth
```
POST  /login                          Login (returns role + redirect)
GET   /logout                         End session
```

### Employee APIs  (role: employee)
```
GET   /api/employee/profile           My profile
GET   /api/employee/tasks             My assigned tasks
POST  /api/employee/update-task       Update task status/progress
POST  /api/employee/weekly-update     Submit weekly self-report
GET   /api/employee/performance       My performance metrics
GET   /api/employee/notifications     My notifications
```

### Team Leader APIs  (role: teamleader)
```
GET   /api/tl/team                    All team members
GET   /api/tl/tasks                   Tasks created by me
POST  /api/tl/create-task             Create new task
POST  /api/tl/ai-suggest-employee     AI smart assignment
POST  /api/tl/update-score            Update TL score for employee
```

### HR APIs  (role: hr)
```
GET   /api/hr/employees               All employees
GET   /api/hr/attendance              Monthly attendance summary
GET   /api/hr/performance-all         All performance data
GET   /api/hr/stats                   Dashboard stats
POST  /api/hr/ai-predict-performance  AI performance prediction
POST  /api/hr/ai-promotion            AI promotion recommendation
POST  /api/hr/ai-attrition            AI attrition risk
POST  /api/hr/skill-gap               Skill gap analysis
POST  /api/hr/ats-analyze             ATS resume scoring
POST  /api/hr/send-notification       Send notification
GET   /api/hr/report/<type>           Download CSV report
        types: performance | attendance | promotion | attrition | salary
```

### Admin APIs  (role: admin)
```
GET   /api/admin/users                All users (no passwords)
POST  /api/admin/create-user          Create new user
POST  /api/admin/toggle-user          Activate / deactivate
POST  /api/admin/delete-user          Delete user (cascades)
POST  /api/admin/reset-password       Reset password
GET   /api/admin/login-logs           Last 50 login events
GET   /api/admin/system-stats         System metrics
```

---

## 🚀 Production Deployment

### With Gunicorn
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app_mysql:app
```

### With Nginx + Gunicorn
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Environment Variables for Production
```bash
export SECRET_KEY="generate-a-strong-random-key"
export MYSQL_HOST="your-db-host"
export MYSQL_USER="pulsehr_user"
export MYSQL_PASSWORD="strong-password"
export MYSQL_DB="pulsehr"
export DEBUG="False"
```

---

## 🔒 Production Security Checklist

- [ ] Change `SECRET_KEY` to a random 50+ character string
- [ ] Enable password hashing with `Flask-Bcrypt`
- [ ] Use environment variables for all credentials (never hardcode)
- [ ] Enable HTTPS via SSL certificate
- [ ] Set `DEBUG=False`
- [ ] Configure MySQL user with minimal privileges
- [ ] Enable MySQL SSL connections
- [ ] Set `SESSION_COOKIE_SECURE=True`
- [ ] Configure CORS properly

### Enable Bcrypt Password Hashing
In `app_mysql.py`, uncomment:
```python
from flask_bcrypt import Bcrypt
bcrypt = Bcrypt(app)
```
In login route:
```python
if user and bcrypt.check_password_hash(user.password_hash, password):
```
In create-user route:
```python
password_hash=bcrypt.generate_password_hash(data['password']).decode('utf-8')
```

---

## 🔄 Version Differences

| Feature | `app.py` (JSON) | `app_mysql.py` (MySQL) |
|---------|-----------------|------------------------|
| Database | `data.json` file | MySQL server |
| ORM | None (raw dict) | Flask-SQLAlchemy |
| Models | `db_init.py` | `database/models.py` |
| Reports | `report_gen.py` | `report_gen_mysql.py` |
| Seed | Auto on startup | `seed_mysql.py` |
| Production | ❌ Not suitable | ✅ Production ready |


### Environment Variables:
```env
SECRET_KEY=your-secure-secret-key
DATABASE_URL=mysql+pymysql://user:pass@host/pulsehr
FIREBASE_CONFIG={"apiKey":"..."}
```
# Flask Configuration
FLASK_APP=app.py
FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=e0e73a63de038d385d62ef957224b40e5730d8253b885aa1975262e45343009f

# Database Configuration
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=Root12345
MYSQL_DB=employee_system
MYSQL_PORT=3306

# Firebase Configuration (optional)
FIREBASE_API_KEY=AIzaSyBaZX_TeqWvRp4ZFokGJdvvrkXbJ8fCCXQ
FIREBASE_AUTH_DOMAIN=ai-employee-performance-3ab62.firebaseapp.com
FIREBASE_DATABASE_URL=https://console.firebase.google.com/project/ai-employee-performance-3ab62/database/ai-employee-performance-3ab62-default-rtdb/data/~2F
FIREBASE_PROJECT_ID=ai-employee-performance-3ab62
FIREBASE_STORAGE_BUCKET=ai-employee-performance-3ab62.firebasestorage.app

# Email Configuration (for alerts)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=pai321135@gmail.com
MAIL_PASSWORD=obsbmpjvileavyoo
MAIL_DEFAULT_SENDER=rajjayaraj957@gmail
.com

# Application Settings
APP_NAME=AI Employee Performance System
APP_VERSION=1.0.0
ADMIN_EMAIL=admin@company.com
COMPANY_NAME=TechCorp Inc.

# Security Settings
SESSION_TIMEOUT=3600
MAX_LOGIN_ATTEMPTS=5
PASSWORD_EXPIRY_DAYS=90

# Thresholds
PERFORMANCE_THRESHOLD=60
ATTENDANCE_THRESHOLD=75
WORKLOAD_THRESHOLD=80

# API Keys (if any)
API_KEY=d37c46d8fd97955d51afe2a2d0cfae1d

# Paths
UPLOAD_FOLDER=uploads
LOG_FOLDER=logs
BACKUP_FOLDER=backups
MODEL_FOLDER=models/saved