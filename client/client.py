import json
import base64
import asyncio
from connect import WebSocketClient
from security.security_module import Encryption

class Client:
    def __init__(self, server_address):
        self.encryption = Encryption()
        self.counter = 0
        self.client = WebSocketClient(server_address)
        self.public_key, self.private_key = self.encryption.generate_rsa_key_pair()
        

    async def connect(self):
        # Await connection to WebSocket server
        await self.client.connect()

    async def send_hello(self):
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
        await self.client.send(json_message)
        print(f"Sent hello message: {json_message}")
        
    async def send_chat(self, chat_message, recipient_public_key):
        self.counter += 1

        iv = self.encryption.generate_iv()
        symm_key = self.encryption.generate_aes_key()
        
        encrypted_chat, tag = self.encryption.encrypt_aes_gcm(chat_message.encode(), symm_key, iv)
        
        ## Send to recepient
        # encrypted_symm_key = self.encryption.encrypt_rsa(symm_key, recipient_public_key)

        # send to multiple recepients
        encrypted_symm_keys = [ 
            base64.b64encode(self.encryption.encrypt_rsa(symm_key, recipient_public_key)).decode()
            for recipient_public_key in recipient_public_key
        ]

        message = {
            "type": "signed_data",
            "data": {
                "type": "chat",
                "destination_servers": [],
                "iv": base64.b64encode(iv).decode(),
                "symm_keys": base64.b64encode(encrypted_symm_keys).decode(),
                "chat": base64.b64encode(encrypted_chat).decode(),
                "tag": base64.b64encode(tag).decode()
            },
            "counter": self.counter,
            "signature": ""
        }
        
        message_json = json.dumps(message)
        
        signature = self.encryption.sign_rsa(message_json.encode(), self.private_key)
        message["signature"] = base64.b64encode(signature).decode()
        
        message_json = json.dumps(message)
        
        await self.client.send(message_json)
        print(f"Sent chat message: {message_json}")
        
    async def send_public_chat(self, message):
        self.counter += 1
        
        encoded_fingerprint = base64.b64encode(self.public_key).decode()
        
        message = {
            "type": "signed_data",
            "data": {
                "type": "public_message",
                "sender" : encoded_fingerprint,
                "message": message
            },
            "counter": self.counter,
            "signature": "",
        }
        message_json = json.dumps(message)
        signature = self.encryption.sign_rsa(message_json.encode(), self.private_key)
        
        message["signature"] = base64.b64encode(signature).decode()
        
        
        message_json = json.dumps(message)
        await self.client.send(message_json)
        print(f"Sent public message: {message_json}")
        
        
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
    

    async def receive_public_message(self):
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

            # Extract the sender's fingerprint and decode it to get the public key
            sender_fingerprint = base64.b64decode(message["data"]["sender"])

            # Validate message type
            if message["type"] != "signed_data":
                raise Exception("Invalid message type")

            if message["data"]["type"] != "public_message":
                raise Exception("Invalid message data type")

            # Extract sender and message
            decoded_sender = base64.b64decode(message["data"]["sender"]).decode("utf-8")
            public_message = message["data"]["message"]

            print(f"Public message from {decoded_sender}: {public_message}")
            return public_message

        except Exception as e:
            print(f"Error receiving public message: {e}")
            return None

    async def receive_chat(self):
        """
        Receives a chat message.
        Expects a message in the format:
        {
            "type": "signed_data",
            "data": {
                "type": "chat",
                "destination_servers": [],
                "iv": "<iv>",
                "symm_keys": "<symm_keys>",
                "chat": "<chat>"
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

            # Validate message type
            if message["type"] != "signed_data":
                raise Exception("Invalid message type")

            if message["data"]["type"] != "chat":
                raise Exception("Invalid message data type")

            # Extract message data
            iv = base64.b64decode(message["data"]["iv"])
            symm_keys = base64.b64decode(message["data"]["symm_keys"])
            chat = base64.b64decode(message["data"]["chat"])
            tag = base64.b64decode(message["data"]["tag"])

            # Decrypt the symmetric key
            symm_key = self.encryption.decrypt_rsa(symm_keys, self.private_key)

            # Decrypt the chat message
            decrypted_chat = self.encryption.decrypt_aes_gcm(chat, symm_key, iv, tag)

            print(f"Decrypted chat message: {decrypted_chat.decode()}")
            return decrypted_chat.decode()

        except Exception as e:
            print(f"Error receiving chat message: {e}")
            return None


        

