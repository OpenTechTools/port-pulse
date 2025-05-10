"""
Configuration module for PortPulse.
Defines default settings and constants used across the system.
"""

# === Port Configuration ===
BASE_PORT = 5000               # Starting port for process assignment
MAX_PORT = 6000                # Maximum port number
PORT_STEP = 1                  # Increment step to assign ports

# === Process Settings ===
MAX_PARENT_PROCESSES = 5       # Limit on how many parent processes can be created
MAX_CHILD_PROCESSES = 10       # Max children per parent
PROCESS_TIMEOUT = 60           # Time (in seconds) to keep child alive for test/demo

# === Logging ===
LOG_DIR = "logs"
LOG_FILE = f"{LOG_DIR}/logs.json"
LOG_LEVEL = "INFO"             # Levels: DEBUG, INFO, ERROR

# === Monitor ===
MONITOR_REFRESH_RATE = 2       # In seconds, refresh interval for dashboard

# === Networking ===
USE_TCP = True                 # Use TCP over UDP for message passing
BUFFER_SIZE = 1024             # Size of message buffer
ENCODING = "utf-8"             # Message encoding format

# === UI Settings (optional, if using Tkinter/Web) ===
UI_UPDATE_INTERVAL = 1000      # Milliseconds (used in Tkinter's after())
MAX_LOG_LINES_IN_UI = 100      # For display window scrollback

# === Misc ===
DEBUG_MODE = True              # Enable extra prints/logs for debugging
