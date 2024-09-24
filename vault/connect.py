import websockets
import asyncio
import logging

logging.basicConfig(level=logging.INFO)

class WebSocketClient:
    def __init__(self, server_address, max_retries=3, ping_interval=None):
        self.server_address = server_address
        self.connection = None
        self.max_retries = max_retries  # Maximum retries for reconnection
        self.ping_interval = ping_interval
        self.ping_timeout = None
    async def connect(self):
        retries = 0
        while retries < self.max_retries:
            try:
                self.connection = await websockets.connect(
                    self.server_address,
                    ping_interval=self.ping_interval,
                    ping_timeout=self.ping_timeout
                )
                logging.info(f"Connected to {self.server_address}")
                return
            except Exception as e:
                retries += 1
                logging.error(f"Failed to connect (attempt {retries}/{self.max_retries}): {e}")
                if retries < self.max_retries:
                    await asyncio.sleep(min(2 ** retries, 30))  # Exponential backoff (max 30s)
                else:
                    logging.error("Max retries reached. Connection failed.")
                    self.connection = None  # Ensure connection is set to None on failure
                    raise e

    async def close(self):
        if self.connection is not None:
            try:
                await self.connection.close()
                logging.info("Connection closed")
            except Exception as e:
                logging.error(f"Failed to close connection: {e}")
            finally:
                self.connection = None  # Ensure connection is reset

    async def send(self, message):
        if self.connection:
            try:
                await self.connection.send(message)
                logging.info(f"Sent message: {message}")
            except websockets.ConnectionClosedError as e:
                logging.error(f"Connection closed while sending: {e}")
                await self.reconnect()
                await self.send(message)  # Retry sending after reconnect
            except Exception as e:
                logging.error(f"Error sending message: {e}")
                await self.close()
        else:
            raise RuntimeError("Connection not established.")

    async def receive(self):
        if self.connection:
            try:
                message = await self.connection.recv()
                logging.info(f"Received message: {message}")
                return message
            except websockets.ConnectionClosedError as e:
                logging.error(f"Connection closed while receiving: {e}")
                await self.reconnect()
                return await self.receive()  # Retry receiving after reconnect
            except Exception as e:
                logging.error(f"Error receiving message: {e}")
                await self.close()
                return None
        else:
            raise RuntimeError("Connection not established.")

    async def reconnect(self):
        """Re-establishes the WebSocket connection if lost."""
        logging.info("Attempting to reconnect...")
        await self.connect()
