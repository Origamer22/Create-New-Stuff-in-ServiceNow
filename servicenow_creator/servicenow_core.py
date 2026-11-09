"""
Shared ServiceNow simulation engine.

All REST API calls, lifecycle progression, quota enforcement, scheduling and
weekend logic live here. The language-specific entry points
(create_records.py for Hebrew with English IT terms, create_records_en.py for
pure English) only supply a LanguagePack with the text that ends up in
ServiceNow, and then call run(pack).
"""
import os
import sys
import random
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta

import requests
import pytz

# Ensure stdout and stderr handle UTF-8 Hebrew characters safely
try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass


@dataclass(frozen=True)
class LanguagePack:
    """All user-visible text written to ServiceNow (and to the run summary) for one language."""
    name: str
    change_templates: list
    default_change_plan: str
    # Change request payload texts
    change_reason: str
    change_review_comments: str
    change_user_input: str
    change_work_notes: str
    change_comments: str
    # Lifecycle notes
    implement_start_note: str
    implement_done_note: str
    review_close_notes: str
    quota_close_notes: str
    # Incident lifecycle
    incident_close_notes: str
    incident_resolution_notes: str
    # Sporadic incident / problem texts
    incident_short_description: str
    incident_description: str
    incident_work_notes: str
    incident_comments: str
    problem_short_description: str
    problem_description: str
    problem_work_notes: str
    problem_comments: str
    # Running changes summary labels
    summary_no_description: str
    summary_default_assignee: str
    summary_state_label: str
    summary_from_label: str
    summary_to_label: str
    summary_assigned_label: str


# Connection settings, populated by load_config()
SN_INSTANCE = None
SN_USERNAME = None
SN_PASSWORD = None
BASE_URL = None
HEADERS = {"Content-Type": "application/json", "Accept": "application/json"}
AUTH = None


def _load_env_files():
    # Try loading .env from various standard locations if credentials are not in os.environ
    if all([os.environ.get('SN_INSTANCE') or os.environ.get('SNOW_INSTANCE'),
            os.environ.get('SN_USERNAME') or os.environ.get('SNOW_USERNAME'),
            os.environ.get('SN_PASSWORD') or os.environ.get('SNOW_PASSWORD')]):
        return
    search_dirs = [
        os.path.join(os.path.dirname(__file__), '..', '.env'),
        os.path.join(os.path.dirname(__file__), '.env'),
        os.path.join(os.path.dirname(__file__), '..', '..', 'Service-Now-Changes-Schedule', '.env'),
        os.path.join(os.getcwd(), '.env'),
        os.path.join(os.getcwd(), '..', 'Service-Now-Changes-Schedule', '.env'),
    ]
    for sp in search_dirs:
        sp = os.path.abspath(sp)
        if os.path.exists(sp):
            try:
                with open(sp, 'r', encoding='utf-8', errors='replace') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            k, v = line.split('=', 1)
                            k, v = k.strip(), v.strip().strip("'\"")
                            if k not in os.environ:
                                os.environ[k] = v
                break
            except Exception:
                pass


def load_config():
    """Load ServiceNow credentials from the environment (or a .env file) and build the API settings."""
    global SN_INSTANCE, SN_USERNAME, SN_PASSWORD, BASE_URL, AUTH
    _load_env_files()

    SN_INSTANCE = os.environ.get('SN_INSTANCE') or os.environ.get('SNOW_INSTANCE')
    SN_USERNAME = os.environ.get('SN_USERNAME') or os.environ.get('SNOW_USERNAME')
    SN_PASSWORD = os.environ.get('SN_PASSWORD') or os.environ.get('SNOW_PASSWORD')

    if not all([SN_INSTANCE, SN_USERNAME, SN_PASSWORD]):
        print("Error: Missing ServiceNow credentials.")
        sys.exit(1)

    SN_INSTANCE = SN_INSTANCE.replace('https://', '').replace('http://', '').rstrip('/')
    if SN_INSTANCE.endswith('.service-now.com'):
        SN_INSTANCE = SN_INSTANCE.replace('.service-now.com', '')

    BASE_URL = f"https://{SN_INSTANCE}.service-now.com/api/now/table"
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
        except Exception:
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
    if not sys_created_on_str:
        return 0
    try:
        created = datetime.strptime(sys_created_on_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        return (now - created).total_seconds() / 3600
    except Exception:
        return 0


def approve_all_pending(sys_id):
    approvals = get_records("sysapproval_approver", f"sysapproval={sys_id}^state=requested")
    for app in approvals:
        update_record("sysapproval_approver", app['sys_id'], {"state": "approved"}, silent=True)


def generate_change_payload(lang, state_target="implement", ag_id="", user_id=""):
    """
    Generates a full change request payload using the language pack's templates.
    The change duration is configured between several hours to several days,
    so that on the calendar it appears spanning across multiple days.
    """
    tmpl = random.choice(lang.change_templates)
    now = datetime.now(timezone.utc)

    # Duration options: from 3 hours to 5 days (120 hours)
    duration_distribution = [
        random.randint(3, 6),     # Short changes: 3 to 6 hours long
        random.randint(8, 18),    # Moderate changes: 8 to 18 hours long
        random.randint(24, 48),   # 1 to 2 days
        random.randint(48, 72),   # 2 to 3 days
        random.randint(96, 120),  # Long changes: 4 to 5 days long (spanning the calendar)
    ]
    duration_hours = random.choice(duration_distribution)

    if state_target == "implement":
        # Actively running right now: started in the past, ends in the future
        # For short 3h changes, elapsed is 1-2 hours; for multi-day, elapsed can be up to 48h
        if duration_hours <= 6:
            elapsed_hours = random.randint(1, max(1, duration_hours - 1))
        else:
            max_elapsed = min(duration_hours - 2, 48)
            elapsed_hours = random.randint(2, max(2, max_elapsed))
        start_dt = now - timedelta(hours=elapsed_hours)
        end_dt = start_dt + timedelta(hours=duration_hours)
    elif state_target == "pipeline":
        # Scheduled in the future (starting today, tomorrow, or over the next 5 days)
        future_start_hours = random.choice([2, 6, 12, 24, 36, 48, 72, 96, 120])
        start_dt = now + timedelta(hours=future_start_hours)
        end_dt = start_dt + timedelta(hours=duration_hours)
    elif state_target == "closed":
        # Completed in the past
        past_days = random.randint(4, 7)
        start_dt = now - timedelta(days=past_days, hours=random.randint(0, 12))
        end_dt = start_dt + timedelta(hours=duration_hours)
    else:
        start_dt = now
        end_dt = now + timedelta(hours=duration_hours)

    start_str = start_dt.strftime("%Y-%m-%d %H:%M:%S")
    end_str = end_dt.strftime("%Y-%m-%d %H:%M:%S")
    due_str = (end_dt + timedelta(hours=12)).strftime("%Y-%m-%d %H:%M:%S")
    req_by_str = (start_dt - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")
    rev_str = end_dt.strftime("%Y-%m-%d %H:%M:%S")

    payload = {
        "short_description": tmpl["short_description"],
        "description": tmpl["description"],
        "justification": tmpl["justification"],
        "implementation_plan": tmpl["implementation_plan"],
        "risk_impact_analysis": tmpl["risk_impact_analysis"],
        "backout_plan": tmpl["backout_plan"],
        "test_plan": tmpl["test_plan"],
        "change_plan": tmpl.get("change_plan", lang.default_change_plan),
        "type": "Normal",
        "priority": tmpl.get("priority", "3"),
        "category": tmpl.get("category", "Other"),
        "scope": tmpl.get("scope", "Medium"),
        "assignment_group": ag_id,
        "start_date": start_str,
        "end_date": end_str,
        "expected_start": start_str,
        "work_start": start_str,
        "work_end": end_str,
        "due_date": due_str,
        "requested_by_date": req_by_str,
        "review_date": rev_str,
        "contact_type": "Phone",
        "impact": "3",
        "urgency": "3",
        "outside_maintenance_schedule": "false",
        "production_system": "true" if "Production" in tmpl["short_description"] else "false",
        "unauthorized": "false",
        "upon_approval": "Proceed to Next Task",
        "upon_reject": "Cancel all future Tasks",
        "work_notes": lang.change_work_notes,
        "comments": lang.change_comments,
        "escalation": "Normal",
        "conflict_status": "Not Run",
        "phase": "Requested",
        "phase_state": "Open",
        "approval": "Approved",
        "approval_set": now.strftime("%Y-%m-%d %H:%M:%S"),
        "reason": lang.change_reason,
        "review_comments": lang.change_review_comments,
        "review_status": "Reviewed",
        "route_reason": "Standard routing",
        "user_input": lang.change_user_input,
        "knowledge": "false",
        "made_sla": "true",
        "on_hold": "false",
        "on_hold_reason": "Not on hold",
        "activity_due": (now + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
    }
    if user_id:
        payload["assigned_to"] = user_id
    return payload


def progress_change(lang, chg):
    chg_id = chg['sys_id']
    chg_num = chg['number']

    # State mapping:
    # -5 = New, -4 = Assess, -3 = Authorize, -2 = Scheduled, -1 = Implement, 0 = Review, 3 = Closed

    state_str = chg.get('state', '-5')
    try:
        state = int(state_str)
    except Exception:
        state = -5

    print(f"Progressing change {chg_num} from state {state}...")
    age_hours = get_age_hours(chg.get('sys_created_on'))
    now_utc = datetime.now(timezone.utc)

    if state == -5:  # New -> Assess
        ag_id, user_id = get_random_group_and_user()
        payload = {"state": "-4", "assignment_group": ag_id}
        if user_id:
            payload["assigned_to"] = user_id
        update_record("change_request", chg_id, payload, silent=True)

    elif state == -4:  # Assess -> Authorize
        update_record("change_request", chg_id, {"state": "-3"}, silent=True)

    elif state == -3:  # Authorize -> Scheduled
        approve_all_pending(chg_id)
        update_record("change_request", chg_id, {"state": "-2"}, silent=True)

    elif state == -2:  # Scheduled -> Implement
        # Check if planned start_date has arrived
        start_date_str = chg.get('start_date')
        ready_to_start = True
        if start_date_str:
            try:
                start_dt = datetime.strptime(start_date_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                ready_to_start = now_utc >= start_dt
            except Exception:
                ready_to_start = True

        if ready_to_start:
            update_record("change_request", chg_id, {
                "state": "-1",
                "work_notes": lang.implement_start_note
            }, silent=True)
            print(f"Moved {chg_num} to Implement.")
        else:
            print(f"Keeping {chg_num} in Scheduled (starts at {start_date_str}).")

    elif state == -1:  # Implement -> Review
        # Stay in Implement until end_date arrives, or after planned duration
        end_date_str = chg.get('end_date')
        ready_to_review = False
        if end_date_str:
            try:
                end_dt = datetime.strptime(end_date_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                ready_to_review = now_utc >= end_dt
            except Exception:
                ready_to_review = abs(age_hours) > 24
        else:
            ready_to_review = abs(age_hours) > 24

        if ready_to_review:
            update_record("change_request", chg_id, {
                "state": "0",
                "work_notes": lang.implement_done_note
            }, silent=True)
            print(f"Moved {chg_num} to Review (age {abs(age_hours):.1f}h)")
        else:
            print(f"Keeping {chg_num} in Implement (scheduled until {end_date_str or 'N/A'}, age {abs(age_hours):.1f}h)")

    elif state == 0:  # Review -> Closed
        # Keep in review for 12 to 48 hours before closing
        threshold = random.randint(12, 48)
        if abs(age_hours) > threshold:
            payload = {
                "state": "3",
                "close_code": "successful",
                "close_notes": lang.review_close_notes
            }
            update_record("change_request", chg_id, payload, silent=True)
            print(f"Closed {chg_num} (age {abs(age_hours):.1f}h)")
        else:
            print(f"Keeping {chg_num} in Review (age {abs(age_hours):.1f}h, threshold {threshold}h)")


def process_all_changes(lang):
    print("\n--- Processing Change Requests ---")
    changes = get_records("change_request", "active=true")
    for chg in changes:
        progress_change(lang, chg)


_CACHED_GRMEMBERS = []


def get_random_group_and_user():
    global _CACHED_GRMEMBERS
    if not _CACHED_GRMEMBERS:
        members = get_records("sys_user_grmember", "group.active=true^user.active=true", limit=100)
        valid = []
        for m in members:
            ag = m['group']['value'] if isinstance(m.get('group'), dict) else m.get('group', '')
            u = m['user']['value'] if isinstance(m.get('user'), dict) else m.get('user', '')
            if ag and u:
                valid.append((ag, u))
        _CACHED_GRMEMBERS = valid

    if _CACHED_GRMEMBERS:
        return random.choice(_CACHED_GRMEMBERS)

    groups = get_records("sys_user_group", "active=true", limit=20)
    if groups:
        ag_id = random.choice(groups)['sys_id']
        return ag_id, ""
    return "", ""


def ensure_closed_changes(lang, min_closed=5):
    print("\n--- Ensuring Minimum Closed Changes ---")
    closed_changes = get_records("change_request", "active=false^state=3")
    current_count = len(closed_changes)
    print(f"Currently have {current_count} closed changes.")

    if current_count < min_closed:
        needed = min_closed - current_count
        print(f"Need to create {needed} more closed change(s).")
        for _ in range(needed):
            ag_id, user_id = get_random_group_and_user()
            payload = generate_change_payload(lang, state_target="closed", ag_id=ag_id, user_id=user_id)
            payload["state"] = "-5"
            chg = create_record("change_request", payload)
            if chg:
                chg_id = chg.get('sys_id')
                if chg_id:
                    payload_assess = {"state": "-4", "assignment_group": ag_id}
                    if user_id:
                        payload_assess["assigned_to"] = user_id
                    update_record("change_request", chg_id, payload_assess, silent=True)
                    update_record("change_request", chg_id, {"state": "-3"}, silent=True)
                    approve_all_pending(chg_id)
                    update_record("change_request", chg_id, {"state": "-2"}, silent=True)
                    update_record("change_request", chg_id, {"state": "-1"}, silent=True)
                    update_record("change_request", chg_id, {"state": "0"}, silent=True)
                    update_record("change_request", chg_id, {
                        "state": "3",
                        "active": "false",
                        "close_code": "successful",
                        "close_notes": lang.quota_close_notes
                    }, silent=True)


def ensure_minimum_active_changes(lang, min_count=4):
    print("\n--- Ensuring Minimum Active Changes ---")
    implement_changes = get_records("change_request", "active=true^state=-1")
    current_count = len(implement_changes)
    print(f"Currently have {current_count} active changes in Implement.")

    if current_count < min_count:
        needed_active = min_count - current_count
        print(f"Need to create {needed_active} more change(s) directly in Implement state.")
        for _ in range(needed_active):
            ag_id, user_id = get_random_group_and_user()
            payload = generate_change_payload(lang, state_target="implement", ag_id=ag_id, user_id=user_id)
            payload["state"] = "-5"  # Create in New, then fast-forward to Implement

            chg = create_record("change_request", payload)
            if chg:
                chg_id = chg.get('sys_id')
                if chg_id:
                    # Fast-forward to Implement
                    payload_assess = {"state": "-4", "assignment_group": ag_id}
                    if user_id:
                        payload_assess["assigned_to"] = user_id
                    update_record("change_request", chg_id, payload_assess, silent=True)  # Assess
                    update_record("change_request", chg_id, {"state": "-3"}, silent=True)  # Authorize
                    approve_all_pending(chg_id)
                    update_record("change_request", chg_id, {"state": "-2"}, silent=True)  # Scheduled
                    payload_imp = {
                        "state": "-1",
                        "work_notes": lang.implement_start_note,
                        "assignment_group": ag_id,
                    }
                    if user_id:
                        payload_imp["assigned_to"] = user_id
                    update_record("change_request", chg_id, payload_imp, silent=True)  # Implement

    # Ensure healthy pipeline of upcoming changes
    pipeline_changes = get_records("change_request", "active=true")
    if len(pipeline_changes) < min_count * 2:
        needed = (min_count * 2) - len(pipeline_changes)
        print(f"Need to create {needed} more change(s) for the pipeline.")
        for _ in range(needed):
            ag_id, user_id = get_random_group_and_user()
            payload = generate_change_payload(lang, state_target="pipeline", ag_id=ag_id, user_id=user_id)
            create_record("change_request", payload)


def reassign_incidents():
    return


def process_incidents(lang):
    print("\n--- Processing Incidents ---")
    incidents = get_records("incident", "active=true^stateNOT IN7,8")
    for inc in incidents:
        inc_id = inc['sys_id']
        inc_num = inc['number']
        age_hours = abs(get_age_hours(inc.get('sys_created_on')))
        close_prob = min(0.9, age_hours / 48.0)

        if random.random() < close_prob:
            print(f"Closing incident {inc_num} (age: {age_hours:.1f}h)...")
            payload = {
                "state": "7",  # Closed
                "close_code": "Solved (Permanently)",
                "resolution_code": "Software",
                "close_notes": lang.incident_close_notes,
                "resolution_notes": lang.incident_resolution_notes
            }
            update_record("incident", inc_id, payload, silent=True)
        else:
            print(f"Keeping incident {inc_num} open (age: {age_hours:.1f}h).")


def print_running_changes(lang):
    print("\n--- Running Changes ---")
    changes = get_records("change_request", "active=true^stateIN-1,0")
    summary = f"### Running Changes ({len(changes)})\n\n"

    if changes:
        for chg in changes:
            num = chg.get('number', 'Unknown')
            short_desc = chg.get('short_description', lang.summary_no_description)
            state = chg.get('state', 'Unknown')
            state_str = "Implement" if str(state) == "-1" else "Review" if str(state) == "0" else str(state)
            start_date = chg.get('start_date', 'N/A')
            end_date = chg.get('end_date', 'N/A')

            assignee = chg.get('assigned_to')
            if type(assignee) is dict:
                assignee_name = assignee.get('display_value', 'Unknown')
            else:
                assignee_name = str(assignee) if assignee else lang.summary_default_assignee

            line = (
                f"- **{num}**: {short_desc} | {lang.summary_state_label}: {state_str} | "
                f"{lang.summary_from_label}: {start_date} {lang.summary_to_label}: {end_date} | "
                f"{lang.summary_assigned_label}: {assignee_name}"
            )
            print(line.replace("**", ""))
            summary += line + "\n"
    else:
        msg = "No running changes found."
        print(msg)
        summary += msg + "\n"

    print("-----------------------\n")

    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a', encoding='utf-8') as f:
            f.write(summary)


def create_daily_records(lang):
    ag_id, user_id = get_random_group_and_user()
    now = datetime.now(timezone.utc)

    # Sporadically create incident
    if random.random() < 0.5:
        print("\n--- Creating New Records ---")
        inc_p = {
            "short_description": lang.incident_short_description,
            "description": lang.incident_description,
            "urgency": "2",
            "impact": "2",
            "priority": "3",
            "assignment_group": ag_id,
            "category": "software",
            "subcategory": "os",
            "contact_type": "Phone",
            "state": "1",
            "escalation": "Normal",
            "work_notes": lang.incident_work_notes,
            "comments": lang.incident_comments,
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
        }
        if user_id:
            inc_p["assigned_to"] = user_id
        create_record("incident", inc_p)

    if random.random() < 0.2:
        prob_p = {
            "short_description": lang.problem_short_description,
            "description": lang.problem_description,
            "urgency": "2",
            "impact": "2",
            "priority": "3",
            "assignment_group": ag_id,
            "state": "1",
            "category": "software",
            "subcategory": "os",
            "work_notes": lang.problem_work_notes,
            "comments": lang.problem_comments,
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
        }
        if user_id:
            prob_p["assigned_to"] = user_id
        create_record("problem", prob_p)


def backfill_records_missing_dates():
    """
    Safely backfills only records that lack start_date or end_date,
    without overwriting existing valid records or their text.
    """
    print("\n--- Checking for Records Missing Dates ---")
    now = datetime.now(timezone.utc)

    empty_changes = get_records("change_request", "start_dateISEMPTY^ORend_dateISEMPTY", limit=50)
    if empty_changes:
        print(f"Found {len(empty_changes)} changes missing dates. Backfilling...")
        for r in empty_changes:
            duration_days = random.choice([1, 2, 3, 4])
            start_dt = now - timedelta(hours=random.randint(2, 24))
            end_dt = start_dt + timedelta(days=duration_days)
            payload = {
                "start_date": start_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "end_date": end_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "expected_start": start_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "work_start": start_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "work_end": end_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "due_date": (end_dt + timedelta(hours=12)).strftime("%Y-%m-%d %H:%M:%S")
            }
            update_record("change_request", r['sys_id'], payload, silent=True)
    else:
        print("No changes missing dates.")


def is_israel_weekend(now_il):
    """True during the Israeli weekend pause (Friday 13:00 to Saturday 21:00 Israel time)."""
    return (now_il.weekday() == 4 and now_il.hour >= 13) or \
           (now_il.weekday() == 5 and now_il.hour < 21)


def run(lang):
    """Run one full simulation cycle using the given language pack."""
    # Check for Israel weekend (Friday 13:00 to Saturday 21:00)
    tz = pytz.timezone('Asia/Jerusalem')
    now_il = datetime.now(tz)

    if is_israel_weekend(now_il):
        print(f"Current time in Israel is {now_il.strftime('%Y-%m-%d %H:%M:%S')}.")
        print("Weekend schedule active (Fri 13:00 - Sat 21:00 IST), skipping execution.")
        return

    load_config()
    print(f"Starting ServiceNow Scheduled Tasks ({lang.name})...")

    # 0. Backfill only records missing dates
    backfill_records_missing_dates()

    # 1. Process existing changes through their lifecycle
    process_all_changes(lang)

    # 2. Process incidents (close or reassign)
    process_incidents(lang)
    reassign_incidents()

    # 3. Create new records sporadically
    create_daily_records(lang)

    # 4. Ensure pipeline has changes (multi-day spans)
    ensure_minimum_active_changes(lang, 8)
    ensure_closed_changes(lang, 8)

    # 5. Display what's running
    print_running_changes(lang)

