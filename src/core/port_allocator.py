import socket
import os
import portalocker  # Cross-platform file locking

class PortAllocator:
    """
    Cross-platform PortAllocator that ensures unique port assignment across processes.
    Uses file-based locking and tracking.
    """

    def __init__(self, start_port=5000, end_port=6000, lockfile='/tmp/port_allocator.lock'):
        self.start_port = start_port
        self.end_port = end_port
        self.lockfile = lockfile
        self.used_ports_file = '/tmp/used_ports.txt'

        # Ensure used_ports_file exists
        if not os.path.exists(self.used_ports_file):
            with open(self.used_ports_file, 'w') as f:
                f.write('')

    def is_port_available(self, port):
        """
        Checks if a specific port is available on localhost.
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
        Returns the next available port in the range, ensuring cross-process uniqueness.
        """
        with portalocker.Lock(self.lockfile, timeout=10):
            used_ports = self._read_used_ports()
            for port in range(self.start_port, self.end_port):
                if port not in used_ports and self.is_port_available(port):
                    used_ports.add(port)
                    self._write_used_ports(used_ports)
                    return port
        raise RuntimeError("No available ports in the defined range.")

    def release_port(self, port):
        """
        Releases a previously used port so it can be reused.
        """
        with portalocker.Lock(self.lockfile, timeout=10):
            used_ports = self._read_used_ports()
            if port in used_ports:
                used_ports.remove(port)
                self._write_used_ports(used_ports)

    def _read_used_ports(self):
        """
        Reads currently allocated ports from the file.
        """
        with open(self.used_ports_file, 'r') as f:
            content = f.read().strip()
            return set(map(int, content.split())) if content else set()

    def _write_used_ports(self, ports):
        """
        Writes the updated port list back to the file.
        """
        with open(self.used_ports_file, 'w') as f:
            f.write(' '.join(map(str, ports)))
