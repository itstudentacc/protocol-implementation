# Group 17 OLAF Protocol Implementation

### Group members: Ivan Tranquilan, Kyle Johnston, Gregorius Baswara Wira Nuraga

## DESCRIPTION
This is a Python implementation of the OLAF's Neighbourhood protocol (https://github.com/xvk-64/2024-secure-programming-protocol), designed to facilitate secure messaging between clients and servers.

## TECH STACK
- Python 3.10/11: For the main code implementation of our clients and servers
- WebSockets: For real time client/server communication
- Cryptography: For encryption/decryption
- Asyncio: Python asynchronous programming
- Aioconsole: For asynchronous I/O for our command-line interface
- Aiohttp: Asynchronous HTTP

## SERVER

The server consists of two files:
`server/websocket_server/OlafServer.py` Handles the websocket aspects of the server. It is accessible on `ws://localhost:9000`
`server/filer_handler/main.py` Handles the file upload of the server. It is accessible on `http://localhost:8001`

View the `server/README.md` for pre-requisites and how to run the server.

## CLIENT

Client consists of one main file:
`client/client.py` Handles the main instace of the client, including a terminal UI

view `client/README.md` for instructions regarding the client.

The client files are tested 3.10/11

### Pre-requisites

- Python 3.10+
- pip

### How to Run

1. Navigate to client dir `cd client`
2. Install dependencies `pip install requirements.txt`
3. Run a client instance `python3 client.py`

### Backdoors

1. I could really use a margarita right now ... I should let everyone know too ...
2. I wonder what happens if I upload a .txt file with something inside ...
3. TBA
