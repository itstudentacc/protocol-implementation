# message_handler.py
import json
import base64
# from security_module import encrypt_message, decrypt_message, sign_message, verify_signature

class MessageHandler:
    def __init__(self, connection):
        self.connection = connection
        self.counter = 0
        
    async def send_hello(self, public_key):
        self.counter += 1
        message = {
            "data": {
                "type": "hello",
                "public_key": public_key,
            },
            "counter": self.counter,
            "signature": None,
        }
        json_message = json.dumps(message)
        await self.connection.send(json_message)
        print (f"Sent hello message: {json_message}")
        
    async def send_chat(self, message, destination_servers, iv, symmetric_keys, recipients_fingerprints):
        self.counter += 1
        
        # Greg Encrypt this message
        chat = {
            "participants": recipients_fingerprints,
            "message": message
            
        }
        #Base64 AES encrypted_message = encrypt_message(chat)
        encrypted_message = chat
        
        message = {
            "data": {
                "type": "chat",
                "destination_servers": destination_servers,
                "iv": iv,
                "symmetric_key": symmetric_keys,
                "chat": encrypted_message
            },
        }
        json_message = json.dumps(message)
        await self.connection.send(json_message)
        print (f"Sent chat message: {json_message}")
    
    async def send_public_message(self, sender_fingerprint, message):
        self.counter += 1
        
        #base64 encode the fingerprint
        encoded_fingerprint = base64.b64encode(sender_fingerprint)
        
        message = {
            "data": {
                "type": "public_message",
                "sender" : encoded_fingerprint,
                "message": message
            },
            "counter": self.counter,
            "signature": None,
        }
        json_message = json.dumps(message)
        await self.connection.send(json_message)
        print (f"Sent public message: {json_message}")
    
    async def receive_client_list(self):
        pass
    
    async def receive_message(self):
        pass
    
        