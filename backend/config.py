import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(
    dotenv_path=Path(__file__).resolve().parents[1] / ".env"
)

APP_NAME = os.getenv("AEGIS_APP_NAME", "AEGIS")
APP_VERSION = os.getenv("AEGIS_APP_VERSION", "0.1.0")
HOST = os.getenv("AEGIS_HOST", "127.0.0.1")


def _port() -> int:
    raw = os.getenv("AEGIS_PORT", "8000")
    try:
        port = int(raw)
    except ValueError as exc:
        raise ValueError("AEGIS_PORT must be an integer") from exc
    if not 1 <= port <= 65535:
        raise ValueError("AEGIS_PORT must be between 1 and 65535")
    return port


PORT = _port()
