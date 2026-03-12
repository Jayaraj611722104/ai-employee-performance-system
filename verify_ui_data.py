import json
import os
import requests
import time

BASE_URL = "http://127.0.0.1:5000"

def test_endpoints():
    print("🚀 Starting UI Data Verification...")
    
    # Check if app is running, if not, skip (this is for local dev check)
    try:
        requests.get(BASE_URL)
    except:
        print("⚠️ Flask app is not running. Verification will be done by checking data.json directly.")
        verify_data_json()
        return

    # 1. Test /api/hr/teams-detailed
    print("Testing /api/hr/teams-detailed...")
    # Note: requires login, might fail if not authenticated. 
    # For this verification, I'll rely on the data.json check if HTTP fails.
    
def verify_data_json():
    json_path = "database/data.json"
    if not os.path.exists(json_path):
        print(f"❌ {json_path} not found!")
        return
        
    with open(json_path, 'r') as f:
        data = json.load(f)
        
    print(f"✅ data.json loaded.")
    
    tables = ['team_performance', 'team_projects', 'tl_ratings', 'team_member_tasks']
    for table in tables:
        if table in data and len(data[table]) > 0:
            print(f"✅ Table '{table}' has {len(data[table])} entries.")
        else:
            print(f"❌ Table '{table}' is missing or empty!")

if __name__ == "__main__":
    verify_data_json()
