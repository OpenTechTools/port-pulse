import multiprocessing
import os
import time

from .port_allocator import PortAllocator
from .logger import log_event
from .monitor import ProcessMonitor
from .config import PROCESS_TIMEOUT

class Handler:
    """
    Handler class fetches the number of parent and child processes.
    Used for UI or CLI to customize process creation.
    """

    def __init__(self):
        self.test_p_process = 2
        self.test_c_process = 2

    def get_processes(self):
        """
        Returns number of parent and child processes to create.

        Returns:
            tuple: (num_parents, num_children)
        """
        return self.test_p_process, self.test_c_process


class ProcessCreator:
    """
    Creates and manages parent and child processes for PortPulse.
    Each parent spawns its own children.
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
        Logic for individual child process.

        Args:
            child_id (int): Identifier for the child.
            port (int): Port assigned to this child.
        """
        pid = os.getpid()
        log_event(f"Child-{child_id} started", pid=pid, port=port)
        print(f"[Child-{child_id}] PID: {pid} running on port {port}")

        try:
            ProcessMonitor.register_process(pid, port, role=f"child-{child_id}")
        except:
            pass  # Monitoring optional

        start_time = time.time()
        while time.time() - start_time < PROCESS_TIMEOUT:
            time.sleep(1)

        log_event(f"Child-{child_id} exiting", pid=pid, port=port)
        self.port_allocator.release_port(port)  # Release the port

    def parent_handler(self, parent_id, num_children):
        """
        Logic for parent process to spawn children.

        Args:
            parent_id (int): Identifier for the parent.
            num_children (int): How many children to spawn.
        """
        pid = os.getpid()
        parent_port = self.port_allocator.get_next_free_port()
        log_event(f"Parent-{parent_id} started", pid=pid, port=parent_port)
        print(f"[Parent-{parent_id}] PID: {pid} running on port {parent_port}")

        try:
            ProcessMonitor.register_process(pid, parent_port, role=f"parent-{parent_id}")
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
        self.port_allocator.release_port(parent_port)  # Release the port

    def create_parent_processes(self):
        """
        Launches parent processes and assigns children.
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
    Helper class to get next available port.
    """

    def __init__(self, start=5000):
        self.port_allocator = PortAllocator(start_port=start)

    def assign_port(self):
        """
        Get next available port.

        Returns:
            int: Free port number
        """
        return self.port_allocator.get_next_free_port()


class ProcessTerminator:
    """
    Terminates PortPulse processes gracefully or forcefully.
    """

    def terminate_process(self, process):
        """
        Force kill a process.

        Args:
            process (multiprocessing.Process): Target process
        """
        if process.is_alive():
            process.terminate()
            log_event("Process terminated", pid=process.pid)
            print(f"Terminated process with PID: {process.pid}")