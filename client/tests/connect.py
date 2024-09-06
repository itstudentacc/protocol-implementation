import websockets
import asyncio
# from message_handler import MessageHandler

class WebSocketClient:
    def __init__(self, server_address):
        self.server_address = server_address
        self.connection = None
        self.message_handler = None

    async def connect(self):
        try:
            self.connection = await websockets.connect(self.server_address)
            # self.message_handler = MessageHandler(self.connection)
            print(f"Connected to {self.server_address}")
        except Exception as e:
            print(f"Failed to connect: {e}")
            raise e

    async def close(self):
        if self.connection is not None:
            await self.connection.close()
            self.connection = None
            print("Connection closed")


        