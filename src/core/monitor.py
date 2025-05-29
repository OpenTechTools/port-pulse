import os
import time
from src.core.logger import read_latest_logs
from src.core.process_registry import ProcessRegistry
from .config import MONITOR_REFRESH_RATE


class ProcessMonitor:
    """
    Live dashboard showing process states and recent logs using a global registry.
    """

    def __init__(self, refresh_rate=MONITOR_REFRESH_RATE):
        self.refresh_rate = refresh_rate
        self.registry = ProcessRegistry()

    def check_process_alive(self, pid):
        """
        Check if a process is still running.
        """
        try:
            os.kill(int(pid), 0)
            return True
        except OSError:
            return False

    def show_dashboard(self):
        """
        Continuously prints the live dashboard.
        """
        while True:
            os.system("clear" if os.name == "posix" else "cls")

            print("=== 🧠 PortPulse Process Monitor ===\n")

            # Parents
            parents = self.registry.get_all_parents()
            print("👨‍👧 PARENT PROCESSES")
            if not parents:
                print("  No parent processes registered.")
            for pid, info in parents.items():
                status = "🟢 ALIVE" if self.check_process_alive(int(pid)) else "🔴 DEAD"
                print(f"  [{status}] PID: {pid} | Port: {info['port']} | Children: {len(info['children'])}")

            print("\n👶 CHILD PROCESSES")
            children = self.registry.get_all_children()
            if not children:
                print("  No child processes registered.")
            for pid, info in children.items():
                status = "🟢 ALIVE" if self.check_process_alive(int(pid)) else "🔴 DEAD"
                print(f"  [{status}] PID: {pid} | Port: {info['port']} | Parent PID: {info['parent']}")

            print("\n=== 📜 Recent Logs ===")
            logs = read_latest_logs(n=6)
            for log in logs:
                print(f"{log['timestamp']} | PID {log['pid']} | {log['level']}: {log['message']}")

            time.sleep(self.refresh_rate)
