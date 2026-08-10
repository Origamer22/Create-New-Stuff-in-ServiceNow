import os
import requests
from datetime import datetime, timezone

SN_INSTANCE = os.environ.get('SN_INSTANCE')
SN_USERNAME = os.environ.get('SN_USERNAME')
SN_PASSWORD = os.environ.get('SN_PASSWORD')

if not all([SN_INSTANCE, SN_USERNAME, SN_PASSWORD]):
    print("Error: Missing ServiceNow credentials.")
    exit(1)

BASE_URL = f"https://{SN_INSTANCE}.service-now.com/api/now/table"
HEADERS = {"Content-Type": "application/json", "Accept": "application/json"}
AUTH = (SN_USERNAME, SN_PASSWORD)

def create_record(table, payload):
    url = f"{BASE_URL}/{table}"
    response = requests.post(url, auth=AUTH, headers=HEADERS, json=payload)
    if response.status_code in [200, 201]:
        print(f"Created {table}: {response.json()['result'].get('number', 'unknown')}")
        return response.json()['result']
    else:
        print(f"Failed to create {table}: {response.text}")
        return None

def start_planned_changes():
    url = f"{BASE_URL}/change_request"
    # Query changes where start_date is on or before today, and state is not Implement (or closed)
    # -1 is typically Implement.
    query = "active=true^stateNOT IN-1,3,4^start_date<=javascript:gs.nowNoTZ()"
    params = {"sysparm_query": query}
    response = requests.get(url, auth=AUTH, headers=HEADERS, params=params)
    if response.status_code == 200:
        changes = response.json().get('result', [])
        for chg in changes:
            chg_id = chg['sys_id']
            chg_num = chg['number']
            print(f"Starting change {chg_num}...")
            update_url = f"{url}/{chg_id}"
            # Update state to Implement (-1)
            update_payload = {"state": "-1"}
            res = requests.put(update_url, auth=AUTH, headers=HEADERS, json=update_payload)
            if res.status_code == 200:
                print(f"Successfully started change {chg_num}")
            else:
                print(f"Failed to start change {chg_num}: {res.text}")

def main():
    print("Starting ServiceNow Scheduled Tasks...")
    
    print("Creating Incidents...")
    create_record("incident", {"short_description": "Auto-generated incident", "urgency": "2", "impact": "2"})
    
    print("Creating Problems...")
    create_record("problem", {"short_description": "Auto-generated problem from recurring incidents"})
    
    print("Creating Change Requests...")
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    create_record("change_request", {
        "short_description": "Auto-generated change request",
        "type": "normal",
        "start_date": now_str
    })
    
    print("Checking for planned changes to start...")
    start_planned_changes()

if __name__ == '__main__':
    main()
