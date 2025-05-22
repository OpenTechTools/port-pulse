"""
Handles message sending between processes.
"""

import asyncio
from .logger import log_event

class MessageQueue:
    """
    Handles message passing between processes using TCP sockets.
    """

    async def send_message(self, host, port, message):
        """
        Sends a message to the specified host and port.

        Args:
            host (str): Target host (e.g., '127.0.0.1').
            port (int): Target port.
            message (str): Message to send.
        """
        try:
            reader, writer = await asyncio.open_connection(host, port)
            writer.write(message.encode())
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            log_event(f"Message sent to port {port}: {message}", port=port)
        except Exception as e:
            log_event(f"Failed to send message to port {port}: {e}", port=port, level="ERROR")
            raise