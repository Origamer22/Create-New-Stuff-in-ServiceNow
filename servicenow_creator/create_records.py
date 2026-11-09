"""
ServiceNow Creator - Hebrew edition.

Creates and progresses Change Requests, Incidents and Problems written in
natural Hebrew with English IT terminology. All shared logic lives in
servicenow_core.py; this file only provides the Hebrew text.

The pure-English edition is create_records_en.py.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from servicenow_core import LanguagePack, run  # noqa: E402


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


HEBREW_PACK = LanguagePack(
    name="Hebrew",
    change_templates=HEBREW_CHANGE_TEMPLATES,
    default_change_plan="תוכנית עבודה מפורטת לביצוע השינוי.",
    change_reason="עדכון ותחזוקת מערכות תשתית",
    change_review_comments="התוכנית נבדקה ואושרה לביצוע.",
    change_user_input="אישור המשך תהליך השינוי.",
    change_work_notes="בקשת השינוי נרשמה במערכת ונמצאת בביצוע על פי התוכנית.",
    change_comments="השינוי נוצר ומנוהל באמצעות אוטומציה ארגונית.",
    implement_start_note="תחילת יישום (Implementation) של השינוי לפי התוכנית.",
    implement_done_note="היישום (Implementation) הושלם בהצלחה. העברה לשלב Review ובדיקות קבלה.",
    review_close_notes="השינוי נסגר בהצלחה לאחר סיום שלב ה-Review ואימות יציבות המערכות בסביבת Production.",
    quota_close_notes="השינוי יושם במלואו ונסגר בהצלחה.",
    incident_close_notes="התקלה נפתרה ונבדקה בהצלחה מול המשתמשים.",
    incident_resolution_notes="טופל ונפתר על ידי צוות התמיכה והתשתיות.",
    incident_short_description="ירידה בביצועים (Performance Degradation) בפורטל האפליקציה הראשי",
    incident_description="משתמשים מדווחים על זמני תגובה איטיים ועיכובים בטעינת דפים ב-Web Portal.",
    incident_work_notes="נפתחה קריאת תקלה אוטומטית לניטור וחקר ביצועים.",
    incident_comments="התקלה נרשמה במערכת הניטור הארגונית.",
    problem_short_description="חקר שורש תקלה (Root Cause Analysis): זמני השהייה חוזרים ב-Database",
    problem_description="אירועים חוזרים של Latency גבוה וחיבורי DB תלויים בשעות עומס.",
    problem_work_notes="הבעיה נפתחה לטובת חקירת גורם השורש (Root Cause).",
    problem_comments="מעקב אחר שגיאות latency והתנהגות שאילתות כבדות.",
    summary_no_description="ללא תיאור",
    summary_default_assignee="צוות תשתיות",
    summary_state_label="מצב",
    summary_from_label="מתאריך",
    summary_to_label="עד",
    summary_assigned_label="מוקצה ל",
)


def main():
    run(HEBREW_PACK)


if __name__ == '__main__':
    main()
