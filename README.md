# ServiceNow Creator

`servicenow_creator` is a Python automation script that programmatically interacts with your ServiceNow instance via its REST API. It is designed to be run as a daily scheduled GitHub Action to automatically generate test records or routine tickets in your ServiceNow environment, as well as progress existing ones through their lifecycle.

## Features

The `create_records.py` script automatically performs the following actions:
- **Clean up existing records**: 
  - Closes active Change Requests that are in the "Implement" or "Review" state.
  - Closes active Incidents with a "Solved (Permanently)" code.
- **Generate new records**: 
  - Creates a new Incident, Problem, and normal Change Request.
- **Progress record states**: 
  - Starts planned Change Requests (moves Scheduled changes to Implement if their start date is reached).
  - Reassigns active Incidents to a random active user group.
- **Display Running Changes**: 
  - Automatically queries and lists all running changes ("Implement" or "Review" states).
  - Appends this list to the GitHub Actions Job Summary (`GITHUB_STEP_SUMMARY`) for immediate visibility.
- **GitHub Actions Integration**: Designed to be run effortlessly via GitHub Actions, either on a daily cron schedule or manually via `workflow_dispatch`.

## Setup

### Prerequisites

- Python 3.x
- `requests` library
- A ServiceNow instance (developer or enterprise) with API access

### ServiceNow Credentials Configuration

The script uses environment variables to authenticate with your ServiceNow instance. 

| Variable Name | Description | Example |
|---|---|---|
| `SN_INSTANCE` | Your ServiceNow instance name, full FQDN, or URL. (e.g., `dev12345` or `https://dev12345.service-now.com`) | `dev12345` |
| `SN_USERNAME` | A ServiceNow username with permissions to create and update records. | `admin` |
| `SN_PASSWORD` | The password for the ServiceNow user. | `SuperSecret123!` |

*Note: The script automatically cleans the `SN_INSTANCE` variable to extract the correct instance name even if a full URL or FQDN is provided.*

## Usage

### GitHub Actions (Recommended)

This repository includes a GitHub Actions workflow (`.github/workflows/servicenow_creator.yml`) that runs the script automatically at midnight every day. You can also trigger it manually.

**Setting up GitHub Actions:**

1. Navigate to your GitHub repository on the web.
2. Go to **Settings** > **Secrets and variables** > **Actions**.
3. Under the "Repository secrets" section, click **New repository secret**.
4. Add the following three secrets matching the configuration above:
   - Name: `SN_INSTANCE` | Value: Your instance name (e.g., `dev12345`)
   - Name: `SN_USERNAME` | Value: Your API username
   - Name: `SN_PASSWORD` | Value: Your API user's password
5. Navigate to the **Actions** tab in your repository.
6. If prompted, click the button to **Enable workflows**.
7. In the left sidebar, click on the **ServiceNow Creator** workflow.
8. To run it immediately, click the **Run workflow** dropdown on the right side and click the **Run workflow** button.

**Checking if it works:**

1. **Check GitHub Logs & Summary**: After triggering the workflow, click on the workflow run in the Actions tab. You will see a rich **Job Summary** showing the "Running Changes" right on the summary page. Click on the `run-scripts` job to view the raw console output under "Run ServiceNow Script and Show Running Changes" to see detailed logs like `Creating Incidents...`, `Created incident: INC0012345`, etc.
2. **Verify in ServiceNow**: Log into your ServiceNow instance and navigate to the respective lists (e.g., type `incident.list`, `problem.list`, or `change_request.list` in the filter navigator). Verify that new records have been created, or existing records have been closed/reassigned at the exact time the script was run.

### Running Locally

To test the script locally on your machine:

1. Navigate to the `servicenow_creator` folder.
2. Install the requirements:
   ```bash
   pip install -r requirements.txt
   ```
3. Set the required environment variables in your terminal and run the script:

**Windows (PowerShell):**
```powershell
$env:SN_INSTANCE="dev12345"
$env:SN_USERNAME="admin"
$env:SN_PASSWORD="password"
python create_records.py
```

**Linux/macOS:**
```bash
export SN_INSTANCE="dev12345"
export SN_USERNAME="admin"
export SN_PASSWORD="password"
python create_records.py
```
