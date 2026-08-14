# ServiceNow Creator

`servicenow_creator` is a Python automation script that programmatically interacts with your ServiceNow instance via its REST API. It is designed to be run as a daily scheduled GitHub Action to automatically generate test records or routine tickets in your ServiceNow environment.

## Features

- **Automated Record Creation**: Automatically creates incidents, problems, and normal change requests on a schedule.
- **Change Request Management**: Queries for planned changes whose start date has arrived and automatically updates their state to "Implement" (-1).
- **GitHub Actions Integration**: Designed to be run effortlessly via GitHub Actions, either on a daily cron schedule or manually via `workflow_dispatch`.

## Setup

### Prerequisites

- Python 3.x
- `requests` library
- A ServiceNow instance (developer or enterprise) with API access

### Configuration

The script uses environment variables to authenticate with your ServiceNow instance. If you are using GitHub Actions, you should configure these as repository secrets (`Settings` > `Secrets and variables` > `Actions`).

| Variable Name | Description | Example |
|---|---|---|
| `SN_INSTANCE` | Your ServiceNow instance name, full FQDN, or URL. (e.g., `dev12345` or `https://dev12345.service-now.com`) | `dev12345` |
| `SN_USERNAME` | A ServiceNow username with permissions to create and update records. | `admin` |
| `SN_PASSWORD` | The password for the ServiceNow user. | `SuperSecret123!` |

*Note: The script automatically cleans the `SN_INSTANCE` variable to extract the correct instance name even if a full URL or FQDN is provided.*

## Usage

### Running Locally

To test the script locally, ensure you have the `requests` library installed:

```bash
pip install -r requirements.txt
```

Set the required environment variables in your terminal and run the script:

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

### GitHub Actions

This repository includes a GitHub Actions workflow (`.github/workflows/servicenow_creator.yml`) that runs the script automatically at midnight every day. You can also trigger it manually from the "Actions" tab in GitHub.
