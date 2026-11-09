"""
ServiceNow Creator - English edition.

Creates and progresses Change Requests, Incidents and Problems written in
pure English with English IT terminology. All shared logic lives in
servicenow_core.py; this file only provides the English text.

The Hebrew edition is create_records.py.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from servicenow_core import LanguagePack, run  # noqa: E402

# Catalog of realistic IT Change Requests in English
ENGLISH_CHANGE_TEMPLATES = [
    {
        "short_description": "Upgrade Production Kubernetes Cluster to version 1.29",
        "description": "Upgrade the Control Plane and Worker Nodes of the Kubernetes Cluster from version 1.28 to 1.29 for improved security and to address the EOL of the previous version.",
        "justification": "Version 1.28 has reached End of Life (EOL) and no longer receives vendor security updates.",
        "implementation_plan": (
            "1. Take a full etcd snapshot backup.\n"
            "2. Upgrade the Control Plane (API Server, Controller Manager, Scheduler).\n"
            "3. Perform a gradual Rolling Update across all Node Pools.\n"
            "4. Verify the status of all Pods and Services."
        ),
        "risk_impact_analysis": "Medium risk. Zero Downtime - Pods are automatically rescheduled between Nodes during the upgrade.",
        "backout_plan": "Roll Worker Nodes back to the previous version and restore the etcd snapshot from the dedicated backup.",
        "test_plan": "Run cluster Health Checks, verify Ingress Controller traffic and confirm response times in Grafana.",
        "change_plan": "Structured, phased Kubernetes upgrade plan.",
        "category": "System software",
        "scope": "Large",
        "priority": "3",
        "min_duration_hours": 48,
        "max_duration_hours": 96
    },
    {
        "short_description": "Upgrade Production Linux servers and apply Security Patches",
        "description": "Apply routine Security Patches to all Production servers in the RedHat Linux environment and update core packages.",
        "justification": "Compliance with corporate information security standards and remediation of recently published CVE vulnerabilities.",
        "implementation_plan": (
            "1. Create a backup and Snapshot of each server through the virtualization platform.\n"
            "2. Install system updates via dnf/yum.\n"
            "3. Perform a controlled reboot of the servers one at a time.\n"
            "4. Run sanity checks on the active services."
        ),
        "risk_impact_analysis": "Low risk. Zero Downtime thanks to the Redundant architecture and the Load Balancer.",
        "backout_plan": "Restore servers from the previous Snapshot and revert to the old Kernel version if needed.",
        "test_plan": "Run Health Checks, verify network traffic and confirm all Daemons are up.",
        "change_plan": "Periodic security update for Linux servers.",
        "category": "System software",
        "scope": "Medium",
        "priority": "3",
        "min_duration_hours": 8,
        "max_duration_hours": 24
    },
    {
        "short_description": "Replace main Core Switches in the Data Center network cabinet",
        "description": "Replace the pair of legacy Cisco Core Switches with the new Cisco Nexus 9000 model to improve bandwidth and network resiliency.",
        "justification": "The current switches are at peak capacity and do not support the 100Gb Uplink required for new traffic loads.",
        "implementation_plan": (
            "1. Back up the Running Config of the switches.\n"
            "2. Connect the new switch in parallel and copy the VLAN and BGP settings.\n"
            "3. Gradually migrate the fiber optic cabling between the switches.\n"
            "4. Verify routing tables and STP convergence."
        ),
        "risk_impact_analysis": "Medium risk. Brief interruption (about 5 minutes) during BGP route Failover, with no extended service outage.",
        "backout_plan": "Reconnect the fiber optic cables to the previous switches and load the original configuration.",
        "test_plan": "Ping and Traceroute tests to various segments, routing stability checks and site-to-site VPN connectivity checks.",
        "change_plan": "Core switch replacement and advanced network infrastructure upgrade.",
        "category": "Network",
        "scope": "Large",
        "priority": "3",
        "min_duration_hours": 48,
        "max_duration_hours": 96
    },
    {
        "short_description": "Upgrade Production PostgreSQL Cluster database to version 16",
        "description": "Upgrade the primary database to version 16 to improve query performance and gain enhanced Logical Replication support.",
        "justification": "Roughly 25% better database performance and resolution of memory utilization issues under peak load.",
        "implementation_plan": (
            "1. Perform a Full Backup and verify backup integrity.\n"
            "2. Upgrade the Standby server using pg_upgrade.\n"
            "3. Perform a controlled Switchover, promoting the Standby to Master.\n"
            "4. Upgrade the secondary server and re-establish Replication."
        ),
        "risk_impact_analysis": "Medium risk. Short planned outage of about 10 minutes during the overnight Switchover window, approved by the system administrator.",
        "backout_plan": "Fail over back to the original server and restore using Point-in-Time Recovery (PITR).",
        "test_plan": "Run automated validation queries, check Replication sync and verify data integrity.",
        "change_plan": "PostgreSQL database version upgrade.",
        "category": "Software",
        "scope": "Large",
        "priority": "3",
        "min_duration_hours": 24,
        "max_duration_hours": 72
    },
    {
        "short_description": "Install new Check Point Firewall rules and harden DMZ traffic",
        "description": "Update the Policy and define new Rules on the Check Point Security Gateway to separate Production from Staging environments.",
        "justification": "Security Audit requirement to reduce the Attack Surface.",
        "implementation_plan": (
            "1. Test the rules in the Lab environment.\n"
            "2. Publish and apply the policy (Install Policy) during off-peak hours.\n"
            "3. Monitor blocked traffic Logs and verify correct behavior."
        ),
        "risk_impact_analysis": "Low risk. Zero Downtime, fully transparent to users.",
        "backout_plan": "Restore the previous Firewall policy using Revision History in SmartConsole.",
        "test_plan": "Verify access to authorized services and confirm unnecessary ports are blocked using nmap.",
        "change_plan": "Firewall rule hardening in the DMZ environment.",
        "category": "Network",
        "scope": "Small",
        "priority": "4",
        "min_duration_hours": 6,
        "max_duration_hours": 18
    },
    {
        "short_description": "Migrate and expand corporate SAN Storage capacity",
        "description": "Add All-Flash NVMe Shelves to the NetApp SAN Storage array and migrate critical LUNs.",
        "justification": "Current storage utilization has reached 85% and the corporate data growth rate requires a fast response.",
        "implementation_plan": (
            "1. Physically install the shelves in the server rack.\n"
            "2. Configure a new Aggregate on the storage array.\n"
            "3. Perform a non-disruptive Vol Move of the LUNs.\n"
            "4. Verify I/O performance."
        ),
        "risk_impact_analysis": "Medium risk. No service outage thanks to the live migration (Vol Move) capabilities of the Storage.",
        "backout_plan": "Stop the Vol Move process and revert to the existing Aggregate.",
        "test_plan": "Monitor Storage IOPS and Latency, verify LUN integrity.",
        "change_plan": "SAN storage capacity expansion and load distribution.",
        "category": "Hardware",
        "scope": "Large",
        "priority": "3",
        "min_duration_hours": 48,
        "max_duration_hours": 96
    },
    {
        "short_description": "Renew and replace SSL/TLS Certificates on the API Gateway",
        "description": "Replace expiring Wildcard SSL Certificates on the API Gateway, NGINX and Load Balancers.",
        "justification": "Prevent security errors and blocked user and customer access to company services.",
        "implementation_plan": (
            "1. Issue the new certificates from the trusted CA.\n"
            "2. Upload the keys to Cert Manager and the Web servers.\n"
            "3. Perform a Graceful Reload of the servers and the API Gateway."
        ),
        "risk_impact_analysis": "Low risk. Zero Downtime, a Graceful Reload does not drop existing client connections.",
        "backout_plan": "Restore the previous certificates from the backup folder and run another Reload.",
        "test_plan": "Validate the certificate with an external check script and multiple browsers (Chrome, Edge, Safari).",
        "change_plan": "Periodic renewal of SSL/TLS encryption certificates.",
        "category": "Software",
        "scope": "Small",
        "priority": "4",
        "min_duration_hours": 6,
        "max_duration_hours": 18
    },
    {
        "short_description": "Upgrade Active Directory Domain Controllers to Windows Server 2022",
        "description": "Add two new Domain Controllers running Windows Server 2022, sync Replication and decommission the legacy servers.",
        "justification": "Retire 2012R2 servers that have reached End of Life (EOL) and improve Kerberos security.",
        "implementation_plan": (
            "1. Install the new DC servers and configure networking.\n"
            "2. Run dcpromo and fully synchronize the Active Directory Database.\n"
            "3. Transfer the FSMO Roles to the new primary server.\n"
            "4. Monitor health before demoting the legacy servers."
        ),
        "risk_impact_analysis": "Medium risk. No downtime, corporate clients query the different DCs in parallel.",
        "backout_plan": "Transfer the FSMO roles back to the original servers if a sync issue is detected.",
        "test_plan": "Run dcdiag and repadmin /replsummary to confirm full replication health across all branches.",
        "change_plan": "Identity management infrastructure and Domain Controllers upgrade.",
        "category": "System software",
        "scope": "Large",
        "priority": "3",
        "min_duration_hours": 48,
        "max_duration_hours": 96
    },
    {
        "short_description": "Major application Release Deployment v3.5.0",
        "description": "Deploy a new release of the corporate CRM system including performance improvements and critical security fixes.",
        "justification": "Ship new features developed last quarter according to the development team roadmap.",
        "implementation_plan": (
            "1. Run Database Migrations in the Production environment.\n"
            "2. Deploy new containers using Blue/Green Deployment.\n"
            "3. Route 10% of traffic (Canary), verify metrics, then route all traffic."
        ),
        "risk_impact_analysis": "Medium risk. Zero Downtime, Blue/Green allows a seamless cutover.",
        "backout_plan": "Switch Load Balancer traffic back to the Blue environment (previous version).",
        "test_plan": "Run comprehensive E2E and Smoke tests in the Production environment.",
        "change_plan": "Major software release deployment to Production.",
        "category": "Software",
        "scope": "Medium",
        "priority": "3",
        "min_duration_hours": 12,
        "max_duration_hours": 36
    },
    {
        "short_description": "Upgrade backup infrastructure and install new Veeam Backup & Replication version",
        "description": "Upgrade the Veeam management servers and backup agents to v12.1 and connect to Immutable Cloud Storage for ransomware resiliency.",
        "justification": "Protection against Ransomware attacks and compliance with isolated, secure backup regulations.",
        "implementation_plan": (
            "1. Run a Veeam Configuration Backup.\n"
            "2. Upgrade the primary management server.\n"
            "3. Update the backup agents on the ESXi hosts.\n"
            "4. Run test backup jobs."
        ),
        "risk_impact_analysis": "Low risk. No service outage for Production systems (performed in a window with no active backup jobs).",
        "backout_plan": "Restore the Veeam management server from the previous Snapshot.",
        "test_plan": "Perform a trial restore (SureBackup) of a virtual machine to verify backup integrity.",
        "change_plan": "Backup and business continuity systems upgrade.",
        "category": "Software",
        "scope": "Medium",
        "priority": "4",
        "min_duration_hours": 24,
        "max_duration_hours": 48
    },
    {
        "short_description": "Upgrade virtualization environment to VMware ESXi 8.0 Cluster",
        "description": "Upgrade the Hypervisor version on all ESXi hosts in the primary cluster, including server Firmware updates.",
        "justification": "Support for modern operating systems and security fixes in the Virtualization Layer.",
        "implementation_plan": (
            "1. Upgrade vCenter Server to a compatible version.\n"
            "2. Migrate virtual machines with vMotion to other hosts in the cluster.\n"
            "3. Upgrade one Host at a time and return it to service.\n"
            "4. Verify environment stability."
        ),
        "risk_impact_analysis": "Low risk. No server downtime thanks to vMotion and the cluster design (High Availability).",
        "backout_plan": "Exit Maintenance Mode and roll back to the previous ESXi version in case of failure.",
        "test_plan": "Verify the health of all VMs and run vMotion again to rebalance load.",
        "change_plan": "Virtualization infrastructure and server cluster upgrade.",
        "category": "Hardware",
        "scope": "Large",
        "priority": "3",
        "min_duration_hours": 48,
        "max_duration_hours": 96
    },
    {
        "short_description": "Implement Single Sign-On (SSO) and MFA for the employee portal",
        "description": "Connect the corporate service portal to Azure AD using SAML 2.0 and enforce Conditional Access and MFA.",
        "justification": "Improve the user sign-in experience and strengthen corporate security in line with ISO 27001.",
        "implementation_plan": (
            "1. Configure an Enterprise Application in Azure AD.\n"
            "2. Enter the Metadata details in the service portal.\n"
            "3. Run a pilot with a selected group of users.\n"
            "4. Roll out to all company employees."
        ),
        "risk_impact_analysis": "Low risk. No downtime, Local Auth sign-in is retained for emergencies.",
        "backout_plan": "Disable SAML and restore the legacy local password sign-in.",
        "test_plan": "Successful sign-in tests in multiple browsers and confirmation of verification codes in Microsoft Authenticator.",
        "change_plan": "Unified corporate identity based on SSO and MFA.",
        "category": "Software",
        "scope": "Medium",
        "priority": "4",
        "min_duration_hours": 24,
        "max_duration_hours": 48
    },
    {
        "short_description": "Upgrade Redis Cache Cluster infrastructure to improve response times",
        "description": "Upgrade the Redis nodes to version 7.2 and expand Memory Allocation to improve the Cache Hit Ratio of the main application.",
        "justification": "Address Bottlenecks under peak load and improve Web service response times.",
        "implementation_plan": (
            "1. Upgrade the Replica nodes one at a time.\n"
            "2. Perform a controlled Failover to an upgraded node.\n"
            "3. Upgrade the former primary node and resync it to the cluster."
        ),
        "risk_impact_analysis": "Low risk. No service outage (Failover takes less than one second).",
        "backout_plan": "Return the Primary role to the previous node using the cluster failover command.",
        "test_plan": "Check response times and correct data reads from all Backend servers.",
        "change_plan": "Redis cluster and Caching infrastructure upgrade.",
        "category": "Software",
        "scope": "Small",
        "priority": "4",
        "min_duration_hours": 6,
        "max_duration_hours": 18
    },
    {
        "short_description": "Replace Internet Service Provider links and update BGP Multihoming configuration",
        "description": "Connect a new fiber optic line from an alternate carrier and configure BGP Peering for dual redundancy at company headquarters.",
        "justification": "Ensure Business Continuity and prevent network outages at the headquarters site.",
        "implementation_plan": (
            "1. Inspect the physical infrastructure and transmission lines.\n"
            "2. Configure BGP neighbors on the main corporate router.\n"
            "3. Gradually advertise the corporate Subnets on the new route."
        ),
        "risk_impact_analysis": "Medium risk. No downtime, traffic is routed dynamically between both providers.",
        "backout_plan": "Withdraw the BGP advertisement on the new line and revert to the single legacy line.",
        "test_plan": "Deliberately disconnect the primary line and verify fully transparent failover to the secondary line.",
        "change_plan": "Dual-redundant corporate Internet connectivity.",
        "category": "Network",
        "scope": "Large",
        "priority": "3",
        "min_duration_hours": 48,
        "max_duration_hours": 96
    },
    {
        "short_description": "Upgrade monitoring and log collection servers (Elasticsearch & Kibana Cluster)",
        "description": "Upgrade the ELK Stack to version 8.x and add Data Nodes to retain log data for 90 days.",
        "justification": "Meet regulatory requirements and improve search query performance in the SIEM.",
        "implementation_plan": (
            "1. Upgrade the Kibana and Logstash servers.\n"
            "2. Perform a Rolling Upgrade of each node in the Elasticsearch Cluster.\n"
            "3. Verify index integrity (Green Cluster Health)."
        ),
        "risk_impact_analysis": "Low risk. No service outage, the system continues collecting logs without interruption.",
        "backout_plan": "Restore legacy nodes from the dedicated backup and resync the indices.",
        "test_plan": "Verify a healthy Cluster status and run searches and dashboards in Kibana.",
        "change_plan": "Monitoring, logging and SIEM systems upgrade.",
        "category": "Software",
        "scope": "Medium",
        "priority": "4",
        "min_duration_hours": 24,
        "max_duration_hours": 72
    }
]


ENGLISH_PACK = LanguagePack(
    name="English",
    change_templates=ENGLISH_CHANGE_TEMPLATES,
    default_change_plan="Detailed work plan for implementing the change.",
    change_reason="Infrastructure systems update and maintenance",
    change_review_comments="The plan was reviewed and approved for implementation.",
    change_user_input="Approval to continue the change process.",
    change_work_notes="The change request was logged and is being implemented according to plan.",
    change_comments="This change was created and is managed by enterprise automation.",
    implement_start_note="Starting Implementation of the change according to plan.",
    implement_done_note="Implementation completed successfully. Moving to Review and acceptance testing.",
    review_close_notes="The change was closed successfully after completing Review and verifying system stability in Production.",
    quota_close_notes="The change was fully implemented and closed successfully.",
    incident_close_notes="The incident was resolved and successfully verified with the users.",
    incident_resolution_notes="Handled and resolved by the support and infrastructure team.",
    incident_short_description="Performance Degradation in the main application portal",
    incident_description="Users report slow response times and delays loading pages in the Web Portal.",
    incident_work_notes="An automatic incident was opened for performance monitoring and investigation.",
    incident_comments="The incident was logged in the enterprise monitoring system.",
    problem_short_description="Root Cause Analysis: recurring Database latency",
    problem_description="Recurring high Latency events and hanging DB connections during peak hours.",
    problem_work_notes="The problem was opened to investigate the Root Cause.",
    problem_comments="Tracking latency errors and heavy query behavior.",
    summary_no_description="No description",
    summary_default_assignee="Infrastructure Team",
    summary_state_label="State",
    summary_from_label="From",
    summary_to_label="To",
    summary_assigned_label="Assigned to",
)


def main():
    run(ENGLISH_PACK)


if __name__ == '__main__':
    main()

