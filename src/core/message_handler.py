import asyncio
from src.core.logger import log_event
from config import BUFFER_SIZE, ENCODING


class MessageQueue:
    """
    Asynchronous message queue for each process.
    - Receives messages over TCP.
    - Sends messages to other ports.
    - Maintains internal queue for incoming messages.
    """

    def __init__(self, host: str = '127.0.0.1', port: int = 5000):
        self.host = host
        self.port = port
        self.queue = asyncio.Queue()
        self.server = None

    async def start_server(self):
        """
        Starts TCP server to receive incoming messages.
        """
        self.server = await asyncio.start_server(
            self.handle_connection, self.host, self.port
        )
        addr = self.server.sockets[0].getsockname()
        log_event(f"MessageQueue listening on {addr}", port=self.port)

        async with self.server:
            await self.server.serve_forever()

    async def handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """
        Handles a single incoming message.
        """
        data = await reader.read(BUFFER_SIZE)
        message = data.decode(ENCODING)
        peername = writer.get_extra_info('peername')

        log_event(f"Received from {peername}: {message}", port=self.port)
        await self.queue.put(message)

        writer.close()
        await writer.wait_closed()

    async def send_message(self, target_host: str, target_port: int, message: str):
        """
        Sends message to another process via TCP.
        """
        try:
            reader, writer = await asyncio.open_connection(target_host, target_port)
            writer.write(message.encode(ENCODING))
            await writer.drain()
            log_event(f"Sent to {target_host}:{target_port} -> {message}", port=self.port)
            writer.close()
            await writer.wait_closed()
        except ConnectionRefusedError:
            log_event(f"Failed to send to {target_host}:{target_port} (connection refused)", level="ERROR", port=self.port)
