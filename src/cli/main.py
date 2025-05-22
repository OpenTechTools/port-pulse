"""
CLI Entry Point for PortPulse.
Handles command-line parsing and dispatches to corresponding command handlers.
"""

import argparse
from .commands import (
    handle_init,
    handle_create_process,
    handle_send_message,
    handle_monitor,
    handle_ui,
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
    send_parser = subparsers.add_parser('send', help='Send message to a process by port')
    send_parser.add_argument('--to', type=int, required=True, help='Destination port')
    send_parser.add_argument('--message', type=str, required=True, help='Message to send')

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
            handle_send_message(args.to, args.message)
        case 'monitor':
            handle_monitor()
        case 'ui':
            handle_ui()
        case _:
            parser.print_help()

if __name__ == "__main__":
    main()