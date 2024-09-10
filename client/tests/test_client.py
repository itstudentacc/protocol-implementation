import asyncio
import json
import base64
from client import Client
from security_module import Encryption

# Ensure to include your Client and Encryption classes here

async def test_send_hello():
    # Setup the client
    client = Client(server_address="ws://localhost:8765")
    
    # Connect to the server
    await client.connect()
    
    # Send the "hello" message
    await client.send_hello()
    
    # Optionally, close the connection
    # await client.client.close()
    
# Test the send_chat function
async def test_send_chat():
    encryption = Encryption()
    
    public_key, private_key = encryption.generate_rsa_key_pair()
    client = Client('ws://localhost:8765')
    await client.connect()
    
    
    recipient_public_key = public_key  # Replace with actual recipient's public key
    chat_message = "Hello, this is a secure message!"
    
    await client.send_chat(chat_message, recipient_public_key)
    
async def test_send_public_chat():

    client = Client('ws://localhost:8765')
    await client.connect()
    
    chat_message = "Hello, this is a public message!"
    
    await client.send_public_chat(chat_message)
    
    
# Run the test
asyncio.run(test_send_public_chat())
