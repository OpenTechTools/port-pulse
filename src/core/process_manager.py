import multiprocessing
import os
import time
from cli import cli  # Placeholder for future CLI integration
from src.core.port_allocator import PortAllocator
from src.core.logger import log_event
from src.core.monitor import monitor  # Assuming monitor is initialized globally
from config import PROCESS_TIMEOUT


class Handler:
    """
    Handler class fetches the number of parent and child processes
    from CLI or other UI interfaces.
    """

    def __init__(self):
        self.test_p_process = 2
        self.test_c_process = 2

    def get_processes(self):
        """
        Gets the number of parent and child processes to be created.

        Returns:
            tuple: (num_parents, num_children)
        """
        # Placeholder for dynamic CLI input (e.g., cli.get_p_processes())
        return self.test_p_process, self.test_c_process


class ProcessCreator:
    """
    Creates and manages parent and child processes for PortPulse.
    Each parent process will spawn its own children.
    """

    def __init__(self):
        self.handler = Handler()
        self.port_allocator = PortAllocator(start_port=5000)
        self.parent_processes = []

    def main_process(self):
        """
        Returns PID of the main initiating process.
        """
        return os.getpid()

    def child_handler(self, child_id, port):
        """
        Handler function for a child process.

        Args:
            child_id (int): Child process ID.
            port (int): Assigned port for the child.
        """
        pid = os.getpid()
        log_event(f"Child-{child_id} started", pid=pid, port=port)
        print(f"[Child-{child_id}] PID: {pid} running on port {port}")

        # Register with monitor (optional)
        try:
            monitor.register_process(pid, port, role=f"child-{child_id}")
        except:
            pass  # Failsafe if monitor not yet set up

        start_time = time.time()
        while time.time() - start_time < PROCESS_TIMEOUT:
            time.sleep(1)

        log_event(f"Child-{child_id} exiting", pid=pid, port=port)

    def parent_handler(self, parent_id, num_children):
        """
        Handler for a parent process to spawn child processes.

        Args:
            parent_id (int): Parent process ID.
            num_children (int): Number of children to spawn.
        """
        pid = os.getpid()
        parent_port = self.port_allocator.get_next_free_port()
        log_event(f"Parent-{parent_id} started", pid=pid, port=parent_port)
        print(f"[Parent-{parent_id}] PID: {pid} running on port {parent_port}")

        try:
            monitor.register_process(pid, parent_port, role=f"parent-{parent_id}")
        except:
            pass

        child_processes = []
        for i in range(num_children):
            child_port = self.port_allocator.get_next_free_port()
            child = multiprocessing.Process(
                target=self.child_handler, args=(i + 1, child_port)
            )
            child_processes.append(child)
            child.start()

        for child in child_processes:
            child.join()

        log_event(f"Parent-{parent_id} exiting", pid=pid, port=parent_port)

    def create_parent_processes(self):
        """
        Creates multiple parent processes and invokes parent handlers.
        """
        num_parents, num_children = self.handler.get_processes()

        for i in range(num_parents):
            parent = multiprocessing.Process(
                target=self.parent_handler, args=(i + 1, num_children)
            )
            self.parent_processes.append(parent)
            parent.start()

        for parent in self.parent_processes:
            parent.join()


class PortAssigner:
    """
    Utility class to assign the next available port to a process.
    """

    def __init__(self, start=5000):
        self.port_allocator = PortAllocator(start_port=start)

    def assign_port(self):
        """
        Returns:
            int: Next available port.
        """
        return self.port_allocator.get_next_free_port()


class ProcessTerminator:
    """
    Terminates individual or all PortPulse processes.
    """

    def terminate_process(self, process):
        """
        Forcefully terminates a single process.

        Args:
            process (multiprocessing.Process): Process to terminate.
        """
        if process.is_alive():
            process.terminate()
            log_event("Process terminated", pid=process.pid)
            print(f"Terminated process with PID: {process.pid}")
