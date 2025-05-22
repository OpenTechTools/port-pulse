"""
Command Handlers for PortPulse CLI.
Triggered by user commands parsed in cli.py.
"""

import asyncio
from ..core.process_manager import ProcessCreator
from ..core.monitor import ProcessMonitor
from ..core.message_handler import MessageQueue
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

def handle_send_message(port, message):
    """
    Sends a message to a given process on specified port.
    """
    print(f"📬 Sending: '{message}' to port {port}")
    queue = MessageQueue()

    try:
        asyncio.run(queue.send_message("127.0.0.1", port, message))
    except Exception as e:
        print(f"[ERROR] Failed to send message: {e}")

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