from fastapi import WebSocket
import json

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)
    
    async def handler(self, message: str, websocket: WebSocket):
        """
        Handle all messages
        """
        
        # Only accept protocol messages
        if self.msg_fits_protocol(message):
            message = json.loads(message)
            message_type = message['type']

            match message_type:
                case 'signed_data':
                    pass
                case 'client_list_request':
                    pass
                case 'client_update':
                    pass
                case 'client_update_request':
                    pass
            pass
        else:
            self.disconnect(websocket)
    
    
    
    def msg_fits_protocol(self, message: str):
        """
        Validates whether the message fits the protocol
        """

        try:
            message = json.loads(message)
            
            type = message['type']
            valid_types = [
                'signed_data',
                'client_list_request',
                'client_update',
                'client_update_request'
            ]

            if type not in valid_types:
                return False
            
            if type == 'signed_dataa':

                valid_keys = [
                    'type',
                    'data',
                    'counter',
                    'signature'
                ]

                for key in message.keys():
                    if key not in valid_keys:
                        return False

        except json.decoder.JSONDecodeError:
            return False

        except KeyError:
            return False
    
        return True

      