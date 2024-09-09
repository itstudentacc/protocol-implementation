import unittest
from unittest.mock import AsyncMock
import json
import asyncio
from message_handler import MessageHandler

class TestMessageHandler(unittest.TestCase):

    def setUp(self):
        # Create a mock connection
        self.mock_connection = AsyncMock()
        # Pass the mock connection to the MessageHandler
        self.message_handler = MessageHandler(self.mock_connection)
        # Set initial counter for the message
        self.message_handler.counter = 0
        # Create an event loop for async tests
        self.loop = asyncio.get_event_loop()

    def test_send_hello(self):
        public_key = 'mocked_public_key'
        # Construct the expected message format
        expected_message = {
            "type": "signed_data",
            "data": {
                "type": "hello",
                "public_key": public_key
            },
            "counter": 1,  # Incremented counter value
            "signature": "signature"  # Mocked value for signature
        }

        async def run_test():
            await self.message_handler.send_hello(public_key)
        
        # Run the test
        self.loop.run_until_complete(run_test())

        # Assert that the connection's send method was called with the correct JSON payload
        self.mock_connection.send.assert_awaited_once_with(json.dumps(expected_message))
        
    def test_send_chat(self):
        chat_message = 'my chat message'
        destination_servers = ['mocked_destination_server']
        iv = 'mocked_iv'
        symmetric_keys = ['mocked_symmetric_key']
        recipients_fingerprints = ['mocked_recipient_fingerprint']
        # Construct the expected message format
        expected_message = {
            "type": "signed_data",
            "data": {
                "type": "chat",
                "destination_servers": destination_servers,
                "iv": iv,
                "symmetric_key": symmetric_keys,
                "chat": {
                    "participants": recipients_fingerprints,
                    "message": chat_message
                }
            },
            "counter": 1,  # Incremented counter value
            "signature": "signature"  # Mocked value for signature
        }

        async def run_test():
            await self.message_handler.send_chat(chat_message, destination_servers, iv, symmetric_keys, recipients_fingerprints)
        
        # Run the test
        self.loop.run_until_complete(run_test())

        # Assert that the connection's send method was called with the correct JSON payload
        self.mock_connection.send.assert_awaited_once_with(json.dumps(expected_message))
        
        
    def test_send_public_message(self):
        sender_fingerprint = 'mocked_sender_fingerprint'
        message = 'my public message'
        # Construct the expected message format
        expected_message = {
            "type": "signed_data",
            "data": {
                "type": "public_message",
                "sender_fingerprint": sender_fingerprint,
                "message": message
            },
            "counter": 1,  # Incremented counter value
            "signature": "signature"  # Mocked value for signature
        }

        async def run_test():
            await self.message_handler.send_public_message(sender_fingerprint, message)
        
        # Run the test
        self.loop.run_until_complete(run_test())

        # Assert that the connection's send method was called with the correct JSON payload
        self.mock_connection.send.assert_awaited_once_with(json.dumps(expected_message))

if __name__ == '__main__':
    unittest.main()
