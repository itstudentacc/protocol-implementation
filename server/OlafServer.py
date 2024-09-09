import asyncio
import websockets
import json
import hashlib
from websockets.asyncio.client import connect
from websockets.asyncio.server import serve
from aiohttp import web

""""
clients: a list of dicts. each dict is has the structure:
    dict = {
        "server" : <Address of server>
        "clients" : [public keys]
    }

    each dict lists the clients in that server. 
clients could also be a set.
"""


class OLAFServer:
    def __init__(self, host='localhost', port=8000, neighbours=None):
        self.host = host
        self.port = port
        self.neighbours = neighbours or []
        self.clients = {}
        self.server_connections = {}

    async def handler(self, websocket):
        """Main handler for WebSocket connections"""

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
        """Handles the hello message from a client"""

        public_key = msg["data"]["public_key"]
        fingerprint = self.get_fingerprint(public_key)
        self.clients[fingerprint] = {"websocket": websocket, "public_key": public_key}
        print(f"New client connected: {fingerprint}")

        # Send client list after client sucessfully connected.
        await self.handle_client_list_request(websocket)

        # Notify neighbourhood of new client
        await self.broadcast_client_update()
    


    async def handle_chat(self, websocket, msg):
        """Handles a 'chat' message"""

        data = msg["data"]
        dest_servers = data["destination_servers"]

        for server in dest_servers:
            uri = f"ws://{server}"

            async with connect(uri) as websocket:
                try:
                    await websocket.send(json.dumps(msg))

                except:
                    print(f"error in sending message to {server}")
    


    async def handle_public_chat(self, websocket, msg):
        """Handles the 'public_chat' message."""
        await self.broadcast(msg)
    


    async def handle_client_list_request(self, websocket):
        """Handles the 'client_list_request' message."""

        response = {
            "type" : "client_list",
            "servers": [
                {
                    "address" : server_uri,
                    "clients" : self.server_connections[server_uri]["clients"]
                }
                for server_uri in self.server_connections
            ]
        }

        await websocket.send(json.dumps(response))



    async def handle_client_update_request(self, websocket):
        """
        Handles the 'client_udpate_request' message. These messages only come from servers, so also add server to server_connections
        if not already in there.
        """
        server_uri = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"

        self.server_connections[server_uri] = websocket

        client_update = {
            "type" : "client_update",
            "clients" : [self.clients[fingerprint]["public_key"] for fingerprint in self.clients.keys()]
        }

        await websocket.send(json.dumps(client_update))
    


    async def broadcast_client_update(self):
        """Sends a 'client_update' message to servers connected"""

        client_update = {
            "type" : "client_update",
             "clients" : [self.clients[fingerprint]["public_key"] for fingerprint in self.clients.keys()]
        }

        await self.broadcast_to_servers(client_update)
    


    async def broadcast(self, msg: object):
        """Broadcast message to connected clients"""

        for client in self.clients.values():
            await client["websocket"].send(json.dumps(msg))



    async def broadcast_to_servers(self, msg: object):
        """Broadcast message to connected servers"""
        print(self.server_connections)
        for server in self.server_connections.values():
            websocket = server["websocket"]
            await websocket.send(json.dumps(msg))
    


    def get_fingerprint(self, public_key_pem):
        """Generates a SHA-256 fingerprint from a PEM-encoded public key.
            (May not be needed)
        """
        public_key_bytes = public_key_pem.encode('utf-8')
        return hashlib.sha256(public_key_bytes).hexdigest()
    


    async def connect_to_server(self, server_uri):
        """Connects to another server in the neighbourhood"""
        try:
            websocket = await websockets.connect(server_uri)
            self.server_connections[server_uri] = {"websocket": websocket}
            print(f"Connected to server: {server_uri}")

            await websocket.send(json.dumps({"type": "client_update_request"}))

            asyncio.create_task(self.handle_server_messages(websocket,server_uri))

        except Exception as e:
            print(f"Failed to connect to {server_uri}: {e}")
    


    async def handle_server_messages(self, websocket, server_uri):
        """Handles messages from a connected server."""

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
        """Starts the OLAF Server"""

        self.server = await serve(self.handler, self.host, self.port)
        print(f"OLAF/Neighbourhood server started on ws://{self.host}:{self.port}")

        for neighbour in self.neighbours: 
            print(f"Scheduling connection to neighbour: {neighbour}")
            asyncio.create_task(self.connect_to_server(neighbour))

        await self.server.wait_closed()


    async def http_handler(self, request):
        """Handles generic HTTP request."""
        return web.Response(text="Hello! This is OLAF Server.", content_type='text/html')

    async def start_http_server(self):
        """Starts the HTTP and WebSocket server."""

        app = web.Application()

        # Add HTTP routes
        app.router.add_get('/', self.http_handler)

        # Add WebSocket routes
        app.router.add_get('/ws', self.handle_websocket)

        # Start the server
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        print(f"Starting OLAF HTTP/WebSocket server on http://{self.host}:{self.port}")
        await site.start()

        # Connect to neighbour servers
        for neighbour in self.neighbours:
            print(f"Scheduling connection to neighbour: {neighbour}")
            asyncio.create_task(self.connect_to_server(neighbour))
        
        #Keep running the server
        while True:
            await asyncio.sleep(3600)


    # def run(self):
    #     """Run the websocket server"""
    #     asyncio.get_event_loop().run_until_complete(self.start_server())
    #     asyncio.get_event_loop().run_forever()
    
    def run(self):
        """Runs the OLAF server"""
        asyncio.run(self.start_http_server())


if __name__ == "__main__":
    neighbours = [
        "ws://localhost:8001"
    ]
    olaf_server = OLAFServer('localhost', 8000, neighbours=neighbours)
    olaf_server.run()
