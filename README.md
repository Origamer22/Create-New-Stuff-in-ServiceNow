# We stand with Israel 🇮🇱

# ServiceNow Creator

ServiceNow Creator is an automated workflow simulation bot that interacts with the ServiceNow REST API. It is designed to run on a schedule (using GitHub Actions) to simulate an active, living ServiceNow environment. It autonomously creates, updates, progresses, and resolves Change Requests, Incidents, and Problems.

## 🚀 Features

- **Change Request Lifecycle Management**: Automatically progresses active change requests through standard ITIL states (New → Assess → Authorize → Scheduled → Implement → Review → Closed) based on realistic time delays.
- **Minimum State Enforcement**: Continuously monitors the pipeline and ensures there are *always* at least 3 active Change Requests specifically in the **Implement** state, automatically generating urgent changes to fill the gap if needed.
- **Incident & Problem Automation**: Sporadically creates new mock incidents and problems. It also randomly reassigns 20% of active incidents and automatically resolves older incidents to simulate a living helpdesk.
- **Approval Automation**: Automatically approves any pending approvals for changes currently in the "Authorize" state.
- **Weekend Awareness**: Automatically pauses execution during the Israeli weekend (Friday 13:00 to Saturday 21:00 IST) using timezone-aware logic.
- **GitHub Actions Integration**: Runs on a 2-hour cron schedule. It includes a built-in "Keepalive" commit mechanism to prevent GitHub from disabling the scheduled workflow after 60 days of repository inactivity, and outputs running change summaries directly to the GitHub Actions workflow run summary.

## 📁 Repository Structure

- `servicenow_creator/create_records.py`: The core Python engine that handles all ServiceNow API interactions and state machine logic.
- `servicenow_creator/requirements.txt`: Python dependencies (`requests` for API calls, `pytz` for timezone handling).
- `.github/workflows/servicenow_creator.yml`: The GitHub Actions workflow configuration.

---

## 🛠️ Step-by-Step Setup Instructions

Follow these detailed steps to deploy this automation to your own GitHub repository and connect it to your ServiceNow instance.

### Step 1: Fork or Clone the Repository
To run the GitHub Actions workflow, you need this code in your own GitHub account.
1. Click the **Fork** button at the top right of this repository to create a copy in your GitHub account.
2. (Optional) Clone it to your local machine if you wish to run it locally or make modifications:
   ```bash
   git clone https://github.com/YOUR-USERNAME/Create-New-Stuff-in-ServiceNow.git
   cd Create-New-Stuff-in-ServiceNow
   ```

### Step 2: Prepare ServiceNow Credentials
The script requires a ServiceNow user account with sufficient privileges to read, create, update, and delete records in the following tables:
- `change_request`
- `incident`
- `problem`
- `sysapproval_approver`
- `sys_user_group`

Ensure you have the instance URL (e.g., `dev12345`), the username, and the password ready.

### Step 3: Configure GitHub Secrets
You must provide the ServiceNow credentials to GitHub Actions securely.
1. Go to your forked repository on GitHub.
2. Click on **Settings** in the top repository menu.
3. In the left sidebar, navigate to **Secrets and variables** > **Actions**.
4. Click the **New repository secret** button three times to add the following secrets:
   - **Name**: `SN_INSTANCE`
     **Secret**: Your instance ID or URL (e.g., `dev12345` or `dev12345.service-now.com`). The script will automatically parse the URL.
   - **Name**: `SN_USERNAME`
     **Secret**: Your ServiceNow API username.
   - **Name**: `SN_PASSWORD`
     **Secret**: Your ServiceNow API password.

### Step 4: Enable and Trigger GitHub Actions
GitHub disables workflows in forked repositories by default.
1. Go to the **Actions** tab in your GitHub repository.
2. Click **I understand my workflows, go ahead and enable them**.
3. The workflow is scheduled to run automatically every 2 hours (`0 */2 * * *`). 
4. To run it immediately and test your connection, select **ServiceNow Creator** from the left sidebar and click **Run workflow**.

### Step 5: Local Development & Testing (Optional)
If you want to test the script manually on your local machine before relying on GitHub Actions:

1. **Install Python 3.x** on your system.
2. **Install dependencies**:
   Navigate to the project root and install the required packages:
   ```bash
   pip install -r servicenow_creator/requirements.txt
   ```
3. **Set Environment Variables**:
   Export your credentials to your local terminal environment.
   
   *On Windows (PowerShell):*
   ```powershell
   $env:SN_INSTANCE="dev12345"
   $env:SN_USERNAME="your_username"
   $env:SN_PASSWORD="your_password"
   ```
   *On Mac/Linux (Bash):*
   ```bash
   export SN_INSTANCE="dev12345"
   export SN_USERNAME="your_username"
   export SN_PASSWORD="your_password"
   ```
4. **Execute the script**:
   ```bash
   python servicenow_creator/create_records.py
   ```
   You should see terminal output detailing which records are being progressed, created, or closed.
