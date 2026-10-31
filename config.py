import os

# LLM
LLM_MODEL = os.getenv("LLM_MODEL", "gemma3:4b")
LLM_URL = os.getenv("LLM_URL", "http://localhost:11434/v1")

# FILE SETTINGS
PATH_IMPORT = os.getenv("PATH_IMPORT", "./import")
PATH_ERROR = os.getenv("PATH_ERROR", "./failed")

# MONGO-DB Settings
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/")
