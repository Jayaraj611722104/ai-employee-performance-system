import requests
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:5000"

def test_updates():
    session = requests.Session()
    
    # 1. Login to trigger login_logs
    login_data = {"email": "employee@gmail.com", "password": "emp123"}
    resp = session.post(f"{BASE_URL}/login", json=login_data)
    print(f"Login Response: {resp.status_code}, {resp.json()}")
    
    if resp.status_code != 200:
        print("Login failed, skipping remaining tests.")
        return

    # 2. Submit Weekly Update
    wu_data = {
        "project_work": "Testing DB updates",
        "tech_learned": "Python, Flask",
        "problems": "None",
        "task_completion": 90
    }
    resp = session.post(f"{BASE_URL}/api/employee/weekly-update", json=wu_data)
    print(f"Weekly Update Response: {resp.json()}")

    # 3. Submit Training Update (New route)
    train_data = {
        "week": 2,
        "hours": 5,
        "tech_learned": "Database optimization",
        "problems": "None",
        "completion": 100
    }
    resp = session.post(f"{BASE_URL}/api/employee/training-update", json=train_data)
    print(f"Training Update Response: {resp.json()}")

    # 4. Trigger AI Prediction
    pred_data = {"user_id": "U0004", "month": "March"} # Dummy data for predictor
    resp = session.post(f"{BASE_URL}/api/hr/ai-predict-performance", json=pred_data)
    print(f"AI Prediction Response: {resp.status_code}")

    # 5. TL Rate Employee (New route)
    # Login as TL
    session.get(f"{BASE_URL}/logout")
    login_tl = {"email": "tl@company.com", "password": "tl123"}
    session.post(f"{BASE_URL}/login", json=login_tl)
    
    rate_data = {
        "employee_id": "U0004",
        "rating": 5,
        "feedback": "Excellent progress on database updates."
    }
    resp = session.post(f"{BASE_URL}/api/tl/rate-employee", json=rate_data)
    print(f"TL Rate Response: {resp.json()}")

if __name__ == "__main__":
    test_updates()
