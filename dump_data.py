from app_mysql import app, db
from database.models import Team, Employee, User

def dump():
    with app.app_context():
        print("--- Teams Dump ---")
        teams = Team.query.all()
        for t in teams:
            members = Employee.query.filter_by(team_id=t.id).all()
            print(f"Team: {t.id} ({t.name}), Leader: {t.leader_id}, Members: {[m.user_id for m in members]}")
        
        print("\n--- Employees with teams ---")
        emps = Employee.query.filter(Employee.team_id.isnot(None)).all()
        for e in emps:
            print(f"Employee: {e.user_id} ({e.name}), Team: {e.team_id}, Leader: {e.team_leader_id}")

if __name__ == '__main__':
    dump()
