import os
import requests
import random
from datetime import datetime, timezone, timedelta
import pytz

SN_INSTANCE = os.environ.get('SN_INSTANCE')
SN_USERNAME = os.environ.get('SN_USERNAME')
SN_PASSWORD = os.environ.get('SN_PASSWORD')

if not all([SN_INSTANCE, SN_USERNAME, SN_PASSWORD]):
    print("Error: Missing ServiceNow credentials.")
    exit(1)

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

def update_record(table, sys_id, payload, silent=False):
    url = f"{BASE_URL}/{table}/{sys_id}"
    response = requests.put(url, auth=AUTH, headers=HEADERS, json=payload)
    if response.status_code == 200:
        return response.json().get('result')
    
    if not silent:
        try:
            err_detail = response.json().get('error', {}).get('detail', response.text)
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

def get_age_hours(sys_created_on_str):
    if not sys_created_on_str: return 0
    try:
        created = datetime.strptime(sys_created_on_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        return (now - created).total_seconds() / 3600
    except Exception as e:
        return 0

def approve_all_pending(sys_id):
    approvals = get_records("sysapproval_approver", f"sysapproval={sys_id}^state=requested")
    for app in approvals:
        update_record("sysapproval_approver", app['sys_id'], {"state": "approved"}, silent=True)

def progress_change(chg):
    chg_id = chg['sys_id']
    chg_num = chg['number']
    
    # State mapping:
    # -5 = New, -4 = Assess, -3 = Authorize, -2 = Scheduled, -1 = Implement, 0 = Review, 3 = Closed
    
    state_str = chg.get('state', '-5')
    try:
        state = int(state_str)
    except:
        state = -5
        
    print(f"Progressing change {chg_num} from state {state}...")
    age_hours = get_age_hours(chg.get('sys_created_on'))
    
    if state == -5: # New -> Assess
        payload = {"state": "-4"}
        if not chg.get('assignment_group'):
            groups = get_records("sys_user_group", "active=true", limit=10)
            if groups:
                payload["assignment_group"] = random.choice(groups)['sys_id']
        update_record("change_request", chg_id, payload, silent=True)
        
    elif state == -4: # Assess -> Authorize
        update_record("change_request", chg_id, {"state": "-3"}, silent=True)
        
    elif state == -3: # Authorize -> Scheduled
        approve_all_pending(chg_id)
        update_record("change_request", chg_id, {"state": "-2"}, silent=True)
        
    elif state == -2: # Scheduled -> Implement
        update_record("change_request", chg_id, {"state": "-1", "work_notes": "Starting implementation."}, silent=True)
        
    elif state == -1: # Implement -> Review
        # Random duration between 2 to 24 hours
        threshold = random.randint(2, 24)
        if age_hours > threshold:
            update_record("change_request", chg_id, {"state": "0", "work_notes": "Implementation complete. Moving to review."}, silent=True)
            print(f"Moved {chg_num} to Review (age {age_hours:.1f}h)")
        else:
            print(f"Keeping {chg_num} in Implement (age {age_hours:.1f}h, threshold {threshold}h)")
            
    elif state == 0: # Review -> Closed
        # Random duration to keep in review before closing, up to 3 days total
        threshold = random.randint(24, 72)
        if age_hours > threshold:
            payload = {
                "state": "3",
                "close_code": "successful",
                "close_notes": "Auto-closed by script after review period."
            }
            update_record("change_request", chg_id, payload, silent=True)
            print(f"Closed {chg_num} (age {age_hours:.1f}h)")
        else:
            print(f"Keeping {chg_num} in Review (age {age_hours:.1f}h, threshold {threshold}h)")

def process_all_changes():
    print("\n--- Processing Change Requests ---")
    # Only active changes
    changes = get_records("change_request", "active=true")
    for chg in changes:
        progress_change(chg)

def ensure_minimum_active_changes(min_count=3):
    print(f"\n--- Ensuring Minimum Active Changes ---")
    implement_changes = get_records("change_request", "active=true^state=-1")
    current_count = len(implement_changes)
    print(f"Currently have {current_count} active changes in Implement.")
    
    if current_count < min_count:
        needed_active = min_count - current_count
        print(f"Need to create {needed_active} more change(s) directly in Implement state.")
        for _ in range(needed_active):
            now = datetime.now(timezone.utc)
            chg = create_record("change_request", {
                "short_description": "Auto-generated change: Urgent security patch",
                "description": "Urgent security patching to address zero-day vulnerability.",
                "justification": "Required to maintain security posture and prevent unauthorized access.",
                "implementation_plan": "1. Snapshot servers.\n2. Apply patches.\n3. Restart and verify.",
                "risk_impact_analysis": "Medium risk.",
                "backout_plan": "Restore from snapshot.",
                "test_plan": "Run vulnerability scan.",
                "type": "Normal",
                "state": "-5", # Create in New, then fast-forward
                "priority": "3",
                "risk": "3", # Moderate
                "start_date": now.strftime("%Y-%m-%d %H:%M:%S"),
                "end_date": (now + timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"),
                "expected_start": now.strftime("%Y-%m-%d %H:%M:%S"),
                "work_start": now.strftime("%Y-%m-%d %H:%M:%S"),
                "work_end": (now + timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"),
                "cab_date_time": (now - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
                "due_date": (now + timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S"),
                "requested_by_date": (now - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"),
                "review_date": (now + timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"),
                "category": "Other",
                "contact_type": "Phone",
                "impact": "3",
                "urgency": "3",
                "scope": "Medium",
                "cab_required": "false",
                "outside_maintenance_schedule": "false",
                "production_system": "false",
                "unauthorized": "false",
                "upon_approval": "Proceed to Next Task",
                "upon_reject": "Cancel all future Tasks",
                "work_notes": "Change request auto-created to maintain minimum active count.",
                "comments": "This change was opened by automation.",
                "escalation": "Normal",
                "conflict_status": "Not Run",
                "phase": "Requested",
                "phase_state": "Open",
                "approval": "Approved",
                "approval_set": now.strftime("%Y-%m-%d %H:%M:%S"),
                "cab_recommendation": "Approved by CAB.",
                "change_plan": "Standard change plan.",
                "conflict_last_run": now.strftime("%Y-%m-%d %H:%M:%S"),
                "reason": "Routine update",
                "review_comments": "Looks good.",
                "review_status": "Reviewed",
                "route_reason": "Standard routing",
                "user_input": "Proceed with change.",
                "knowledge": "false",
                "made_sla": "true",
                "on_hold": "false",
                "on_hold_reason": "Not on hold",
                "activity_due": (now + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
            })

            if chg:
                chg_id = chg.get('sys_id')
                if chg_id:
                    # Fast-forward to Implement
                    groups = get_records("sys_user_group", "active=true", limit=10)
                    ag_id = random.choice(groups)['sys_id'] if groups else ""
                    
                    payload_assess = {"state": "-4"}
                    if ag_id:
                        payload_assess["assignment_group"] = ag_id
                        
                    update_record("change_request", chg_id, payload_assess, silent=True) # Assess
                    update_record("change_request", chg_id, {"state": "-3"}, silent=True) # Authorize
                    approve_all_pending(chg_id)
                    update_record("change_request", chg_id, {"state": "-2"}, silent=True) # Scheduled
                    update_record("change_request", chg_id, {"state": "-1", "work_notes": "Starting implementation."}, silent=True) # Implement

    # Let's ensure we have enough total active changes in pipeline to reach the states
    pipeline_changes = get_records("change_request", "active=true")
    if len(pipeline_changes) < min_count * 2: # Keep a healthy pipeline
        needed = (min_count * 2) - len(pipeline_changes)
        print(f"Need to create {needed} more change(s) for the pipeline.")
        for _ in range(needed):
            now = datetime.now(timezone.utc)
            chg = create_record("change_request", {
                "short_description": "Auto-generated active change: Routine maintenance",
                "description": "Routine maintenance and security patching for infrastructure servers.",
                "justification": "Required to keep servers compliant with the latest security baseline.",
                "implementation_plan": "1. Verify backups.\n2. Apply patches.\n3. Restart services.",
                "risk_impact_analysis": "Low risk.",
                "backout_plan": "Restore from backups.",
                "test_plan": "Run automated health check scripts.",
                "type": "Normal",
                "priority": "4",
                "risk": "4", # Moderate
                "start_date": now.strftime("%Y-%m-%d %H:%M:%S"),
                "end_date": (now + timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"),
                "expected_start": now.strftime("%Y-%m-%d %H:%M:%S"),
                "work_start": now.strftime("%Y-%m-%d %H:%M:%S"),
                "work_end": (now + timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"),
                "cab_date_time": (now - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
                "due_date": (now + timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S"),
                "requested_by_date": (now - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"),
                "review_date": (now + timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"),
                "category": "Other",
                "contact_type": "Phone",
                "impact": "3",
                "urgency": "3",
                "scope": "Medium",
                "cab_required": "false",
                "outside_maintenance_schedule": "false",
                "production_system": "false",
                "unauthorized": "false",
                "upon_approval": "Proceed to Next Task",
                "upon_reject": "Cancel all future Tasks",
                "work_notes": "Change request auto-created.",
                "comments": "This change was opened by automation.",
                "escalation": "Normal",
                "conflict_status": "Not Run",
                "phase": "Requested",
                "phase_state": "Open",
                "approval": "Approved",
                "approval_set": now.strftime("%Y-%m-%d %H:%M:%S"),
                "cab_recommendation": "Approved by CAB.",
                "change_plan": "Routine maintenance change plan.",
                "conflict_last_run": now.strftime("%Y-%m-%d %H:%M:%S"),
                "reason": "Routine update",
                "review_comments": "Looks good.",
                "review_status": "Reviewed",
                "route_reason": "Standard routing",
                "user_input": "Proceed with change.",
                "knowledge": "false",
                "made_sla": "true",
                "on_hold": "false",
                "on_hold_reason": "Not on hold",
                "activity_due": (now + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
            })

def reassign_incidents():
    print("\n--- Reassigning Incidents ---")
    groups = get_records("sys_user_group", "active=true", limit=10)
    if not groups:
        return

    incidents = get_records("incident", "active=true^stateIN1,2")
    for inc in incidents:
        # Reassign roughly 20% of incidents each run
        if random.random() < 0.2:
            inc_id = inc['sys_id']
            inc_num = inc['number']
            group = random.choice(groups)
            print(f"Reassigning incident {inc_num} to {group.get('name')}...")
            update_record("incident", inc_id, {"assignment_group": group['sys_id']}, silent=True)

def process_incidents():
    print("\n--- Processing Incidents ---")
    incidents = get_records("incident", "active=true^stateNOT IN7,8")
    for inc in incidents:
        inc_id = inc['sys_id']
        inc_num = inc['number']
        age_hours = get_age_hours(inc.get('sys_created_on'))
        
        # Older incidents have higher chance of closing
        # E.g. at 24 hours, maybe 50% chance to close
        close_prob = min(0.9, age_hours / 48.0)
        
        if random.random() < close_prob:
            print(f"Closing incident {inc_num} (age: {age_hours:.1f}h)...")
            payload = {
                "state": "7", # Closed
                "close_code": "Solved (Permanently)",
                "resolution_code": "Software", # Using a more standard SNOW resolution code
                "close_notes": "Auto-closed by script after investigation.",
                "resolution_notes": "Auto-resolved by script."
            }
            update_record("incident", inc_id, payload, silent=True)
        else:
            print(f"Keeping incident {inc_num} open (age: {age_hours:.1f}h).")

def print_running_changes():
    print("\n--- Running Changes ---")
    changes = get_records("change_request", "active=true^stateIN-1,0")
    summary = f"### Running Changes ({len(changes)})\n\n"
    
    if changes:
        for chg in changes:
            num = chg.get('number', 'Unknown')
            short_desc = chg.get('short_description', 'No description')
            state = chg.get('state', 'Unknown')
            state_str = "Implement" if str(state) == "-1" else "Review" if str(state) == "0" else str(state)
            
            assignee = chg.get('assigned_to')
            if type(assignee) is dict:
                assignee_name = assignee.get('display_value', 'Unknown')
            else:
                assignee_name = str(assignee) if assignee else "N/A"
                
            line = f"- **{num}**: {short_desc} (State: {state_str}, Assigned: {assignee_name})"
            print(line.replace("**", ""))
            summary += line + "\n"
    else:
        msg = "No running changes found."
        print(msg)
        summary += msg + "\n"
        
    print("-----------------------\n")
    
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as f:
            f.write(summary)

def create_daily_records():
    now = datetime.now(timezone.utc)
    # Only create new records randomly so we don't flood if it runs every 2 hours
    if random.random() < 0.5:
        print("\n--- Creating New Records ---")
        create_record("incident", {
            "short_description": "Auto-generated incident: Application performance degradation",
            "description": "Users report slow response times in the main application portal.",
            "urgency": "2",
            "impact": "2",
            "priority": "3",
            "category": "software",
            "subcategory": "os",
            "contact_type": "Phone",
            "state": "1",
            "escalation": "Normal",
            "work_notes": "Incident auto-created to track performance issues.",
            "comments": "Automated incident logged.",
            "notify": "1",
            "knowledge": "false",
            "due_date": (now + timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S"),
            "expected_start": now.strftime("%Y-%m-%d %H:%M:%S"),
            "start_date": now.strftime("%Y-%m-%d %H:%M:%S"),
            "end_date": (now + timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"),
            "work_start": now.strftime("%Y-%m-%d %H:%M:%S"),
            "work_end": (now + timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"),
            "activity_due": (now + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
            "approval": "Approved",
            "approval_set": now.strftime("%Y-%m-%d %H:%M:%S"),
            "made_sla": "true",
            "route_reason": "Standard routing",
            "time_worked": "1970-01-01 01:00:00",
            "calendar_duration": "1970-01-01 02:00:00",
            "business_duration": "1970-01-01 02:00:00"
        })
    
    if random.random() < 0.2:
        create_record("problem", {
            "short_description": "Auto-generated problem: Recurring application latency",
            "description": "Multiple incidents reported for app performance.",
            "urgency": "2",
            "impact": "2",
            "priority": "3",
            "state": "1",
            "category": "software",
            "subcategory": "os",
            "work_notes": "Problem auto-created.",
            "comments": "Tracking recurring latency across systems.",
            "knowledge": "false",
            "due_date": (now + timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S"),
            "expected_start": now.strftime("%Y-%m-%d %H:%M:%S"),
            "start_date": now.strftime("%Y-%m-%d %H:%M:%S"),
            "end_date": (now + timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"),
            "work_start": now.strftime("%Y-%m-%d %H:%M:%S"),
            "work_end": (now + timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"),
            "activity_due": (now + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
            "approval": "Approved",
            "approval_set": now.strftime("%Y-%m-%d %H:%M:%S"),
            "made_sla": "true",
            "route_reason": "Standard routing",
            "escalation": "Normal",
            "known_error": "false",
            "contact_type": "Phone",
            "time_worked": "1970-01-01 01:00:00",
            "calendar_duration": "1970-01-01 02:00:00",
            "business_duration": "1970-01-01 02:00:00"
        })

def backfill_all_records():
    print("\n--- Backfilling All Existing Records ---")
    now = datetime.now(timezone.utc)
    
    chg_payload = {
        "start_date": now.strftime("%Y-%m-%d %H:%M:%S"),
        "end_date": (now + timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"),
        "expected_start": now.strftime("%Y-%m-%d %H:%M:%S"),
        "work_start": now.strftime("%Y-%m-%d %H:%M:%S"),
        "work_end": (now + timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"),
        "cab_date_time": (now - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
        "due_date": (now + timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S"),
        "requested_by_date": (now - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"),
        "review_date": (now + timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"),
        "approval": "Approved",
        "approval_set": now.strftime("%Y-%m-%d %H:%M:%S"),
        "cab_recommendation": "Approved by CAB.",
        "change_plan": "Standard change plan.",
        "conflict_last_run": now.strftime("%Y-%m-%d %H:%M:%S"),
        "reason": "Routine update",
        "review_comments": "Looks good.",
        "review_status": "Reviewed",
        "route_reason": "Standard routing",
        "user_input": "Proceed with change.",
        "knowledge": "false",
        "made_sla": "true",
        "on_hold": "false",
        "on_hold_reason": "Not on hold",
        "activity_due": (now + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
        "conflict_status": "Not Run",
        "unauthorized": "false",
        "production_system": "false",
        "outside_maintenance_schedule": "false",
        "cab_required": "false",
        "time_worked": "1970-01-01 01:00:00",
        "calendar_duration": "1970-01-01 02:00:00",
        "business_duration": "1970-01-01 02:00:00"
    }
    
    inc_payload = {
        "due_date": (now + timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S"),
        "expected_start": now.strftime("%Y-%m-%d %H:%M:%S"),
        "start_date": now.strftime("%Y-%m-%d %H:%M:%S"),
        "end_date": (now + timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"),
        "work_start": now.strftime("%Y-%m-%d %H:%M:%S"),
        "work_end": (now + timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"),
        "activity_due": (now + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
        "approval": "Approved",
        "approval_set": now.strftime("%Y-%m-%d %H:%M:%S"),
        "knowledge": "false",
        "made_sla": "true",
        "route_reason": "Standard routing",
        "escalation": "Normal",
        "notify": "1",
        "contact_type": "Phone",
        "category": "software",
        "subcategory": "os",
        "time_worked": "1970-01-01 01:00:00",
        "calendar_duration": "1970-01-01 02:00:00",
        "business_duration": "1970-01-01 02:00:00"
    }
    
    prb_payload = {
        "due_date": (now + timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S"),
        "expected_start": now.strftime("%Y-%m-%d %H:%M:%S"),
        "start_date": now.strftime("%Y-%m-%d %H:%M:%S"),
        "end_date": (now + timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"),
        "work_start": now.strftime("%Y-%m-%d %H:%M:%S"),
        "work_end": (now + timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"),
        "activity_due": (now + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
        "approval": "Approved",
        "approval_set": now.strftime("%Y-%m-%d %H:%M:%S"),
        "knowledge": "false",
        "made_sla": "true",
        "route_reason": "Standard routing",
        "escalation": "Normal",
        "known_error": "false",
        "contact_type": "Phone",
        "category": "software",
        "subcategory": "os",
        "time_worked": "1970-01-01 01:00:00",
        "calendar_duration": "1970-01-01 02:00:00",
        "business_duration": "1970-01-01 02:00:00"
    }
    
    for table, payload in [("change_request", chg_payload), ("incident", inc_payload), ("problem", prb_payload)]:
        # Let's get up to 200 records to prevent script timeout, focusing on the ones that are likely empty.
        records = get_records(table, "sys_created_onANYTHING", limit=200)
        print(f"Backfilling {len(records)} records for {table}...")
        for r in records:
            update_record(table, r['sys_id'], payload, silent=True)

def main():
    # Check for Israel weekend (Friday 13:00 to Saturday 21:00)
    tz = pytz.timezone('Asia/Jerusalem')
    now_il = datetime.now(tz)
    
    if (now_il.weekday() == 4 and now_il.hour >= 13) or \
       (now_il.weekday() == 5 and now_il.hour < 21):
        print(f"Current time in Israel is {now_il.strftime('%Y-%m-%d %H:%M:%S')}.")
        print("Weekend schedule active (Fri 13:00 - Sat 21:00 IST), skipping execution.")
        return

    print("Starting ServiceNow Scheduled Tasks...")
    
    # 0. Backfill all existing records with full fields
    backfill_all_records()
    
    # 1. Process existing changes through their lifecycle
    process_all_changes()
    
    # 2. Process incidents (close or reassign)
    process_incidents()
    reassign_incidents()
    
    # 3. Create new records sporadically
    create_daily_records()
    
    # 4. Ensure pipeline has changes
    ensure_minimum_active_changes(3)
    
    # 5. Display what's running
    print_running_changes()

if __name__ == '__main__':
    main()
