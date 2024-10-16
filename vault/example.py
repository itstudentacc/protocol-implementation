import asyncio
import websockets

async def websocket_client():
    uri = "ws://localhost:8000"  # Replace with your WebSocket server URI
    
    # Connect to WebSocket server
    async with websockets.connect(uri) as websocket:
        # Send a message
        message = "Hello, WebSocket Server!"
        await websocket.send(message)
        print(f"Sent to server: {message}")

        # Wait to receive a message from the server
        response = await websocket.recv()
        print(f"Received from server: {response}")

# Run the client
asyncio.get_event_loop().run_until_complete(websocket_client())
