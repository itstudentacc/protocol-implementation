import websockets
import asyncio
import json
import base64
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class Client:
    def __init__(self, server_address):
        self.server_address = server_address
        self.public_key, self.private_key = self.generate_key_pair()
        self.counter = 0
        self.connection = None

    async def connect(self):
        self.connection = await websockets.connect(self.server_address)
        await self.send_hello()

    async def send_hello(self):
        hello_message = {
            "data": {
                "type": "hello",
                "public_key": self.export_public_key()
            }
        }
        await self.connection.send(json.dumps(hello_message))

    async def send_message(self, destination, message):
        self.counter += 1
        # Encrypt and sign the message here
        chat_message = {
            "type": "signed_data",
            "data": {
                "type": "chat",
                "destination_servers": [destination],
                "iv": "<Base64 encoded AES IV>",
                "symm_keys": ["<Base64 encoded AES key>"],
                "chat": "<Base64 encoded AES encrypted message>"
            },
            "counter": self.counter,
            "signature": "<Base64 signature>"
        }
        await self.connection.send(json.dumps(chat_message))

    async def receive_message(self):
        async for message in self.connection:
            # Decrypt and verify the message here
            print(f"Received message: {message}")

    async def request_client_list(self):
        client_list_request = {"type": "client_list_request"}
        await self.connection.send(json.dumps(client_list_request))

    async def disconnect(self):
        await self.connection.close()

    def generate_key_pair(self):
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        public_key = private_key.public_key()
        return public_key, private_key

    def export_public_key(self):
        return base64.b64encode(
            self.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
        ).decode('utf-8')

