import socket
import os
import portalocker  # Ensure this is installed: pip install portalocker

class PortAllocator:
    """
    Cross-platform port allocator that assigns and tracks ports across processes
    using file locking and availability checking.
    """

    def __init__(self, start_port=5000, end_port=6000,
                 lockfile='/tmp/port_allocator.lock',
                 used_ports_file='/tmp/used_ports.txt'):
        self.start_port = start_port
        self.end_port = end_port
        self.lockfile = lockfile
        self.used_ports_file = used_ports_file

        os.makedirs(os.path.dirname(self.used_ports_file), exist_ok=True)
        if not os.path.exists(self.used_ports_file):
            open(self.used_ports_file, 'w').close()

    def is_port_available(self, port):
        """
        Check if the port is free on localhost.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(('localhost', port))
                return True
            except OSError:
                return False

    def get_next_free_port(self):
        """
        Return the next available and unused port within the defined range.
        Locks the operation to prevent conflicts across processes.
        """
        with portalocker.Lock(self.lockfile, timeout=5):
            used_ports = self._read_used_ports()
            for port in range(self.start_port, self.end_port):
                if port not in used_ports and self.is_port_available(port):
                    used_ports.add(port)
                    self._write_used_ports(used_ports)
                    return port
        raise RuntimeError("No available ports found in the defined range.")

    def release_port(self, port):
        """
        Release a port from the used list so it can be reused later.
        """
        with portalocker.Lock(self.lockfile, timeout=5):
            used_ports = self._read_used_ports()
            if port in used_ports:
                used_ports.remove(port)
                self._write_used_ports(used_ports)

    def _read_used_ports(self):
        """
        Read the list of currently used ports from the tracking file.
        """
        try:
            with open(self.used_ports_file, 'r') as f:
                content = f.read().strip()
                return set(map(int, content.split())) if content else set()
        except Exception as e:
            print(f"[PortAllocator] Failed to read used ports: {e}")
            return set()

    def _write_used_ports(self, ports):
        """
        Write the set of used ports back to the file.
        """
        try:
            with open(self.used_ports_file, 'w') as f:
                f.write(' '.join(map(str, sorted(ports))))
        except Exception as e:
            print(f"[PortAllocator] Failed to write used ports: {e}")

    def reset(self):
        """
        (Optional) Reset the used ports file – useful for testing or dev.
        """
        with portalocker.Lock(self.lockfile, timeout=5):
            open(self.used_ports_file, 'w').close()
