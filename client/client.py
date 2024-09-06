import asyncio
import json
from connect import WebSocketClient
from message_handler import MessageHandler

class Client:
    def __init__(self, server_address):
        self.server_address = server_address
        
    