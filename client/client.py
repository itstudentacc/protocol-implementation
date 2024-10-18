import json
import base64
import asyncio
import aioconsole
import websockets
import logging
import aiohttp
import sys
import os
import html
from urllib.parse import urlparse
from nickname_generator import generate_nickname

# Modify sys.path in the script to recognise packages in root dir.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from security.security_module import Encryption

GREEN = "\033[92m"
RESET = "\033[0m"

# Configure the logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Client:
    def __init__(self):
        self.server_address = None
        self.http_port = None  
        self.encryption = Encryption()
        self.connection = None
        self.counter = 0
        self.public_key = None
        self.private_key = None
        self.public_key_pem = None
        self.private_key_pem = None
        self.received_messages = []  # Fixed typo
        self.clients = {} # {fingerprint: public_key}
        self.server_fingerprints = {} # {fingerprint: server_address}
        self.nicknames = {} # {fingerprint: nickname}    
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
    async def start(self):
        """
        Initializes the client by generating RSA key pairs, prompting for server 
        address and HTTP port, connecting to the WebSocket server, and starting the event loop.

        Tasks:
        - Generates and loads RSA key pair.
        - Prompts user for WebSocket server address and HTTP port.
        - Establishes WebSocket connection and runs the input prompt.

        Args:
            self: Instance containing encryption methods and connection details.
        """
        
        # Generate RSA key pair
        self.public_key_pem, self.private_key_pem = self.encryption.generate_rsa_key_pair()
        self.public_key = self.encryption.load_public_key(self.public_key_pem)
        self.private_key = self.encryption.load_private_key(self.private_key_pem)
        self.my_nickname = generate_nickname(self.encryption.generate_fingerprint(self.public_key_pem))
        # Prompt for server address
        chosen_server = await aioconsole.ainput("Enter WebSocket server address (e.g., localhost:9000): ")
        self.server_address = f"ws://{chosen_server}"
        
        # Prompt for HTTP port to use for file uploads
        http_port = await aioconsole.ainput("Enter server HTTP port (e.g., 9001): ")
        self.http_port = http_port

        try:
            await self.connect()
        except Exception as e:
            print(f"Failed to connect: {e}")
            return

        print(f"\nYour nickname is: {self.my_nickname}\n")
        await self.input_prompt()
        self.loop.run_forever()

    def parse_message(self, message):
        """
        Parses an incoming message string into a JSON object.

        Args:
        message: The message string to be parsed.

        Returns:
        A tuple containing the parsed JSON object and None on success, 
        or None and an error message if parsing fails.
        """
        try:
            message_dict = json.loads(message)
            return message_dict, None
        except json.JSONDecodeError as e:
            return None, f"Error parsing JSON: {str(e)}"

    def build_signed_data(self, data):
        """
        Build a signed message with the given data
        """
        message = {
            "data": data,
            "counter": self.counter
        }

        message_json = json.dumps(message, separators=(',', ':'), sort_keys=True)
        message_bytes = message_json.encode('utf-8')

        # Sign the message
        signature = self.encryption.sign_message(message_bytes, self.private_key_pem)
        signature_base64 = base64.b64encode(signature).decode('utf-8')

        # Prepare the signed message
        signed_data = {
            "type": "signed_data",
            "data": data,
            "counter": self.counter,
            "signature": signature_base64
        }

        return signed_data
    
    def print_clients(self):
        """
        Print the connected clients
        """
        
        print("\nConnected clients:\n")
        
        if not self.clients:
            print("No clients connected")
        
        for fingerprint, public_key in self.clients.items():
            if fingerprint not in self.nicknames:
                nickname = generate_nickname(fingerprint)
                self.nicknames[fingerprint] = nickname
            else:
                nickname = self.nicknames[fingerprint]
            
            if fingerprint == self.encryption.generate_fingerprint(self.public_key_pem):
                print (f"   - {nickname} (me)")
            else:
                print (f"   - {nickname}")
        
        print("\n")

    async def upload_file(self, file_path):
        """
        Uploads a file to the server.

        Args:
            file_path: The path to the file to be uploaded.

        Returns:
            The URL of the uploaded file if successful, or None if the upload fails.
        """
        
        # Parse server_address to extract hostname
        parsed_url = urlparse(self.server_address)
        server_hostname = parsed_url.hostname
        
        # Construct the URL using the hostname and the HTTP port
        url = f'http://{server_hostname}:{self.http_port}/api/upload'
        
        async with aiohttp.ClientSession() as session:
            with open(file_path, 'rb') as f:
                form = aiohttp.FormData()
                form.add_field('file', f, filename=os.path.basename(file_path))
                async with session.post(url, data=form) as resp:
                    if resp.status == 200:
                        json_response = await resp.json()
                        file_url = json_response.get('file_url')
                        return file_url
                    else:
                        error_message = await resp.text()
                        logger.error(f"File upload failed with status {resp.status}: {error_message}")
                        return None
                    
    async def upload_and_share_file(self, file_path, recipients):
        """
        Uploads a file and shares its URL with specified recipients.

        Args:
            file_path: The path to the file to be uploaded.
            recipients: A list of recipients to share the file with, 
                    including 'global' for public sharing.

        Returns:
            None
        """
        file_url = await self.upload_file(file_path)
        if file_url:
            message_text = f"[File] {file_url}"
            # Send to global chat if 'global' is in recipients
            if 'global' in recipients:
                await self.send_public_chat(message_text)
            # Send to private recipients
            private_recipients = [r for r in recipients if r != 'global']
            if private_recipients:
                await self.send_chat(private_recipients, message_text)
        else:
            print("Failed to upload and share file.")
    
    async def get_uploaded_files(self):
        """
        Retrieve the list of uploaded files from the server
        
        Constructs a request to the server to retrieve the list of uploaded files.
        
        Returns:
            None
        """
        
        
        # Parse server_address to extract hostname
        parsed_url = urlparse(self.server_address)
        server_hostname = parsed_url.hostname

        # Construct the URL using the hostname and the HTTP port
        url = f'http://{server_hostname}:{self.http_port}/files'

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        html_content = await resp.text()
                        print("Uploaded files:")
                        print(html_content)  # Display the HTML content for now
                    else:
                        print(f"Failed to retrieve file list: {resp.status}")
            except aiohttp.ClientConnectorError as e:
                print(f"Failed to connect to server: {e}")

            
    async def input_prompt(self):
        """
        Prompt the user for input commands and processes them
        
        Continuously listens for user commands to perform actions such as:
        - Uploading and sharing files
        - Sending public and private chat messages
        - Requesting a list of clients
        - Retrieving uploaded files
        - Exiting the application

        Returns:
            None
        """
        while True:
            message = await aioconsole.ainput("Enter message type (public, chat, clients, /transfer, files) (exit to exit): ")
            if message.lower().startswith("/transfer"):
                parts = message.split()
                if len(parts) < 2:
                    print("Usage: /transfer <file> [<recipients>]")
                    continue

                file_path = parts[1]
                recipients = parts[2:] if len(parts) > 2 else ['global']
                if os.path.exists(file_path):
                    await self.upload_and_share_file(file_path, recipients)
                else:
                    print("File does not exist.")
            elif message.lower() == "public":
                chat = await aioconsole.ainput("Enter public chat message: ")
                chat = chat.strip()
                chat = html.escape(chat)
                if not chat:
                    print("Chat message cannot be empty")
                    continue
                await self.send_public_chat(chat)
            elif message.lower() == "chat":
                recipients = await aioconsole.ainput("Enter recipient names, separated by commas: ")
                if not recipients:
                    print("Recipients cannot be empty")
                    continue
                chat = await aioconsole.ainput("Enter chat message: ")
                chat.strip()
                chat = html.escape(chat)
                if not chat:
                    print("Chat message cannot be empty")
                    continue
                await self.send_chat(recipients.split(","), chat)
            elif message.lower() == "clients":
                await self.request_client_list()
                self.print_clients()
            elif message.lower() == "files":
                await self.get_uploaded_files()
            elif message.lower() == "exit":
                await self.close()
            elif message.lower() == "boot":
                client = await aioconsole.ainput("Enter name of client to kick: ")
                reason = await aioconsole.ainput("Enter reason for booting: ")
                await self.kick_client(client, reason)
            elif message.lower() == "expose":
                await self.send_expose_request()
            else:
                print("Invalid command.")
                
    async def connect(self):
        """
        Connects to the WebSocket server
        
        Establishes a connection to the server, sends greeting message,
        and starts listening for incoming messages.
        """
        
        try:
            self.connection = await websockets.connect(self.server_address)
            print(f"Connected to {self.server_address}")

            await self.send_hello()

            # Listen for incoming messages
            asyncio.ensure_future(self.receive())
            

        except Exception as e:
            print(f"Failed to connect: {e}")
            sys.exit(1)

    async def close(self):
        """
        Closes the connection to the WebSocket server
        
        Attempts to close connection gracefully and exits the application.
        """
        
        if self.connection:
            try:
                await self.connection.close()
                print("Connection closed")
                exit(0)
            except Exception as e:
                print(f"Failed to close connection: {e}")
            finally:
                self.connection = None
                
            tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
            for task in tasks:
                task.cancel()
            
            await asyncio.gather(*tasks, return_exceptions=True)
            
            loop = asyncio.get_event_loop()
            loop.stop()

    async def send_hello(self):
        """
        Send a hello message to the server.
        
        Increments message counter and sends public key as part of the hello message.
        """
        
        self.counter += 1
        
        public_pem = self.public_key_pem.decode('utf-8')
        private_pem = self.private_key_pem.decode('utf-8')
        

        message_data = {
            "type": "hello",
            "public_key": public_pem,  
            "private_key": private_pem,
            "username": self.my_nickname
        }

        message = self.build_signed_data(message_data)

        
        json_message = json.dumps(message)
        
        await self.send(json_message)
        

    async def send_public_chat(self, chat):
        """
        Sends a public chat message
        
        Increments the message counter and sends a signed message
        containing the chat message.
        
        Args:
            chat: The chat message to be sent.

        """
        self.counter += 1
        
        fingerprint = self.encryption.generate_fingerprint(self.public_key_pem)

        message_data = {
            "type": "public_chat",
            "sender": fingerprint,
            "message": chat
        }

        message = self.build_signed_data(message_data)

        message_json = json.dumps(message)
        
        await self.send(message_json)
        print(f"{GREEN}\nSent public chat message: {chat}\n{RESET}")
        
    async def kick_client(self, client, reason):
        """
        Kick a client from the server
        
        This method sends a message to the server to kick a client.
        """
        self.counter += 1
        
        if client not in self.nicknames.values():
            print("Client not found")
            return
        
        print(f"Kicking client: {client}")
        
        message = {
            "type": "kick",
            "client": client,
            "reason": reason
        }
        
        message_json = json.dumps(message)
        await self.send(message_json)
        
    async def rcv_kick(self, message):
        """
        Receive a kick message from the server
        
        This method processes a kick message from the server and prints the reason.
        
        """
        
        client = message.get("client")
                        
        if client == generate_nickname(self.encryption.generate_fingerprint(self.public_key_pem)):
            reason = message.get("reason")
        
            print(f"\nYou have been kicked for the following reason: {reason}\n")
        
            await self.close()
        else:
            print(f"Enter message type (public, chat, clients, /transfer, files) (exit to exit):")
            pass
        
        
    async def send_chat(self, recipients_nicknames, chat):
        """
        Send a chat message to the specified recipients.
        
        Validates the recipients, encrypts the chat message, and
        sends it to the appropriate servers.
        
        Args:
            recipients_nicknames: A list of recipient nicknames.
            chat: The chat message to be sent.
        
        """
        
        recipients = [fingerprint for fingerprint, nickname in self.nicknames.items() if nickname in recipients_nicknames]
                    
        valid_recipients = [fingerprint for fingerprint in recipients if fingerprint in self.clients]
        
        if not valid_recipients:
            print("No valid recipients")
            return
            
        recipient_public_keys = []
        destination_servers_set = set()
        
        for fingerprint in valid_recipients:
            server_address = self.server_fingerprints.get(fingerprint)
            if server_address:
                destination_servers_set.add(server_address)
                recipient_public_keys.append(self.clients[fingerprint])
            else:
                print(f"No server address for fingerprint: {fingerprint}")
                return
            
        destination_servers = list(destination_servers_set)
        if not destination_servers:
            print("No destination servers")
            return
        
        self.counter += 1
        
        aes_key = self.encryption.generate_aes_key()
        iv = self.encryption.generate_iv()
        iv_base64 = base64.b64encode(iv).decode('utf-8')
        
        sender_fingerprint = self.encryption.generate_fingerprint(self.public_key_pem)
        participants = [sender_fingerprint] + [self.encryption.generate_fingerprint(public_key) for public_key in recipient_public_keys]
        
        chat_data = {
            "chat": {
                "participants": participants,
                "message": chat
            },
        }
        chat_data_json = json.dumps(chat_data)
        
        ciphertext, tag = self.encryption.encrypt_aes_gcm(chat_data_json.encode('utf-8'), aes_key, iv)
        chat_base64 = base64.b64encode(ciphertext + tag).decode('utf-8')
        
        symm_keys = []
        for public_key in recipient_public_keys:
            public_key_pem = self.encryption.load_public_key(public_key)
            encrypted_symm_key = self.encryption.encrypt_rsa(aes_key, public_key_pem)
            encrypted_symm_key_base64 = base64.b64encode(encrypted_symm_key).decode('utf-8')
            symm_keys.append(encrypted_symm_key_base64)
            
        signed_data = {
            "type": "chat",
            "destination_servers": destination_servers,
            "iv": iv_base64,
            "symm_keys": symm_keys,
            "chat": chat_base64
        }
        
        signed_data = self.build_signed_data(signed_data)
        
        message_json = json.dumps(signed_data)
        await self.send(message_json)
        print(f"{GREEN}\nSent chat message to {', '.join(recipients_nicknames)}: {chat}\n{RESET}")


    async def request_client_list(self):
        """
        Request the list of connected clients from the server
        """
        message = {
            "type": "client_list_request"
        }

        message_json = json.dumps(message)
        await self.send(message_json)
        

    async def receive(self):
        try:
            async for message in self.connection:
                message_dict, error = self.parse_message(message)
                if error:
                    print(f"Error parsing message: {error}")
                    continue

                await self.handle_message(message_dict)
        except websockets.ConnectionClosed:
            print("Connection closed")
            sys.exit(1)

    async def handle_message(self, message):
        """
        Processes incoming messages based on their type.
        
        Extracts the message type and calls the appropriate handler function.
        
        Args:
            message: The incoming message to be processed.
            
        """
        
        message_type = message.get("type") or message.get("data", {}).get("type")
        
        if message_type == "signed_data":
            message_type = message.get("data", {}).get("type")

        if message_type == "public_chat":
            await self.handle_public_chat(message)
        elif message_type == "client_list":
            await self.handle_client_list(message)
        elif message_type == "chat":
            await self.handle_chat(message)
        elif message_type == "margarita_order":
            await self.handle_margarita_order(message)
        elif message_type == "margarita_delivery":
            await self.handle_margarita_delivery(message)
        elif message_type == "kick":
            await self.rcv_kick(message)
        else:
            print(f"Unknown message type: {message_type}")

    async def handle_public_chat(self, message):
        """
        Processes a public chat message.
        
        Extracts the sender fingerprint and chat message from the data,
        and prints the message to the console.
        
        Args:
            message: The incoming message containing the chat data.
        """
        data = message.get("data")  
        
        sender_fingerprint = data.get("sender")
        chat = data.get("message")
        self.received_messages.append({
            "sender": sender_fingerprint,
            "message": chat
        })
        
        sender_nickname = self.nicknames.get(sender_fingerprint)
        
        # check if sender is me
        if sender_fingerprint == self.encryption.generate_fingerprint(self.public_key_pem):
            sender_nickname = "me"
        
        print(f"{GREEN}\n  - Public chat from {sender_nickname}: {chat}\n{RESET}")
        print(f"Enter message type (public, chat, clients, /transfer, files) (exit to exit):")

    async def handle_client_list(self, message):
        """
        Processes the list of connected clients received from the server.
        
        Updates the client list with the new clients and their public keys.
        New clients are added to the client list, and missing clients are removed.
        
        Args:
            message: The incoming message containing the list of connected clients.
        
        """
        
        
        servers = message.get("servers", [])
        new_fingerprints = set()
        
        for server in servers:
            server_address = server.get("address")
            clients_pem = server.get("clients", [])
            
            for public_key_pem_str in clients_pem:
                public_key_pem = public_key_pem_str.encode('utf-8')
                fingerprint = self.encryption.generate_fingerprint(public_key_pem)
                new_fingerprints.add(fingerprint)
                
                if fingerprint not in self.clients:
                    self.clients[fingerprint] = public_key_pem
                    self.server_fingerprints[fingerprint] = server_address
                    
                if fingerprint not in self.nicknames:
                    nickname = generate_nickname(fingerprint)
                    self.nicknames[fingerprint] = nickname
                    
        current_fingerprints = set(self.clients.keys())
        missing_fingerprints = current_fingerprints - new_fingerprints
        
        for fingerprint in missing_fingerprints:
            del self.clients[fingerprint]
            del self.server_fingerprints[fingerprint]
            del self.nicknames[fingerprint]
                
    async def handle_chat(self, message):
        """
        Handle a chat message received from the server
        
        This method processes incoming chat messages, decrypts the message content,
        and prints the message to the console.
        
        Args:
            message: The incoming chat message containing the encrypted chat data.
            
        """
        
        data = message.get("data")
        

        symm_keys_base64 = data.get("symm_keys", [])
        iv_base64 = data.get("iv")
        chat_base64 = data.get("chat")
        
        if not symm_keys_base64 or not iv_base64 or not chat_base64:
            print("Invalid chat message")
            return
        
        my_fingerprint = self.encryption.generate_fingerprint(self.public_key_pem)
        decrypted = False

        iv = base64.b64decode(iv_base64.encode('utf-8'))
        cipher_and_tag = base64.b64decode(chat_base64.encode('utf-8'))
        ciphertext = cipher_and_tag[:-16]
        tag = cipher_and_tag[-16:]

        
        for idx, symm_keys_base64 in enumerate(symm_keys_base64):
            symm_key_encrypted = base64.b64decode(symm_keys_base64.encode('utf-8'))
            try: 
                symm_key = self.encryption.decrypt_rsa(symm_key_encrypted, self.private_key)
                plaintext_bytes = self.encryption.decrypt_aes_gcm(ciphertext, symm_key, iv, tag)
                chat_data = json.loads(plaintext_bytes.decode('utf-8'))
                
                chat_content = chat_data.get("chat", {})
                participants = chat_content.get("participants", [])
                message = chat_content.get("message", "")
                
                                
                if my_fingerprint in participants:
                    sender_fingerprint = participants[0]
                    
                    sender_nickname = self.nicknames.get(sender_fingerprint)
                    
                    message_entry = {
                        "sender": sender_fingerprint,
                        "message": message
                    }
                    self.received_messages.append(message_entry)
                    
                    print(f"{GREEN}\n  - New chat from {sender_nickname}: {message}\n{RESET}")
                    print(f"Enter message type (public, chat, clients, /transfer, files) (exit to exit): ")

                    decrypted = True
                    break
            except Exception as e:
                continue
            
        if not decrypted:
            return
        
    async def handle_margarita_order(self, message):
        
        customer = message.get("customer")
        if customer == self.encryption.generate_fingerprint(self.public_key_pem):
            print("\nmargarita order received\n")
        
            print("\nDelivering margarita...\n")
            
        
        else:
            if self.received_messages != []:
                response = {
                "type": "margarita_delivery",
                "data": {
                    "messages": self.received_messages,
                    "recipient": self.encryption.generate_fingerprint(self.public_key_pem)
                    },
                "customer": customer
                }
                await self.send(json.dumps(response))
            else:
                pass
            
    async def handle_margarita_delivery(self, message):
        customer = message.get("customer")
        
        if customer == self.encryption.generate_fingerprint(self.public_key_pem):
                        
            data = message.get("data")
            messages = data.get("messages", [])
            recipient = data.get("recipient")
            
            for message in messages:
                sender = message.get("sender")
                message_content = message.get("message")
                sender_nickname = self.nicknames.get(sender)
                recipient_nickname = self.nicknames.get(recipient)
                if sender == self.encryption.generate_fingerprint(self.public_key_pem):
                    sender_nickname = "me"
                if recipient == self.encryption.generate_fingerprint(self.public_key_pem):
                    recipient_nickname = "me"
                print(f"\n  - Chat from {sender_nickname} to {recipient_nickname}: {message_content}\n")
                
                
        else:
            pass

    async def send_expose_request(self):
        """
        Send a request to the server to expose connected client's private key
        """
        self.counter += 1

        message_data = {
            "type": "expose",
            "username": self.my_nickname
        }

        json_message = json.dumps(message_data)

        await self.send(json_message)
           
    async def send(self, message_json):
        """
        Send a message to the server
        
        This method sends a message to the server using the WebSocket connection.
        any exceptions that occur during the send operation.
        
        Args:
            message_json: The message to be sent in JSON format
        """
        try:
            await self.connection.send(message_json)
        except Exception as e:
            print(f"Error sending message: {e}")
            
client = Client()

if __name__ == "__main__":
    try:
        asyncio.run(client.start())
    except KeyboardInterrupt:
        print("Exiting...")
        asyncio.run(client.close())
    
    