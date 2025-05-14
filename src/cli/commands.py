"""
Command Handlers for PortPulse CLI.
Triggered by user commands parsed in cli.py.
"""

import asyncio
from src.core import process_manager, monitor
from src.core.message_handler import MessageQueue
from src.core.logger import log_event

def handle_init():
    """
    Initializes PortPulse system (currently placeholder).
    """
    print("🔧 PortPulse Initialized (no persistent services needed)")
    log_event("PortPulse system initialized")

def handle_create_process(process_type, num_children):
    """
    Handles creation of parent or child processes.
    """
    creator = process_manager.ProcessCreator()

    if process_type == 'parent':
        print(f"🚀 Creating 1 parent with {num_children} child(ren)...")
        creator.instance_process.test_c_process = num_children
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
    dashboard = monitor.ProcessMonitor()
    dashboard.show_dashboard()
