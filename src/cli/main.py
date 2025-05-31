"""
CLI Entry Point for PortPulse.
Handles command-line parsing and dispatches to corresponding command handlers.
"""

import argparse
from .commands import (
    handle_init,
    handle_create_process,
    handle_send_message,
    handle_child_message,
    handle_broadcast,
    handle_monitor,
    handle_ui,
    handle_terminate_process, 
    handle_terminate_parent
)

def main():
    parser = argparse.ArgumentParser(
        prog="portpulse",
        description="PortPulse: Messaging Hub for Process Communication via Ports"
    )

    subparsers = parser.add_subparsers(dest='command', required=True)

    # Init
    subparsers.add_parser('init', help='Initialize PortPulse system')

    # Create Process
    create_parser = subparsers.add_parser('create-process', help='Create parent and/or child processes')
    create_parser.add_argument('--type', choices=['parent', 'child'], required=True, help='Type of process to create')
    create_parser.add_argument('--parents', type=int, default=1, help='Number of parent processes (if parent)')
    create_parser.add_argument('--children', type=int, default=0, help='Number of children per parent (if parent)')

    # Send Message
    send_parser = subparsers.add_parser('send', help='Send message from a process to another process by port')
    send_parser.add_argument('--port', type=int, required=True, help='Destination port')
    send_parser.add_argument('--from-pid', type=int, required=True, help='Sender process PID')
    send_parser.add_argument('--message', type=str, required=True, help='Message to send')

    # Child to Child Message
    child_msg_parser = subparsers.add_parser('child-message', help='Send message from one child to another by PID')
    child_msg_parser.add_argument('--from-pid', type=int, required=True, help='Sender child PID')
    child_msg_parser.add_argument('--to-pid', type=int, required=True, help='Receiver child PID')
    child_msg_parser.add_argument('--message', type=str, required=True, help='Message to send')

    # Broadcast Message
    broadcast_parser = subparsers.add_parser('broadcast', help='Broadcast message to children of a parent or all processes')
    broadcast_parser.add_argument('--parent-pid', type=int, default=0, help='Parent PID (0 for all processes)')
    broadcast_parser.add_argument('--message', type=str, required=True, help='Message to broadcast')

    # Terminate Child
    terminate_parser = subparsers.add_parser('terminate-child', help='Terminate child process by port')
    terminate_parser.add_argument('--port', type=int, required=True, help='Port of the child process')

    # Terminate Parent
    terminate_parent_parser = subparsers.add_parser('terminate-parent', help='Terminate parent and its children')
    terminate_parent_parser.add_argument('--pid', type=int, required=True, help='Parent PID')

    # Monitor
    subparsers.add_parser('monitor', help='Start monitor dashboard')

    # UI Dashboard
    subparsers.add_parser('ui', help='Launch the Tkinter UI dashboard')

    args = parser.parse_args()

    # Command dispatcher
    match args.command:
        case 'init':
            handle_init()
        case 'create-process':
            handle_create_process(args.type, args.parents, args.children)
        case 'send':
            handle_send_message(args.port, args.from_pid, args.message)
        case 'child-message':
            handle_child_message(args.from_pid, args.to_pid, args.message)
        case 'broadcast':
            handle_broadcast(args.parent_pid, args.message)
        case 'terminate-child':
            handle_terminate_process(args.port)  
        case 'terminate-parent':
            handle_terminate_parent(args.pid)
        case 'monitor':
            handle_monitor()
        case 'ui':
            handle_ui()
        case _:
            parser.print_help()

if __name__ == "__main__":
    main()