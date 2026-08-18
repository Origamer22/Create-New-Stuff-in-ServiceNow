# 🛠️ ServiceNow Creator

ServiceNow Creator is a fully automated workflow simulation bot that continuously interacts with a ServiceNow instance via its REST API. Running on a scheduled GitHub Action, it simulates a living, breathing IT environment by autonomously creating, updating, progressing, and resolving Change Requests, Incidents, and Problems.

## 🌟 Key Features

- **Change Request Lifecycle Management**: Automatically moves active change requests through standard ITIL states (New ➔ Assess ➔ Authorize ➔ Scheduled ➔ Implement ➔ Review ➔ Closed) with realistic simulated delays.
- **Minimum Pipeline Enforcement**: Continuously monitors the change pipeline to ensure there are *always* at least 3 active Change Requests in the **Implement** state. If there are fewer, it auto-generates urgent changes to fulfill the requirement.
- **Incident & Problem Automation**: Sporadically creates mock incidents and problems, simulating an active helpdesk. It automatically resolves older incidents and randomly reassigns 20% of active incidents to keep the environment dynamic.
- **Automated Approvals**: Detects and automatically approves any pending approvals for changes stuck in the "Authorize" state.
- **Timezone & Weekend Awareness**: Implements intelligent pausing during the Israeli weekend (Friday 13:00 to Saturday 21:00 IST), skipping execution based on `pytz` timezone calculations.
- **GitHub Actions Integration**: Built to run entirely serverless on a 2-hour cron schedule. It features a built-in "Keepalive" commit mechanism to prevent GitHub from disabling the scheduled workflow after 60 days of inactivity.

## 📂 Repository Structure

- `servicenow_creator/create_records.py`: The core Python engine handling all REST API calls and ServiceNow state machine logic.
- `servicenow_creator/requirements.txt`: Python package dependencies (`requests` for API interactions, `pytz` for timezone handling).
- `.github/workflows/servicenow_creator.yml`: The GitHub Actions CI/CD configuration file defining the schedule and execution environment.

## 🚀 Step-by-Step Setup Instructions

Deploy this automation to your own GitHub repository and connect it to your ServiceNow developer instance by following these instructions:

### Step 1: Fork or Clone the Repository
To utilize the automated GitHub Actions workflow, you must have this code in your own repository.
1. Click the **Fork** button at the top right of this repository to create a copy under your own GitHub account.
2. (Optional) Clone it locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/Create-New-Stuff-in-ServiceNow.git
   cd Create-New-Stuff-in-ServiceNow
   ```

### Step 2: Prepare ServiceNow Credentials
The automation requires a ServiceNow user account with sufficient read/write/delete permissions for the following tables:
- `change_request`
- `incident`
- `problem`
- `sysapproval_approver`
- `sys_user_group`

*Note: The default `admin` account on a ServiceNow Personal Developer Instance (PDI) is recommended for testing.*

### Step 3: Configure GitHub Secrets
You need to pass your ServiceNow credentials securely to GitHub Actions.
1. Navigate to your forked repository on GitHub.
2. Click on **Settings** in the top navigation bar.
3. In the left sidebar, navigate to **Secrets and variables** > **Actions**.
4. Click **New repository secret** and add the following three secrets:
   - **Name**: `SN_INSTANCE`
     **Secret**: Your instance ID (e.g., `dev12345` or `dev12345.service-now.com`).
   - **Name**: `SN_USERNAME`
     **Secret**: Your ServiceNow API username (e.g., `admin`).
   - **Name**: `SN_PASSWORD`
     **Secret**: Your ServiceNow API password.

### Step 4: Enable the GitHub Action
By default, GitHub disables scheduled workflows in forked repositories.
1. Go to the **Actions** tab in your GitHub repository.
2. Click the green button: **I understand my workflows, go ahead and enable them**.
3. The workflow will now automatically run every 2 hours.
4. **To test immediately:** Select **ServiceNow Creator** from the left sidebar, click the **Run workflow** dropdown, and click **Run workflow**.

### Step 5: Local Development & Testing (Optional)
If you prefer to run the bot locally or develop new features:

1. Ensure **Python 3.x** is installed on your machine.
2. **Install dependencies**:
   Navigate to the repository root and run:
   ```bash
   pip install -r servicenow_creator/requirements.txt
   ```
3. **Set Environment Variables**:
   Export your ServiceNow credentials to your local environment.
   
   *Windows (PowerShell):*
   ```powershell
   $env:SN_INSTANCE="dev12345"
   $env:SN_USERNAME="your_username"
   $env:SN_PASSWORD="your_password"
   ```
   *Mac/Linux (Bash):*
   ```bash
   export SN_INSTANCE="dev12345"
   export SN_USERNAME="your_username"
   export SN_PASSWORD="your_password"
   ```
4. **Execute the Script**:
   ```bash
   python servicenow_creator/create_records.py
   ```
   You will see console output detailing the lifecycle progression of your records in ServiceNow!

## 🤝 Contributing
Feel free to open issues or submit pull requests if you want to add new record types, lifecycle rules, or enhance the simulation logic!

---
# We stand with Israel 🇮🇱
