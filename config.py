import os

# LLM
# "gemma3:4b", "qwen3.8:latest"
LLM_MODEL = "gemma3:4b"
LLM_URL = os.getenv("LLM_URL", "http://localhost:51234/v1")

#FILE SETTINGS
PATH_IMPORT = "./import"
PATH_ERROR = "./failed"
PATH_DONE = "./done"

#MONGO-DB Settings
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/")

#API-Settings
API_PORT = 8000

# Startup configuration. None prompts for Docker/Podman; set either for unattended starts.
CONTAINER_RUNTIME = None
MONGO_CONTAINER_NAME = "mongodb"
MONGO_IMAGE = "mongodb/mongodb-community-server:latest"
MONGO_VOLUME = "mongodb_data"
LLM_EXECUTABLE = "llama-server"  # Command in PATH or full path.
LLM_HF_MODEL = "ggml-org/gemma-3-4b-it-GGUF:Q8_0"
LLM_GPU_LAYERS = "all"  # "0" for CPU only.
LLM_CONTEXT_SIZE = 16384
LLM_EXTRA_ARGS = []  # Additional llama-server arguments.
VENV_PATH = ".venv"  # Relative to the project directory, or absolute.
# All durations below are in seconds.
RUNTIME_TIMEOUT = 120
MONGO_TIMEOUT = 120
MONGO_IMAGE_TIMEOUT = 600
LLM_TIMEOUT = 1800
API_TIMEOUT = 30
COMMAND_TIMEOUT = 30
POLL_SECONDS = 1.0
WORKER_STARTUP_SECONDS = 3
STOP_TIMEOUT = 10
KILL_TIMEOUT = 5

# Application database and collections (shared by processing and export).
MONGO_DATABASE = "incident_db"
MONGO_INCIDENTS_COLLECTION = "incidents"

# API bind address and address used by local clients/readiness checks.
API_HOST = "127.0.0.1"
API_CLIENT_HOST = "127.0.0.1"  # Keep a reachable address when API_HOST is 0.0.0.0.
UPLOAD_REQUEST_TIMEOUT = 30

# Processing, export and sample upload settings.
WORKER_INTERVAL_SECONDS = 2
PATH_COMPARISON = "./comparison/comparison.csv"
PATH_SAMPLES = "samples"  # Relative to the project directory, or absolute.
UPLOAD_SAMPLES = [
    ("incidents_batch.json", "application/json"),
    ("incidents_batch.xml", "application/xml"),
    ("incident_invalid_document.json", "application/json")
]

# Schema Settings
PATH_JSON_SCHEMA = "schemas/incidents.schema.json"
PATH_XML_SCHEMA = "schemas/incidents.xsd"

# LLM request settings (separate from server startup timeout).
LLM_API_KEY = None
LLM_TEMPERATURE = 0.1
LLM_REQUEST_TIMEOUT = 600

# Prompt text used for incident assessment.
LLM_PROMPT_DESCRIPTION = "Analyze the following Incident ticket:\n"
LLM_IMPACT_PROMPT = """
Assess the ACTUAL impact of this IT incident on a scale of 1-10.

Evaluate business and security impact independently.
Use the higher JUSTIFIED score.

BUSINESS IMPACT:
Consider documented service disruption, affected users,
operational consequences, and available workarounds.

SECURITY IMPACT:
Consider documented confidentiality, integrity, and
availability violations, confirmed compromises, and
credible, explicitly documented security exposure.

SCORING:
1-2: Negligible impact, cosmetic or temporary inconvenience.
3-4: Localized disruption, limited functionality, workaround
     available, normal operations largely unaffected.
5-6: Significant disruption affecting multiple users or
     important processes, or confirmed limited security breach.
7-8: Major operational disruption, critical business process
     unavailable, or significant confirmed security compromise.
9-10: Production shutdown, widespread business outage,
      severe data breach, or destructive security incident.

STRICT RULES:
- Only use explicitly documented consequences.
- NEVER invent affected users, dependencies, or consequences.
- NEVER infer criticality from a system's name alone.
- NEVER confuse a broken interface with an unavailable service.
- A working alternative means the underlying process remains available.
- Technical failure does not automatically imply business disruption.
- A security suspicion is not a confirmed compromise.
- No documented security impact means no security-related score increase.
- Ignore the provided 'schweregrad' when assessing impact.
- Do not use hypothetical worst-case scenarios.

SCORING LIMITS:
- Isolated non-critical issue with a functional workaround:
  Maximum 3, unless concrete higher impact is documented.
- Limited disruption without significant operational impact:
  Maximum 4, unless concrete higher impact is documented.
- Scores 5-6 require evidence of significant business
  disruption or a documented security incident.
- Scores 7-8 require evidence of major business or security impact.
- Scores 9-10 require evidence of critical consequences.
- Never exceed these limits based on assumptions.

CALIBRATION:
Single room panel blank, Outlook booking works: 3
Printer offline, fixed by restart: 2
Suspicious login blocked by MFA: 3
ERP slow for 20 users, work continues: 5
Confirmed compromised account, unauthorized access: 7
Entire production stopped: 10
Confirmed severe customer data breach: 10

OUTPUT:
Return only JSON matching the specified schema.
Reason: maximum 20 words, one short sentence.
Mention only the decisive documented impact.
No speculation, recommendations or extended analysis.
"""



# Start of Definitions for Rule-Based assessment
WEIGHTS = {
    "impact": 0.15,
    "keywords": 0.60,
    "category": 0.25,
}

IMPACT_SCORES = {
    "minimal": 1, "minimal impact": 1,
    "very low": 2, "sehr niedrig": 2,
    "low": 3, "niedrig": 3, "gering": 3,
    "minor": 3, "geringfügig": 3,
    "medium": 5, "moderate": 5, "mittel": 5,
    "moderately high": 6, "erhöht": 6,
    "high": 8, "hoch": 8, "major": 8,
    "severe": 9, "schwerwiegend": 9,
    "critical": 10, "kritisch": 10,
    "catastrophic": 10, "katastrophal": 10,
}

CATEGORY_SCORES = {
    # Security
    "security": 8, "sicherheit": 8,
    "cybersecurity": 8, "cybersicherheit": 8,
    "security incident": 8, "sicherheitsvorfall": 8,
    "malware": 8, "ransomware": 9,
    "data protection": 8, "datenschutz": 8,
    "identity security": 8,

    # Infrastructure
    "network": 7, "netzwerk": 7,
    "network infrastructure": 7,
    "lan": 7, "wan": 7, "vpn": 6,
    "firewall": 7, "dns": 7, "dhcp": 6,
    "routing": 7, "switching": 6,
    "wireless": 5, "wlan": 5, "wifi": 5,
    "internet": 7,
    "server": 7, "infrastruktur": 7,
    "virtualization": 7, "virtualisierung": 7,
    "hypervisor": 7,
    "cloud": 7, "cloud services": 7,

    # Data
    "database": 7, "datenbank": 7,
    "sql": 7, "mongodb": 7,
    "postgresql": 7, "mssql": 7,
    "storage": 7, "speicher": 7,
    "fileserver": 6, "dateiserver": 6,
    "nas": 6, "san": 7,
    "backup": 7, "datensicherung": 7,
    "restore": 7, "wiederherstellung": 7,
    "disaster recovery": 9,

    # Identity
    "authentication": 6, "authentifizierung": 6,
    "authorization": 6, "autorisierung": 6,
    "identity": 6, "identität": 6,
    "access management": 6,
    "berechtigungen": 6,
    "active directory": 7,
    "entra id": 7, "sso": 7,
    "mfa": 6, "login": 5,

    # Business Applications
    "application": 5, "applikation": 5,
    "software": 5, "anwendung": 5,
    "business application": 6,
    "erp": 8, "sap": 8,
    "crm": 6,
    "mes": 9, "manufacturing": 9,
    "produktion": 9,
    "ot": 9, "scada": 9,
    "api": 6, "integration": 6,
    "schnittstelle": 6,
    "web service": 6, "webservice": 6,
    "itsm": 5, "servicedesk": 5,
    "portal": 5,

    # Workplace
    "hardware": 4, "endpoint": 4,
    "client": 4, "workstation": 4,
    "arbeitsplatz": 4,
    "laptop": 4, "desktop": 4,
    "mobile device": 4, "mobilgerät": 4,
    "printer": 2, "drucker": 2,
    "printing": 2, "drucken": 2,
    "peripheral": 2, "peripherie": 2,
    "display": 2, "monitor": 2,
    "keyboard": 2, "tastatur": 2,

    # Communication
    "email": 4, "e-mail": 4, "mail": 4,
    "exchange": 5, "outlook": 4,
    "teams": 5, "collaboration": 4,
    "telephony": 5, "telefonie": 5,
    "voip": 5,

    # Other
    "certificate": 6, "zertifikat": 6,
    "pki": 7, "tls": 6, "ssl": 6,
    "performance": 5, "leistung": 5,
    "capacity": 6, "kapazität": 6,
    "monitoring": 5, "überwachung": 5,
    "patching": 5, "update": 5,
    "configuration": 4, "konfiguration": 4,
    "deployment": 5, "bereitstellung": 5,
}


# Highest matching keyword determines the keyword score.
# Matching should be case-insensitive.
# Scores represent the typical severity suggested by the keyword.

KEYWORD_SCORES = {

    # ==========================================
    # 10 - CRITICAL / CATASTROPHIC
    # ==========================================

    # Security / Data
    "ransomware": 10,
    "cryptolocker": 10,
    "files encrypted": 10,
    "dateien verschlüsselt": 10,
    "mass encryption": 10,
    "massenverschlüsselung": 10,
    "data breach": 10,
    "datenschutzverletzung": 10,
    "data exfiltration": 10,
    "datenexfiltration": 10,
    "datenabfluss": 10,
    "massive data leak": 10,
    "massiver datenabfluss": 10,
    "sensitive data exposed": 10,
    "sensible daten offengelegt": 10,
    "customer data leaked": 10,
    "kundendaten abgeflossen": 10,
    "data destruction": 10,
    "datenvernichtung": 10,
    "irreversible data loss": 10,
    "irreversibler datenverlust": 10,
    "permanent data loss": 10,
    "permanenter datenverlust": 10,
    "complete data loss": 10,
    "vollständiger datenverlust": 10,
    "database destroyed": 10,
    "datenbank zerstört": 10,

    # Production / Business
    "production stopped": 10,
    "production halted": 10,
    "production line stopped": 10,
    "produktionsstillstand": 10,
    "produktion steht still": 10,
    "produktion vollständig gestoppt": 10,
    "fertigung steht still": 10,
    "fertigungsstillstand": 10,
    "gesamte produktion ausgefallen": 10,
    "entire production unavailable": 10,
    "complete business shutdown": 10,
    "geschäftsbetrieb vollständig eingestellt": 10,
    "company-wide outage": 10,
    "unternehmensweiter ausfall": 10,
    "all sites affected": 10,
    "alle standorte betroffen": 10,
    "complete infrastructure failure": 10,
    "gesamte infrastruktur ausgefallen": 10,

    # Safety / Compliance
    "patient safety at risk": 10,
    "patientensicherheit gefährdet": 10,
    "risk to human life": 10,
    "lebensgefahr": 10,
    "safety critical failure": 10,
    "sicherheitskritischer ausfall": 10,
    "loss of critical production data": 10,
    "verlust kritischer produktionsdaten": 10,


    # ==========================================
    # 9 - VERY HIGH
    # ==========================================

    # Security
    "active intrusion": 9,
    "aktiver einbruch": 9,
    "system compromised": 9,
    "system kompromittiert": 9,
    "domain compromised": 9,
    "domäne kompromittiert": 9,
    "domain controller compromised": 9,
    "administrator account compromised": 9,
    "admin-konto kompromittiert": 9,
    "privileged account compromised": 9,
    "privilegiertes konto kompromittiert": 9,
    "unauthorized data access confirmed": 9,
    "unberechtigter daten zugriff bestätigt": 9,
    "critical vulnerability exploited": 9,
    "kritische schwachstelle ausgenutzt": 9,
    "remote code execution": 9,
    "privilege escalation": 9,
    "rechteausweitung": 9,
    "lateral movement": 9,
    "ddos attack": 9,
    "ddos-angriff": 9,
    "denial of service attack": 9,

    # Infrastructure
    "total outage": 9,
    "totalausfall": 9,
    "complete outage": 9,
    "complete system failure": 9,
    "kompletter systemausfall": 9,
    "datacenter outage": 9,
    "rechenzentrum ausgefallen": 9,
    "site-wide outage": 9,
    "standortausfall": 9,
    "entire site offline": 9,
    "ganzer standort offline": 9,
    "core network down": 9,
    "kernnetzwerk ausgefallen": 9,
    "core switch failure": 9,
    "core-switch ausgefallen": 9,
    "firewall cluster down": 9,
    "firewall-cluster ausgefallen": 9,
    "storage cluster failure": 9,
    "storage-cluster ausgefallen": 9,
    "hypervisor cluster down": 9,
    "virtualization cluster down": 9,

    # Business Systems
    "erp system unavailable": 9,
    "erp system down": 9,
    "erp vollständig ausgefallen": 9,
    "sap unavailable": 9,
    "sap ausgefallen": 9,
    "mes unavailable": 9,
    "mes ausgefallen": 9,
    "scada unavailable": 9,
    "scada ausgefallen": 9,
    "all users affected": 9,
    "alle benutzer betroffen": 9,
    "alle mitarbeiter betroffen": 9,
    "entire department unable to work": 9,
    "gesamte abteilung arbeitsunfähig": 9,
    "critical business process blocked": 9,
    "kritischer geschäftsprozess blockiert": 9,

    # Recovery
    "recovery impossible": 9,
    "wiederherstellung unmöglich": 9,
    "restore impossible": 9,
    "all backups failed": 9,
    "alle backups fehlgeschlagen": 9,
    "no usable backup": 9,
    "kein verwendbares backup": 9,
    "backup repository corrupted": 9,
    "backup-repository beschädigt": 9,


    # ==========================================
    # 8 - HIGH
    # ==========================================

    # Availability
    "outage": 8,
    "ausfall": 8,
    "service unavailable": 8,
    "dienst nicht verfügbar": 8,
    "system unavailable": 8,
    "system nicht verfügbar": 8,
    "unavailable": 8,
    "nicht erreichbar": 8,
    "service down": 8,
    "server down": 8,
    "server ausgefallen": 8,
    "service interruption": 8,
    "dienstunterbrechung": 8,
    "major outage": 8,
    "grössere störung": 8,
    "größere störung": 8,
    "business interruption": 8,
    "betriebsunterbrechung": 8,
    "critical service affected": 8,
    "kritischer dienst betroffen": 8,

    # Database / Storage
    "database unavailable": 8,
    "datenbank nicht verfügbar": 8,
    "database offline": 8,
    "datenbank offline": 8,
    "database corruption": 8,
    "datenbankkorruption": 8,
    "database inconsistent": 8,
    "datenbank inkonsistent": 8,
    "data corruption": 8,
    "datenbeschädigung": 8,
    "data loss": 8,
    "datenverlust": 8,
    "no space left on device": 8,
    "disk full": 8,
    "festplatte voll": 8,
    "storage full": 8,
    "speicher voll": 8,
    "filesystem read-only": 8,
    "dateisystem schreibgeschützt": 8,
    "storage inaccessible": 8,
    "storage nicht erreichbar": 8,
    "raid failure": 8,
    "raid-ausfall": 8,
    "multiple disk failures": 8,
    "mehrere festplatten ausgefallen": 8,

    # Security / Authentication
    "unauthorized access": 8,
    "unberechtigter zugriff": 8,
    "account takeover": 8,
    "kontoübernahme": 8,
    "account compromised": 8,
    "konto kompromittiert": 8,
    "credential theft": 8,
    "zugangsdaten gestohlen": 8,
    "password leak": 8,
    "passwort leak": 8,
    "malware infection": 8,
    "malware-infektion": 8,
    "virus outbreak": 8,
    "virenausbruch": 8,
    "authentication outage": 8,
    "authentifizierung ausgefallen": 8,
    "sso outage": 8,
    "sso ausgefallen": 8,
    "mfa outage": 8,
    "mfa ausgefallen": 8,

    # Operational
    "fatal": 8,
    "fatal error": 8,
    "fataler fehler": 8,
    "system crash": 8,
    "systemabsturz": 8,
    "kernel panic": 8,
    "blue screen": 8,
    "bsod": 8,
    "critical process failed": 8,
    "kritischer prozess fehlgeschlagen": 8,
    "cannot process orders": 8,
    "aufträge können nicht verarbeitet werden": 8,
    "shipment blocked": 8,
    "versand blockiert": 8,
    "production blocked": 8,
    "produktion blockiert": 8,


    # ==========================================
    # 7 - ELEVATED
    # ==========================================

    # Network
    "packet loss": 7,
    "paketverlust": 7,
    "high packet loss": 7,
    "hoher paketverlust": 7,
    "network disruption": 7,
    "netzwerkunterbrechung": 7,
    "network instability": 7,
    "netzwerk instabil": 7,
    "intermittent connectivity": 7,
    "sporadische verbindungsabbrüche": 7,
    "connection reset": 7,
    "connection refused": 7,
    "verbindung verweigert": 7,
    "connection lost": 7,
    "verbindung verloren": 7,
    "network unreachable": 7,
    "netzwerk nicht erreichbar": 7,
    "gateway unreachable": 7,
    "gateway nicht erreichbar": 7,
    "dns resolution failed": 7,
    "dns-auflösung fehlgeschlagen": 7,
    "routing failure": 7,
    "routing-fehler": 7,
    "vpn connection failed": 7,
    "vpn-verbindung fehlgeschlagen": 7,
    "certificate expired": 7,
    "zertifikat abgelaufen": 7,
    "ssl handshake failed": 7,
    "tls handshake failed": 7,

    # Database
    "deadlock": 7,
    "deadlock detected": 7,
    "database connection failed": 7,
    "datenbankverbindung fehlgeschlagen": 7,
    "connection pool exhausted": 7,
    "connection slots exhausted": 7,
    "too many connections": 7,
    "zu viele verbindungen": 7,
    "database locked": 7,
    "datenbank gesperrt": 7,
    "transaction rollback": 7,
    "transaktion zurückgerollt": 7,
    "replication failed": 7,
    "replikation fehlgeschlagen": 7,
    "replication lag": 7,
    "replikationsverzögerung": 7,
    "query canceled": 7,
    "abfrage abgebrochen": 7,
    "sqlstate 57": 7,
    "database read-only": 7,
    "datenbank schreibgeschützt": 7,

    # Backup
    "backup failed": 7,
    "backup fehlgeschlagen": 7,
    "backup job failed": 7,
    "backup incomplete": 7,
    "backup unvollständig": 7,
    "restore failed": 7,
    "wiederherstellung fehlgeschlagen": 7,
    "restore point missing": 7,
    "wiederherstellungspunkt fehlt": 7,
    "snapshot failed": 7,
    "snapshot fehlgeschlagen": 7,
    "vss error": 7,
    "backup repository unavailable": 7,
    "backup repository full": 7,
    "incremental backup failed": 7,

    # Applications
    "application crash": 7,
    "applikationsabsturz": 7,
    "application not responding": 7,
    "anwendung reagiert nicht": 7,
    "http 500": 7,
    "http 502": 7,
    "http 503": 7,
    "http 504": 7,
    "internal server error": 7,
    "bad gateway": 7,
    "service unavailable error": 7,
    "gateway timeout": 7,
    "api unavailable": 7,
    "api nicht verfügbar": 7,
    "integration failed": 7,
    "schnittstelle fehlgeschlagen": 7,
    "synchronization failed": 7,
    "synchronisation fehlgeschlagen": 7,
    "job execution failed": 7,
    "batchjob fehlgeschlagen": 7,
    "workflow blocked": 7,
    "workflow blockiert": 7,

    # Scope / Operational
    "multiple systems affected": 7,
    "mehrere systeme betroffen": 7,
    "several departments affected": 7,
    "mehrere abteilungen betroffen": 7,
    "no workaround": 7,
    "kein workaround": 7,
    "keine überbrückungslösung": 7,
    "business critical": 7,
    "geschäftskritisch": 7,
    "production delayed": 7,
    "produktion verzögert": 7,


    # ==========================================
    # 6 - MODERATE TO HIGH
    # ==========================================

    # Scope
    "multiple users": 6,
    "mehrere benutzer": 6,
    "mehrere personen": 6,
    "several users": 6,
    "multiple employees": 6,
    "mehrere mitarbeiter": 6,
    "team affected": 6,
    "team betroffen": 6,
    "department affected": 6,
    "abteilung betroffen": 6,
    "multiple clients": 6,
    "mehrere clients": 6,
    "widespread issue": 6,
    "weit verbreitete störung": 6,
    "produktiver betrieb beeinträchtigt": 6,
    "produktivbetrieb zeitweise beeinträchtigt": 6,

    # Technical
    "timeout": 6,
    "timed out": 6,
    "zeitüberschreitung": 6,
    "connection timeout": 6,
    "verbindungszeitüberschreitung": 6,
    "request timeout": 6,
    "request failed": 6,
    "anfrage fehlgeschlagen": 6,
    "service degraded": 6,
    "dienst eingeschränkt": 6,
    "degraded performance": 6,
    "eingeschränkte leistung": 6,
    "performance degradation": 6,
    "leistungsverschlechterung": 6,
    "high latency": 6,
    "hohe latenz": 6,
    "response time exceeded": 6,
    "antwortzeit überschritten": 6,
    "resource exhaustion": 6,
    "ressourcen erschöpft": 6,
    "memory exhausted": 6,
    "arbeitsspeicher erschöpft": 6,
    "out of memory": 6,
    "oom killer": 6,
    "cpu 100%": 6,
    "cpu 99%": 6,
    "cpu utilization 100": 6,
    "high cpu usage": 6,
    "hohe cpu-auslastung": 6,
    "memory leak": 6,
    "speicherleck": 6,
    "disk i/o error": 6,
    "i/o error": 6,
    "input/output error": 6,
    "raid degraded": 6,
    "disk degraded": 6,

    # Security
    "phishing": 6,
    "phishing email": 6,
    "phishing-mail": 6,
    "suspicious login": 6,
    "verdächtige anmeldung": 6,
    "suspicious activity": 6,
    "verdächtige aktivität": 6,
    "brute force": 6,
    "brute-force": 6,
    "multiple failed logins": 6,
    "mehrere fehlgeschlagene anmeldungen": 6,
    "malware detected": 6,
    "malware erkannt": 6,
    "virus detected": 6,
    "virus erkannt": 6,
    "endpoint protection disabled": 6,
    "virenschutz deaktiviert": 6,
    "firewall disabled": 6,
    "firewall deaktiviert": 6,
    "security alert": 6,
    "sicherheitsalarm": 6,
    "suspicious process": 6,
    "verdächtiger prozess": 6,

    # Business Applications
    "payment processing failed": 6,
    "zahlungsverarbeitung fehlgeschlagen": 6,
    "report generation failed": 6,
    "reporterstellung fehlgeschlagen": 6,
    "data synchronization delayed": 6,
    "datensynchronisation verzögert": 6,
    "document processing failed": 6,
    "dokumentenverarbeitung fehlgeschlagen": 6,
    "mail delivery delayed": 6,
    "mailzustellung verzögert": 6,
    "message queue blocked": 6,
    "nachrichtenwarteschlange blockiert": 6,


    # ==========================================
    # 5 - MEDIUM
    # ==========================================

    # General
    "error": 5,
    "fehler": 5,
    "failure": 5,
    "störung": 5,
    "failed": 5,
    "fehlgeschlagen": 5,
    "not working": 5,
    "funktioniert nicht": 5,
    "unexpected behavior": 5,
    "unerwartetes verhalten": 5,
    "intermittent issue": 5,
    "sporadischer fehler": 5,
    "recurring issue": 5,
    "wiederkehrender fehler": 5,
    "repeated error": 5,
    "wiederholter fehler": 5,
    "temporarily unavailable": 5,
    "temporär nicht verfügbar": 5,
    "partially unavailable": 5,
    "teilweise nicht verfügbar": 5,
    "partial failure": 5,
    "teilausfall": 5,

    # Application
    "http 400": 5,
    "http 401": 5,
    "http 403": 5,
    "http 404": 5,
    "http 408": 5,
    "http 429": 5,
    "bad request": 5,
    "unauthorized": 5,
    "forbidden": 5,
    "access denied": 5,
    "zugriff verweigert": 5,
    "permission denied": 5,
    "berechtigung verweigert": 5,
    "authentication failed": 5,
    "authentifizierung fehlgeschlagen": 5,
    "login failed": 5,
    "anmeldung fehlgeschlagen": 5,
    "invalid credentials": 5,
    "ungültige anmeldedaten": 5,
    "password expired": 5,
    "passwort abgelaufen": 5,
    "account locked": 5,
    "konto gesperrt": 5,
    "account disabled": 5,
    "konto deaktiviert": 5,
    "session expired": 5,
    "sitzung abgelaufen": 5,
    "login loop": 5,
    "anmeldeschleife": 5,
    "mfa required": 5,
    "mfa erforderlich": 5,

    # Software / Systems
    "application error": 5,
    "applikationsfehler": 5,
    "software error": 5,
    "softwarefehler": 5,
    "configuration error": 5,
    "konfigurationsfehler": 5,
    "dependency failed": 5,
    "abhängigkeit fehlgeschlagen": 5,
    "service restart required": 5,
    "dienstneustart erforderlich": 5,
    "update failed": 5,
    "update fehlgeschlagen": 5,
    "installation failed": 5,
    "installation fehlgeschlagen": 5,
    "deployment failed": 5,
    "deployment fehlgeschlagen": 5,
    "scheduled task failed": 5,
    "geplanter task fehlgeschlagen": 5,
    "batch job failed": 5,
    "script failed": 5,
    "skript fehlgeschlagen": 5,


    # ==========================================
    # 4 - LOW TO MEDIUM
    # ==========================================

    # Performance
    "slow": 4,
    "langsam": 4,
    "sluggish": 4,
    "träge": 4,
    "performance issue": 4,
    "performanceproblem": 4,
    "long loading time": 4,
    "lange ladezeit": 4,
    "slow response": 4,
    "langsame antwort": 4,
    "delayed response": 4,
    "verzögerte antwort": 4,
    "minor delay": 4,
    "geringe verzögerung": 4,
    "occasional freeze": 4,
    "gelegentliches einfrieren": 4,
    "high resource usage": 4,
    "hohe ressourcenauslastung": 4,

    # Workplace
    "printer offline": 4,
    "drucker offline": 4,
    "printer not responding": 4,
    "drucker reagiert nicht": 4,
    "print job stuck": 4,
    "druckauftrag hängt": 4,
    "printing failed": 4,
    "drucken fehlgeschlagen": 4,
    "scanner not working": 4,
    "scanner funktioniert nicht": 4,
    "usb device not recognized": 4,
    "usb-gerät nicht erkannt": 4,
    "device disconnected": 4,
    "gerät getrennt": 4,
    "driver error": 4,
    "treiberfehler": 4,
    "audio not working": 4,
    "audio funktioniert nicht": 4,
    "microphone not working": 4,
    "mikrofon funktioniert nicht": 4,
    "camera not working": 4,
    "kamera funktioniert nicht": 4,
    "monitor flickering": 4,
    "monitor flackert": 4,
    "display issue": 4,
    "anzeigeproblem": 4,

    # Communication
    "email delayed": 4,
    "e-mail verzögert": 4,
    "mail not syncing": 4,
    "mail synchronisiert nicht": 4,
    "calendar sync failed": 4,
    "kalendersynchronisierung fehlgeschlagen": 4,
    "teams connection issue": 4,
    "teams verbindungsproblem": 4,
    "call quality poor": 4,
    "schlechte gesprächsqualität": 4,


    # ==========================================
    # 3 - LOW
    # ==========================================

    "low impact": 3,
    "geringe auswirkung": 3,
    "minor issue": 3,
    "kleines problem": 3,
    "limited impact": 3,
    "begrenzte auswirkung": 3,
    "isolated issue": 3,
    "isoliertes problem": 3,
    "single workstation": 3,
    "einzelner arbeitsplatz": 3,
    "single device": 3,
    "einzelnes gerät": 3,
    "only one device": 3,
    "nur ein gerät": 3,
    "printer issue": 3,
    "druckerproblem": 3,
    "paper jam": 3,
    "papierstau": 3,
    "toner empty": 3,
    "toner leer": 3,
    "no paper": 3,
    "kein papier": 3,
    "local configuration issue": 3,
    "lokales konfigurationsproblem": 3,
    "temporary workaround": 3,
    "temporäre umgehungslösung": 3,
    "workaround available": 3,
    "workaround vorhanden": 3,
    "alternative available": 3,
    "alternative verfügbar": 3,
    "manual workaround": 3,
    "manuelle umgehungslösung": 3,


    # ==========================================
    # 2 - VERY LOW
    # ==========================================

    "single user": 2,
    "einzelner benutzer": 2,
    "one user affected": 2,
    "ein benutzer betroffen": 2,
    "nur ein benutzer betroffen": 2,
    "individual user": 2,
    "einzelperson": 2,
    "non critical": 2,
    "unkritisch": 2,
    "no business impact": 2,
    "keine geschäftsauswirkung": 2,
    "no production impact": 2,
    "keine produktionsauswirkung": 2,
    "no operational impact": 2,
    "keine betriebliche auswirkung": 2,
    "resolved by restart": 2,
    "durch neustart behoben": 2,
    "restart resolved": 2,
    "neustart hat geholfen": 2,
    "reboot fixed": 2,
    "reboot resolved": 2,
    "problem behoben nach neustart": 2,
    "temporary glitch": 2,
    "kurzzeitige störung": 2,
    "user error": 2,
    "bedienungsfehler": 2,
    "incorrect setting": 2,
    "falsche einstellung": 2,
    "local issue": 2,
    "lokales problem": 2,


    # ==========================================
    # 1 - MINIMAL / COSMETIC
    # ==========================================

    "cosmetic": 1,
    "kosmetisch": 1,
    "cosmetic issue": 1,
    "kosmetischer fehler": 1,
    "visual defect": 1,
    "optischer fehler": 1,
    "display glitch": 1,
    "anzeigefehler": 1,
    "layout issue": 1,
    "layoutproblem": 1,
    "formatting issue": 1,
    "formatierungsfehler": 1,
    "typo": 1,
    "tippfehler": 1,
    "spelling error": 1,
    "rechtschreibfehler": 1,
    "incorrect label": 1,
    "falsche beschriftung": 1,
    "minor visual issue": 1,
    "kleiner darstellungsfehler": 1,
    "no functional impact": 1,
    "keine funktionale auswirkung": 1,
    "informational only": 1,
    "nur informativ": 1,
}
