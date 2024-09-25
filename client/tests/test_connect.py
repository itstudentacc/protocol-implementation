# test_connect.py
import asyncio
import unittest
from vault.connect import WebSocketClient

class TestWebSocketClient(unittest.TestCase):
    def setUp(self):
        self.client = WebSocketClient("ws://localhost:8765")

    def run_async(self, coro):
        return asyncio.get_event_loop().run_until_complete(coro)

    def test_connect(self):
        try:
            self.run_async(self.client.connect())
            self.assertIsNotNone(self.client.connection, "Connection should be established")
        except Exception as e:
            self.fail(f"Connection failed with exception: {e}")

    def test_close(self):
        try:
            self.run_async(self.client.connect())
            self.run_async(self.client.close())
            self.assertIsNone(self.client.connection, "Connection should be closed")
        except Exception as e:
            self.fail(f"Close failed with exception: {e}")

if __name__ == "__main__":
    unittest.main()
