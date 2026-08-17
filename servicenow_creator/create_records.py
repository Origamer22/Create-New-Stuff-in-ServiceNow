import os
import requests
import random
from datetime import datetime, timezone

SN_INSTANCE = os.environ.get('SN_INSTANCE')
SN_USERNAME = os.environ.get('SN_USERNAME')
SN_PASSWORD = os.environ.get('SN_PASSWORD')

if not all([SN_INSTANCE, SN_USERNAME, SN_PASSWORD]):
    print("Error: Missing ServiceNow credentials.")
    exit(1)

# Clean up SN_INSTANCE in case full URL or FQDN was provided
SN_INSTANCE = SN_INSTANCE.replace('https://', '').replace('http://', '').rstrip('/')
if SN_INSTANCE.endswith('.service-now.com'):
    SN_INSTANCE = SN_INSTANCE.replace('.service-now.com', '')

BASE_URL = f"https://{SN_INSTANCE}.service-now.com/api/now/table"
HEADERS = {"Content-Type": "application/json", "Accept": "application/json"}
AUTH = (SN_USERNAME, SN_PASSWORD)

def get_records(table, query, limit=None):
    url = f"{BASE_URL}/{table}"
    params = {"sysparm_query": query}
    if limit:
        params["sysparm_limit"] = limit
    response = requests.get(url, auth=AUTH, headers=HEADERS, params=params)
    if response.status_code == 200:
        return response.json().get('result', [])
    print(f"Failed to fetch {table}: {response.text}")
    return []

def update_record(table, sys_id, payload):
    url = f"{BASE_URL}/{table}/{sys_id}"
    response = requests.put(url, auth=AUTH, headers=HEADERS, json=payload)
    if response.status_code == 200:
        return response.json().get('result')
    
    # Try to parse a cleaner error message
    try:
        err_detail = response.json().get('error', {}).get('detail', response.text)
        # Clean up newlines in error details for single-line logging
        err_detail = err_detail.replace('\n', ' ').replace('\t', '')
        print(f"Failed to update {table} {sys_id}: {err_detail}")
    except:
        print(f"Failed to update {table} {sys_id}: {response.text}")
        
    return None

def delete_record(table, sys_id):
    url = f"{BASE_URL}/{table}/{sys_id}"
    response = requests.delete(url, auth=AUTH, headers=HEADERS)
    if response.status_code == 204:
        return True
    print(f"Failed to delete {table} {sys_id}: {response.text}")
    return False

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
    # Query changes where start_date is on or before today, and state is Scheduled (-2)
    # Only Scheduled changes can transition directly to Implement (-1).
    changes = get_records("change_request", "active=true^state=-2^start_date<=javascript:gs.nowNoTZ()")
    for chg in changes:
        chg_id = chg['sys_id']
        chg_num = chg['number']
        print(f"Starting change {chg_num}...")
        if update_record("change_request", chg_id, {"state": "-1"}):
            print(f"Successfully started change {chg_num}")

def end_active_changes():
    print("Checking for active changes to close...")
    # Query changes in Implement (-1) or Review (0)
    changes = get_records("change_request", "active=true^stateIN-1,0")
    
    # Close changes probabilistically so some run longer and some shorter
    changes_to_close = [chg for chg in changes if random.choice([True, False])]
    
    for chg in changes_to_close:
        chg_id = chg['sys_id']
        chg_num = chg['number']
        print(f"Closing change {chg_num}...")
        payload = {
            "state": "3", # Closed
            "close_code": "successful",
            "close_notes": "Auto-closed by script"
        }
        if update_record("change_request", chg_id, payload):
            print(f"Successfully closed change {chg_num}")

def ensure_minimum_active_changes(min_count=3):
    print(f"Ensuring at least {min_count} active changes in Implement/Review state...")
    changes = get_records("change_request", "active=true^stateIN-1,0")
    current_count = len(changes)
    print(f"Currently have {current_count} active changes.")
    
    if current_count < min_count:
        needed = min_count - current_count
        print(f"Need to create {needed} more change(s) to reach minimum.")
        for _ in range(needed):
            now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            chg = create_record("change_request", {
                "short_description": "Auto-generated active change request",
                "type": "normal",
                "start_date": now_str
            })
            if chg:
                # Force state to Implement (-1) so they show up as running
                update_record("change_request", chg['sys_id'], {"state": "-1"})

def reassign_incidents():
    print("Checking for active incidents to reassign...")
    # Fetch some active groups
    groups = get_records("sys_user_group", "active=true", limit=10)
    if not groups:
        print("No active groups found to reassign to.")
        return

    # Fetch active incidents (New or In Progress)
    incidents = get_records("incident", "active=true^stateIN1,2")
    for inc in incidents:
        inc_id = inc['sys_id']
        inc_num = inc['number']
        group = random.choice(groups)
        group_id = group['sys_id']
        group_name = group.get('name', 'Unknown Group')
        
        print(f"Reassigning incident {inc_num} to {group_name}...")
        if update_record("incident", inc_id, {"assignment_group": group_id}):
            print(f"Successfully reassigned incident {inc_num}")

def close_incidents():
    print("Checking for incidents to close...")
    # Query incidents not closed (7) or canceled (8)
    incidents = get_records("incident", "active=true^stateNOT IN7,8")
    for inc in incidents:
        inc_id = inc['sys_id']
        inc_num = inc['number']
        print(f"Closing incident {inc_num}...")
        payload = {
            "state": "7", # Closed
            "close_code": "Solved (Permanently)",
            "resolution_code": "Solved (Permanently)", # Some instances use this field name
            "close_notes": "Auto-closed by script"
        }
        if update_record("incident", inc_id, payload):
            print(f"Successfully closed incident {inc_num}")

def main():
    print("Starting ServiceNow Scheduled Tasks...")

    # 1. Close out previous runs
    end_active_changes()
    close_incidents()
    
    # 3. Create new records for today
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
    
    # 4. Progress states for active records
    print("Checking for planned changes to start...")
    start_planned_changes()
    
    # 5. Ensure we always have at least 3 running changes
    ensure_minimum_active_changes(3)
    
    reassign_incidents()

if __name__ == '__main__':
    main()
