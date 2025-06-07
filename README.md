# Applicant Tracking System (ATS) - Kelompok Tubes3

This project is an Applicant Tracking System (ATS) built with a Python backend (Flask) and a Flet-based GUI. It allows users to search through a collection of CVs using various pattern-matching algorithms.

## Project Architecture

- Backend: A Flask API server that handles all business logic, including file parsing, searching (KMP/BM), and data retrieval.

- Frontend: A Flet GUI application that provides the user interface. It runs in a separate process and communicates with the backend via HTTP requests.

- Orchestration: A main.py script launches and manages both the backend and frontend processes.

## Setup Instructions for Developers

Follow these steps to set up the development environment on a Debian-based Linux system (like Ubuntu/WSL).

1. System Dependencies
   First, we need to install a system library required by the Flet GUI.

# Update your package list

```bash
sudo apt update
```

# Install the libmpv library (version 2)

```bash
sudo apt install libmpv2
```

WSL/Linux Hotfix: The Flet client specifically looks for an older version of this library (libmpv.so.1). We need to create a symbolic link (a shortcut) to trick it into using the newer version we just installed.

# Create the symbolic link

```bash
sudo ln -s /usr/lib/x86_64-linux-gnu/libmpv.so.2 /usr/lib/x86_64-linux-gnu/libmpv.so.1
```

2. Python Virtual Environment
   We use a virtual environment to keep our project's Python packages isolated from the system.

# 1. Create the virtual environment folder named 'venv' from project's root

```bash
python3 -m venv venv
```

# 2. Activate it (do this every time you open a new terminal)

```bash
source venv/bin/activate
```

3. Install Python Packages
   With the virtual environment active, install all the required Python libraries using the requirements.txt file.

# Install all packages from the list

```bash
pip install -r requirements.txt
```

How to Run the Application
Once the setup is complete, you can run the application with a single command from the project's root directory.

# Make sure your virtual environment is active

```bash
python3 src/main.py
```

This will launch the backend API server in the background and then open the Flet GUI window.
