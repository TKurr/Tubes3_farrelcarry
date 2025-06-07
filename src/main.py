# main.py

# This is the main entry point for the entire application.
# It launches the backend API server in a background process,
# then starts the Flet GUI in the main process.

import multiprocessing
import time
import os
import sys
import requests

# --- Path Correction ---
# This ensures that we can import modules from the 'src' directory
# and the project root, regardless of where main.py is located.
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if 'src' not in PROJECT_ROOT: # If running from root
    sys.path.append(os.path.join(PROJECT_ROOT, 'src'))
    PROJECT_ROOT = os.path.join(PROJECT_ROOT, 'src')
else: # If running from src
     sys.path.append(os.path.dirname(PROJECT_ROOT))


from api.app import app
from ui.flet_frontend import start_gui # Updated import
from config import API_HOST, API_PORT


def start_backend():
    """
    Target function for the backend process.
    This will run the Flask development server.
    """
    print("[Main] Starting backend API server in a background process...")
    # debug=False is important for multiprocessing contexts
    app.run(host=API_HOST, port=API_PORT, debug=False)

def wait_for_backend():
    """
    Actively polls the backend's /status endpoint until it gets a successful
    response, ensuring the server is ready to accept connections.
    """
    print("[Main] Waiting for backend to become available...")
    start_time = time.time()
    while time.time() - start_time < 30: # 30-second timeout
        try:
            response = requests.get(f"http://{API_HOST}:{API_PORT}/status", timeout=1)
            if response.status_code == 200:
                print("[Main] Backend is ready!")
                return True
        except requests.exceptions.RequestException:
            # Server is not up yet, wait a bit before retrying
            time.sleep(0.5)
    
    print("[Main] Error: Backend did not start within the timeout period.")
    return False


if __name__ == '__main__':
    print("[Main] Launching application...")

    # Create and start the backend server in a separate process
    # daemon=True ensures it exits when the main script does
    backend_process = multiprocessing.Process(target=start_backend, daemon=True)
    backend_process.start()

    # Wait for the backend to be confirmed ready
    if wait_for_backend():
        # Now, run the Flet GUI in the MAIN process.
        # This function will block until the GUI window is closed.
        start_gui()
    
    # After the GUI window is closed, the script will proceed here.
    print("[Main] GUI closed. Shutting down backend server...")
    if backend_process.is_alive():
        backend_process.terminate()
        backend_process.join()

    print("[Main] Application has shut down cleanly.")
