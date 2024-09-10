# connect.py
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
            raise e

    async def close(self):
        if self.connection is not None:
            await self.connection.close()
            self.connection = None
            print("Connection closed")

    async def send(self, message):
        if self.connection:
            await self.connection.send(message)
        else:
            raise RuntimeError("Connection not established.")
    
    async def receive(self):
        if self.connection:
            return await self.connection.recv()
        else:
            raise RuntimeError("Connection not established.")
        