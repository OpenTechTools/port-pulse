import os
import time
from src.core.logger import read_latest_logs
from .config import MONITOR_REFRESH_RATE

class ProcessMonitor:
    """
    Tracks active processes and displays real-time dashboard.
    """

    def __init__(self, refresh_rate=MONITOR_REFRESH_RATE):
        self.refresh_rate = refresh_rate
        self.tracked_processes = []

    def register_process(self, pid, port, role):
        """
        Add process info to monitor.
        """
        self.tracked_processes.append({
            "pid": pid,
            "port": port,
            "role": role,
            "alive": True
        })

    def check_process_alive(self, pid):
        """
        Check if the process is currently running.
        """
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

    def refresh_status(self):
        """
        Update status of all tracked processes.
        """
        for proc in self.tracked_processes:
            proc["alive"] = self.check_process_alive(proc["pid"])

    def show_dashboard(self):
        """
        Terminal dashboard for process statuses and recent logs.
        """
        while True:
            os.system("clear" if os.name == "posix" else "cls")
            self.refresh_status()

            print("=== PortPulse Process Monitor ===")
            for proc in self.tracked_processes:
                status = "🟢 ALIVE" if proc["alive"] else "🔴 DEAD"
                print(f"[{status}] {proc['role'].upper()} | PID: {proc['pid']} | Port: {proc['port']}")

            print("\n=== Recent Logs ===")
            logs = read_latest_logs(n=5)
            for log in logs:
                print(f"{log['timestamp']} | PID {log['pid']} | {log['level']}: {log['message']}")

            time.sleep(self.refresh_rate)
