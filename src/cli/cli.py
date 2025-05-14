"""
CLI Entry Point for PortPulse.
Handles command-line parsing and dispatches to corresponding command handlers.
"""

import argparse
from cli import commands

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
    create_parser.add_argument('--children', type=int, default=0, help='Number of children (if parent)')

    # Send Message
    send_parser = subparsers.add_parser('send', help='Send message to a process by port')
    send_parser.add_argument('--to', type=int, required=True, help='Destination port')
    send_parser.add_argument('--message', type=str, required=True, help='Message to send')

    # Monitor
    subparsers.add_parser('monitor', help='Start monitor dashboard')

    args = parser.parse_args()

    match args.command:
        case 'init':
            commands.handle_init()
        case 'create-process':
            commands.handle_create_process(args.type, args.children)
        case 'send':
            commands.handle_send_message(args.to, args.message)
        case 'monitor':
            commands.handle_monitor()
        case _:
            parser.print_help()

if __name__ == "__main__":
    main()
