import socket

class PortAllocator:
    """
    PortAllocator is responsible for assigning unique, available ports
    to processes and managing the port pool.
    """

    def __init__(self, start_port=5000, end_port=6000):
        """
        Initializes the PortAllocator with a range of ports.

        Args:
            start_port (int): The starting port in the range.
            end_port (int): The ending port in the range.
        """
        self.start_port = start_port
        self.end_port = end_port
        self.used_ports = set()  # Stores ports that are currently allocated

    def is_port_available(self, port):
        """
        Checks if a port is free on localhost.

        Args:
            port (int): The port number to check.

        Returns:
            bool: True if the port is available, False otherwise.
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
        Finds and returns the next available port in the range.

        Returns:
            int: A free port number.

        Raises:
            RuntimeError: If no available ports are found.
        """
        for port in range(self.start_port, self.end_port):
            if port not in self.used_ports and self.is_port_available(port):
                self.used_ports.add(port)
                return port
        raise RuntimeError("No available ports in the defined range.")

    def release_port(self, port):
        """
        Releases a previously used port so it can be reused.

        Args:
            port (int): The port number to release.
        """
        self.used_ports.discard(port)
