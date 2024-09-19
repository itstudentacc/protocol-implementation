import asyncio
import websockets

connected_clients = set()

async def mock_server(websocket, path):
    # Register the client
    connected_clients.add(websocket)
    print(f"New client connected: {websocket.remote_address}")

    try:
        async for message in websocket:
            print(f"Received message: {message}")
            await broadcast_message(message)
    except websockets.exceptions.ConnectionClosed as e:
        print(f"Client {websocket.remote_address} disconnected with exception: {e}")
    finally:
        connected_clients.remove(websocket)

async def broadcast_message(message):
    if connected_clients:
        tasks = [client.send(message) for client in connected_clients]
        await asyncio.gather(*tasks)

async def start_server():
    server = await websockets.serve(mock_server, "localhost", 8000)
    print("Server started on ws://localhost:8000")
    await server.wait_closed()

asyncio.run(start_server())
