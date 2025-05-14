import os
import json
import datetime
from config import LOG_DIR, LOG_FILE, LOG_LEVEL

def ensure_log_dir():
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

def log_event(message: str, pid: int = None, port: int = None, level: str = LOG_LEVEL):
    """
    Appends a structured log entry to the log file.
    """
    ensure_log_dir()
    log_entry = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "pid": pid or os.getpid(),
        "port": port,
        "level": level,
        "message": message
    }

    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

def read_latest_logs(n=50):
    """
    Reads the last `n` log entries.
    """
    if not os.path.exists(LOG_FILE):
        return []

    with open(LOG_FILE, "r") as f:
        lines = f.readlines()[-n:]

    logs = []
    for line in lines:
        try:
            logs.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return logs[::-1] 

def initialize_logger():
    """
    Placeholder for any future logger service (e.g., server).
    """
    ensure_log_dir()
    log_event("Logger initialized")
