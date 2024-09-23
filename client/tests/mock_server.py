import asyncio
import websockets
import json
import hashlib

class OLAFServer:
    def __init__(self, host='localhost', port=8000, neighbours=None):
        self.host = host
        self.port = port
        self.neighbours = neighbours or []
        self.clients = {}
        self.server_connections = {}

    async def handler(self, websocket):
        async for message in websocket:
            msg = json.loads(message)
            print(msg)
            if msg["type"] == "signed_data":
                signed_data_type = msg["data"]["type"]

                match signed_data_type:
                    case "hello":
                        await self.handle_hello(websocket, msg)
                    case "chat":
                        await self.handle_chat(websocket, msg)
                    case "public_chat":
                        await self.handle_public_chat(websocket, msg)

            elif msg["type"] == "client_list_request":
                await self.handle_client_list_request(websocket)

            elif msg["type"] == "client_update_request":
                await self.handle_client_update_request(websocket)

    async def handle_hello(self, websocket, msg):
        public_key = msg["data"]["public_key"]
        fingerprint = self.get_fingerprint(public_key)
        self.clients[fingerprint] = {"websocket": websocket, "public_key": public_key}
        print(f"New client connected: {fingerprint}")

        await self.handle_client_list_request(websocket)
        await self.broadcast_client_update()

    async def handle_chat(self, websocket, msg):
        data = msg["data"]
        dest_servers = data["destination_servers"]

        for server in dest_servers:
            uri = f"ws://{server}"
            try:
                async with websockets.connect(uri) as server_ws:
                    await server_ws.send(json.dumps(msg))
            except Exception as e:
                print(f"Error sending message to {server}: {e}")

    async def handle_public_chat(self, websocket, msg):
        await self.broadcast(msg)

    async def handle_client_list_request(self, websocket):
        response = {
            "type": "client_list",
            "servers": [
                {
                    "address": server_uri,
                    "clients": self.server_connections[server_uri]["clients"]
                }
                for server_uri in self.server_connections
            ]
        }
        await websocket.send(json.dumps(response))

    async def handle_client_update_request(self, websocket):
        server_uri = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        self.server_connections[server_uri] = {"websocket": websocket, "clients": []}

        client_update = {
            "type": "client_update",
            "clients": [self.clients[fingerprint]["public_key"] for fingerprint in self.clients.keys()]
        }
        await websocket.send(json.dumps(client_update))

    async def broadcast_client_update(self):
        client_update = {
            "type": "client_update",
            "clients": [self.clients[fingerprint]["public_key"] for fingerprint in self.clients.keys()]
        }
        await self.broadcast_to_servers(client_update)

    async def broadcast(self, msg):
        for client in self.clients.values():
            try:
                await client["websocket"].send(json.dumps(msg))
            except Exception as e:
                print(f"Error broadcasting message: {e}")

    async def broadcast_to_servers(self, msg):
        for server in self.server_connections.values():
            websocket = server["websocket"]
            try:
                await websocket.send(json.dumps(msg))
            except Exception as e:
                print(f"Error sending message to server: {e}")

    def get_fingerprint(self, public_key_pem):
        return hashlib.sha256(public_key_pem.encode('utf-8')).hexdigest()

    async def connect_to_server(self, server_uri):
        while True:
            try:
                websocket = await websockets.connect(server_uri)
                self.server_connections[server_uri] = {"websocket": websocket}
                print(f"Connected to server: {server_uri}")
                await websocket.send(json.dumps({"type": "client_update_request"}))
                asyncio.create_task(self.handle_server_messages(websocket, server_uri))
                break  # Exit the retry loop on success
            except Exception as e:
                print(f"Failed to connect to {server_uri}: {e}")
                await asyncio.sleep(5)  # Retry after a delay

    async def handle_server_messages(self, websocket, server_uri):
        try:
            async for message in websocket:
                msg_json = json.loads(message)
                print(f"Received message from {server_uri}: {msg_json}")

                if msg_json["type"] == 'client_update':
                    self.server_connections[server_uri]["clients"] = msg_json["clients"]
        except websockets.ConnectionClosed:
            print(f"Connection to {server_uri} closed.")
            del self.server_connections[server_uri]

    async def start_server(self):
        async with websockets.serve(self.handler, self.host, self.port):
            print(f"OLAF Server started on ws://{self.host}:{self.port}")

            for neighbour in self.neighbours:
                print(f"Scheduling connection to neighbour: {neighbour}")
                asyncio.create_task(self.connect_to_server(neighbour))

            await asyncio.Future()  # Run forever

    def run(self):
        asyncio.run(self.start_server())

if __name__ == "__main__":
    neighbours = []  # Add any neighbour server URIs if needed
    olaf_server = OLAFServer('localhost', 8000, neighbours=neighbours)
    olaf_server.run()
