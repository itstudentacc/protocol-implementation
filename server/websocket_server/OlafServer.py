import asyncio
import websockets
import json
import hashlib
import os
import traceback
import time
from websockets.asyncio.client import connect
from websockets.asyncio.server import serve, ServerConnection


class ConnectionHandler():
    websocket = None
    public_key = ""
    counter = 0

    async def send(self, message: dict) -> None:
        """
        Sends a message to the websocket
        """
        data = json.dumps(message)
        await self.websocket.send(data)

class OlafServerConnection(ConnectionHandler):
    def __init__(self, websocket: ServerConnection, server_addr: str, public_key: str):
        self.websocket = websocket
        self.server_addr = server_addr
        self.public_key = public_key

class OlafClientConnection(ConnectionHandler):
    def __init__(self, websocket: ServerConnection, public_key: str):
        self.websocket = websocket
        self.public_key = public_key

class WebSocketServer():
    def __init__(self, host: str ='', port: int =8000, neighbours: dict[str,str] = {}, public_key: str = "default_public_key"):
        self.host = host
        self.port = port
        self.server_address = f"ws://{self.host}:{self.port}"
        self.clients = set()
        self.neighbours = neighbours
        self.all_clients = {}
        self.neighbour_connections = set()
        self.server = None
        self.public_key = public_key
    
    def exisiting_client(self, websocket: ServerConnection) -> bool:
        """
        Returns true if websocket is part of existing client list
        """
        client_websockets = [client.websocket for client in self.clients]
        return websocket in client_websockets
    
    def existing_neighbour(self, websocket: ServerConnection) -> bool:
        """
        Returns true if websocket is part of neighbourhood
        """
        neighbour_websockets = [neighbour.websocket for neighbour in self.neighbour_connections]
        return websocket in neighbour_websockets

    def existing_connection(self, websocket:ServerConnection) -> OlafClientConnection | OlafServerConnection | None:
        """
        If a connection exists, returns the connection object.
        """
        if self.exisiting_client(websocket):
            for client in self.clients:
                if websocket == client.websocket:
                    return client
        
        elif self.existing_neighbour(websocket):
            for neighbour in self.neighbour_connections:
                if websocket == neighbour.websocket:
                    return neighbour
        
        return None

    async def recv(self, websocket: ServerConnection) -> None:
        """
        Receive the message and turn into python object
        """
        while True:
            try:
                # async for message in websocket:
                message = await websocket.recv()
                try:
                    data = json.loads(message)
                    # print(f"Message received: {data}")
                    # Handle all messages
                    await self.handler(websocket, data)

                except json.decoder.JSONDecodeError:
                    print("Invalid Format")
                    err = {
                        "error" : "Message received not in JSON string."
                    }
                    await self.send(websocket, err)
            except websockets.ConnectionClosedOK:
                break
            except websockets.exceptions.ConnectionClosed as conn_closed:
                print(str(conn_closed))
                print('line 91')
                # Remove from clients / neighbours list
                await self.disconnect(websocket)
        

    async def disconnect(self, websocket: ServerConnection) -> None:
        """
        Handles a disconnection
        """
        tmp = []
        for client in self.clients:
            client_addr = f"{client.websocket.remote_address[0]}:{client.websocket.remote_address[1]}"
            print(f"Client: {client_addr}")

            if websocket == client.websocket:
                print(f"Client {client.public_key} scheduled for disconnection.")
                tmp.append(client)

        for neighbour in self.neighbour_connections:
            if websocket == neighbour.websocket:
                print(f"Neighbour {neighbour.public_key} scheduled for removal")
                tmp.append(neighbour)
        
        for conn in tmp:
            if conn in self.clients:
                self.clients.remove(conn)
                print(f"Client {conn.public_key} removed.")
                await self.send_client_update_to_neighbours()
            elif conn in self.neighbour_connections:
                self.neighbour_connections.remove(conn)
                print(f"Neighbour {conn.public_key} removed.")

        await websocket.close(code=1000)


    
    async def send(self, websocket: ServerConnection, data: dict) -> None:
        """
        Send the data as serialised message to websocket
        """
        message = json.dumps(data)
        await websocket.send(message)
    
    def message_fits_standard(self, message: dict) -> bool:
        """
        Returns True if message fits an OLAF Protocol message.
        Extent of checking is if whether the message has the correct keys.
        No checks performed on the values - which leaves a backdoor open.
        """

        valid_keys = [
            "type",
            "data",
            "counter",
            "signature"
        ]

        # for key in message.keys():
        #     if key not in valid_keys:
        #         return False

        msg_type = message["type"]

        valid_types = [
            "signed_data",
            "client_list_request",
            "client_list",
            "client_update",
            "client_update_request"
        ]

        if msg_type not in valid_types:
            return False
        
        return True


    async def echo(self, websocket: ServerConnection) -> None:
        """
        Relays the message back to the sender.
        """
        data = await self.recv(websocket)
        await self.send(websocket, data)

    async def handler(self, websocket: ServerConnection, message: dict) -> None:
        """
        Handle websocket messages
        """

        # Check whether message meets standardised format
        if not self.message_fits_standard(message):
            # Return invalid message error.
            print(f"Unkown message type received")
            err_msg = {
                "error" : "Message does not fit OLAF Protocol standard."
            }
            await self.send(websocket, err_msg)
            return

        # Only valid messages from this point.

        # Handle each type accordingly
        msg_type = message["type"]
        match msg_type:
            case "signed_data":
                await self.signed_data_handler(websocket, message)
            case "client_list_request":
                await self.client_list_request_handler(websocket)
            case "client_update":
                self.client_update_handler(websocket, message)
            case "client_update_request":
                await self.client_update_request_handler(websocket)
            case _:

                print("Unknown entity trying to communicate.")
                err_msg = {
                    "error" : "Connection must be established with hello / hello_server message first."
                }
                await self.send(websocket, err_msg)
    
    async def client_list_request_handler(self, websocket: ServerConnection) -> None:
        """
        Generates a client list and sends to the websocket that requested it.
        """

        if not self.existing_connection(websocket):
            err_msg = {
                "error" : "Must establish connection first before asking for client list"
            }
            await self.send(websocket, err_msg)
            await websocket.close(code=1000)
            return

        # Generate client list
        all_clients = []

        for address, clients in self.all_clients.items():
            tmp = {
                "address" : address,
                "clients" : clients
            }
            all_clients.append(tmp)

        own_clients = {
            "address" : f"{self.host}:{self.port}",
            "clients" : [client.public_key for client in self.clients]
        }
        
        servers = all_clients + [own_clients]

        # Create client_list message
        client_list = {
            "type" : "client_list",
            "servers" : servers
        }

        await self.send(websocket, client_list)

    def print_all_clients(self) -> None:
        """
        FOR DEBUGGING - print all clients
        """
        # other_servers_clients = [
        #     {
        #         "address" : address,
        #         "clients" :  client_list
        #     } for address, client_list in self.all_clients.items()
        # ]

        all_clients = []

        for address, clients in self.all_clients.items():
            tmp = {
                "address" : address,
                "clients" : clients
            }
            all_clients.append(tmp)

        own_clients = {
            "address" : f"{self.host}:{self.port}",
            "clients" : [client.public_key for client in self.clients]
        }
        
        servers = all_clients.append(own_clients)

        print(f"All Clients: {servers}")


    def client_update_handler(self, websocket: ServerConnection, message: dict) -> None:
        """
        Updates the client list for a particular server
        """
        print("client_update received")
        updated_client_list = message['clients']

        # client udpates should only come from known neighbours
        existing_connection = self.existing_connection(websocket)
        if existing_connection is None:
            # Unknown server is sending data
            print("Unknown server is requesting data")
        server_to_update = existing_connection.server_addr

        # Update clients for particular server.
        self.all_clients[server_to_update] = updated_client_list
        print(self.all_clients)
        

    async def client_update_request_handler(self, websocket: ServerConnection):
        """
        Handles the 'client_update_request' message.
        """
        print("client_update_request received")
        client_update = {
            "type" : "client_update",
            "clients" : [client.public_key for client in self.clients]
        }

        await self.send(websocket, client_update)

    async def signed_data_handler(self, websocket: ServerConnection, message: dict) -> None:
        """
        Handles all signed_data
        """
        try:
            signed_data = message['data']
            signed_data_type = signed_data['type']

        except KeyError:
            err_msg = {
                "error" : "Invalid signed_data format"
            }
            await self.send(websocket, err_msg)
            await websocket.close(code=100)
            return

        
        if not self.existing_connection(websocket):
            match signed_data_type:
                case "server_hello":
                    await self.signed_data_handler_hello_server(websocket, message)

                case "hello":
                    await self.signed_data_handler_hello(websocket, message)

                case _:

                    err_msg = {
                        "error" : "Please send a hello message first to establish connection"
                    }

                    await self.send(websocket, err_msg)
                    await websocket.close(code=1000)
            return

        
        # Handle each type of signed_data
        match signed_data_type:
            case "chat":
                # Route message to destination server
                await self.relay_chat(websocket,message)
            case "public_chat":
                # Broadcast to all clients.
                await self.relay_public_chat(websocket, message)
            case _:
                err_msg = {
                    "error" : "Invalid data type from established connection"
                }
                await self.send(websocket, err_msg)


    async def relay_chat(self, websocket, message: dict) -> None:
        """
        Relay chat to required destination servers
        """
        data = message ["data"]
        destination_servers = data["destination_servers"]
        neighbour_addresses = {}
        for neighbour in self.neighbour_connections:
            neighbour_addresses[neighbour.server_addr] = neighbour

        for destination_server in destination_servers:

            if destination_server in self.server_address: # Comparison includes ws:// or wss://
                for client in self.clients:
                    await client.send(message)
                continue
            
            if websocket == neighbour_addresses[destination_server].websocket:
                # Do not send back to the server which you received the public chat from
                continue

            if destination_server in neighbour_addresses.keys():
                await neighbour_addresses[destination_server].send(message)
            else:
                print("Unknown Destination server.")


    async def relay_public_chat(self, websocket: ServerConnection, message: dict) -> None:
        """
        Broadcasts the message to all clients in every server.
        """
        
        # Send public Chat Message to all clients.
        for client in self.clients:
            await client.send(message)
        
        # Send public Chat Message to all servers.
        for server in self.neighbour_connections:
            # print(server.websocket != websocket)
            print(server.server_addr)
            if server.websocket != websocket:
                # Do not send back to the server which you received the public chat from
                pass


    async def signed_data_handler_hello(self, websocket: ServerConnection, message: dict[str, str]) -> None:
        """
        Adds a client connection to maintain
        """

        signed_data = message['data']

        # Check if websocket is an active connection. Reject hello if so.
        active_connections = [client.websocket for client in self.clients]

        if websocket in active_connections:
            err_msg = {
                "error" : "Connection exists. Unable to process hello message"
            }
            await self.send(websocket, err_msg)
            return

        public_key = signed_data['public_key']
        client_connection = OlafClientConnection(websocket, public_key)
        self.clients.add(client_connection)
        
        await self.send_client_update_to_neighbours()
    
    async def send_client_update_to_neighbours(self) -> None:
        """
        Generates a client_update_message and sends to neighbours.
        """
        client_update = {
            "type" : "client_update",
            "clients" : [client.public_key for client in self.clients]
        }

        for neighbour in self.neighbour_connections:
            await neighbour.send(client_update)
    
    async def signed_data_handler_hello_server(self, websocket: ServerConnection, message: dict) -> None:
        """
        Handles the 'hello_server' message
        """
        signed_data = message['data']
        public_key = "default_key"
        server_addr = signed_data['sender']
        # websocket = await websockets.connect(server_addr)
        neighbour_connection = OlafServerConnection(websocket, server_addr, public_key)
        self.neighbour_connections.add(neighbour_connection)
        
        print(f"New neighbour added: {server_addr}")


    async def connect_to_server(self, server_addr: str, public_key: str) -> None:
        """
        Connects to another server
        """
        try:
            websocket = await websockets.connect(server_addr)
            
            active_neighbour_connections = [neighbour.server_addr for neighbour in self.neighbour_connections]
            if server_addr in active_neighbour_connections:
                print(f"{server_addr} already a part of the neighbourhood. ")
                return
            
            neighbour_connection = OlafServerConnection(websocket, server_addr, public_key)
           
            self.neighbour_connections.add(neighbour_connection)
            print(f"New neighbour added: {neighbour_connection.server_addr}")
            
            # Send server_hello upon established connection
            signed_data = {
                "type" : "signed_data",
                "data" : None
            }

            server_hello = {
                "type" : "server_hello",
                "sender" : f"{self.host}:{self.port}"
            }
            signed_data["data"] = server_hello
            await neighbour_connection.send(signed_data)

            client_update_request = {
                "type" : "client_update_request"
            }

            await neighbour_connection.send(client_update_request)

        except Exception as e:
            print(f"Failed to connect to {server_addr}: {e}")
            # Wait 10 secs before trying again.
            time.sleep(10)
            await self.connect_to_server(server_addr, public_key)

    async def start_server(self) -> None:
        """
        Start the websocket server
        """

        self.server = await serve(self.recv, self.host, self.port, ping_interval=20, ping_timeout=10)
        print(f"WebsocketServer started on ws://{self.host}:{self.port}")

        for neighbour_addr, neighbour_public_key in self.neighbours.items():
            print(f"Scheduling connection to {neighbour_addr}...")
            # asyncio.create_task(self.connect_to_server(neighbour_addr, neighbour_public_key))
            await self.connect_to_server(neighbour_addr,neighbour_public_key)

        await self.server.wait_closed()

    def run(self) -> None:
        """
        Run the websocket server
        """
        asyncio.get_event_loop().run_until_complete(self.start_server())
        asyncio.get_event_loop().run_forever()


if __name__ == "__main__":
    neighbours = {
        "ws://localhost:8001" : "server2_key"
    }
    ws_server = WebSocketServer('localhost', 9000)
    ws_server.run()