import asyncio
import websockets
import json
import os
import sys
import time
import logging
import base64
from aiohttp import web
from websockets.asyncio.server import serve, ServerConnection

# Modify sys.path in the script to recognise packages in root dir.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from security.security_module import Encryption

# Required Directories
UPLOAD_DIR = 'uploads/'
KEYS_DIR = 'server_keys/'

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(KEYS_DIR, exist_ok=True)

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
    def __init__(self, bind_address: str, host: str, ws_port: int, http_port: int, neighbours_list: list):

        
        # Self related info
        self.bind_address = bind_address
        self.host = host
        self.port = ws_port
        self.server_address = f"ws://{self.host}:{self.port}"
        self.server_name = f"{self.host}:{self.port}"
        self.server = None
        self.http_port = http_port
        self.counter = 0
        self.encryption = Encryption()

        # Configure the logger
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        logging.getLogger('websockets.server').setLevel(logging.ERROR)
        logging.getLogger('aiohttp.access').setLevel(logging.ERROR)
        self.logger = logging.getLogger(f"{self.host}:{self.port}")

        # Load private and public keys
        self.private_key, self.public_key = self.load_keys()

        # Client related info
        self.clients = set()
        self.all_clients = {}

        # Server related info
        self.neighbour_connections = set()
        self.neighbours_list = neighbours_list
        self.neighbours = self.load_neighbour_keys()


        self.loop = asyncio.get_event_loop()
    
    def load_keys(self) -> tuple:
        """
        This function loads the private and public keys from a file onto the server.
        If no keys are found, it generates a pair and saves them to files for future use.

        Returns:
            tuple: A tuple containing the loaded or generated private and public keys.
        """
        private_key_path = os.path.join(KEYS_DIR, f"{self.host}_{self.port}_private_key.pem")
        public_key_path = os.path.join(KEYS_DIR, f"{self.host}_{self.port}_public_key.pem")

        if os.path.exists(private_key_path) and os.path.exists(public_key_path):

            with open(private_key_path, 'rb') as f:
                self.private_pem = f.read()
            with open(public_key_path, 'rb') as f:
                self.public_pem = f.read()

            private_key = self.encryption.load_private_key(self.private_pem)
            public_key = self.encryption.load_public_key(self.public_pem)

            self.logger.info("Key pair successfully loaded from files.")

        else:
            self.public_pem, self.private_pem = self.encryption.generate_rsa_key_pair()

            with open(private_key_path, 'wb') as f:
                f.write(self.private_pem)

            with open(public_key_path, 'wb') as f:
                f.write(self.public_pem)

            private_key = self.encryption.load_private_key(self.private_pem)
            public_key = self.encryption.load_public_key(self.public_pem)

            self.logger.info("Key pair successfully generateed and saved to files.")

        return private_key, public_key

    def get_server_host_port(self, server_name) -> tuple:
        """
        Retrieves the host and port of from a servername.

        Args:
            server_name: string of the neighbour's name
        
        Returns:
            tuple of host, port
        """
        try:
            server_host = server_name.split(':')[0]
            server_port = server_name.split(':')[1]
        except IndexError:
            server_host = server_name
            server_port = 80 #default
        
        return server_host, server_port

    def load_neighbour_keys(self) -> dict:
        """
        This functions loads the neighbours public keys from a file. 
        These must be shared before starting any servers in the neighbourhood.
        
        Returns:
            dictionary of { server_addr : public_key }
        """
        neighbours = {}

        if len(self.neighbours_list) < 1:
            return neighbours
        
        try:
            for server_name in self.neighbours_list:
                
                if server_name == self.server_name:
                    continue
                
                server_host, server_port = self.get_server_host_port(server_name)

                public_key_path = os.path.join(KEYS_DIR, f"{server_host}_{server_port}_public_key.pem")
                with open(public_key_path, 'rb') as f:
                    self.public_pem = f.read()

                public_key = self.encryption.load_public_key(self.public_pem)
                neighbours[server_name] = public_key

                self.logger.info(f"Public key successfully loaded for {server_name} from file.")

        except Exception as e:
            self.logger.critical(f"Exiting server due to reason: {e}", exc_info=True)
            sys.exit()

        return neighbours


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

                    # Handle all messages
                    await self.handler(websocket, data)

                except json.decoder.JSONDecodeError:
                    self.logger.info(f"Failed to JSON decode message: {message}")
                    err = {
                        "error" : "Message received not in JSON string."
                    }
                    await self.send(websocket, err)
            except websockets.ConnectionClosedOK:
                await self.disconnect(websocket)
                break
            except websockets.exceptions.ConnectionClosed as conn_closed:
                # Remove from clients / neighbours list
                await self.disconnect(websocket)
                break
                        
    async def disconnect(self, websocket: ServerConnection) -> None:
        """
        Handles a disconnection
        """
        tmp = []
        for client in self.clients:

            if websocket == client.websocket:
                tmp.append(client)

        for neighbour in self.neighbour_connections:
            if websocket == neighbour.websocket:
                tmp.append(neighbour)
        
        for conn in tmp:
            if conn in self.clients:
                self.clients.remove(conn)
                await self.send_client_update_to_neighbours()
                self.logger.info(f"Client Disconnected: {conn.public_key}")
            elif conn in self.neighbour_connections:
                self.neighbour_connections.remove(conn)
                self.logger.warning(f"Neighbour Disconnected: {conn.server_addr}")
                        
        await self.broadcast_client_list()
        await websocket.close(code=1000)


    
    async def send(self, websocket: ServerConnection, data: dict) -> None:
        """
        Send the data as serialised message to websocket
        """
        message = json.dumps(data)
        await websocket.send(message)
    
    def message_fits_standard(self, message: dict) -> bool:
        """
        Validates that the message has the required fields according to its type.
        Returns True if valid, False otherwise.
        """

        def has_required_fields(msg, required_fields):
            """
            Helper function to check if required fields are present.
            """
            for field in required_fields:
                if field not in msg:
                    self.logger.error(f"Validation Error: Message missing required field '{field}'.")
                    return False
            return True

        try:
            # Determine message type
            message_type = message.get("type") or message.get("data", {}).get("type")
            if not message_type:
                self.logger.error("Validation Error: Message missing 'type' field.")
                return False

            # Define required fields based on message_type
            message_type_to_fields = {
                "signed_data": ["data", "counter", "signature"],
                "client_list_request": ["type"],
                "client_update": ["type", "clients"],
                "client_list": ["type", "servers"],
                "client_update_request": ["type"]
            }

            data_type_to_fields = {
                "hello": ["type", "public_key"],
                "chat": ["type", "destination_servers", "iv", "symm_keys", "chat"],
                "public_chat": ["type", "sender", "message"],
                "server_hello": ["type", "sender"]
            }

            # Validate required fields for top-level message
            if message_type in message_type_to_fields:
                if not has_required_fields(message, message_type_to_fields[message_type]):
                    return False

                # Check nested data if message_type is "signed_data"
                if message_type == "signed_data":
                    data = message.get("data", {})
                    data_type = data.get("type")
                    if data_type in data_type_to_fields:
                        return has_required_fields(data, data_type_to_fields[data_type])
                    else:
                        self.logger.error(f"Validation Error: Unknown signed data type '{data_type}'.")
                        return False

            else:
                self.logger.error(f"Validation Error: Unknown message type '{message_type}'.")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Validation Error: Exception occurred - {e}")
            return False

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
            self.logger.info(f"Unknown message type received: {message}")
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
                await self.client_update_handler(websocket, message)
            case "client_update_request":
                await self.client_update_request_handler(websocket)
            case _:

                self.logger.info("Unknown party attempt to communicate")
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

    
    async def client_update_handler(self, websocket: ServerConnection, message: dict) -> None:
        """
        Updates the client list for a particular server
        """
        updated_client_list = message['clients']

        # client udpates should only come from known neighbours
        existing_connection = self.existing_connection(websocket)
        if existing_connection is None:
            # Unknown server is sending data
            self.logger.warning("Unknown server is requesting data")
        server_to_update = existing_connection.server_addr

        # Update clients for particular server.
        self.all_clients[server_to_update] = updated_client_list

        await self.broadcast_client_list()
        

    async def client_update_request_handler(self, websocket: ServerConnection):
        """
        Handles the 'client_update_request' message.
        """
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
                self.logger.warning(f"Unknown destination server {destination_server} listed in chat message. Check if neighbourhood is complete.")


    async def relay_public_chat(self, websocket: ServerConnection, message: dict) -> None:
        """
        Broadcasts the message to all clients in every server.
        """
        
        # Send public Chat Message to all clients.
        for client in self.clients:
            await client.send(message)
        
        # Send public Chat Message to all servers.
        for server in self.neighbour_connections:
            if server.websocket == websocket:
                # Do not send back to the server which you received the public chat from
                continue
            
            await self.send(server.websocket, message)


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
        self.logger.info(f"New Client Added: {public_key}")

        await self.send_client_update_to_neighbours()
        await self.broadcast_client_list()
        
        
    async def broadcast_client_list(self) -> None:
        """
        Broadcasts the client list to all clients.
        """
                
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
                
        for client in self.clients:
            await client.send(client_list)
    
    
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
        counter = message['counter']
        public_key = "default_key"
        server_addr = signed_data['sender']

        if 'ws://' in server_addr:
            server_addr = server_addr[5:]
        elif 'wss://' in server_addr:
            server_addr = server_addr[6:]

        connection = self.existing_connection(websocket)

        if not connection:            
            neighbour_connection = OlafServerConnection(websocket, server_addr, public_key)
            neighbour_connection.counter = counter
            self.neighbour_connections.add(neighbour_connection)

            self.logger.info(f"Successfully added neighbour {server_addr}")
        else:
            if counter <= connection.counter:
                # Message is a replay
                await self.disconnect(websocket)
                return
            self.logger.warning(f"Neighbour {connection.server_addr} is sending a hello_server message with a counter > 1.")
        

    def build_signed_data(self, data: dict) -> dict:
        """
        Build a signed message with the given data
        """
        message = {
            "data": data,
            "counter": self.counter
        }

        message_str = json.dumps(message, separators=(',', ':'), sort_keys=True)
        message_bytes = message_str.encode('utf-8')

        # Sign the message
        signature = self.encryption.sign_message(message_bytes, self.private_pem)
        signature_base64 = base64.b64encode(signature).decode('utf-8')

        # Prepare the signed message
        signed_data = {
            "type": "signed_data",
            "data": data,
            "counter": self.counter,
            "signature": signature_base64
        }

        return signed_data
    
    def build_server_hello(self):
        """
        Send a hello message to the server.
        
        Increments message counter and sends public key as part of the hello message.
        """
        
        self.counter += 1
        
        message_data = {
            "type": "server_hello",
            "sender": f"{self.host}:{self.port}"  
        }

        server_hello = self.build_signed_data(message_data)

        return server_hello

    async def connect_to_server(self, server_addr: str, public_key: str) -> None:
        """
        Connects to another server
        """
        try:
            websocket = await websockets.connect(f"ws://{server_addr}")
        
            if 'ws://' in server_addr:
                base_server_addr = server_addr[5:]
            elif 'wss://' in server_addr:
                base_server_addr = server_addr[6:]
            else:
                base_server_addr = server_addr

            active_neighbour_connections = [neighbour.server_addr for neighbour in self.neighbour_connections]

            if base_server_addr in active_neighbour_connections:
                self.logger.info(f"{server_addr} already a part of the neighbourhood. ")
                return
            
            neighbour_connection = OlafServerConnection(websocket, base_server_addr, public_key)
            self.neighbour_connections.add(neighbour_connection)
            
            # Send server_hello upon established connection
            server_hello = self.build_server_hello()
            client_update_request = {
                "type" : "client_update_request"
            }

            await neighbour_connection.send(server_hello)
            await neighbour_connection.send(client_update_request)

            self.logger.info(f"New neighbour added: {neighbour_connection.server_addr}")
            asyncio.ensure_future(self.recv_from_server(websocket))

        except Exception as e:
            self.logger.error(f"Failed to connect to {server_addr}: {e}", exc_info=True)
            # Wait 5 secs before trying again.
            time.sleep(5)
            await self.connect_to_server(server_addr, public_key)

    async def recv_from_server(self, websocket: ServerConnection) -> None:
        """
        Deal with messages coming from server.
        """
        try: 
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self.handler(websocket, data)
                except json.JSONDecodeError:
                    self.logger.error(f"Unkown Message Format: { message }. Unable to handle message")
        except Exception as e:
            self.logger.error(f"Exception occured: {e}")
        finally:
            await self.disconnect(websocket)

    async def start_server(self) -> None:
        """
        Start the websocket server
        """

        self.server = await serve(self.recv, self.bind_address, self.port, ping_interval=20, ping_timeout=10)

        app = web.Application()
        app.router.add_post('/api/upload', self.handle_file_upload)
        app.router.add_get('/files/{filename}', self.handle_file_download)
        app.router.add_get('/files', self.handle_file_list)
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', self.http_port)
        await site.start()

        self.logger.info(f"Websocket Server started on ws://{self.host}:{self.port}")
        self.logger.info(f"HTTP Server started on http://{self.host}:{self.http_port}/")
        
        asyncio.ensure_future(self.connect_to_neighbours())
        
        await asyncio.Future()

    async def connect_to_neighbours(self):
        """
        Connect to neighbours.
        """
        # Wait for servers to start up
        self.logger.info("Waiting 5 secs for servers to start up.")
        time.sleep(5)
        for neighbour_addr, neighbour_public_key in self.neighbours.items():
            self.logger.info(f"Scheduling connection to {neighbour_addr}...")
            await self.connect_to_server(neighbour_addr,neighbour_public_key)


    async def handle_file_upload(self, request):
        """
        Add endpoint for file uploads
        """

        reader = await request.multipart()
        field = await reader.next()
        if not field or field.name != 'file':
            return web.json_response({'error': 'No file field in request'}, status=400)
        filename = field.filename
        max_file_size = 10 * 1024 * 1024
        size = 0

        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, 'wb') as f:
            while True:
                chunk = await field.read_chunk()
                if not chunk:
                    break
                size += len(chunk)
                if size > max_file_size:
                    os.remove(filepath)
                    return web.json_response({'error': 'File size exceeds limit'}, status=413)
                f.write(chunk)

        # The file URL must be localhost since our client is not dockerised.
        file_url = f"http://localhost:{self.http_port}/files/{filename}"
        return web.json_response({'file_url': file_url})
    
    async def handle_file_download(self, request):
        """
        Serve filename 
        """
        filename = request.match_info['filename']
        filepath = os.path.join(UPLOAD_DIR, filename)
        if not os.path.exists(filepath):
            return web.HTTPNotFound()

        # Serve the file as an HTTP response
        return web.FileResponse(filepath)
    
    async def handle_file_list(self, request):
        """
        Logbook of uploaded files
        """
        files = os.listdir(UPLOAD_DIR)  
        files.sort()  

        # Create a JSON response with the list of files
        return web.json_response({'files': files})


if __name__ == "__main__":

    from dotenv import load_dotenv
    load_dotenv()
    
    # Neighbourhood list contains all the servers in the neighbourhood.
    # Server addresses can take the form:
    # - 10.0.0.27:8001
    # - my.awesomeserver.net
    # - localhost:666
    try:
        NEIGHBOURS = os.getenv('NEIGHBOURS').split(',')
    except AttributeError:
        NEIGHBOURS = []
    WS_PORT = os.getenv('WS_PORT')
    HTTP_PORT = os.getenv('HTTP_PORT')
    BIND_ADDRESS = os.getenv('BIND_ADDRESS', '0.0.0.0')
    HOST = os.getenv('HOST')
 
    ws_server_1 = WebSocketServer(bind_address=BIND_ADDRESS, host=HOST, ws_port=WS_PORT, http_port=HTTP_PORT, neighbours_list=NEIGHBOURS)
    
    try:
        asyncio.run(ws_server_1.start_server())
    except KeyboardInterrupt:
        print("Ctrl + C Detected.. Shutting down servers")