import os
import requests
from datetime import datetime, timezone, timedelta

SN_INSTANCE = os.environ.get('SN_INSTANCE')
SN_USERNAME = os.environ.get('SN_USERNAME')
SN_PASSWORD = os.environ.get('SN_PASSWORD')

SN_INSTANCE = SN_INSTANCE.replace('https://', '').replace('http://', '').rstrip('/')
if SN_INSTANCE.endswith('.service-now.com'):
    SN_INSTANCE = SN_INSTANCE.replace('.service-now.com', '')

BASE_URL = f"https://{SN_INSTANCE}.service-now.com/api/now/table"
HEADERS = {"Content-Type": "application/json", "Accept": "application/json"}
AUTH = (SN_USERNAME, SN_PASSWORD)

now = datetime.now(timezone.utc)
payload = {
    "start_date": now.strftime("%Y-%m-%d %H:%M:%S"),
    "end_date": (now + timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"),
    "time_worked": "1970-01-01 01:00:00",
    "calendar_duration": "1970-01-01 02:00:00",
    "business_duration": "1970-01-01 02:00:00"
}

sys_id = "4e349172839e8f50023553b6feaad369" # sys_id from user's JSON
url = f"{BASE_URL}/change_request/{sys_id}"
response = requests.put(url, auth=AUTH, headers=HEADERS, json=payload)
print(response.status_code)
print(response.text)
