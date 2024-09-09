# message_handler.py
import json
import base64
from security_module import sign_message, verify_signature, aes_encrypt, aes_decrypt

class MessageHandler:
    def __init__(self, connection, private_key, public_key):
        self.connection = connection
        self.counter = 0
        self.private_key = private_key
        self.public_key = public_key
    
    async def send_hello(self, public_key):
        self.counter += 1
        
        signature = sign_message(self.private_key, f"hello{public_key}")
        
        message = {
            "type": "signed_data",
            "data": {
                "type": "hello",
                "public_key": public_key,
            },
            "counter": self.counter,
            "signature": signature,
        }
        json_message = json.dumps(message)
        await self.connection.send(json_message)
        print(f"Sent hello message: {json_message}")
        
    async def send_chat(self, message, destination_servers, iv, symmetric_keys, recipients_fingerprints):
        self.counter += 1
        
        symmetric_key = symmetric_keys[0]
        
        encrypted_message = aes_encrypt(symmetric_key, message)
        
        chat_data = {
            "participants": recipients_fingerprints,
            "message": message
        }
        signature = sign_message(self.private_key, json.dumps(chat_data))
        
        message = {
            "type": "signed_data",
            "data": {
                "type": "chat",
                "destination_servers": destination_servers,
                "iv": base64.b64encode(iv).decode('utf-8'),
                "symm_keys": [base64.b64encode(key).decode('utf-8') for key in symmetric_keys],
                "chat": base64.b64encode(encrypted_message).decode('utf-8'),
            },
            "counter": self.counter,
            "signature": signature
        }
        json_message = json.dumps(message)
        await self.connection.send(json_message)
        print(f"Sent chat message: {json_message}")
    
    async def send_public_message(self, sender_fingerprint, message):
        self.counter += 1
        
        # Base64 encode the fingerprint
        encoded_fingerprint = base64.b64encode(sender_fingerprint.encode('utf-8')).decode('utf-8')
        
        signature = sign_message(self.private_key, message)
        
        message = {
            "type": "signed_data",
            "data": {
                "type": "public_chat",
                "sender": encoded_fingerprint,
                "message": message
            },
            "counter": self.counter,
            "signature": signature,
        }
        json_message = json.dumps(message)
        await self.connection.send(json_message)
        print(f"Sent public message: {json_message}")
    
    async def receive_client_list(self):
        try: 
            raw_message = await self.connection.recv()
            print(f"Received raw message: {raw_message}")
            
            message = json.loads(raw_message)
            
            if message["type"] == "client_list":
                client_list = message["servers"]
                print(f"Received client list: {client_list}")
                return client_list
            else:
                raise ValueError("Received message is not a client list")
            
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error parsing client list: {e}")
            return None
        except Exception as e:
            print(f"Error receiving client list: {e}")
            return None
        
    async def receive_chat_message(self, recipient_fingerprint):
        try: 
            raw_message = await self.connection.recv()
            print(f"Received raw message: {raw_message}")
            
            message = json.loads(raw_message)
            
            self.counter = message["counter"]
            
            if message["type"] == "signed_data":
                if message["data"]["type"] == "chat":
                    participants = message["data"]["chat"]["participants"]
                    
                    # Verify if the receiver is among the intended participants
                    if recipient_fingerprint not in participants:
                        raise Exception(f"Receiver ({recipient_fingerprint}) is not an intended participant.")
                    
                    encrypted_message = base64.b64decode(message["data"]["chat"]["message"])
                    symmetric_keys = [base64.b64decode(key) for key in message["data"]["symm_keys"]]
                    iv = base64.b64decode(message["data"]["iv"])
                    
                    decrypted_message = aes_decrypt(symmetric_keys, iv, encrypted_message)
                    
                    print(f"Chat message for {participants}: {decrypted_message}")
                    return decrypted_message
                else:
                    raise Exception("Invalid message type")
            else:
                raise Exception("Invalid message type")
                
        except Exception as e:
            print(f"Error receiving chat message: {e}")
            return None
        
    async def receive_public_message(self):
        try:
            raw_message = await self.connection.recv()
            print(f"Received raw message: {raw_message}")
            
            message = json.loads(raw_message)
            
            # Verify the message signature
            if not verify_signature(self.public_key, json.dumps(message["data"]), message["signature"]):
                raise Exception("Signature verification failed")
            
            self.counter = message["counter"]
            
            if message["type"] == "signed_data":
                if message["data"]["type"] == "public_chat":
                    
                    sender = base64.b64decode(message["data"]["sender"]).decode("utf-8")
                    message_text = message["data"]["message"]
                    
                    print(f"Public message from {sender}: {message_text}")
                    return message_text
                else:
                    raise Exception("Invalid message type")
            else:
                raise Exception("Invalid message type")
        except Exception as e:
            print(f"Error receiving public message: {e}")
            return None
