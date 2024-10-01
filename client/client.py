import json
import base64
import asyncio
import aioconsole
import websockets
import sys
from security.security_module import Encryption
from nickname_generator import generate_nickname


class Client:
    def __init__(self):
        self.server_address = None
        self.encryption = Encryption()
        self.connection = None
        self.counter = 0
        self.public_key = None
        self.private_key = None
        self.received_messages = []  # Fixed typo
        self.clients = {} # {fingerprint: public_key}
        self.server_fingerprints = {} # {fingerprint: server_address}
        self.nicknames = {} # {fingerprint: nickname}  
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
    async def start(self):
        # Generate RSA key pair
        self.public_key_pem, self.private_key_pem = self.encryption.generate_rsa_key_pair()
        self.public_key = self.encryption.load_public_key(self.public_key_pem)
        self.private_key = self.encryption.load_private_key(self.private_key_pem)
        
        chosen_server = await aioconsole.ainput("Enter server address: ")
        
        self.server_address = f"{chosen_server}"

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
            
    async def input_prompt(self):
        while True:
            
            message = await aioconsole.ainput("Enter message type (public, chat, clients) (exit to exit): ")
            if message.lower() == "public":
                print("\n")
                chat = await aioconsole.ainput("Enter public chat message: ")
                await self.send_public_chat(chat)
            elif message.lower() == "chat":
                recipients = await aioconsole.ainput("Enter recipient names, seperated by commas: ")
                chat = await aioconsole.ainput("Enter chat message: ")
                await self.send_chat(recipients.split(","), chat)
            elif message.lower() == "clients":
                await self.request_client_list()
                self.print_clients()
            elif message.lower() == "exit":
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
        
        public_pem = self.public_key_pem.decode('utf-8')
        

        message_data = {
            "type": "hello",
            "public_key": public_pem  
        }

        message = self.build_signed_data(message_data)

        
        json_message = json.dumps(message)
        
        await self.send(json_message)
        

    async def send_public_chat(self, chat):
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
        print(f"Sent public chat message: {chat}")
        
        
    async def send_chat(self, recipients_nicknames, chat):
        
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
        print(f"Sent chat message to {', '.join(recipients_nicknames)}: {chat}")


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
        "Received message"
    
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
        if sender_fingerprint == self.encryption.generate_fingerprint(self.public_key_pem):
            sender_nickname = "me"
        
        print(f"\nPublic chat from {sender_nickname}: {chat}\n")
        print(f"Enter message type (public, chat, clients): ")

    async def handle_client_list(self, message):
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
                    
                    print(f"\nNew chat from {sender_nickname}: {message}\n")
                    print(f"Enter message type (public, chat, clients): ")

                    decrypted = True
                    break
            except Exception as e:
                continue
            
        if not decrypted:
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
    
    
