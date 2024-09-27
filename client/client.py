import json
import base64
import asyncio
import aioconsole
import websockets
import sys
from security.security_module import Encryption
from nickname_generator import generate_nickname


class Client:
    def __init__(self, server_address="ws://localhost:9000"):
        self.server_address = server_address
        self.encryption = Encryption()
        self.connection = None
        self.counter = 0
        self.public_key = None
        self.private_key = None
        self.last_counters = {} # {fingerprint: counter}
        self.received_messages = []  # Fixed typo
        self.clients = {} # {fingerprint: public_key}
        self.server_fingerprints = {} # {fingerprint: server_address}
        self.nicknames = {} # {fingerprint: nickname}  
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
    async def start(self):
        # Generate RSA key pair
        self.public_key, self.private_key = self.encryption.generate_rsa_key_pair()

        
        await self.connect()
        await self.input_prompt()
        self.loop.run_forever()

    def parse_message(self, message):
        try:
            message_dict = json.loads(message)
            return message_dict, None
        except json.JSONDecodeError as e:
            return None, f"Error parsing JSON: {str(e)}"

    def build_signed_data(self, data):
        message = {
            "data": data,
            "counter": self.counter
        }

        message_json = json.dumps(message, separators=(',', ':'), sort_keys=True)
        message_bytes = message_json.encode('utf-8')

        # Sign the message
        signature = self.encryption.sign_message(message_bytes, self.private_key)
        signature_base64 = base64.b64encode(signature).decode('utf-8')

        # Prepare the signed message
        signed_data = {
            "type": "signed_data",
            "data": data,
            "counter": self.counter,
            "signature": signature_base64
        }

        return signed_data
    
    async def print_clients(self):
        
        await self.request_client_list()
        
        print("Online clients:\n")
        for fingerprint, public_key in self.clients.items():
            nickname = self.nicknames.get(fingerprint)
            if fingerprint == self.encryption.generate_fingerprint(self.public_key):
                nickname += " (me)"
            print(f"{nickname}\n")
            
        if not self.clients:
            print("No clients connected")
            
            
    
    async def input_prompt(self):
        while True:
            
            message = await aioconsole.ainput("Enter message type (public, chat, req_clients, clients): ")
            if message == "public":
                await self.request_client_list()
                chat = await aioconsole.ainput("Enter public chat message: ")
                await self.send_public_chat(chat)
            elif message == "chat":
                await self.request_client_list()
                recipients = await aioconsole.ainput("Enter recipients separated by commas: ")
                chat = await aioconsole.ainput("Enter chat message: ")
                await self.send_chat(recipients.split(','), chat)
            elif message == "clients":
                await self.print_clients()
            elif message == "exit":
                await self.close()
                break
            else:
                print("Invalid message type")
                
                
    async def connect(self):
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
        if self.connection:
            try:
                await self.connection.close()
                print("Connection closed")
                sys.exit(0)
            except Exception as e:
                print(f"Failed to close connection: {e}")
            finally:
                self.connection = None

    async def send_hello(self):
        self.counter += 1
        public_key_base64 = base64.b64encode(self.public_key).decode('utf-8')

        message_data = {
            "type": "hello",
            "public_key": public_key_base64  # Use base64 encoded public_key
        }

        message = self.build_signed_data(message_data)

        
        json_message = json.dumps(message)
        
        try:
            await self.connection.send(json_message)
        except Exception as e:
            print(f"Error sending hello message: {e}")

    async def send_public_chat(self, chat):
        self.counter += 1
        
        fingerprint = self.encryption.generate_fingerprint(self.public_key)

        message_data = {
            "type": "public_chat",
            "sender": fingerprint,
            "message": chat
        }

        message = self.build_signed_data(message_data)

        message_json = json.dumps(message)
        
        await self.send(message_json)
        print(f"Sent public chat message: {chat}")
        
        
    async def send_chat(self, recipients, chat):
        valid_recipients = [fingerprint for fingerprint in recipients if fingerprint in self.clients]
        if not valid_recipients:
            print("No valid recipients")
            return
        
        destination_servers = set()
        recipient_public_keys = []
        
        for fingerprint in valid_recipients:
            server_address = self.server_fingerprints.get(fingerprint)
            if server_address:
                destination_servers.add(server_address)
                recipient_public_keys.append(self.clients[fingerprint])
            else:
                print(f"Unknown server for recipient: {fingerprint}")
            
        destination_servers = list(destination_servers)
        if not destination_servers:
            print("No destination servers")
            return
        
        self.counter += 1
        
        aes_key = self.encryption.generate_aes_key()
        iv = self.encryption.generate_iv()
        ivb64 = base64.b64encode(iv).decode('utf-8')
        
        sender_public_key = self.public_key
        sender_fingerprint = self.encryption.generate_fingerprint(sender_public_key)
        participants = [sender_fingerprint] + [self.encryption.generate_fingerprint(public_key) for public_key in recipient_public_keys]
        
        chat_data = {
            "participants": participants,
            "message": chat
        }
        chat_json = json.dumps(chat_data)
        
        try:
            ciphertext, tag = self.encryption.encrypt_aes_gcm(chat_json.encode('utf-8'), aes_key, iv)
            chat_base64 = base64.b64encode(ciphertext).decode('utf-8')
        except Exception as e:
            print(f"Failed to encrypt chat: {e}")
            return
        
        symm_keys = []
        for public_key in recipient_public_keys:
            try:
                symm_key_encrypted = self.encryption.encrypt_rsa(aes_key, public_key)
                symm_key_base64 = base64.b64encode(symm_key_encrypted).decode('utf-8')
                symm_keys.append(symm_key_base64)
            except Exception as e:
                print(f"Failed to encrypt symmetric key: {e}")
                return
            
        message_data = {
            "type": "chat",
            "destination_servers": destination_servers,
            "iv": ivb64,
            "symm_keys": symm_keys,
            "chat": chat_base64
        }
        
        signed_data = self.build_signed_data(message_data)
        message_json = json.dumps(signed_data)
        await self.send(message_json)
        print(f"Sent chat message: {chat}")

    async def request_client_list(self):
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
        
        await self.request_client_list()

        message_type = message.get("type") or message.get("data", {}).get("type")
        
        if message_type == "signed_data":
            message_type = message.get("data", {}).get("type")

        if message_type == "public_chat":
            await self.handle_public_chat(message)
        elif message_type == "client_list":
            await self.handle_client_list(message)
        elif message_type == "chat":
            await self.handle_chat(message)
        else:
            print(f"Unknown message type: {message_type}")

    async def handle_public_chat(self, message):
        data = message.get("data")  
        
        sender_fingerprint = data.get("sender")
        chat = data.get("message")
        self.received_messages.append({
            "sender": sender_fingerprint,
            "message": chat
        })
        
        sender_nickname = self.nicknames.get(sender_fingerprint)
        
        # check if sender is me
        if sender_fingerprint == self.encryption.generate_fingerprint(self.public_key):
            sender_fingerprint = "me"
        
        print(f"\nPublic chat from {sender_nickname}: {chat}")

    async def handle_client_list(self, message):
        servers = message.get("servers", [])
        for server in servers:
            clients = server.get("clients", [])
            for client in clients:
                server_address = server.get("address")
                public_key_base64 = client
                public_key = base64.b64decode(public_key_base64.encode('utf-8'))
                fingerprint = self.encryption.generate_fingerprint(public_key)
                self.clients[fingerprint] = public_key
                self.server_fingerprints[fingerprint] = server_address
                
                if fingerprint not in self.nicknames:
                    nickname = generate_nickname()
                    self.nicknames[fingerprint] = nickname
                
    async def handle_chat(self, message):
        symm_keys_base64 = message.get("symm_keys", [])
        iv_base64 = message.get("iv")
        chat_base64 = message.get("chat")

        if not symm_keys_base64 or not iv_base64 or not chat_base64:
            print("Invalid chat message")
            return
        
        private_key = self.private_key
        my_fingerprint = self.encryption.generate_fingerprint(self.public_key)

        iv = base64.b64decode(iv_base64.encode('utf-8'))
        cipher_tag = base64.b64decode(chat_base64.encode('utf-8'))
        ciphertext = cipher_tag[:-16]
        tag = cipher_tag[-16:]

        for idx, symm_keys_base64 in enumerate(symm_keys_base64):
            symm_key_encrypted = base64.b64decode(symm_keys_base64.encode('utf-8'))
            try:
                symm_key = self.encryption.decrypt_rsa(symm_key_encrypted, private_key)
                plaintext_bytes = self.encryption.decrypt_aes_gcm(ciphertext, symm_key, iv, tag)
                chat_data = json.loads(plaintext_bytes.decode('utf-8'))
                
                participants = chat_data.get("participants", [])
                if my_fingerprint in participants:
                    sender_fingerprint = participants[0]
                    message = chat_data.get("message")
                    self.received_messages.append({
                        "sender": sender_fingerprint,
                        "message": message
                    })
                    print(f"\nChat from {sender_fingerprint}: {message}")
                    return
            except Exception as e:
                print(f"Failed to decrypt chat: {e}")
                return

    async def send(self, message_json):
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
    
    
