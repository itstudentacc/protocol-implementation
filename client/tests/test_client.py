# send_public_chat.py
import asyncio
from client import Client

async def test_send_public_chat():
    """
    This function sends a public chat message from a client.
    """
    sender_client = Client('ws://localhost:8765')
    await sender_client.connect()

    chat_message = "Hello, this is a public message!"

    # Send the public chat message
    await sender_client.send_public_chat(chat_message)

    # Optionally close the connection after sending
    await sender_client.client.close()

# Run the send public chat test
if __name__ == "__main__":
    asyncio.run(test_send_public_chat())
