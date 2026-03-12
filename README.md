# PulseHR — AI-Based Employee Performance Prediction & Promotion Recommendation System

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- pip

### 1. Install Dependencies
```bash
cd hr_system
pip install flask numpy pandas scikit-learn
```

### 2. Run the Application
```bash
python app.py
```

### 3. Open Browser
```
http://localhost:5000
```

---

## 🔐 Demo Login Credentials

| Role | Email | Password |
|------|-------|----------|
| Employee | employee@gmail.com | emp123 |
| Team Leader | tl@company.com | tl123 |
| HR Manager | hr@company.com | hr123 |
| Admin | admin@company.com | admin123 |

---

## 📁 Project Structure

```
hr_system/
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
├── database/
│   ├── db_init.py             # Database initialization + demo data
│   ├── schema.sql             # MySQL schema (for production)
│   ├── sample_dataset.csv     # Sample employee data
│   └── data.json              # Auto-generated JSON database
├── ml_models/
│   └── predictor.py           # AI/ML prediction engines
├── utils/
│   └── report_gen.py          # CSV report generator
└── templates/
    ├── base.html              # Base layout template
    ├── login.html             # Login page
    ├── employee_dashboard.html
    ├── teamleader_dashboard.html
    ├── hr_dashboard.html
    └── admin_dashboard.html
```

---

## 🧠 AI Modules

### 1. Performance Prediction (Random Forest)
- Input: Productivity, Attendance, Task Completion, Quality, TL Score
- Output: Predicted future score + trend + confidence
- Feature Importance: Productivity (30%), Task Comp (25%), Attendance (20%), Quality (15%), TL Score (10%)

### 2. Promotion Recommendation
- Input: All performance metrics + experience + projects
- Output: Eligibility %, next role, required skills, readiness level

### 3. Attrition Risk Prediction
- Input: Satisfaction, Salary, Attendance, Performance, TL Relationship
- Output: Risk % (0-100), risk level, reasons, recommendations

### 4. Skill Gap Analysis
- Input: Current skills + target role
- Output: Matched skills, gaps, training recommendations

### 5. ATS Resume Analyzer
- Input: Resume text
- Output: ATS score, category breakdown, role suggestions

---

## 📊 Dashboard Features

### Employee Dashboard
- Profile & metrics
- Task management with deadline timer
- Weekly self-update form
- Performance charts (radar, trend, bar)
- Learning & certifications tracker

### Team Leader Dashboard
- Team overview & management
- Task creation & assignment
- AI Smart Assignment (skill match + workload + performance)
- Task monitoring & overdue alerts
- Fresher auto-task assignment
- Weekly score updates

### HR Dashboard
- Employee management (search, filter)
- Attendance monitoring & charts
- Performance analytics
- All 5 AI modules
- Freshers training module
- ATS resume analyzer
- Report generation (CSV export)
- Notification system

### Admin Dashboard
- User CRUD (create, toggle, delete, reset password)
- Login activity logs
- System monitoring
- Security settings
- Configuration panel

---

## 🗄️ Database

**Demo Mode**: Uses `data.json` file (auto-created on first run)

**Production MySQL**: Use `database/schema.sql` to create tables, then update `db_init.py` to use MySQLAlchemy:

```python
from flask_sqlalchemy import SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://user:pass@localhost/pulsehr'
```

---

## 🌐 API Endpoints

### Auth
- `POST /login` — Authenticate user
- `GET /logout` — End session

### Employee
- `GET /api/employee/profile`
- `GET /api/employee/tasks`
- `POST /api/employee/update-task`
- `POST /api/employee/weekly-update`
- `GET /api/employee/performance`
- `GET /api/employee/notifications`

### Team Leader
- `GET /api/tl/team`
- `GET /api/tl/tasks`
- `POST /api/tl/create-task`
- `POST /api/tl/ai-suggest-employee`
- `POST /api/tl/update-score`

### HR
- `GET /api/hr/employees`
- `GET /api/hr/attendance`
- `GET /api/hr/performance-all`
- `GET /api/hr/stats`
- `POST /api/hr/ai-predict-performance`
- `POST /api/hr/ai-promotion`
- `POST /api/hr/ai-attrition`
- `POST /api/hr/skill-gap`
- `POST /api/hr/ats-analyze`
- `GET /api/hr/report/<type>` — performance|attendance|promotion|attrition|salary
- `POST /api/hr/send-notification`

### Admin
- `GET /api/admin/users`
- `POST /api/admin/create-user`
- `POST /api/admin/toggle-user`
- `POST /api/admin/delete-user`
- `POST /api/admin/reset-password`
- `GET /api/admin/login-logs`
- `GET /api/admin/system-stats`

---

## 🔧 Production Deployment

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Firebase Hosting + Cloud Run
- Build and deploy backend to Cloud Run:
  - Install gcloud CLI and authenticate
  - From hr_system:
    - `pwsh ./deploy_cloud_run.ps1 -ProjectId your-gcp-project-id -Region us-central1 -Service pulsehr-api`
- Configure Firebase Hosting rewrite:
  - Install Firebase CLI and login
  - Set project in `.firebaserc` or `firebase use your-firebase-project-id`
  - Deploy hosting:
    - `pwsh ./deploy_firebase.ps1 -Project your-firebase-project-id`
- Required env vars for backend:
  - `FIREBASE_CREDENTIALS` path inside container
  - `FIREBASE_DATABASE_URL` realtime DB URL
  - `SECRET_KEY`
  - `PORT=8080` (set automatically)

### With MySQL (Production):
1. Install MySQL + create database: `CREATE DATABASE pulsehr;`
2. Run `database/schema.sql`
3. Install: `pip install flask-sqlalchemy pymysql`
4. Update DB URI in `app.py`

### Environment Variables:
```env
SECRET_KEY=your-secure-secret-key
DATABASE_URL=mysql+pymysql://user:pass@host/pulsehr
FIREBASE_CONFIG={"apiKey":"..."}
```
