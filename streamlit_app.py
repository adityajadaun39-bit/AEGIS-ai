"""AEGIS - Autonomous AI Agent Security Gateway & SOC Console
Streamlit Community Cloud Root Entrypoint
"""
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

# Ensure root directory is in sys.path
ROOT_DIR = Path(__file__).parent.resolve()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def is_backend_running(host: str = "127.0.0.1", port: int = 8000) -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            return s.connect_ex((host, port)) == 0
    except Exception:
        return False


# In a standalone cloud container (e.g. Streamlit Community Cloud),
# spawn the FastAPI backend in the background so both API and UI operate seamlessly.
if not is_backend_running("127.0.0.1", 8000):
    try:
        subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "backend.app:app",
                "--host",
                "127.0.0.1",
                "--port",
                "8000",
            ],
            cwd=str(ROOT_DIR),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(2)
    except Exception as e:
        print(f"[AEGIS] Notice: Could not auto-spawn FastAPI: {e}")

# Run the frontend SOC console dashboard
dashboard_path = ROOT_DIR / "frontend" / "dashboard.py"
import runpy

runpy.run_path(str(dashboard_path), run_name="__main__")
