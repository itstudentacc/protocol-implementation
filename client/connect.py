import websockets
import asyncio

class WebSocketClient:
    def __init__(self, server_address):
        self.server_address = server_address
        self.connection = None

    async def connect(self):
        try:
            self.connection = await websockets.connect(self.server_address)
            print(f"Connected to {self.server_address}")
        except Exception as e:
            print(f"Failed to connect: {e}")
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
