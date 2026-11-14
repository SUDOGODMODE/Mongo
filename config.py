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
