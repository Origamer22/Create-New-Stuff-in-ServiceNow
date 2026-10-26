# 🛠️ ServiceNow Creator

ServiceNow Creator is a fully automated workflow simulation bot that continuously interacts with a ServiceNow instance via its REST API. Running on an hourly scheduled GitHub Action, it simulates an authentic, living enterprise IT environment by autonomously creating, updating, progressing, and resolving Change Requests, Incidents, and Problems.

## 🌟 Key Features

- **Realistic Hebrew & English IT Change Catalog**: Generates comprehensive, production-grade Change Requests authored in natural Hebrew with authentic English technical terminology (e.g., *Kubernetes Clusters, Check Point Firewalls, PostgreSQL Clusters, NetApp SAN Storage, SSL/TLS Wildcard Certificates, VMware ESXi, Azure AD SSO & MFA, BGP Multihoming*). Every change includes complete ITIL fields: justification, detailed implementation steps, risk/impact analysis, test plan, and backout plan.
- **Calendar-Spanning Durations (3 Hours to 5 Days)**: Change windows are modeled with realistic duration distributions—from rapid 3–6 hour maintenance windows up to multi-day 4–5 day migrations (120 hours). This ensures schedule and calendar views (such as the ServiceNow Changes Schedule calendar) remain visually active and spanned across days and weeks.
- **Date-Aware ITIL Lifecycle Progression**: Moves active change requests through standard ITIL states (**New ➔ Assess ➔ Authorize ➔ Scheduled ➔ Implement ➔ Review ➔ Closed**). Scheduled changes only enter **Implement** when their planned `start_date` arrives, and implement changes stay active until their planned `end_date` is reached.
- **Minimum Pipeline & Quota Enforcement**: Continuously monitors the change pipeline to maintain:
  - At least **8 concurrent active changes** in the **Implement** state.
  - At least **8 completed changes** in the **Closed** state.
  - A healthy forward-looking pipeline of upcoming changes (at least 16 changes overall).
- **Incident & Problem Automation**: Periodically generates realistic mock incidents and problems in Hebrew with English IT terminology, simulating an active service desk. It calculates record age and automatically resolves aging incidents with formal resolution notes.
- **Automated Approvals**: Detects changes pending CAB or manager approval in the **Authorize** state and automatically approves their corresponding `sysapproval_approver` records.
- **Business Rule & Data Integrity Compliance**: Strictly adheres to ServiceNow's OOTB task assignment validation rules (*"Abort changes on group"*). Automatically cross-references verified group memberships from `sys_user_grmember` so that all task assignments remain valid without triggering business rule transaction aborts.
- **Hourly Schedule & Israeli Weekend Awareness**:
  - Runs **hourly** throughout the Israeli work week: Sunday through Thursday (`0 * * * 0-4`).
  - Runs Friday morning until 13:00 Israel time (`0 0-9 * * 5` UTC).
  - Automatically pauses during Shabbat / Israeli weekend (Friday 13:00 to Saturday 21:00 IST), both via cron triggers and runtime `pytz` calculations.
  - Resumes on Saturday night from 21:00 Israel time (`0 18-23 * * 6` UTC).
- **GitHub Actions Job Summary (`GITHUB_STEP_SUMMARY`)**: After each run, publishes a formatted Markdown summary directly into the GitHub Actions run overview, showing all currently running changes, dates, and assignees.
- **Safe Date Backfilling**: Automatically scans for legacy or imported changes missing `start_date` or `end_date` and populates them safely without altering existing descriptions.
- **Keepalive Automation**: Automatically commits an empty keepalive commit if the repository has been idle for more than 50 days, preventing GitHub from disabling scheduled workflows after 60 days.

## 📂 Repository Structure

- [create_records.py](file:///c:/Users/orile/OneDrive/Service%20Now/Create-New-Stuff-in-ServiceNow/servicenow_creator/create_records.py): The core Python engine handling REST API calls, Hebrew templates, duration calculations, date-aware lifecycle state machines, and summary reporting.
- [requirements.txt](file:///c:/Users/orile/OneDrive/Service%20Now/Create-New-Stuff-in-ServiceNow/servicenow_creator/requirements.txt): Python dependencies (`requests` for API communication, `pytz` for Israel timezone calculations).
- [.github/workflows/servicenow_creator.yml](file:///c:/Users/orile/OneDrive/Service%20Now/Create-New-Stuff-in-ServiceNow/.github/workflows/servicenow_creator.yml): GitHub Actions workflow defining hourly cron schedules, UTF-8 environment settings, and keepalive logic.

## 🚀 Step-by-Step Setup Instructions

Deploy this automation to your own GitHub repository and connect it to your ServiceNow developer instance by following these instructions:

### Step 1: Fork or Clone the Repository
To utilize the automated GitHub Actions workflow, you must have this code in your own repository.

Click the **Fork** button at the top right of this repository to create a copy under your own GitHub account.

### Step 2: Prepare ServiceNow Credentials
The automation requires a ServiceNow user account with sufficient read/write/delete permissions for the following tables:
- `change_request`
- `incident`
- `problem`
- `sysapproval_approver`
- `sys_user_group`
- `sys_user`
- `sys_user_grmember` (Used to verify user-to-group assignments and ensure business rule compliance)

*Note: The default `admin` account on a ServiceNow Personal Developer Instance (PDI) is recommended for testing.*

### Step 3: Configure GitHub Secrets
Pass your ServiceNow credentials securely to GitHub Actions:
1. Navigate to your repository on GitHub.
2. Go to **Settings** > **Secrets and variables** > **Actions**.
3. Click **New repository secret** and add the following three secrets:
   - **Name**: `SN_INSTANCE`  
     **Secret**: Your instance ID (e.g., `dev12345` or `dev12345.service-now.com`).
   - **Name**: `SN_USERNAME`  
     **Secret**: Your ServiceNow API username (e.g., `admin`).
   - **Name**: `SN_PASSWORD`  
     **Secret**: Your ServiceNow API password.

### Step 4: Enable the GitHub Action
By default, GitHub disables scheduled workflows in newly forked repositories.
1. Go to the **Actions** tab in your GitHub repository.
2. Click the green button: **I understand my workflows, go ahead and enable them**.
3. The workflow will now automatically run every hour (according to the Israel work week schedule).
4. **To test immediately:** Select **ServiceNow Creator** from the left sidebar, click the **Run workflow** dropdown, and click **Run workflow**.

### Step 5: Local Development & Testing (Optional)
If you prefer to run the bot locally or develop new features:

1. Ensure **Python 3.x** is installed on your machine.
2. **Install dependencies**:
   ```bash
   pip install -r servicenow_creator/requirements.txt
   ```
3. **Configure Environment Variables**:
   The script automatically detects and loads any `.env` file located in the project directory, parent folder, or sister project (`Service-Now-Changes-Schedule/.env`). Both `SN_*` and `SNOW_*` prefixes are supported:
   
   ```env
   SN_INSTANCE=dev12345
   SN_USERNAME=admin
   SN_PASSWORD=your_password
   ```

   Alternatively, you can export them directly in your shell:
   
   *Windows (PowerShell):*
   ```powershell
   $env:SN_INSTANCE="dev12345"
   $env:SN_USERNAME="your_username"
   $env:SN_PASSWORD="your_password"
   $env:PYTHONIOENCODING="utf-8"
   $env:PYTHONUTF8="1"
   ```
   *Mac/Linux (Bash):*
   ```bash
   export SN_INSTANCE="dev12345"
   export SN_USERNAME="your_username"
   export SN_PASSWORD="your_password"
   export PYTHONIOENCODING="utf-8"
   export PYTHONUTF8="1"
   ```
4. **Execute the Script**:
   ```bash
   python servicenow_creator/create_records.py
   ```
   You will see console output detailing record creation, Hebrew change templates, lifecycle state progressions, and a list of running changes!

## 🤝 Contributing
Feel free to open issues or submit pull requests if you want to add new record types, lifecycle rules, or enhance the simulation logic!

---
# We stand with Israel 🇮🇱
