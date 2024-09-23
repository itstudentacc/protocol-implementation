import websockets
import asyncio

class WebSocketClient:
    def __init__(self, server_address, max_retries=3):
        self.server_address = server_address
        self.connection = None
        self.max_retries = max_retries  # Maximum retries for reconnection

    async def connect(self):
        retries = 0
        while retries < self.max_retries:
            try:
                self.connection = await websockets.connect(self.server_address)
                print(f"Connected to {self.server_address}")
                return
            except Exception as e:
                retries += 1
                print(f"Failed to connect (attempt {retries}/{self.max_retries}): {e}")
                if retries < self.max_retries:
                    await asyncio.sleep(5)  # Wait before retrying
                else:
                    print("Max retries reached. Connection failed.")
                    self.connection = None  # Ensure connection is set to None on failure
                    raise e

    async def close(self):
        if self.connection is not None:
            try:
                await self.connection.close()
                print("Connection closed")
            except Exception as e:
                print(f"Failed to close connection: {e}")
            finally:
                self.connection = None  # Ensure connection is reset

    async def send(self, message):
        if self.connection:
            try:
                await self.connection.send(message)
            except Exception as e:
                print(f"Error sending message: {e}")
                await self.close()  # Close connection on error
        else:
            raise RuntimeError("Connection not established.")

    async def receive(self):
        if self.connection:
            try:
                message = await self.connection.recv()
                print(f"Received message: {message}")
                return message
            except Exception as e:
                print(f"Error receiving message: {e}")
                await self.close()  # Close connection on error
                return None
        else:
            raise RuntimeError("Connection not established.")

    async def reconnect(self):
        """Re-establishes the WebSocket connection if lost."""
        print("Attempting to reconnect...")
        await self.connect()

