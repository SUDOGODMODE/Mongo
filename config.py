import os

# LLM
# "gemma3:4b", "qwen3.8:latest"
LLM_MODEL = "gemma3:4b"
LLM_URL = os.getenv("LLM_URL", "http://localhost:8080/v1")

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
LLM_CONTEXT_SIZE = 8192
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
PATH_COMPARISON = "comparison.csv"
PATH_SAMPLES = "samples"  # Relative to the project directory, or absolute.
UPLOAD_SAMPLES = [
    ("incidents_for_assessment.json", "application/json"),
    ("incidents_for_assessment.xml", "application/xml"),
]

# Schema Settings
PATH_JSON_SCHEMA = "schemas/incidents.schema.json"
PATH_XML_SCHEMA = "schemas/incidents.xsd"

# LLM request settings (separate from server startup timeout).
LLM_API_KEY = None
LLM_TEMPERATURE = 0.1
LLM_REQUEST_TIMEOUT = 600

# Rule-based rating mappings and weights.
WEIGHTS = {"impact": 0.15, "keywords": 0.60, "category": 0.25}
IMPACT_SCORES = {
    "very low": 2, "sehr niedrig": 2,
    "low": 3, "niedrig": 3,
    "medium": 5, "moderate": 5, "mittel": 5,
    "high": 8, "hoch": 8,
    "critical": 10, "kritisch": 10,
}
CATEGORY_SCORES = {
    "security": 8, "sicherheit": 8,
    "database": 7, "datenbank": 7,
    "network": 7, "netzwerk": 7,
    "authentication": 6, "authentifizierung": 6,
    "application": 5, "applikation": 5, "software": 5,
    "hardware": 4, "email": 4, "e-mail": 4,
    "backup": 7, "storage": 7, "zertifikat": 6, "certificate": 6,
    "endpoint": 4, "performance": 5,
    "printer": 2, "drucker": 2,
}
# The strongest keyword match determines
# the keyword score, so repeated words or long descriptions cannot inflate it.
KEYWORD_SCORES = {
    "ransomware": 10, "data loss": 10, "datenverlust": 10,
    "data breach": 10, "datenabfluss": 10,
    "production stopped": 10, "produktionsstillstand": 10,
    "outage": 9, "totalausfall": 9, "ausfall": 8,
    "unavailable": 8, "nicht erreichbar": 8,
    "no space left on device": 8, "fatal": 8,
    "packet loss": 7, "deadlock": 7,
    "mehrere personen": 6, "multiple users": 6,
    "produktivbetrieb zeitweise beeinträchtigt": 6,
    "timeout": 6, "slow": 4, "langsam": 4,
    "single user": 2, "einzelner benutzer": 2,
    "cosmetic": 1, "kosmetisch": 1,
}
