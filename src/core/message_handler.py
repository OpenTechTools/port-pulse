import asyncio
from .logger import log_event

class MessageQueue:
    """
    Handles message passing between processes using TCP sockets.
    """

    async def send_message(self, host, port, message):
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

    async def start_message_listener(self, port, message_handler):
        """
        Starts a TCP server to receive messages on a given port.
        `message_handler` is a callback function.
        """
        server = await asyncio.start_server(
            lambda r, w: self._handle_client(r, w, message_handler),
            host='127.0.0.1',
            port=port
        )

        addr = server.sockets[0].getsockname()
        log_event(f"Listening for messages on {addr}", port=port)

        async with server:
            await server.serve_forever()

    async def _handle_client(self, reader, writer, handler_callback):
        data = await reader.read(1024)
        message = data.decode()
        peername = writer.get_extra_info('peername')
        log_event(f"Received message from {peername}: {message}")

        if handler_callback:
            await handler_callback(message)

        writer.close()
        await writer.wait_closed()
