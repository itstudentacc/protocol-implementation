import json

class MessageHandler:
    def create_signed_message(self, message_type, data, counter, private_key):
        message = {
            "type": "signed_data",
            "data": {
                "type": message_type,
                **data
            },
            "counter": counter
        }
        message_json = json.dumps(message)
        signature = self.sign_message(message_json, private_key)
        message["signature"] = signature
        return json.dumps(message)
    
    def sign_message(self, message, private_key):
        #placeholder function to simulate signing
        
        
        return "signature"