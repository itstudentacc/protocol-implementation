import asyncio
import json
import logging
# import websockets
from websockets.asyncio.server import serve, broadcast

logging.basicConfig()

USERS = set()

MESSAGE = "New Client connected to server"

def users_event():
    return json.dumps({"type": "users", "count": len(USERS)})

def message_event():
    return json.dumps({"type" : "broadcast", "value" : MESSAGE})

async def new_user(websocket):
    global USERS, MESSAGE
    try:
        # Register User
        USERS.add(websocket)
        broadcast(USERS, users_event())

        # Send current state to user
        await websocket.send(message_event())

    finally:
        USERS.remove(websocket)
        broadcast(USERS, users_event())

async def main():
    async with serve(new_user, "localhost", 8000):
        await asyncio.get_running_loop().create_future() # run forever

if __name__ == "__main__":
    asyncio.run(main())