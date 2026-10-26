import os
import sys
import requests
import random
from datetime import datetime, timezone, timedelta
import pytz

# Ensure stdout and stderr handle UTF-8 Hebrew characters safely
try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

SN_INSTANCE = os.environ.get('SN_INSTANCE')
SN_USERNAME = os.environ.get('SN_USERNAME')
SN_PASSWORD = os.environ.get('SN_PASSWORD')

if not all([SN_INSTANCE, SN_USERNAME, SN_PASSWORD]):
    print("Error: Missing ServiceNow credentials.")
    exit(1)

SN_INSTANCE = SN_INSTANCE.replace('https://', '').replace('http://', '').rstrip('/')
if SN_INSTANCE.endswith('.service-now.com'):
    SN_INSTANCE = SN_INSTANCE.replace('.service-now.com', '')

BASE_URL = f"https://{SN_INSTANCE}.service-now.com/api/now/table"
HEADERS = {"Content-Type": "application/json", "Accept": "application/json"}
AUTH = (SN_USERNAME, SN_PASSWORD)

# Catalog of realistic IT Change Requests in Hebrew with English IT terms
HEBREW_CHANGE_TEMPLATES = [
    {
        "short_description": "שדרוג Kubernetes Cluster בסביבת Production לגרסה 1.29",
        "description": "שדרוג גרסת ה-Control Plane ו-Worker Nodes ב-Kubernetes Cluster מגרסה 1.28 ל-1.29 לצורך תמיכה באבטחה משופרת וטיפול ב-EOL של הגרסה הקודמת.",
        "justification": "גרסה 1.28 הגיעה ל-End of Life (EOL) ואינה נתמכת יותר בעדכוני אבטחה של הספק.",
        "implementation_plan": (
            "1. יצירת גיבוי מלא ל-etcd snapshot.\n"
            "2. שדרוג ה-Control Plane (API Server, Controller Manager, Scheduler).\n"
            "3. ביצוע Rolling Update הדרגתי לכל ה-Node Pools.\n"
            "4. אימות סטטוס כל ה-Pods וה-Services."
        ),
        "risk_impact_analysis": "סיכון בינוני. ללא השבתה (Zero Downtime) - ה-Pods מנוידים אוטומטית בין ה-Nodes בזמן השדרוג.",
        "backout_plan": "החזרת Worker Nodes מגרסה קודמת ושחזור etcd snapshot מגיבוי ייעודי.",
        "test_plan": "הרצת בדיקות Health Check לקלאסטר, אימות תעבורת Ingress Controller ווידוא זמני תגובה ב-Grafana.",
        "change_plan": "תוכנית שדרוג Kubernetes סדורה ומדורגת.",
        "category": "System software",
        "scope": "Large",
        "priority": "3",
        "min_duration_hours": 48,
        "max_duration_hours": 96
    },
    {
        "short_description": "שדרוג שרתי Production Linux ועדכון Security Patches",
        "description": "ביצוע עדכוני Security Patches שגרתיים לכל שרתי ה-Production בסביבת Linux RedHat ועדכון חבילות ליבה.",
        "justification": "עמידה בתקני אבטחת מידע ארגוניים וסגירת חולשות CVE שפורסמו לאחרונה.",
        "implementation_plan": (
            "1. יצירת גיבוי ו-Snapshot לשרתים דרך מערכת הוירטואליזציה.\n"
            "2. התקנת עדכוני מערכת דרך dnf/yum.\n"
            "3. אתחול מבוקר של השרתים בזה אחר זה.\n"
            "4. בדיקת שפיות לשירותים הפעילים."
        ),
        "risk_impact_analysis": "סיכון נמוך. ללא השבתת שירות (Zero Downtime) הודות למבנה ה-Redundant וה-Load Balancer.",
        "backout_plan": "שחזור שרתים מ-Snapshot קודם והחזרת גרסת Kernel ישנה במידת הצורך.",
        "test_plan": "הרצת בדיקות Health Check, אימות תעבורת רשת ווידוא עליית כלל ה-Daemons.",
        "change_plan": "עדכון אבטחה תקופתי לשרתי לינוקס.",
        "category": "System software",
        "scope": "Medium",
        "priority": "3",
        "min_duration_hours": 8,
        "max_duration_hours": 24
    },
    {
        "short_description": "החלפת מתגי Core Switch ראשיים בארון תקשורת Data Center",
        "description": "החלפת זוג מתגי Cisco Core Switch ישנים בדגם חדש של Cisco Nexus 9000 לשיפור רוחב הפס ושרידות הרשת.",
        "justification": "המתגים הנוכחיים בשיא הקיבולת וללא תמיכה ב-100Gb Uplink הנדרש לעומסי התעבורה החדשים.",
        "implementation_plan": (
            "1. גיבוי קונפיגורציית ה-Running Config של המתגים.\n"
            "2. חיבור המתג החדש במקביל והעתקת הגדרות VLAN ו-BGP.\n"
            "3. העברת כבילה אופטית בהדרגה בין המתגים.\n"
            "4. אימות טבלאות ניתוב וסנכרון STP."
        ),
        "risk_impact_analysis": "סיכון בינוני. השבתה רגעית (כ-5 דקות) בזמן Failover של מסלולי BGP, ללא השבתת שירות ממושכת.",
        "backout_plan": "חיבור מחדש של הסיבים האופטיים למתגים הקודמים וטעינת הקונפיגורציה המקורית.",
        "test_plan": "בדיקות Ping ו-Traceroute לסגמנטים שונים, בדיקת יציבות ניתוב וחיבורי VPN בין האתרים.",
        "change_plan": "החלפת מתגי ליבה ותשתיות רשת מתקדמות.",
        "category": "Network",
        "scope": "Large",
        "priority": "3",
        "min_duration_hours": 48,
        "max_duration_hours": 96
    },
    {
        "short_description": "שדרוג בסיס נתונים Production PostgreSQL Cluster לגרסה 16",
        "description": "שדרוג מסד הנתונים הראשי לגרסה 16 לצורך שיפור ביצועי שאילתות ותמיכה ב-Logical Replication משופר.",
        "justification": "שיפור של כ-25% בביצועי מסד הנתונים ופתרון בעיות ניצול זיכרון בעומסי שיא.",
        "implementation_plan": (
            "1. ביצוע Full Backup ואימות תקינות הגיבוי.\n"
            "2. שדרוג שרת ה-Standby באמצעות pg_upgrade.\n"
            "3. ביצוע Switchover מבוקר והפיכת ה-Standby ל-Master.\n"
            "4. שדרוג השרת המשני וסנכרון Replication מחדש."
        ),
        "risk_impact_analysis": "סיכון בינוני. השבתה קצרה מתוכננת של כ-10 דקות בחלון ה-Switchover בלילה באישור מנהל המערכות.",
        "backout_plan": "ביצוע Failover חזרה לשרת המקורי ושחזור מ-Point-in-Time Recovery (PITR).",
        "test_plan": "הרצת שאילתות ולידציה אוטומטיות, בדיקת סנכרון Replication ואימות שלמות נתונים.",
        "change_plan": "שדרוג גרסת מסד נתונים פוסטגרס.",
        "category": "Software",
        "scope": "Large",
        "priority": "3",
        "min_duration_hours": 24,
        "max_duration_hours": 72
    },
    {
        "short_description": "התקנת חוקי Firewall חדשים ב-Check Point והקשחת תעבורת DMZ",
        "description": "עדכון Policy והגדרת Rules חדשים ב-Check Point Security Gateway להפרדה בין סביבות Production לסביבות Staging.",
        "justification": "דרישת ביקורת אבטחת מידע (Security Audit) לצמצום משטח התקיפה (Attack Surface).",
        "implementation_plan": (
            "1. בדיקת חוקים בסביבת Lab.\n"
            "2. פרסום והחלת המדיניות (Install Policy) בשעות שפל.\n"
            "3. ניטור Logs של תעבורה חסומה ווידוא תקינות."
        ),
        "risk_impact_analysis": "סיכון נמוך. ללא השבתה (Zero Downtime), מבוצע באופן שקוף לחלוטין למשתמשים.",
        "backout_plan": "שחזור מדיניות Firewall קודמת באמצעות Revision History ב-SmartConsole.",
        "test_plan": "אימות גישה לשירותים מורשים ווידוא חסימת פורטים לא נחוצים באמצעות nmap.",
        "change_plan": "הקשחת חוקי חומת אש בסביבת DMZ.",
        "category": "Network",
        "scope": "Small",
        "priority": "4",
        "min_duration_hours": 6,
        "max_duration_hours": 18
    },
    {
        "short_description": "מיגרציה והרחבת אחסון בשרתי SAN Storage של הארגון",
        "description": "הוספת מדפי דיסקים (All-Flash NVMe Shelves) למערך NetApp SAN Storage והעברת LUNs קריטיים.",
        "justification": "ניצול שטח האחסון הנוכחי הגיע ל-85% ונדרש מענה מהיר לקצב גידול הנתונים הארגוני.",
        "implementation_plan": (
            "1. התקנה פיזית של המדפים בארון השרתים.\n"
            "2. הגדרת Aggregate חדש במערך האחסון.\n"
            "3. ביצוע Vol Move ללא השבתה של ה-LUNs.\n"
            "4. אימות ביצועי I/O."
        ),
        "risk_impact_analysis": "סיכון בינוני. ללא השבתת שירות הודות ליכולות המיגרציה החיה (Vol Move) של ה-Storage.",
        "backout_plan": "עצירת תהליך ה-Vol Move וחזרה ל-Aggregate הקיים.",
        "test_plan": "ניטור ביצועי IOPS וזמני השהייה (Latency) ב-Storage, בדיקת שלמות LUNs.",
        "change_plan": "הרחבת נפח אחסון SAN וחלוקת עומסים.",
        "category": "Hardware",
        "scope": "Large",
        "priority": "3",
        "min_duration_hours": 48,
        "max_duration_hours": 96
    },
    {
        "short_description": "חידוש והחלפת תעודות SSL/TLS Certificate ב-API Gateway",
        "description": "החלפת תעודות Wildcard SSL Certificate שתוקפן עומד לפוג ב-API Gateway, NGINX ו-Load Balancers.",
        "justification": "מניעת שגיאות אבטחה וחסימת גישת משתמשים ולקוחות לשירותי החברה.",
        "implementation_plan": (
            "1. הנפקת התעודות החדשות מול ה-CA המוסמך.\n"
            "2. העלאת המפתחות ל-Cert Manager ולשרתי ה-Web.\n"
            "3. ביצוע Graceful Reload לשרתים ול-API Gateway."
        ),
        "risk_impact_analysis": "סיכון נמוך. ללא השבתה, ביצוע Graceful Reload אינו מנתק חיבורי לקוחות קיימים.",
        "backout_plan": "החזרת התעודות הקודמות מתיקיית הגיבוי והרצת Reload חוזר.",
        "test_plan": "בדיקת תוקף התעודה מול סקריפט בדיקה חיצוני ודפדפנים שונים (Chrome, Edge, Safari).",
        "change_plan": "חידוש תקופתי של תעודות הצפנה SSL/TLS.",
        "category": "Software",
        "scope": "Small",
        "priority": "4",
        "min_duration_hours": 6,
        "max_duration_hours": 18
    },
    {
        "short_description": "שדרוג שרתי Active Directory Domain Controller ל-Windows Server 2022",
        "description": "הוספת שני שרתי Domain Controller חדשים מבוססי Windows Server 2022, סנכרון Replications והורדת שרתים ישנים.",
        "justification": "הוצאה משימוש של שרתי 2012R2 שהגיעו לסוף מחזור חיים (EOL) ושיפור אבטחת Kerberos.",
        "implementation_plan": (
            "1. התקנת שרתי ה-DC החדשים והגדרת רשת.\n"
            "2. ביצוע dcpromo וסנכרון מלא של ה-Active Directory Database.\n"
            "3. העברת תפקידי FSMO Roles לשרת הראשי החדש.\n"
            "4. ניטור תקינות לפני Demote של השרתים הישנים."
        ),
        "risk_impact_analysis": "סיכון בינוני. ללא השבתה, לקוחות הארגון פונים ל-DCs השונים במקביל.",
        "backout_plan": "החזרת תפקידי FSMO לשרתים המקוריים במידה ומתגלה חוסר סנכרון.",
        "test_plan": "הרצת dcdiag ו-repadmin /replsummary לווידוא תקינות סנכרון מלא בכל הסניפים.",
        "change_plan": "שדרוג תשתית ניהול זהויות ו-Domain Controllers.",
        "category": "System software",
        "scope": "Large",
        "priority": "3",
        "min_duration_hours": 48,
        "max_duration_hours": 96
    },
    {
        "short_description": "פריסת גרסת אפליקציה ראשית (Release Deployment v3.5.0)",
        "description": "פריסת גרסת תוכנה חדשה של מערכת ה-CRM הארגונית הכוללת שיפורי ביצועים ותיקוני אבטחה קריטיים.",
        "justification": "שחרור תכונות חדשות שפותחו ברבעון האחרון בהתאם לתוכנית העבודה של צוות הפיתוח.",
        "implementation_plan": (
            "1. הרצת Database Migrations בסביבת ה-Production.\n"
            "2. פריסת קונטיינרים חדשים בשיטת Blue/Green Deployment.\n"
            "3. ניתוב 10% מהתנועה (Canary), אימות מדדים וניתוב מלא."
        ),
        "risk_impact_analysis": "סיכון בינוני. ללא השבתה (Zero Downtime), שימוש ב-Blue/Green מאפשר החלפה רציפה.",
        "backout_plan": "הסטת התעבורה ב-Load Balancer בחזרה לסביבת ה-Blue (גרסה קודמת).",
        "test_plan": "הרצת בדיקות E2E ובדיקות Smoke מקיפות בסביבת ה-Production.",
        "change_plan": "פריסת גרסת תוכנה ראשית בסביבת Production.",
        "category": "Software",
        "scope": "Medium",
        "priority": "3",
        "min_duration_hours": 12,
        "max_duration_hours": 36
    },
    {
        "short_description": "שדרוג מערך הגיבוי והתקנת גרסה חדשה של Veeam Backup & Replication",
        "description": "שדרוג שרתי הניהול וסוכני הגיבוי של Veeam לגרסה v12.1 וחיבור ל-Immutable Cloud Storage לשרידות כופר.",
        "justification": "הגנה מפני התקפות Ransomware ועמידה בתקנות גיבוי מבודד ומאובטח.",
        "implementation_plan": (
            "1. ביצוע גיבוי תצורת Veeam Configuration Backup.\n"
            "2. שדרוג שרת הניהול הראשי.\n"
            "3. עדכון סוכני הגיבוי בשרתי ה-ESXi.\n"
            "4. הפעלת משימות גיבוי לבדיקה."
        ),
        "risk_impact_analysis": "סיכון נמוך. ללא השבתת שירות למערכות ה-Production (מבוצע בחלון ללא משימות גיבוי פעילות).",
        "backout_plan": "שחזור שרת הניהול של Veeam מ-Snapshot קודם.",
        "test_plan": "ביצוע שחזור ניסיון (SureBackup) של שרת וירטואלי לווידוא תקינות הגיבויים.",
        "change_plan": "שדרוג מערכות גיבוי והמשכיות עסקית.",
        "category": "Software",
        "scope": "Medium",
        "priority": "4",
        "min_duration_hours": 24,
        "max_duration_hours": 48
    },
    {
        "short_description": "שדרוג סביבת הוירטואליזציה ל-VMware ESXi 8.0 Cluster",
        "description": "שדרוג גרסאות Hypervisor בכל שרתי ה-ESXi בקלאסטר הראשי כולל עדכוני Firmware לשרתים.",
        "justification": "תמיכה במערכות הפעלה מתקדמות ותיקוני אבטחה ב-Virtualization Layer.",
        "implementation_plan": (
            "1. שדרוג ה-vCenter Server לגרסה תואמת.\n"
            "2. העברת שרתים וירטואליים במצב vMotion לשרתים אחרים בקלאסטר.\n"
            "3. שדרוג Host בודד בכל פעם והחזרתו לפעילות.\n"
            "4. אימות יציבות המערך."
        ),
        "risk_impact_analysis": "סיכון נמוך. ללא השבתת שרתים הודות ל-vMotion ולמבנה הקלאסטר (High Availability).",
        "backout_plan": "יציאה מ-Maintenance Mode וחזרה לגרסת ESXi הקודמת במידת תקלה.",
        "test_plan": "וידוא תקינות כל ה-VMs וביצוע vMotion חוזר לחלוקת עומסים מאוזנת.",
        "change_plan": "שדרוג תשתיות וירטואליזציה וקלאסטר שרתים.",
        "category": "Hardware",
        "scope": "Large",
        "priority": "3",
        "min_duration_hours": 48,
        "max_duration_hours": 96
    },
    {
        "short_description": "הטמעת מנגנון Single Sign-On (SSO) ו-MFA עבור פורטל העובדים",
        "description": "חיבור פורטל השירות הארגוני ל-Azure AD באמצעות SAML 2.0 ואכיפת Conditional Access ו-MFA.",
        "justification": "שיפור חוויית ההתחברות של המשתמשים והגברת האבטחה הארגונית לפי תקני ISO 27001.",
        "implementation_plan": (
            "1. הגדרת Enterprise Application ב-Azure AD.\n"
            "2. הזנת פרטי ה-Metadata בפורטל השירות.\n"
            "3. ביצוע פיילוט מול קבוצת משתמשים נבחרת.\n"
            "4. הפעלה גורפת לכלל עובדי החברה."
        ),
        "risk_impact_analysis": "סיכון נמוך. ללא השבתה, שמירת אפשרות כניסה מקומית (Local Auth) למקרה חירום.",
        "backout_plan": "השבתת מנגנון ה-SAML והחזרת ההתחברות הישנה דרך סיסמה מקומית.",
        "test_plan": "בדיקות התחברות מוצלחות בדפדפנים שונים ווידוא קבלת קוד אימות ב-Microsoft Authenticator.",
        "change_plan": "הטמעת הזדהות ארגונית אחידה מבוססת SSO ו-MFA.",
        "category": "Software",
        "scope": "Medium",
        "priority": "4",
        "min_duration_hours": 24,
        "max_duration_hours": 48
    },
    {
        "short_description": "שדרוג תשתית Redis Cache Cluster לשיפור זמני תגובה",
        "description": "שדרוג צמתי ה-Redis לגרסה 7.2 והרחבת ה-Memory Allocation לשיפור Cache Hit Ratio באפליקציה הראשית.",
        "justification": "טיפול בצווארי בקבוק (Bottlenecks) בעומסי שיא ושיפור זמני תגובה של שירותי Web.",
        "implementation_plan": (
            "1. שדרוג צמתי ה-Replica בזה אחר זה.\n"
            "2. ביצוע Failover מבוקר לצומת משודרג.\n"
            "3. שדרוג הצומת הראשי לשעבר וסנכונו מחדש לקלאסטר."
        ),
        "risk_impact_analysis": "סיכון נמוך. ללא השבתת שירות (זמן מעבר Failover של פחות משנייה אחת).",
        "backout_plan": "החזרת ה-Primary לצומת הקודם באמצעות פקודת cluster failover.",
        "test_plan": "בדיקת זמני תגובה וקריאת נתונים תקינה מכלל שרתי ה-Backend.",
        "change_plan": "שדרוג קלאסטר רדיס ותשתיות Caching.",
        "category": "Software",
        "scope": "Small",
        "priority": "4",
        "min_duration_hours": 6,
        "max_duration_hours": 18
    },
    {
        "short_description": "החלפת תשתית ספקי אינטרנט ועדכון הגדרות BGP Multihoming",
        "description": "חיבור קו תקשורת סיב אופטי חדש מחברת תקשורת חלופית והגדרת BGP Peering לשרידות כפולה במטה החברה.",
        "justification": "הבטחת המשכיות עסקית (Business Continuity) ומניעת השבתת רשת של סניף המטה.",
        "implementation_plan": (
            "1. בדיקת תשתית פיזית וקווי תמסורת.\n"
            "2. הגדרת שכנות BGP בנתב הראשי של הארגון.\n"
            "3. הכנסת ה-Subnets הארגוניים לפרסום ניתוב הדרגתי."
        ),
        "risk_impact_analysis": "סיכון בינוני. ללא השבתה, התעבורה מנווטת בצורה דינמית בין שני הספקים.",
        "backout_plan": "ביטול פרסום BGP לקו החדש וחזרה לקו הבודד הישן.",
        "test_plan": "ניתוק יזום של הקו הראשי ובדיקת מעבר תעבורה שקוף לחלוטין לקו המשני.",
        "change_plan": "הטמעת שרידות כפולה של חיבורי אינטרנט ארגוניים.",
        "category": "Network",
        "scope": "Large",
        "priority": "3",
        "min_duration_hours": 48,
        "max_duration_hours": 96
    },
    {
        "short_description": "שדרוג שרתי ניטור ואיסוף לוגים (Elasticsearch & Kibana Cluster)",
        "description": "שדרוג ה-ELK Stack לגרסה 8.x והרחבת ה-Data Nodes לשימור נתוני לוגים ל-90 יום.",
        "justification": "עמידה בדרישות רגולטוריות ושיפור ביצועי שאילתות חיפוש במערכת ה-SIEM.",
        "implementation_plan": (
            "1. שדרוג שרתי Kibana ו-Logstash.\n"
            "2. ביצוע Rolling Upgrade לכל צומת ב-Elasticsearch Cluster.\n"
            "3. אימות שלמות האינדקסים (Green Cluster Health)."
        ),
        "risk_impact_analysis": "סיכון נמוך. ללא השבתת שירות, המערכת ממשיכה לאסוף לוגים באופן רציף.",
        "backout_plan": "החזרת צמתים ישנים מגיבוי ייעודי וסנכרון אינדקסים.",
        "test_plan": "אימות סטטוס Cluster תקין והרצת חיפושים ודשבורדים ב-Kibana.",
        "change_plan": "שדרוג מערכות ניטור, לוגים ו-SIEM.",
        "category": "Software",
        "scope": "Medium",
        "priority": "4",
        "min_duration_hours": 24,
        "max_duration_hours": 72
    }
]

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
        except:
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
    if not sys_created_on_str: return 0
    try:
        created = datetime.strptime(sys_created_on_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        return (now - created).total_seconds() / 3600
    except Exception as e:
        return 0

def approve_all_pending(sys_id):
    approvals = get_records("sysapproval_approver", f"sysapproval={sys_id}^state=requested")
    for app in approvals:
        update_record("sysapproval_approver", app['sys_id'], {"state": "approved"}, silent=True)

def generate_change_payload(state_target="implement", ag_id="", user_id=""):
    """
    Generates a full change request payload in Hebrew with English IT terms.
    The change duration is configured between several hours to several days,
    so that on the calendar it appears spanning across multiple days.
    """
    tmpl = random.choice(HEBREW_CHANGE_TEMPLATES)
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
        "change_plan": tmpl.get("change_plan", "תוכנית עבודה מפורטת לביצוע השינוי."),
        "type": "Normal",
        "priority": tmpl.get("priority", "3"),
        "category": tmpl.get("category", "Other"),
        "scope": tmpl.get("scope", "Medium"),
        "assignment_group": ag_id,
        "assigned_to": user_id,
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
        "work_notes": "בקשת השינוי נרשמה במערכת ונמצאת בביצוע על פי התוכנית.",
        "comments": "השינוי נוצר ומנוהל באמצעות אוטומציה ארגונית.",
        "escalation": "Normal",
        "conflict_status": "Not Run",
        "phase": "Requested",
        "phase_state": "Open",
        "approval": "Approved",
        "approval_set": now.strftime("%Y-%m-%d %H:%M:%S"),
        "reason": "עדכון ותחזוקת מערכות תשתית",
        "review_comments": "התוכנית נבדקה ואושרה לביצוע.",
        "review_status": "Reviewed",
        "route_reason": "Standard routing",
        "user_input": "אישור המשך תהליך השינוי.",
        "knowledge": "false",
        "made_sla": "true",
        "on_hold": "false",
        "on_hold_reason": "Not on hold",
        "activity_due": (now + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
    }
    return payload

def progress_change(chg):
    chg_id = chg['sys_id']
    chg_num = chg['number']
    
    # State mapping:
    # -5 = New, -4 = Assess, -3 = Authorize, -2 = Scheduled, -1 = Implement, 0 = Review, 3 = Closed
    
    state_str = chg.get('state', '-5')
    try:
        state = int(state_str)
    except:
        state = -5
        
    print(f"Progressing change {chg_num} from state {state}...")
    age_hours = get_age_hours(chg.get('sys_created_on'))
    now_utc = datetime.now(timezone.utc)
    
    if state == -5: # New -> Assess
        payload = {"state": "-4"}
        update_record("change_request", chg_id, payload, silent=True)
        
    elif state == -4: # Assess -> Authorize
        update_record("change_request", chg_id, {"state": "-3"}, silent=True)
        
    elif state == -3: # Authorize -> Scheduled
        approve_all_pending(chg_id)
        update_record("change_request", chg_id, {"state": "-2"}, silent=True)
        
    elif state == -2: # Scheduled -> Implement
        # Check if planned start_date has arrived
        start_date_str = chg.get('start_date')
        ready_to_start = True
        if start_date_str:
            try:
                start_dt = datetime.strptime(start_date_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                ready_to_start = now_utc >= start_dt
            except:
                ready_to_start = True
                
        if ready_to_start:
            update_record("change_request", chg_id, {
                "state": "-1",
                "work_notes": "תחילת יישום (Implementation) של השינוי לפי התוכנית."
            }, silent=True)
            print(f"Moved {chg_num} to Implement.")
        else:
            print(f"Keeping {chg_num} in Scheduled (starts at {start_date_str}).")
        
    elif state == -1: # Implement -> Review
        # Stay in Implement until end_date arrives, or after planned duration
        end_date_str = chg.get('end_date')
        ready_to_review = False
        if end_date_str:
            try:
                end_dt = datetime.strptime(end_date_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                ready_to_review = now_utc >= end_dt
            except:
                ready_to_review = age_hours > 24
        else:
            ready_to_review = age_hours > 24
            
        if ready_to_review:
            update_record("change_request", chg_id, {
                "state": "0",
                "work_notes": "היישום (Implementation) הושלם בהצלחה. העברה לשלב Review ובדיקות קבלה."
            }, silent=True)
            print(f"Moved {chg_num} to Review (age {age_hours:.1f}h)")
        else:
            print(f"Keeping {chg_num} in Implement (scheduled until {end_date_str or 'N/A'}, age {age_hours:.1f}h)")
            
    elif state == 0: # Review -> Closed
        # Keep in review for 12 to 48 hours before closing
        threshold = random.randint(12, 48)
        if age_hours > threshold:
            payload = {
                "state": "3",
                "close_code": "successful",
                "close_notes": "השינוי נסגר בהצלחה לאחר סיום שלב ה-Review ואימות יציבות המערכות בסביבת Production."
            }
            update_record("change_request", chg_id, payload, silent=True)
            print(f"Closed {chg_num} (age {age_hours:.1f}h)")
        else:
            print(f"Keeping {chg_num} in Review (age {age_hours:.1f}h, threshold {threshold}h)")

def process_all_changes():
    print("\n--- Processing Change Requests ---")
    changes = get_records("change_request", "active=true")
    for chg in changes:
        progress_change(chg)

def get_random_group_and_user():
    groups = get_records("sys_user_group", "active=true", limit=10)
    ag_id = random.choice(groups)['sys_id'] if groups else ""
    users = get_records("sys_user", "active=true", limit=10)
    user_id = random.choice(users)['sys_id'] if users else ""
    return ag_id, user_id

def ensure_closed_changes(min_closed=5):
    print("\n--- Ensuring Minimum Closed Changes ---")
    closed_changes = get_records("change_request", "active=false^state=3")
    current_count = len(closed_changes)
    print(f"Currently have {current_count} closed changes.")
    
    if current_count < min_closed:
        needed = min_closed - current_count
        print(f"Need to create {needed} more closed change(s).")
        for _ in range(needed):
            ag_id, user_id = get_random_group_and_user()
            payload = generate_change_payload(state_target="closed", ag_id=ag_id, user_id=user_id)
            payload.update({
                "state": "3",
                "active": "false",
                "close_code": "successful",
                "close_notes": "השינוי יושם במלואו, נבדק בסביבת ה-Production ונסגר בהצלחה."
            })
            chg = create_record("change_request", payload)
            if chg:
                chg_id = chg.get('sys_id')
                if chg_id:
                    update_record("change_request", chg_id, {
                        "state": "3",
                        "active": "false",
                        "close_code": "successful",
                        "close_notes": "השינוי יושם במלואו ונסגר בהצלחה."
                    }, silent=True)

def ensure_minimum_active_changes(min_count=4):
    print(f"\n--- Ensuring Minimum Active Changes ---")
    implement_changes = get_records("change_request", "active=true^state=-1")
    current_count = len(implement_changes)
    print(f"Currently have {current_count} active changes in Implement.")
    
    if current_count < min_count:
        needed_active = min_count - current_count
        print(f"Need to create {needed_active} more change(s) directly in Implement state.")
        for _ in range(needed_active):
            ag_id, user_id = get_random_group_and_user()
            payload = generate_change_payload(state_target="implement", ag_id=ag_id, user_id=user_id)
            payload["state"] = "-5" # Create in New, then fast-forward to Implement
            
            chg = create_record("change_request", payload)
            if chg:
                chg_id = chg.get('sys_id')
                if chg_id:
                    # Fast-forward to Implement
                    payload_assess = {"state": "-4", "assignment_group": ag_id, "assigned_to": user_id}
                    update_record("change_request", chg_id, payload_assess, silent=True) # Assess
                    update_record("change_request", chg_id, {"state": "-3"}, silent=True) # Authorize
                    approve_all_pending(chg_id)
                    update_record("change_request", chg_id, {"state": "-2"}, silent=True) # Scheduled
                    update_record("change_request", chg_id, {
                        "state": "-1",
                        "work_notes": "תחילת יישום (Implementation) של השינוי לפי התוכנית.",
                        "assignment_group": ag_id,
                        "assigned_to": user_id
                    }, silent=True) # Implement

    # Ensure healthy pipeline of upcoming changes
    pipeline_changes = get_records("change_request", "active=true")
    if len(pipeline_changes) < min_count * 2:
        needed = (min_count * 2) - len(pipeline_changes)
        print(f"Need to create {needed} more change(s) for the pipeline.")
        for _ in range(needed):
            ag_id, user_id = get_random_group_and_user()
            payload = generate_change_payload(state_target="pipeline", ag_id=ag_id, user_id=user_id)
            create_record("change_request", payload)

def reassign_incidents():
    return

def process_incidents():
    print("\n--- Processing Incidents ---")
    incidents = get_records("incident", "active=true^stateNOT IN7,8")
    for inc in incidents:
        inc_id = inc['sys_id']
        inc_num = inc['number']
        age_hours = get_age_hours(inc.get('sys_created_on'))
        close_prob = min(0.9, age_hours / 48.0)
        
        if random.random() < close_prob:
            print(f"Closing incident {inc_num} (age: {age_hours:.1f}h)...")
            payload = {
                "state": "7", # Closed
                "close_code": "Solved (Permanently)",
                "resolution_code": "Software",
                "close_notes": "התקלה נפתרה ונבדקה בהצלחה מול המשתמשים.",
                "resolution_notes": "טופל ונפתר על ידי צוות התמיכה והתשתיות."
            }
            update_record("incident", inc_id, payload, silent=True)
        else:
            print(f"Keeping incident {inc_num} open (age: {age_hours:.1f}h).")

def print_running_changes():
    print("\n--- Running Changes ---")
    changes = get_records("change_request", "active=true^stateIN-1,0")
    summary = f"### Running Changes ({len(changes)})\n\n"
    
    if changes:
        for chg in changes:
            num = chg.get('number', 'Unknown')
            short_desc = chg.get('short_description', 'ללא תיאור')
            state = chg.get('state', 'Unknown')
            state_str = "Implement" if str(state) == "-1" else "Review" if str(state) == "0" else str(state)
            start_date = chg.get('start_date', 'N/A')
            end_date = chg.get('end_date', 'N/A')
            
            assignee = chg.get('assigned_to')
            if type(assignee) is dict:
                assignee_name = assignee.get('display_value', 'Unknown')
            else:
                assignee_name = str(assignee) if assignee else "N/A"
                
            line = f"- **{num}**: {short_desc} | מצב: {state_str} | מתאריך: {start_date} עד: {end_date} | מוקצה ל: {assignee_name}"
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

def create_daily_records():
    ag_id, user_id = get_random_group_and_user()
    now = datetime.now(timezone.utc)
    
    # Sporadically create incident in Hebrew with English IT terms
    if random.random() < 0.5:
        print("\n--- Creating New Records ---")
        create_record("incident", {
            "short_description": "ירידה בביצועים (Performance Degradation) בפורטל האפליקציה הראשי",
            "description": "משתמשים מדווחים על זמני תגובה איטיים ועיכובים בטעינת דפים ב-Web Portal.",
            "urgency": "2",
            "impact": "2",
            "priority": "3",
            "assignment_group": ag_id,
            "assigned_to": user_id,
            "category": "software",
            "subcategory": "os",
            "contact_type": "Phone",
            "state": "1",
            "escalation": "Normal",
            "work_notes": "נפתחה קריאת תקלה אוטומטית לניטור וחקר ביצועים.",
            "comments": "התקלה נרשמה במערכת הניטור הארגונית.",
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
        })
    
    if random.random() < 0.2:
        create_record("problem", {
            "short_description": "חקר שורש תקלה (Root Cause Analysis): זמני השהייה חוזרים ב-Database",
            "description": "אירועים חוזרים של Latency גבוה וחיבורי DB תלויים בשעות עומס.",
            "urgency": "2",
            "impact": "2",
            "priority": "3",
            "assignment_group": ag_id,
            "assigned_to": user_id,
            "state": "1",
            "category": "software",
            "subcategory": "os",
            "work_notes": "הבעיה נפתחה לטובת חקירת גורם השורש (Root Cause).",
            "comments": "מעקב אחר שגיאות latency והתנהגות שאילתות כבדות.",
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
        })

def backfill_records_missing_dates():
    """
    Safely backfills only records that lack start_date or end_date,
    without overwriting existing valid records or Hebrew text.
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

def main():
    # Check for Israel weekend (Friday 13:00 to Saturday 21:00)
    tz = pytz.timezone('Asia/Jerusalem')
    now_il = datetime.now(tz)
    
    if (now_il.weekday() == 4 and now_il.hour >= 13) or \
       (now_il.weekday() == 5 and now_il.hour < 21):
        print(f"Current time in Israel is {now_il.strftime('%Y-%m-%d %H:%M:%S')}.")
        print("Weekend schedule active (Fri 13:00 - Sat 21:00 IST), skipping execution.")
        return

    print("Starting ServiceNow Scheduled Tasks...")
    
    # 0. Backfill only records missing dates
    backfill_records_missing_dates()
    
    # 1. Process existing changes through their lifecycle
    process_all_changes()
    
    # 2. Process incidents (close or reassign)
    process_incidents()
    reassign_incidents()
    
    # 3. Create new records sporadically
    create_daily_records()
    
    # 4. Ensure pipeline has changes (in Hebrew with IT terms and multi-day spans)
    ensure_minimum_active_changes(8)
    ensure_closed_changes(8)
    
    # 5. Display what's running
    print_running_changes()

if __name__ == '__main__':
    main()
