# message_handler.py
import json
import base64
# from security_module import encrypt_message, decrypt_message, sign_message, verify_signature

class MessageHandler:
    def __init__(self, connection):
        self.connection = connection
        self.counter = 0
    
    '''
    Greg make sure this works
    
    def validate_message(self, message):
        if not verify_signature(message["signature"], message["data"]):
            raise Exception("Invalid message signature")
        if message["counter"] <= self.counter:
            raise Exception("Counter value is not valid")
        self.counter = message["counter"]
    '''

        
    async def send_hello(self, public_key):
        self.counter += 1
        
        #Greg sign the message
        #signature = sign_message(public_key)
        signature = "signature"
        
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
        print (f"Sent hello message: {json_message}")
        
    async def send_chat(self, message, destination_servers, iv, symmetric_keys, recipients_fingerprints):
        self.counter += 1
        
        # Greg Encrypt this message
        chat = {
            "participants": recipients_fingerprints,
            "message": message
            
        }
        #Base64 AES encrypted_message = encrypt_message(chat)
        
        #Greg sign the message
        #signature = sign_message(public_key)
        signature = "signature"
        encrypted_message = chat
        
        message = {
            "type": "signed_data",
            "data": {
                "type": "chat",
                "destination_servers": destination_servers,
                "iv": iv,
                "symmetric_key": symmetric_keys,
                "chat": encrypted_message
            },
            "counter": self.counter,
            "signature": signature
        }
        json_message = json.dumps(message)
        await self.connection.send(json_message)
        print (f"Sent chat message: {json_message}")
    
    async def send_public_message(self, sender_fingerprint, message):
        self.counter += 1
        
        #base64 encode the fingerprint
        encoded_fingerprint = base64.b64encode(sender_fingerprint)
        
        #Greg sign the message
        #signature = sign_message(public_key)
        signature = "signature"
        
        message = {
            "type": "signed_data",
            "data": {
                "type": "public_message",
                "sender" : encoded_fingerprint,
                "message": message
            },
            "counter": self.counter,
            "signature": signature,
        }
        json_message = json.dumps(message)
        await self.connection.send(json_message)
        print (f"Sent public message: {json_message}")
    
    '''
        
    async def request_client_list(self):
        #request a list of clients from the server
        
        pass
        
    '''
    
    async def receive_client_list(self):
        """
        
        Receives a list of clients from the server
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
            raw_message = await self.connection.receive()
            print(f"Received raw message: {raw_message}")
            
            message = json.loads(raw_message)
            
            if message["type"] == "client_list":
                client_list = message["servers"]
                print(f"Received client list: {client_list}")
                return client_list
            else:
                raise ValueError("Received message is not a client list")
            
        except(json.JSONDecodeError, ValueError) as e:
            print(f"Error parsing client list: {e}")
            return None
        except Exception as e:
            print(f"Error receiving client list: {e}")
            return None
        
                
    
    async def receive_chat_message(self, recipient_fingerprint):
        """
        Receives messages
        Expects a message in the format:
        {
            "type": "signed_data",
            "data": {
                "type": "chat",
                "destination_servers": ["<server_address>"],
                "iv": "<iv>",
                "symmetric_key": "<symmetric_key>",
                "chat": "<encrypted_message>"
            },
            "counter": "<counter>",
            "signature": "<signature>"
            
            
            "chat": {
                "participants": ["<fingerprints>"],
                "message": "<encrypted_message>"
            }
        }
        
        """
        
        try: 
            raw_message = await self.connection.receive()
            print(f"Received raw message: {raw_message}")
            
            message = json.loads(raw_message)
            
            # Greg Verify the signature
            # self.validate_message(message)
            
            # Remove after validate_message is implemented
            self.counter = message["counter"]
            
            if message["type"] == "signed_data":
                if message["data"]["type"] == "chat":
                    participants = message["chat"]["participants"]
                    
                    # Verify if the receiver is among the intended participants
                    if recipient_fingerprint not in participants:
                        raise Exception(f"Receiver ({recipient_fingerprint}) is not an intended participant.")
                    
                    encrypted_message = message["data"]["chat"]
                    
                    # Greg Decrypt this message
                    # decrypted_message = decrypt_message(encrypted_message)
                    
                    print(f"Chat message for {participants}: {encrypted_message}")
                    return encrypted_message
                else:
                    raise Exception("Invalid message type")
            else:
                raise Exception("Invalid message type")
                
        except Exception as e:
            print(f"Error receiving chat message: {e}")
            return None
        
    async def receive_public_message(self):
        """
        Receives a public message
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
            raw_message = await self.connection.receive()
            print(f"Received raw message: {raw_message}")
            
            message = json.loads(raw_message)
            
            # Greg Verify the signature
            # self.validate_message(message)
            
            # Remove after validate_message is implemented
            self.counter = message["counter"]
            
            if message["type"] == "signed_data":
                if message["data"]["type"] == "public_message":
                    
                    sender = message["data"]["sender"]
                    decoded_sender = base64.b64decode(sender).decode("utf-8")
                    
                    message = message["data"]["message"]
                    
                    print(f"Public message from {decoded_sender}: {message}")
                    return message
                else:
                    raise Exception("Invalid message type")
            else:
                raise Exception("Invalid message type")
        except Exception as e:
            print(f"Error receiving public message: {e}")
            return None
    
        