import websockets
import asyncio

class WebSocketClient:
    def __init__(self, server_address):
        self.server_address = server_address
        self.connection = None

    async def connect(self):
        self.connection = await websockets.connect(self.server_address)
        print(f"Connected to {self.server_address}")

    async def send(self, message):
        await self.connection.send(message)
        print(f"Sent: {message}")
        
    async def receive(self):
        if self.connection is None:
            raise Exception("Not connected")
        else:
            message = await self.connection.recv()
            print(f"Received: {message}")
            return message
        
    async def close(self):
        if self.connection is not None:
            await self.connection.close()
            print("Connection closed")
        