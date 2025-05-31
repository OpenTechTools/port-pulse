"""
Command Handlers for PortPulse CLI.
Triggered by user commands parsed in cli.py.
"""
import signal
import os
import asyncio
import json
from ..core.process_manager import ProcessCreator, send_message_to_process
from ..core.monitor import ProcessMonitor
from ..core.message_handler import MessageQueue
from ..core.process_registry import ProcessRegistry
from ..core.port_allocator import PortAllocator 
from ..core.logger import log_event
from ..ui.dashboard import launch_dashboard

def handle_init():
    """
    Initializes PortPulse system (currently placeholder).
    """
    print("🔧 PortPulse Initialized (no persistent services needed)")
    log_event("PortPulse system initialized")

def handle_create_process(process_type, num_parents, num_children):
    """
    Handles creation of parent or child processes.

    Args:
        process_type (str): Type of process ('parent' or 'child').
        num_parents (int): Number of parent processes to create.
        num_children (int): Number of children per parent.
    """
    creator = ProcessCreator()

    if process_type == 'parent':
        print(f"🚀 Creating {num_parents} parent(s) with {num_children} child(ren) each...")
        creator.handler.test_p_process = num_parents
        creator.handler.test_c_process = num_children
        creator.create_parent_processes()

    elif process_type == 'child':
        print("👶 Creating standalone child process...")
        port = creator.port_allocator.get_next_free_port()
        creator.child_handler(child_id=1, port=port)

def handle_send_message(port, from_pid, message):
    """
    Sends a message from a process (by PID) to another process (by port).
    """
    print(f"📬 Sending: '{message}' from PID {from_pid} to port {port}")
    registry = ProcessRegistry()
    target_pid = registry.get_pid_by_port(port)
    
    if target_pid:
        send_message_to_process(target_pid, message, sender_pid=from_pid)
        log_event(f"Message sent from PID {from_pid} to PID {target_pid} on port {port}", 
                 pid=from_pid, port=port)
    else:
        print(f"[❌] No process found for port {port}")
        log_event(f"Failed to send message: No process found for port {port}", level="ERROR")

def handle_child_message(from_pid, to_pid, message):
    """
    Sends a message from one child process to another child process by PID.
    """
    registry = ProcessRegistry()
    from_port = registry.get_port_by_pid(from_pid)
    to_port = registry.get_port_by_pid(to_pid)
    
    if from_port and to_port:
        print(f"📩 Sending: '{message}' from PID {from_pid} to PID {to_pid}")
        send_message_to_process(port=to_port, message=message, sender_pid=from_pid)
        log_event(f"Child message sent from PID {from_pid} to PID {to_pid}: {message}", 
                 pid=from_pid, port=to_port)
    else:
        print(f"[❌] Invalid PID(s) for message sending")
        log_event(f"Failed to send child message: Invalid PID(s)", level="ERROR")

def handle_broadcast(parent_pid, message):
    """
    Sends a message to all children of a parent or all processes if parent_pid is 0.
    """
    registry = ProcessRegistry()
    if parent_pid == 0:
        print(f"📢 Broadcasting: '{message}' to all processes")
        processes = registry.list_all_processes()
        for port, pid in processes["port_to_pid"].items():
            if port != -1:
                send_message_to_process(port=port, message=message, sender_pid=None)
    else:
        print(f"📢 Broadcasting: '{message}' to children of PID {parent_pid}")
        children = registry.get_children_by_parent(parent_pid)
        for child_pid in children:
            port = registry.get_port_by_pid(child_pid)
            if port and port != -1:
                send_message_to_process(port=port, message=message, sender_pid=None)

def handle_monitor():
    """
    Starts the terminal monitor dashboard.
    """
    print("📊 Launching Process Monitor...")
    dashboard = ProcessMonitor()
    dashboard.show_dashboard()

def handle_ui():
    """
    Launches the Tkinter UI dashboard.
    """
    print("🖥️ Launching UI Dashboard...")
    launch_dashboard()

def handle_terminate_process(port):
    """
    Terminates a specific child process by port and updates registry.
    """
    registry = ProcessRegistry()
    pid = registry.get_pid_by_port(port)
    
    if pid:
        try:
            os.kill(pid, signal.SIGTERM)
            print(f"[✅] Terminated child PID {pid} on port {port}")
            
            allocator = PortAllocator()
            allocator.release_port(port)
            registry.remove_process(port)
        except ProcessLookupError:
            print(f"[⚠️] Process {pid} already not running.")
    else:
        print(f"[❌] No process found for port {port}")

def handle_terminate_parent(parent_pid):
    """
    Terminates a parent and all its associated children.
    """
    registry = ProcessRegistry()
    children = registry.get_children_by_parent(parent_pid)
    allocator = PortAllocator()

    for child_pid in children:
        port = registry.get_port_by_pid(child_pid)
        if port:
            try:
                os.kill(child_pid, signal.SIGTERM)
                print(f"[✅] Terminated child PID {child_pid} on port {port}")
                allocator.release_port(port)
                registry.remove_process(port)
            except ProcessLookupError:
                print(f"[⚠️] Child PID {child_pid} already not running")

    try:
        os.kill(int(parent_pid), signal.SIGTERM)
        print(f"[✅] Terminated parent PID {parent_pid}")
        parent_port = registry.get_port_by_pid(parent_pid)
        if parent_port:
            allocator.release_port(parent_port)
            registry.remove_parent_and_children(parent_pid)
    except ProcessLookupError:
        print(f"[⚠️] Parent PID {parent_pid} already not running")