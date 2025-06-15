import multiprocessing
import time
import os
import sys
import requests

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if 'src' not in PROJECT_ROOT: 
    sys.path.append(os.path.join(PROJECT_ROOT, 'src'))
    PROJECT_ROOT = os.path.join(PROJECT_ROOT, 'src')
else: 
     sys.path.append(os.path.dirname(PROJECT_ROOT))


from api.app import app
from ui.flet_frontend import start_gui # Updated import
from config import API_HOST, API_PORT


def start_backend():
    print("[Main] Starting backend API server in a background process...")

    app.run(host=API_HOST, port=API_PORT, debug=False)

def wait_for_backend():
    print("[Main] Waiting for backend to become available...")
    start_time = time.time()
    while time.time() - start_time < 30:
        try:
            response = requests.get(f"http://{API_HOST}:{API_PORT}/status", timeout=1)
            if response.status_code == 200:
                print("[Main] Backend is ready!")
                return True
        except requests.exceptions.RequestException:

            time.sleep(0.5)
    
    print("[Main] Error: Backend did not start within the timeout period.")
    return False


if __name__ == '__main__':
    print("[Main] Launching application...")

    backend_process = multiprocessing.Process(target=start_backend, daemon=True)
    backend_process.start()

    if wait_for_backend():
        start_gui()
    
    print("[Main] GUI closed. Shutting down backend server...")
    if backend_process.is_alive():
        backend_process.terminate()
        backend_process.join()

    print("[Main] Application has shut down cleanly.")
