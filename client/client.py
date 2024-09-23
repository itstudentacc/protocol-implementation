import json
import base64
import asyncio
import hashlib
from connect import WebSocketClient
from security.security_module import Encryption

class Client:
    def __init__(self):
        self.server_address = "ws://localhost:8000"
        self.encryption = Encryption()
        self.counter = 0
        self.client = WebSocketClient(self.server_address)
        self.public_key, self.private_key = self.encryption.generate_rsa_key_pair()
        self.client_list = []
        

    def fingerprint(self, public_key):
        """
        Generates a fingerprint from a public key.
        """
        # Hash the public key using SHA-256
        sha256_hash = hashlib.sha256(public_key).digest()
        # Get the hexadecimal representation of the hash
        return base64.b64encode(sha256_hash).decode()
    
    async def connect(self):
        try:
            await self.client.connect()
        except Exception as e:
            print(f"Connection failed: {e}")
            
    async def close(self):
        await self.client.close()
    
    async def send_hello(self):
        print("Sending hello message")
        self.counter += 1

        # Convert public_key to a base64 encoded string if it is in bytes format
        public_key_base64 = base64.b64encode(self.public_key).decode()

        message_data = json.dumps({
            "type": "hello",
            "public_key": public_key_base64  # Use base64 encoded public_key
        })

        # Sign the message data
        signature = self.encryption.sign_rsa(message_data.encode(), self.private_key)

        # Convert signature to a base64 encoded string
        signature_base64 = base64.b64encode(signature).decode()

        message = {
            "type": "signed_data",
            "data": {
                "type": "hello",
                "public_key": public_key_base64,  # Use base64 encoded public_key
            },
            "counter": self.counter,
            "signature": signature_base64  # Use base64 encoded signature
        }

        json_message = json.dumps(message)
        
        try:
            await self.client.send(json_message)
            print("Sent hello message")
        except Exception as e:
            print(f"Error sending hello message: {e}")
        
    async def send_chat(self, chat_message, recipient_public_key):
        self.counter += 1

        iv = self.encryption.generate_iv()
        symm_key = self.encryption.generate_aes_key()
        
        encrypted_chat = self.encryption.encrypt_aes_gcm(chat_message.encode(), symm_key, iv)
        
        encrypted_symm_key = self.encryption.encrypt_rsa(symm_key, recipient_public_key)
        
        message = {
            "type": "signed_data",
            "data": {
                "type": "chat",
                "destination_servers": [],
                "iv": base64.b64encode(iv).decode(),
                "symm_keys": base64.b64encode(encrypted_symm_key).decode(),
                "chat": base64.b64encode(encrypted_chat).decode()
            },
            "counter": self.counter,
            "signature": ""
        }
        
        message_data = json.dumps(message["data"])
        signature = self.encryption.sign_rsa(message_data.encode(), self.private_key)
        
        message["signature"] = base64.b64encode(signature).decode()
        
        message_json = json.dumps(message)
        try:
            await self.client.send(message_json)
            print(f"Sent chat message: {message_json}")
        except Exception as e:
            print (f"Error sending chat message: {e}")
        
    async def send_public_chat(self, message):
        self.counter += 1
        
        encoded_fingerprint = self.fingerprint(self.public_key)
            
        message_data = {
            "type": "public_chat",
            "data": {
                "sender" : encoded_fingerprint,
                "message": message
            },
            "counter": self.counter,
        }
        
        
        # Create JSON and sign it
        message_json = json.dumps(message_data)
        
        
        try:
            await self.client.send(message_json)
            print(f"Sent public message: {message}")
        except Exception as e:
            print(f"Error sending public message: {e}")
        
        
    async def receive_client_list(self):
        """
        Receives a list of clients from the server.
        Expected format:
        {
            "type": "client_list",
            "servers": [
                {
                    "address": "<server_address>",
                    "clients": [
                        "<exported RSA public key of client>",
                    ]
                },
            ]
        }
        """
        try:
            # Receive raw message from WebSocket
            raw_message = await self.client.receive()
            print(f"Received raw message: {raw_message}")

            # Parse JSON message
            message = json.loads(raw_message)
        
            # Validate message type
            if message.get("type") == "client_list":
                # Extract and print client list
                client_list = message.get("servers", [])
                print(f"Received client list: {client_list}")
                return client_list
            else:
                raise ValueError("Received message is not a client list")
    
        except json.JSONDecodeError as e:
            print(f"Error parsing client list JSON: {e}")
            return None
        except ValueError as e:
            print(f"Value error: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None
    
    def get_public_key(self, fingerprint, client_list):
        """
        Returns the public key associated with the given fingerprint.
        """
        for server in client_list:
            for client_public_key in server["clients"]:
                client_fingerprint = self.fingerprint_public_key(base64.b64decode(client_public_key))
                if client_fingerprint == fingerprint:
                    return base64.b64decode(client_public_key)
        return None

    async def receive_public_chat(self):
        """
        Receives a public message.
        Expects a message in the format:
        {
            "type": "signed_data",
            "data": {
                "type": "public_message",
                "sender": "<encoded_fingerprint>",
                "message": "<message>"
            },
            "counter": "<counter>",
            "signature": "<signature>"
        }
        """
        try:
            # Receive the raw message
            raw_message = await self.client.receive()
            print(f"Received raw message: {raw_message}")

            # Parse the message from JSON
            message = json.loads(raw_message)
            
            if message["type"] != "public_chat":
                raise ValueError("Invalid message type")


            # Extract sender and message
            decoded_sender = base64.b64decode(message["data"]["sender"]).decode("utf-8")
            public_message = message["data"]["message"]

            print(f"Public message from {decoded_sender}: {public_message}")
            return public_message

        except Exception as e:
            print(f"Error receiving public message: {e}")
            return None

    
        

