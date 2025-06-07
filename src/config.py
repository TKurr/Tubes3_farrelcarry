# config.py

# This file contains the configuration settings for the application.
# It's a central place to manage database credentials, API settings,
# and other configurable parameters.

import os

# --- Database Configuration ---
# Replace with your actual MySQL database credentials.
# It's recommended to use environment variables for sensitive data in a production environment.
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', 'your_password'),
    'database': os.environ.get('DB_NAME', 'ats_database')
}

# --- API Server Configuration ---
API_HOST = '127.0.0.1'
API_PORT = 5000

# --- File Paths ---
# Defines the root directory of the project to construct absolute paths.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')

# --- Search Configuration ---
# Default number of top matches to return if not specified by the client.
DEFAULT_TOP_N_MATCHES = 5

# --- Fuzzy Matching Configuration ---
# Similarity threshold for Levenshtein distance.
# A value between 0 and 1. Higher means more strict matching.
FUZZY_SIMILARITY_THRESHOLD = 0.8
