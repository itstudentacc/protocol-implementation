import asyncio
import json
from client import Client

async def test_receive_public_chat():
    client = Client('ws://localhost:8765')
    await client.connect()

    message = await client.receive_public_message()
    print(f"Received public message: {message}")

asyncio.run(test_receive_public_chat())
