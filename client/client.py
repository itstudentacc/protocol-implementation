import json
import base64
import asyncio
import aioconsole
import websockets
from security.security_module import Encryption


class Client:
    def __init__(self, server_address="ws://localhost:8000"):
        self.server_address = server_address
        self.encryption = Encryption()
        self.connection = None
        self.counter = 0
        self.last_counters = {}
        self.received_messages = []  # Fixed typo
        self.clients = {}
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
    
    async def input_prompt(self):
        while True:
            message = await aioconsole.ainput("Enter message type (public, chat, clients): ")
            if message == "public":
                chat = await aioconsole.ainput("Enter public chat message: ")
                await self.send_public_chat(chat)
            elif message == "chat":
                recipients = await aioconsole.ainput("Enter recipients separated by commas: ")
                chat = await aioconsole.ainput("Enter chat message: ")
                await self.send_chat(recipients.split(','), chat)
            elif message == "clients":
                await self.request_client_list()
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

    async def close(self):
        if self.connection:
            try:
                await self.connection.close()
                print("Connection closed")
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
        await self.connection.send(json_message)
        print(f"Sent hello message")

    async def send_public_chat(self, chat):
        self.counter += 1
        
        fingerprint = self.encryption.generate_fingerprint(self.private_key.public_key())

        message_data = {
            "type": "public_chat",
            "sender": fingerprint,
            "message": chat
        }

        message = self.build_signed_data(message_data)

        message_json = json.dumps(message)
        await self.send(message_json)
        print(f"Sent public message: {message_json}")

    async def send_chat(self, recipients, chat):
        recipient_public_keys = [self.clients[fingerprint] for fingerprint in recipients if fingerprint in self.clients]
        destination_servers = [self.server_address]
        self.counter += 1

        # Generate AES key and IV
        aes_key = self.encryption.generate_aes_key()
        iv = self.encryption.generate_iv()
        iv_base64 = base64.b64encode(iv).decode('utf-8')

        sender_fingerprint = self.encryption.generate_fingerprint(self.private_key.public_key())
        participants = [sender_fingerprint] + [self.encryption.generate_fingerprint(public_key) for public_key in recipient_public_keys]

        # Prepare the message data
        message_data = {
            "participants": participants,
            "message": chat
        }

        message_json = json.dumps(message_data)

        # Encrypt the chat message using AES-GCM
        ciphertext = self.encryption.encrypt_aes_gcm(message_json.encode('utf-8'), aes_key, iv)
        chat_base64 = base64.b64encode(ciphertext).decode('utf-8')

        # Encrypt AES key for each recipient
        symm_keys = []
        for recipient_public_key in recipient_public_keys:
            encrypted_key = self.encryption.encrypt_rsa(aes_key, recipient_public_key)
            encrypted_key_base64 = base64.b64encode(encrypted_key).decode('utf-8')
            symm_keys.append(encrypted_key_base64)

        # Build the final chat message with encrypted components
        data = {
            "type": "chat",
            "destination_servers": destination_servers,
            "iv": iv_base64,
            "symm_keys": symm_keys,
            "chat": chat_base64
        }

        signed_message = self.build_signed_data(data)

        message_json = json.dumps(signed_message)
        await self.send(message_json)
        print(f"Sent chat message: {chat}")

    async def request_client_list(self):
        message = {
            "type": "client_list_request"
        }

        message_json = json.dumps(message)
        await self.send(message_json)
        print("Sent client list request")

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

    async def handle_message(self, message):
        print(f"Received message")

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
        sender_fingerprint = message.get("sender")
        chat = message.get("message")
        self.received_messages.append({
            "sender": sender_fingerprint,
            "message": chat
        })
        print(f"Public chat from {sender_fingerprint}: {chat}")

    async def handle_client_list(self, message):
        servers = message.get("servers", [])
        for server in servers:
            clients = server.get("clients", [])
            for client in clients:
                fingerprint = client.get("fingerprint")
                public_key_base64 = client.get("public_key")
                public_key = base64.b64decode(public_key_base64)
                self.clients[fingerprint] = public_key
        print(f"Received client list: {self.clients}")

    async def handle_chat(self, message):
        symm_keys = message.get("symm_keys", [])
        iv_base64 = message.get("iv")
        chat_base64 = message.get("chat")

        if not symm_keys or not iv_base64 or not chat_base64:
            print("Invalid chat message")
            return

        iv = base64.b64decode(iv_base64.encode('utf-8'))
        cipher_tag = base64.b64decode(chat_base64.encode('utf-8'))
        ciphertext = cipher_tag[:-16]
        tag = cipher_tag[-16:]

        for symm_key_base64 in symm_keys:
            symm_key_encrypted = base64.b64decode(symm_key_base64.encode('utf-8'))
            try:
                symm_key = self.encryption.decrypt_rsa(symm_key_encrypted, self.private_key)
                plaintext_bytes = self.encryption.decrypt_aes_gcm(ciphertext, symm_key, iv, tag)
                chat = json.loads(plaintext_bytes.decode('utf-8'))

                participants = chat.get("participants", [])
                if self.encryption.generate_fingerprint(self.public_key) in participants:
                    sender_fingerprint = participants[0]
                    chat_message = chat.get("message")
                    self.received_messages.append({
                        "sender": sender_fingerprint,
                        "message": chat_message
                    })
                    print(f"Chat from {sender_fingerprint}: {chat_message}")
                    return
            except Exception as e:
                print(f"Failed to decrypt chat: {e}")
        print("Failed to decrypt chat")

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
    
    
