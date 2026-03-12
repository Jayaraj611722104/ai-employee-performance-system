import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from app_mysql import app, db
from database.models import (
    User, Employee, Team, Task, Performance, Attendance, 
    Notification, WeeklyUpdate, LoginLog, Training, AIPrediction, LeaveRequest,
    TeamPerformance, TeamProject, TLRating, TeamMemberTask
)

def verify():
    with app.app_context():
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"Total tables: {len(tables)}")
        print(f"Tables found: {', '.join(tables)}")
        
        models = [
            User, Employee, Team, Task, Performance, Attendance, 
            Notification, WeeklyUpdate, LoginLog, Training, AIPrediction, LeaveRequest,
            TeamPerformance, TeamProject, TLRating, TeamMemberTask
        ]
        
        print("\nRecord Counts:")
        for model in models:
            count = model.query.count()
            print(f"  {model.__tablename__:<20}: {count}")

if __name__ == '__main__':
    verify()
