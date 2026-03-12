"""
database/models.py
SQLAlchemy ORM models — mirrors schema.sql exactly
"""
import json
from datetime import datetime, date, time
from decimal import Decimal
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def _model_to_dict(self):
    res = {}
    for c in self.__table__.columns:
        val = getattr(self, c.name)
        if isinstance(val, (datetime, date, time)):
            res[c.name] = str(val)
        elif isinstance(val, Decimal):
            res[c.name] = float(val)
        elif c.name in ('required_skills', 'monthly_trend', 'monthly_scores', 'input_data', 'result_data'):
            try:
                res[c.name] = json.loads(val) if val else []
            except:
                res[c.name] = val
        else:
            res[c.name] = val
    return res

db.Model.to_dict = _model_to_dict


# ─── Users ────────────────────────────────────────────────────────────────────
class User(db.Model):
    __tablename__ = 'users'

    id            = db.Column(db.String(10),  primary_key=True)
    name          = db.Column(db.String(100), nullable=False)
    email         = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role          = db.Column(db.Enum('employee','teamleader','hr','admin'), nullable=False)
    status        = db.Column(db.Enum('Active','Inactive'), default='Active')
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    last_login    = db.Column(db.DateTime, nullable=True)

    # relationships
    employee       = db.relationship(
        'Employee',
        back_populates='user',
        uselist=False,
        cascade='all, delete-orphan',
        foreign_keys='Employee.user_id'
    )
    team_members   = db.relationship(
        'Employee',
        back_populates='team_leader',
        foreign_keys='Employee.team_leader_id'
    )
    login_logs     = db.relationship('LoginLog', back_populates='user', cascade='all, delete-orphan')
    weekly_updates = db.relationship('WeeklyUpdate', back_populates='user', cascade='all, delete-orphan')
    notifications_sent = db.relationship('Notification', back_populates='sender', cascade='all, delete-orphan')
    assigned_tasks = db.relationship('Task', foreign_keys='Task.assigned_to', back_populates='assignee')
    created_tasks  = db.relationship('Task', foreign_keys='Task.assigned_by', back_populates='creator')


# ─── Employees ────────────────────────────────────────────────────────────────
class Employee(db.Model):
    __tablename__ = 'employees'

    user_id            = db.Column(db.String(10), db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    employee_id        = db.Column(db.String(20), unique=True, nullable=False)
    name               = db.Column(db.String(100), nullable=False)
    role               = db.Column(db.String(100), nullable=False)
    department         = db.Column(db.String(100), nullable=False)
    skills             = db.Column(db.Text)
    experience         = db.Column(db.Integer, default=0)
    joining_date       = db.Column(db.Date)
    projects_completed = db.Column(db.Integer, default=0)
    status             = db.Column(db.Enum('Active','Inactive'), default='Active')
    team_leader_id     = db.Column(db.String(10), db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    team_id            = db.Column(db.String(10), db.ForeignKey('teams.id', ondelete='SET NULL'), nullable=True)
    salary             = db.Column(db.Numeric(10,2), default=0)

    # relationships
    user        = db.relationship('User', back_populates='employee', foreign_keys=[user_id])
    team_leader = db.relationship('User', back_populates='team_members', foreign_keys=[team_leader_id])
    team        = db.relationship('Team', back_populates='members', foreign_keys=[team_id])
    performance = db.relationship('Performance', back_populates='employee', cascade='all, delete-orphan')
    training    = db.relationship('Training', back_populates='employee', cascade='all, delete-orphan')


# ─── Performance ─────────────────────────────────────────────────────────────
class Performance(db.Model):
    __tablename__ = 'performance'

    id                 = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id            = db.Column(db.String(10), db.ForeignKey('employees.user_id', ondelete='CASCADE'), nullable=False)
    productivity_score = db.Column(db.Float, default=0)
    attendance_pct     = db.Column(db.Float, default=0)
    task_completion    = db.Column(db.Float, default=0)
    quality_rating     = db.Column(db.Float, default=0)
    tl_score           = db.Column(db.Float, default=0)
    satisfaction       = db.Column(db.Integer, default=75)
    monthly_trend      = db.Column(db.Text)  # JSON string
    month              = db.Column(db.String(20))
    year               = db.Column(db.Integer)
    recorded_at        = db.Column(db.DateTime, default=datetime.utcnow)

    employee = db.relationship('Employee', back_populates='performance')


# ─── Tasks ────────────────────────────────────────────────────────────────────
class Task(db.Model):
    __tablename__ = 'tasks'

    id              = db.Column(db.String(10), primary_key=True)
    title           = db.Column(db.String(200), nullable=False)
    description     = db.Column(db.Text)
    priority        = db.Column(db.Enum('High','Medium','Low'), default='Medium')
    deadline        = db.Column(db.Date)
    required_skills = db.Column(db.Text)  # JSON list
    assigned_to     = db.Column(db.String(10), db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    assigned_by     = db.Column(db.String(10), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    status          = db.Column(db.Enum('Pending','In Progress','Completed','Cancelled'), default='Pending')
    progress        = db.Column(db.Integer, default=0)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at      = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    assignee = db.relationship('User', foreign_keys=[assigned_to], back_populates='assigned_tasks')
    creator  = db.relationship('User', foreign_keys=[assigned_by], back_populates='created_tasks')


# ─── Attendance ───────────────────────────────────────────────────────────────
class Attendance(db.Model):
    __tablename__  = 'attendance'
    __table_args__ = (db.UniqueConstraint('user_id','date', name='uq_attendance'),)

    id           = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id      = db.Column(db.String(10), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    date         = db.Column(db.Date, nullable=False)
    status       = db.Column(db.Enum('Present','Absent','Late','Leave'), default='Present')
    check_in     = db.Column(db.Time,  nullable=True)
    check_out    = db.Column(db.Time,  nullable=True)
    hours_worked = db.Column(db.Float, default=0)


# ─── Notifications ────────────────────────────────────────────────────────────
class Notification(db.Model):
    __tablename__ = 'notifications'

    id         = db.Column(db.Integer, primary_key=True, autoincrement=True)
    message    = db.Column(db.Text, nullable=False)
    type       = db.Column(db.Enum('info','success','warning','danger'), default='info')
    target     = db.Column(db.String(50), default='all')
    sent_by    = db.Column(db.String(10), db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_by    = db.Column(db.Text) # JSON string of user IDs

    sender = db.relationship('User', back_populates='notifications_sent')


# ─── Weekly Updates ───────────────────────────────────────────────────────────
class WeeklyUpdate(db.Model):
    __tablename__ = 'weekly_updates'

    id                    = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id               = db.Column(db.String(10), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    project_work          = db.Column(db.Text)
    tech_learned          = db.Column(db.String(255))
    problems              = db.Column(db.Text)
    task_completion_level = db.Column(db.Integer, default=0)
    week_date             = db.Column(db.Date)
    submitted_at          = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='weekly_updates')


# ─── Login Logs ───────────────────────────────────────────────────────────────
class LoginLog(db.Model):
    __tablename__ = 'login_logs'

    id         = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id    = db.Column(db.String(10), db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    name       = db.Column(db.String(100))
    role       = db.Column(db.String(50))
    ip_address = db.Column(db.String(50))
    login_time = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='login_logs')


# ─── Training ─────────────────────────────────────────────────────────────────
class Training(db.Model):
    __tablename__ = 'training'

    id             = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id        = db.Column(db.String(10), db.ForeignKey('employees.user_id', ondelete='CASCADE'), nullable=False)
    week_number    = db.Column(db.Integer)
    hours_completed= db.Column(db.Float, default=0)
    tech_learned   = db.Column(db.String(255))
    problems       = db.Column(db.Text)
    completion_pct = db.Column(db.Integer, default=0)
    recorded_at    = db.Column(db.DateTime, default=datetime.utcnow)

    employee = db.relationship('Employee', back_populates='training')


# ─── Teams ────────────────────────────────────────────────────────────────────
class Team(db.Model):
    __tablename__ = 'teams'

    id                 = db.Column(db.String(10), primary_key=True)
    name               = db.Column(db.String(100), nullable=False)
    description        = db.Column(db.Text)
    leader_id          = db.Column(db.String(10), db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    project_name       = db.Column(db.String(200))
    project_status     = db.Column(db.String(50), default='Not Started')
    project_completion = db.Column(db.Integer, default=0)
    score              = db.Column(db.Integer, default=0)
    monthly_scores     = db.Column(db.Text) # JSON list
    created_at         = db.Column(db.DateTime, default=datetime.utcnow)

    leader  = db.relationship('User', foreign_keys=[leader_id])
    members = db.relationship('Employee', back_populates='team', foreign_keys='Employee.team_id')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'leader_id': self.leader_id,
            'project_name': self.project_name,
            'project_status': self.project_status,
            'project_completion': self.project_completion,
            'score': self.score,
            'monthly_scores': json.loads(self.monthly_scores) if self.monthly_scores else []
        }

# ─── Leave Requests ───────────────────────────────────────────────────────────
class LeaveRequest(db.Model):
    __tablename__ = 'leave_requests'

    id            = db.Column(db.String(10), primary_key=True)
    user_id       = db.Column(db.String(10), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    employee_name = db.Column(db.String(100))
    department    = db.Column(db.String(100))
    type          = db.Column(db.String(50))
    from_date     = db.Column(db.Date)
    to_date       = db.Column(db.Date)
    days          = db.Column(db.Integer)
    reason        = db.Column(db.Text)
    is_emergency  = db.Column(db.Boolean, default=False)
    status        = db.Column(db.String(50), default='Pending')
    applied_on    = db.Column(db.Date)
    reviewed_by   = db.Column(db.String(100))
    reviewed_at   = db.Column(db.DateTime)

    user = db.relationship('User', foreign_keys=[user_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'employee_name': self.employee_name,
            'department': self.department,
            'type': self.type,
            'from_date': str(self.from_date) if self.from_date else None,
            'to_date': str(self.to_date) if self.to_date else None,
            'days': self.days,
            'reason': self.reason,
            'is_emergency': self.is_emergency,
            'status': self.status,
            'applied_on': str(self.applied_on) if self.applied_on else None,
            'reviewed_by': self.reviewed_by,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None
        }

# ─── AI Predictions Log ───────────────────────────────────────────────────────
class AIPrediction(db.Model):
    __tablename__ = 'ai_predictions'

    id              = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id         = db.Column(db.String(10), db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    prediction_type = db.Column(db.Enum('performance','promotion','attrition','skill_gap', name='prediction_type_enum'))
    input_data      = db.Column(db.JSON)
    result_data     = db.Column(db.JSON)
    confidence      = db.Column(db.Float)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)

# ─── Team Performance ─────────────────────────────────────────────────────────
class TeamPerformance(db.Model):
    __tablename__ = 'team_performance'

    id                 = db.Column(db.Integer, primary_key=True, autoincrement=True)
    team_id            = db.Column(db.String(10), db.ForeignKey('teams.id', ondelete='CASCADE'), nullable=False)
    productivity_score = db.Column(db.Float, default=0)
    project_completion = db.Column(db.Float, default=0)
    quality_rating     = db.Column(db.Float, default=0)
    recorded_at        = db.Column(db.DateTime, default=datetime.utcnow)

# ─── Team Project Status ──────────────────────────────────────────────────────
class TeamProject(db.Model):
    __tablename__ = 'team_projects'

    id                 = db.Column(db.Integer, primary_key=True, autoincrement=True)
    team_id            = db.Column(db.String(10), db.ForeignKey('teams.id', ondelete='CASCADE'), nullable=False)
    project_name       = db.Column(db.String(200), nullable=False)
    status             = db.Column(db.String(50), default='Not Started')
    completion_pct     = db.Column(db.Integer, default=0)
    updated_at         = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ─── TL Employee Ratings ──────────────────────────────────────────────────────
class TLRating(db.Model):
    __tablename__ = 'tl_ratings'

    id                 = db.Column(db.Integer, primary_key=True, autoincrement=True)
    employee_id        = db.Column(db.String(10), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    tl_id              = db.Column(db.String(10), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    rating             = db.Column(db.Integer, default=0)
    feedback           = db.Column(db.Text)
    recorded_at        = db.Column(db.DateTime, default=datetime.utcnow)

# ─── Team Member Task Completion ──────────────────────────────────────────────
class TeamMemberTask(db.Model):
    __tablename__ = 'team_member_tasks'

    id                 = db.Column(db.Integer, primary_key=True, autoincrement=True)
    team_id            = db.Column(db.String(10), db.ForeignKey('teams.id', ondelete='CASCADE'), nullable=False)
    user_id            = db.Column(db.String(10), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    tasks_completed    = db.Column(db.Integer, default=0)
    tasks_pending      = db.Column(db.Integer, default=0)
    updated_at         = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)