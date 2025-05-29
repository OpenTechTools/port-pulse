import multiprocessing
import os
import socket
import asyncio
import signal
import json
import threading

from .port_allocator import PortAllocator
from .logger import log_event
from .monitor import ProcessMonitor
from .message_handler import MessageQueue
from .process_registry import ProcessRegistry

def send_message_to_process(pid, message, sender_pid=None):
    """
    Sends a message to a process using its registered port.
    Looks up the port via the persistent ProcessRegistry.
    """
    registry = ProcessRegistry()
    port = registry.get_port_by_pid(pid)

    if port is None or port <= 0:
        print(f"[send_message_to_process] No valid port found for PID {pid}")
        log_event(f"No valid port found for PID {pid}", pid=pid, level="ERROR")
        return False

    try:
        with socket.create_connection(("localhost", port), timeout=2) as sock:
            payload = json.dumps({"message": message, "sender_pid": sender_pid}).encode()
            sock.sendall(payload)
        print(f"[send_message_to_process] Message sent to PID {pid} on port {port}")
        log_event(f"Message sent to PID {pid} on port {port} from sender_pid {sender_pid}", 
                 pid=pid, port=port)
        return True
    except Exception as e:
        print(f"[send_message_to_process] Failed to send message to PID {pid} on port {port}: {e}")
        log_event(f"Failed to send message to PID {pid}: {e}", pid=pid, port=port, level="ERROR")
        return False

class Handler:
    """
    Handler class fetches the number of parent and child processes.
    Used for UI or CLI to customize process creation.
    """
    def __init__(self):
        self.test_p_process = 2
        self.test_c_process = 2

    def get_processes(self):
        return self.test_p_process, self.test_c_process

class ProcessCreator:
    """
    Creates and manages parent and child processes for PortPulse.
    Each parent listens on its own port and spawns children, which also listen on separate ports.
    Tracks all processes in a registry to support termination and monitoring.
    """
    def __init__(self):
        self.handler = Handler()
        self.port_allocator = PortAllocator(start_port=5000)
        self.parent_processes = []
        self.process_registry = {}  # pid -> (process, port) for local tracking
        self.registry = ProcessRegistry()  # Global persistent registry
        self.loop = None  # To store the asyncio event loop for signal handling
        self.terminate_event = threading.Event()  # For graceful termination in threads

    def main_process(self):
        return os.getpid()

    def register_process(self, proc_obj, port, parent_pid=None):
        """
        Track each launched process for future reference or termination.
        Also register in the shared persistent registry.
        """
        if proc_obj and hasattr(proc_obj, 'pid'):
            self.process_registry[proc_obj.pid] = (proc_obj, port)
            self.registry.register_process(proc_obj.pid, port or -1, parent_pid)
            log_event(f"Registered process PID {proc_obj.pid} with port {port}", pid=proc_obj.pid, port=port)
        else:
            print(f"[ProcessCreator] Invalid process object for registration: {proc_obj}")

    def child_handler(self, child_id, port):
        """
        Function run inside each child process.
        - Starts TCP listener
        - Logs lifecycle events
        - Registers with monitor and registry
        - Runs until SIGINT or SIGTERM
        """
        pid = os.getpid()
        log_event(f"Child-{child_id} started", pid=pid, port=port)
        print(f"[Child-{child_id}] PID: {pid} running on port {port}")

        try:
            monitor = ProcessMonitor()
            monitor.register_process(pid, port, role=f"child-{child_id}")
            log_event(f"Child-{child_id} registered with monitor", pid=pid, port=port)
        except Exception as e:
            log_event(f"Failed to register child-{child_id} with monitor: {e}", pid=pid, port=port, level="ERROR")

        def safe_exit(signum, frame):
            log_event(f"Child-{child_id} received {'SIGINT' if signum == signal.SIGINT else 'SIGTERM'}", pid=pid, port=port)
            self.port_allocator.release_port(port)
            if self.loop:
                self.loop.stop()
                self.loop.close()
            exit(0)

        signal.signal(signal.SIGINT, safe_exit)
        signal.signal(signal.SIGTERM, safe_exit)

        async def handle_incoming(msg):
            print(f"[Child-{child_id}] Received: {msg}")
            log_event(f"Child-{child_id} handled msg: {msg}", pid=pid, port=port)

        async def run_child():
            queue = MessageQueue()
            try:
                asyncio.create_task(queue.start_message_listener(port, handle_incoming))
                log_event(f"Child-{child_id} started TCP listener on port {port}", pid=pid, port=port)
                while not self.terminate_event.is_set():
                    await asyncio.sleep(1)
            except Exception as e:
                log_event(f"Child-{child_id} TCP listener failed: {e}", pid=pid, port=port, level="ERROR")
                raise

        try:
            self.loop = asyncio.get_event_loop()
            asyncio.run(run_child())
        except Exception as e:
            log_event(f"Child-{child_id} crashed: {e}", pid=pid, port=port, level="ERROR")
        finally:
            log_event(f"Child-{child_id} exiting", pid=pid, port=port)
            self.port_allocator.release_port(port)

    def parent_handler(self, parent_id, num_children):
        """
        Function run inside each parent process.
        - Spawns TCP listener for itself
        - Spawns multiple child processes
        - Registers all in monitor and registry
        - Runs until SIGINT or SIGTERM
        """
        pid = os.getpid()
        parent_port = self.port_allocator.get_next_free_port()
        log_event(f"Parent-{parent_id} started", pid=pid, port=parent_port)
        print(f"[Parent-{parent_id}] PID: {pid} running on port {parent_port}")

        # Update registry with parent's port
        self.registry.register_process(pid, parent_port)

        try:
            monitor = ProcessMonitor()
            monitor.register_process(pid, parent_port, role=f"parent-{parent_id}")
            log_event(f"Parent-{parent_id} registered with monitor", pid=pid, port=parent_port)
        except Exception as e:
            log_event(f"Failed to register parent-{parent_id} with monitor: {e}", pid=pid, port=parent_port, level="ERROR")

        def safe_exit(signum, frame):
            log_event(f"Parent-{parent_id} received {'SIGINT' if signum == signal.SIGINT else 'SIGTERM'}", pid=pid, port=parent_port)
            for child_pid, (proc, _) in self.process_registry.items():
                if proc.is_alive() and child_pid != pid:
                    proc.terminate()
                    log_event(f"Parent-{parent_id} terminated child", pid=child_pid)
            self.port_allocator.release_port(parent_port)
            if self.loop:
                self.loop.stop()
                self.loop.close()
            exit(0)

        signal.signal(signal.SIGINT, safe_exit)
        signal.signal(signal.SIGTERM, safe_exit)

        async def handle_incoming(msg):
            print(f"[Parent-{parent_id}] Received: {msg}")
            log_event(f"Parent-{parent_id} handled msg: {msg}", pid=pid, port=parent_port)

        async def run_parent():
            queue = MessageQueue()
            try:
                asyncio.create_task(queue.start_message_listener(port=parent_port, message_handler=handle_incoming))
                log_event(f"Parent-{parent_id} started TCP listener on port {parent_port}", pid=pid, port=parent_port)
                child_processes = []
                for i in range(num_children):
                    child_port = self.port_allocator.get_next_free_port()
                    child = multiprocessing.Process(
                        target=self.child_handler, args=(i + 1, child_port)
                    )
                    child_processes.append((child, child_port))
                    child.start()
                    self.register_process(child, child_port, parent_pid=pid)
                    log_event(f"Parent-{parent_id} started child-{i+1} with PID {child.pid} on port {child_port}", pid=pid, port=child_port)

                while not self.terminate_event.is_set():
                    await asyncio.sleep(1)
            except Exception as e:
                log_event(f"Parent-{parent_id} TCP listener or child creation failed: {e}", pid=pid, port=parent_port, level="ERROR")
                raise

        try:
            self.loop = asyncio.get_event_loop()
            asyncio.run(run_parent())
        except Exception as e:
            log_event(f"Parent-{parent_id} crashed: {e}", pid=pid, port=parent_port, level="ERROR")
        finally:
            log_event(f"Parent-{parent_id} exiting", pid=pid, port=parent_port)
            self.port_allocator.release_port(parent_port)

    def create_parent_processes(self):
        """
        Entry point to create all parent and child processes based on Handler.
        Runs until terminate_event is set or SIGINT is received in main thread.
        """
        if threading.current_thread() is threading.main_thread():
            def main_safe_exit(signum, frame):
                log_event("Main process received SIGINT, terminating all processes")
                self.terminate_event.set()
                self.terminate_all()
                exit(0)

            signal.signal(signal.SIGINT, main_safe_exit)

        num_parents, num_children = self.handler.get_processes()
        log_event(f"Creating {num_parents} parent(s) with {num_children} child(ren) each")

        for i in range(num_parents):
            parent_port = self.port_allocator.get_next_free_port()
            parent = multiprocessing.Process(
                target=self.parent_handler, args=(i + 1, num_children)
            )
            parent.start()
            self.parent_processes.append(parent)
            self.register_process(parent, parent_port)
            log_event(f"Started parent-{i+1} with PID {parent.pid} on port {parent_port}", pid=parent.pid, port=parent_port)

        try:
            for parent in self.parent_processes:
                parent.join()
        except KeyboardInterrupt:
            log_event("Main process caught KeyboardInterrupt, terminating")
            self.terminate_event.set()
            self.terminate_all()

    def terminate_all(self):
        """
        Terminates all tracked processes (parent and child).
        Also releases any associated ports.
        """
        for pid, (proc, port) in list(self.process_registry.items()):
            if proc.is_alive():
                proc.terminate()
                log_event("Process terminated", pid=pid, port=port)
                print(f"Terminated process with PID: {pid}")
                if port and port != -1:
                    self.port_allocator.release_port(port)

class PortAssigner:
    """
    Utility for on-demand port assignment.
    """
    def __init__(self, start=5000):
        self.port_allocator = PortAllocator(start_port=start)

    def assign_port(self):
        return self.port_allocator.get_next_free_port()

class ProcessTerminator:
    """
    Utility to terminate any given multiprocessing.Process.
    """
    def terminate_process(self, process):
        if process is None or process.is_alive():
            pid = process.pid if process else os.getpid()
            log_event("Process terminated", pid=pid)
            print(f"Terminated process with PID: {pid}")