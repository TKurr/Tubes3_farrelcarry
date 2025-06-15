import os


DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "user": os.environ.get("DB_USER", "root"),
    "password": os.environ.get("DB_PASSWORD", "root"),
    "database": os.environ.get("DB_NAME", "cvApplicationDatabase"),
}

# --- API Server Configuration ---
API_HOST = "127.0.0.1"
API_PORT = 5000

# --- File Paths ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

# --- Search Configuration ---
DEFAULT_TOP_N_MATCHES = 5

# --- Fuzzy Matching Configuration ---
FUZZY_SIMILARITY_THRESHOLD = 0.8
