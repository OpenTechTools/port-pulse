import json
from pathlib import Path

# Path to store the registry data
REGISTRY_FILE = Path(__file__).parent / "process_registry.json"

class ProcessRegistry:
    def __init__(self):
        self.registry = {
            "port_to_pid": {},         # Maps port -> pid
            "parent_to_children": {},  # Maps parent_pid -> [child_pid, ...]
            "parents": {},             # Maps parent_pid -> { port, children }
            "children": {}             # Maps child_pid -> { port, parent }
        }
        self._load_registry()

    def _load_registry(self):
        if REGISTRY_FILE.exists():
            with open(REGISTRY_FILE, 'r') as f:
                self.registry = json.load(f)

        # Ensure all required keys exist even if file was from old version
        self.registry.setdefault("port_to_pid", {})
        self.registry.setdefault("parent_to_children", {})
        self.registry.setdefault("parents", {})
        self.registry.setdefault("children", {})

    def _save_registry(self):
        with open(REGISTRY_FILE, 'w') as f:
            json.dump(self.registry, f, indent=4)

    def register_process(self, pid, port, parent_pid=None):
        pid = int(pid)
        port = int(port)
        self.registry["port_to_pid"][str(port)] = pid

        if parent_pid is None:
            # Parent registration
            self.registry["parents"][str(pid)] = {
                "port": port,
                "children": []
            }
        else:
            # Child registration
            parent_pid = str(parent_pid)
            self.registry["children"][str(pid)] = {
                "port": port,
                "parent": int(parent_pid)
            }
            self.registry["parents"].setdefault(parent_pid, {"port": -1, "children": []})
            self.registry["parents"][parent_pid]["children"].append(pid)
            self.registry["parent_to_children"].setdefault(parent_pid, []).append(pid)

        self._save_registry()

    def get_pid_by_port(self, port):
        return self.registry["port_to_pid"].get(str(port))

    def get_port_by_pid(self, pid):
        pid = str(pid)

        if pid in self.registry["parents"]:
            return self.registry["parents"][pid]["port"]
        if pid in self.registry["children"]:
            return self.registry["children"][pid]["port"]

        # Fallback using reverse lookup from port_to_pid
        for port, mapped_pid in self.registry["port_to_pid"].items():
            if mapped_pid == int(pid):
                return int(port)

        return None

    def get_children_by_parent(self, parent_pid):
        return self.registry["parent_to_children"].get(str(parent_pid), [])

    def remove_process(self, port):
        pid = self.registry["port_to_pid"].pop(str(port), None)
        if pid is not None:
            pid_str = str(pid)
            self.registry["children"].pop(pid_str, None)
            for parent in self.registry["parents"].values():
                if pid in parent["children"]:
                    parent["children"].remove(pid)

            for children in self.registry["parent_to_children"].values():
                if pid in children:
                    children.remove(pid)

        self._save_registry()

    def remove_parent_and_children(self, parent_pid):
        parent_pid = str(parent_pid)

        children = self.registry["parent_to_children"].pop(parent_pid, [])
        for child_pid in children:
            self.registry["children"].pop(str(child_pid), None)

            ports_to_remove = [port for port, pid in self.registry["port_to_pid"].items() if pid == child_pid]
            for port in ports_to_remove:
                self.registry["port_to_pid"].pop(port, None)

        self.registry["parents"].pop(parent_pid, None)
        ports_to_remove = [port for port, pid in self.registry["port_to_pid"].items() if pid == int(parent_pid)]
        for port in ports_to_remove:
            self.registry["port_to_pid"].pop(port, None)

        self._save_registry()

    def get_all_parents(self):
        return self.registry["parents"]

    def get_all_children(self):
        return self.registry["children"]

    def list_all_processes(self):
        return self.registry
