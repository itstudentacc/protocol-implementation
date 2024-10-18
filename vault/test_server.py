import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio
from websockets.exceptions import ConnectionClosedOK
from OlafServer import WebSocketServer, OlafClientConnection

class TestWebSocketServer(unittest.TestCase):

    def setUp(self):
        """
        Set up the WebSocket server before each test.
        """
        neighbours = {"ws://localhost:8001": "server2_key"}
        self.ws_server = WebSocketServer('localhost', 9000, 9001, neighbours, 'Server_1_public_key')

    def test_websocket_initialization(self):
        """
        Test that the WebSocket server initializes correctly.
        """
        self.assertEqual(self.ws_server.host, 'localhost')
        self.assertEqual(self.ws_server.port, 9000)
        self.assertEqual(self.ws_server.public_key, 'Server_1_public_key')
        self.assertEqual(self.ws_server.neighbours, {"ws://localhost:8001": "server2_key"})
        self.assertIsNone(self.ws_server.server)

    def test_add_client(self):
        """
        Test that a client is correctly added to the server.
        """
        mock_ws = AsyncMock()
        mock_client = OlafClientConnection(mock_ws, "client_public_key")
        self.ws_server.clients.add(mock_client)

        self.assertEqual(len(self.ws_server.clients), 1)
        self.assertIn(mock_client, self.ws_server.clients)
        self.assertEqual(mock_client.websocket, mock_ws)

    def test_existing_client(self):
        """
        Test that the exisiting_client method works correctly.
        """
        mock_ws = AsyncMock()
        client = OlafClientConnection(mock_ws, "client_public_key")
        self.ws_server.clients.add(client)

        self.assertTrue(self.ws_server.exisiting_client(mock_ws))
        self.assertFalse(self.ws_server.exisiting_client(MagicMock()))

    def test_existing_neighbour(self):
        """
        Test that the existing_neighbour method works correctly.
        """
        mock_ws = AsyncMock()
        neighbour = OlafClientConnection(mock_ws, "server2_key")
        self.ws_server.neighbour_connections.add(neighbour)

        self.assertTrue(self.ws_server.existing_neighbour(mock_ws))
        self.assertFalse(self.ws_server.existing_neighbour(MagicMock()))

    @patch('OlafServer.WebSocketServer.recv')
    @patch('OlafServer.json')
    def test_recv_invalid_message(self, mock_json, mock_recv):
        """
        Test handling of an invalid JSON message.
        """
        mock_ws = AsyncMock()
        mock_recv.return_value = asyncio.Future()
        mock_recv.return_value.set_result("invalid message")
        mock_json.loads.side_effect = ValueError()  # Simulate JSON decoding error

        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.ws_server.recv(mock_ws))

        mock_ws.send.assert_called_with('{"error": "Message received not in JSON string."}')

    @patch('OlafServer.WebSocketServer.send')
    @patch('OlafServer.WebSocketServer.existing_connection')
    def test_client_list_request(self, mock_existing_connection, mock_send):
        """
        Test client list request handler.
        """
        mock_ws = AsyncMock()
        mock_existing_connection.return_value = True
        client = OlafClientConnection(mock_ws, "client_public_key")
        self.ws_server.clients.add(client)

        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.ws_server.client_list_request_handler(mock_ws))

        mock_send.assert_called_once()
        response = mock_send.call_args[0][1]
        self.assertIn("client_list", response)
        self.assertIn("clients", response)

    @patch('OlafServer.WebSocketServer.send')
    def test_disconnect_client(self, mock_send):
        """
        Test that a client is correctly removed after disconnection.
        """
        mock_ws = AsyncMock()
        client = OlafClientConnection(mock_ws, "client_public_key")
        self.ws_server.clients.add(client)

        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.ws_server.disconnect(mock_ws))

        self.assertEqual(len(self.ws_server.clients), 0)
        mock_ws.close.assert_called_once()


class TestWebSocketServerFileUpload(unittest.TestCase):
    
    @patch('OlafServer.os')
    @patch('OlafServer.web.FileResponse')
    def test_file_download(self, mock_file_response, mock_os):
        """
        Test file download functionality.
        """
        # Mocking the os and file existence check
        mock_os.path.exists.return_value = True
        mock_file_response.return_value = "file_content"
        
        # Setup request and filename
        mock_request = MagicMock()
        mock_request.match_info.get.return_value = 'testfile.txt'
        
        # Instantiate the server and run the download handler
        neighbours = {"ws://localhost:8001": "server2_key"}
        ws_server = WebSocketServer('localhost', 9000, 9001, neighbours, 'Server_1_public_key')
        
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(ws_server.download_file(mock_request))

        self.assertEqual(response, "file_content")
        mock_os.path.exists.assert_called_with('uploads/testfile.txt')
        mock_file_response.assert_called_once()

    @patch('OlafServer.web.json_response')
    @patch('OlafServer.os')
    @patch('OlafServer.open', new_callable=MagicMock)
    def test_file_upload(self, mock_open, mock_os, mock_json_response):
        """
        Test file upload functionality.
        """
        mock_request = AsyncMock()
        mock_field = AsyncMock()
        mock_field.name = 'file'
        mock_field.filename = 'testfile.txt'
        mock_field.read_chunk = AsyncMock(return_value=b'test content')
        mock_reader = AsyncMock()
        mock_reader.next.return_value = mock_field
        mock_request.multipart.return_value = mock_reader

        neighbours = {"ws://localhost:8001": "server2_key"}
        ws_server = WebSocketServer('localhost', 9000, 9001, neighbours, 'Server_1_public_key')

        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(ws_server.upload_file(mock_request))

        mock_open.assert_called_once_with('uploads/testfile.txt', 'wb')
        mock_json_response.assert_called_once_with({'file_url': 'http://localhost:9001/download/testfile.txt'})
        self.assertEqual(response, mock_json_response())

if __name__ == "__main__":
    unittest.main()
