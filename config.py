"""Global constants and application configuration."""

UNIVERSITY = "NOVA UNIVERSITY"
APP_NAME = "University Security Event Monitor"

# --- Simulation parameters --------------------------------------------------
REFRESH_MS = 1200
MIN_INTERVAL_MS = 300
MAX_INTERVAL_MS = 10000
MAX_EVENTS = 300
VISIBLE_ROWS = 80
MAX_ACTIVE_USERS = 25
NORMAL_EVENT_PROBABILITY = 0.42
INITIAL_NORMAL_EVENTS = 15

# --- Sample data ------------------------------------------------------------
USERS = [
    "ana.martinez", "carlos.rojas", "juan.perez", "maria.gomez",
    "sofia.diaz", "andres.lopez", "laura.castro", "diego.torres",
    "valentina.ruiz", "mateo.silva", "camila.vargas", "sebastian.mora",
    "admin.systems", "professor.garcia", "library", "laboratory",
]

DEPARTMENTS = [
    "Engineering", "Sciences", "Administration", "Library",
    "Student Welfare", "Research", "Systems",
]

MALICIOUS_DOMAINS = [
    "login-verification.example",
    "document-share.example",
    "campus-security.example",
    "account-check.example",
]

NORMAL_MESSAGES = [
    "Successful login",
    "Academic platform query",
    "Digital library access",
    "Academic material upload",
    "Grades lookup",
]

# --- Severity ---------------------------------------------------------------
SEVERITY_CRITICAL = "CRITICAL"
SEVERITY_HIGH = "HIGH"
SEVERITY_MEDIUM = "MEDIUM"
SEVERITY_LOW = "LOW"
SEVERITY_INFO = "INFO"

SEVERITY_COLORS = {
    SEVERITY_CRITICAL: "#ef4444",
    SEVERITY_HIGH: "#f97316",
    SEVERITY_MEDIUM: "#eab308",
    SEVERITY_LOW: "#22c55e",
    SEVERITY_INFO: "#38bdf8",
}

ALERT_SEVERITIES = (SEVERITY_CRITICAL, SEVERITY_HIGH)

# --- Response actions -------------------------------------------------------
ACTION_BLOCK_IP = "Block IP"
ACTION_FORCE_REVIEW = "Force review"
ACTION_DEACTIVATE_USER = "Deactivate user"
ACTION_ISOLATE_EMAIL = "Isolate email"
ACTION_QUARANTINE = "Quarantine file"
ACTION_NONE = "None"

# --- Event types and their weights ------------------------------------------
EVENT_REPEATED_FAILED_LOGIN = "REPEATED_FAILED_LOGIN"
EVENT_RAPID_PASSWORD_CHANGE = "RAPID_PASSWORD_CHANGE"
EVENT_UNTRUSTED_IP = "UNTRUSTED_IP"
EVENT_OFF_HOURS_USER = "OFF_HOURS_USER"
EVENT_MALICIOUS_EMAIL_LINK = "MALICIOUS_EMAIL_LINK"
EVENT_SUSPICIOUS_EMAIL_DOCUMENT = "SUSPICIOUS_EMAIL_DOCUMENT"

EVENT_TYPES = {
    EVENT_REPEATED_FAILED_LOGIN: 25,
    EVENT_RAPID_PASSWORD_CHANGE: 15,
    EVENT_UNTRUSTED_IP: 18,
    EVENT_OFF_HOURS_USER: 12,
    EVENT_MALICIOUS_EMAIL_LINK: 18,
    EVENT_SUSPICIOUS_EMAIL_DOCUMENT: 12,
}

NORMAL_EVENT_TYPE = "NORMAL_ACTIVITY"

# --- Generation modes (selector text -> forced event type) ------------------
MODE_AUTO = "Automatic"
MODE_NORMAL = "Normal only"
MODE_SUSPICIOUS = "Suspicious only"

MODE_TO_EVENT_TYPE = {
    "Failed login": EVENT_REPEATED_FAILED_LOGIN,
    "Password change": EVENT_RAPID_PASSWORD_CHANGE,
    "Untrusted IP": EVENT_UNTRUSTED_IP,
    "Off-hours user": EVENT_OFF_HOURS_USER,
    "Malicious email": EVENT_MALICIOUS_EMAIL_LINK,
    "Suspicious document": EVENT_SUSPICIOUS_EMAIL_DOCUMENT,
}

GENERATION_MODES = [MODE_AUTO, MODE_NORMAL, MODE_SUSPICIOUS, *MODE_TO_EVENT_TYPE]
