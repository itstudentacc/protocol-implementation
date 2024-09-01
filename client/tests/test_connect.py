# test_connect.py

import unittest
from unittest.mock import patch, AsyncMock
import asyncio
from connect import WebSocketClient

class TestWebSocketClient(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.server_url = "ws://localhost:8000"
        self.client = WebSocketClient(self.server_url)

    @patch("websockets.connect", new_callable=AsyncMock)
    async def test_connect(self, mock_connect):
        # Mock the connect method
        mock_connect.return_value = AsyncMock()

        # Run the connect method
        await self.client.connect()

        # Assert the websocket connection was made
        mock_connect.assert_called_once_with(self.server_url)
        self.assertIsNotNone(self.client.websocket)
        print("Connection test passed.")

    @patch("websockets.connect", new_callable=AsyncMock)
    async def test_send(self, mock_connect):
        # Mock the connect and send method
        mock_ws = AsyncMock()
        mock_connect.return_value = mock_ws

        # Establish connection
        await self.client.connect()

        # Test sending a message
        await self.client.send("Hello, Server!")
        mock_ws.send.assert_called_once_with("Hello, Server!")
        print("Send test passed.")

    @patch("websockets.connect", new_callable=AsyncMock)
    async def test_receive(self, mock_connect):
        # Mock the connect and receive method
        mock_ws = AsyncMock()
        mock_connect.return_value = mock_ws
        mock_ws.recv.return_value = "Hello, Client!"

        # Establish connection
        await self.client.connect()

        # Test receiving a message
        message = await self.client.receive()
        self.assertEqual(message, "Hello, Client!")
        print("Receive test passed.")

    @patch("websockets.connect", new_callable=AsyncMock)
    async def test_disconnect(self, mock_connect):
        # Mock the connect and close method
        mock_ws = AsyncMock()
        mock_connect.return_value = mock_ws

        # Establish connection
        await self.client.connect()

        # Test disconnecting
        await self.client.disconnect()
        mock_ws.close.assert_called_once()
        print("Disconnect test passed.")

if __name__ == "__main__":
    unittest.main()
