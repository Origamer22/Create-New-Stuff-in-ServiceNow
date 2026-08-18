# ServiceNow Creator Automation

ServiceNow Creator is a Python-based automation tool that acts as a bot simulating an active, living IT Service Management (ITSM) environment within a ServiceNow instance. Designed to be run on a schedule using GitHub Actions, it autonomously interacts with the ServiceNow REST API to create, update, progress, and resolve various ITSM records such as Change Requests, Incidents, and Problems.

## 🚀 Key Features

- **Automated Change Request Lifecycle**: Active change requests are automatically progressed through the standard ITIL pipeline (New → Assess → Authorize → Scheduled → Implement → Review → Closed). Transitions occur realistically based on random delays and record age.
- **Pipeline Monitoring & Enforcement**: Ensures there are *always* at least 3 active Change Requests in the **Implement** state. If the number drops below this threshold, it automatically creates urgent mock changes straight into the Implement state. It also maintains a healthy pipeline of active normal changes.
- **Incident & Problem Generation**: Sporadically creates new mock incidents and problems to populate the ServiceNow instance.
- **Helpdesk Simulation**: To simulate active human work, the script randomly reassigns about 20% of active incidents to different user groups, and automatically closes older incidents with proper resolution notes.
- **Automated Approvals**: Pending approvals for change requests entering the "Authorize" state are automatically approved to maintain workflow velocity.
- **Geographic Schedule Awareness**: Detects the Israeli weekend (Friday 13:00 to Saturday 21:00 IST) using timezone-aware logic and pauses execution during this time.
- **Continuous GitHub Actions Workflow**: Runs every 2 hours via a GitHub Actions cron job. It features an automated "Keepalive" mechanism that pushes an empty commit if the repository is inactive for 50 days, preventing GitHub from disabling the workflow. Additionally, it writes summaries of running changes to the GitHub Actions workflow run summary page.

---

## 📁 Repository Structure Breakdown

The repository consists of the following critical files:

- **`servicenow_creator/create_records.py`**: The core execution script. It contains the logic to connect to the ServiceNow REST API (`/api/now/table`), parse the current state of incidents/problems/changes, evaluate aging based on `sys_created_on`, and execute REST payload updates (POST/PUT/DELETE).
- **`servicenow_creator/requirements.txt`**: The Python environment dependencies.
  - `requests==2.31.0`: Used for making REST API calls to ServiceNow.
  - `pytz==2024.1`: Used to handle timezone conversions to implement the weekend suspension feature.
- **`.github/workflows/servicenow_creator.yml`**: The GitHub Actions CI/CD configuration file. It dictates the environment (Ubuntu), Python setup, secrets management, script execution, and keep-alive strategy.

---

## 🛠️ Step-by-Step Setup Instructions

You can run this bot locally for testing, or deploy it to GitHub Actions to continuously simulate traffic to your ServiceNow instance.

### Prerequisites
You will need a ServiceNow developer instance (or sandbox) and a user account with REST API access and privileges to read, create, update, and delete records in the following tables:
- `change_request`
- `incident`
- `problem`
- `sysapproval_approver`
- `sys_user_group`

### Method 1: Continuous Deployment via GitHub Actions (Recommended)

1. **Fork or Clone the Repository**: Click the **Fork** button on the top right of this repository to create your own copy on GitHub.
2. **Configure GitHub Secrets**:
   - In your forked GitHub repository, navigate to **Settings** > **Secrets and variables** > **Actions**.
   - Add the following three "New repository secrets":
     - `SN_INSTANCE`: Your ServiceNow instance URL or ID (e.g., `dev12345` or `https://dev12345.service-now.com`). The script will intelligently parse it.
     - `SN_USERNAME`: The username of your ServiceNow API account.
     - `SN_PASSWORD`: The password of your ServiceNow API account.
3. **Enable GitHub Actions**:
   - GitHub disables workflows in forked repositories by default for security. 
   - Go to the **Actions** tab in your repository and click **"I understand my workflows, go ahead and enable them"**.
4. **Trigger the Workflow**:
   - The script is scheduled to automatically run every 2 hours.
   - To trigger an immediate run, go to the Actions tab, select **ServiceNow Creator** from the left-hand menu, and click the **Run workflow** dropdown to execute it.

### Method 2: Local Development & Testing

If you want to run or debug the script locally:

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/YOUR-USERNAME/Create-New-Stuff-in-ServiceNow.git
   cd Create-New-Stuff-in-ServiceNow
   ```
2. **Install Python & Dependencies**:
   Ensure you have Python 3.x installed. Then, install the required packages using pip:
   ```bash
   pip install -r servicenow_creator/requirements.txt
   ```
3. **Set Environment Variables**:
   Export your credentials so the script can authenticate with ServiceNow.
   
   *On Windows (PowerShell):*
   ```powershell
   $env:SN_INSTANCE="dev12345"
   $env:SN_USERNAME="your_username"
   $env:SN_PASSWORD="your_password"
   ```
   *On macOS / Linux (Bash/Zsh):*
   ```bash
   export SN_INSTANCE="dev12345"
   export SN_USERNAME="your_username"
   export SN_PASSWORD="your_password"
   ```
4. **Run the Script**:
   Execute the core Python script to initiate one lifecycle cycle.
   ```bash
   python servicenow_creator/create_records.py
   ```
   The terminal will output logs detailing which records were discovered, created, transitioned, or closed.

---
*Note: This script will skip its execution block automatically if run between Friday 13:00 and Saturday 21:00 (Israel Standard Time).*
