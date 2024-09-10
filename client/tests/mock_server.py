# mock_server.py
import asyncio
import websockets

async def mock_server(websocket, path):
    async for message in websocket:
        print(f"Received message: {message}")
        # Optionally, send a response back
        # await websocket.send("Message received")

# Start the server
async def start_server():
    server = await websockets.serve(mock_server, "localhost", 8765)
    print("Server started on ws://localhost:8765")
    await asyncio.sleep(3600)  # Keep the server running for 1 hour

asyncio.run(start_server())
