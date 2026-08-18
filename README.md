# We stand with Israel 🇮🇱

## ServiceNow Creator

This repository automates ServiceNow workflow simulation by running a Python script on a schedule using GitHub Actions. The script acts as a bot that interacts with the ServiceNow API to simulate an active environment, ensuring that the pipeline is populated with change requests, advancing existing changes through their lifecycle, and processing incidents.

### Features
- **Lifecycle Management**: Progresses active change requests through various states (New → Assess → Authorize → Scheduled → Implement → Review → Closed) based on defined delays.
- **Incident Processing**: Randomly reassigns or resolves open incidents based on their age.
- **Pipeline Maintenance**: Ensures a minimum number of active change requests are present in the pipeline, automatically creating new routine maintenance changes if necessary.
- **Daily Records Generation**: Sporadically creates new incidents and problems to keep the environment active.
- **Weekend Pause**: Skips execution during the Israeli weekend (Friday 13:00 to Saturday 21:00 IST).

### Setup Instructions

To set up this automation, follow these steps:

1. **Fork or Clone the Repository**
   Fork this repository or clone it to your local machine.

2. **Set up GitHub Secrets**
   The GitHub Actions workflow requires ServiceNow credentials to interact with the API. Navigate to your repository's **Settings > Secrets and variables > Actions** and add the following repository secrets:
   - `SN_INSTANCE`: The URL or instance name of your ServiceNow environment (e.g., `dev12345.service-now.com` or simply `dev12345`).
   - `SN_USERNAME`: Your ServiceNow API username.
   - `SN_PASSWORD`: Your ServiceNow API password.

3. **Workflow Configuration**
   The GitHub Actions workflow is located at `.github/workflows/servicenow_creator.yml`.
   - By default, it runs every 2 hours using the cron schedule (`0 */2 * * *`).
   - You can also trigger it manually from the **Actions** tab in GitHub.
   - A keepalive commit step is included to prevent GitHub from disabling the scheduled workflow after 60 days of inactivity.

4. **Local Development (Optional)**
   If you want to run the script locally:
   - Create a virtual environment and install the required dependencies:
     ```bash
     pip install -r servicenow_creator/requirements.txt
     ```
   - Set the necessary environment variables in your terminal:
     ```bash
     # Windows PowerShell
     $env:SN_INSTANCE="your-instance"
     $env:SN_USERNAME="your-username"
     $env:SN_PASSWORD="your-password"
     ```
   - Run the script:
     ```bash
     python servicenow_creator/create_records.py
     ```

### Repository Structure
- `servicenow_creator/create_records.py`: The main Python script that interacts with the ServiceNow API.
- `servicenow_creator/requirements.txt`: Python dependencies (`requests`, `pytz`).
- `.github/workflows/servicenow_creator.yml`: The GitHub Actions workflow file that schedules and runs the automation.
