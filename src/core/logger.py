import os
import json
import datetime
from .config import LOG_DIR, LOG_FILE, LOG_LEVEL

'''
def ensure_log_dir():
    try:
        if not os.path.exists(LOG_DIR):
            os.makedirs(LOG_DIR, exist_ok=True)
            print(f"[Logger] Created log directory: {LOG_DIR}")
        else:
            print(f"[Logger] Log directory exists: {LOG_DIR}")
    except Exception as e:
        print(f"[Logger] Failed to create log directory {LOG_DIR}: {e}")
'''
def log_event(message: str, pid: int = None, port: int = None, level: str = LOG_LEVEL):
    """
    Appends a structured log entry to the log file.
    """
    log_entry = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "pid": pid or os.getpid(),
        "port": port,
        "level": level,
        "message": message
    }

    try:
        with open(LOG_FILE, "a") as f:
            json.dump(log_entry, f)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
    except Exception as e:
        print(f"[Logger] Failed to write to {LOG_FILE}: {e}")

def read_latest_logs(n=50):
    """
    Reads the last n log entries.
    """
    if not os.path.exists(LOG_FILE):
        print(f"[Logger] Log file {LOG_FILE} does not exist")
        return []

    try:
        with open(LOG_FILE, "r") as f:
            lines = f.readlines()[-n:]
    except Exception as e:
        print(f"[Logger] Failed to read {LOG_FILE}: {e}")
        return []

    logs = []
    for line in lines:
        try:
            logs.append(json.loads(line))
        except json.JSONDecodeError as e:
            print(f"[Logger] Invalid JSON in log file: {e}")
            continue
    return logs[::-1]

def initialize_logger():
    """
    Placeholder for any future logger service (e.g., server).
    """
    log_event("Logger initialized")