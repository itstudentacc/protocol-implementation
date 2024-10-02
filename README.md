# Group 17 OLAF Protocol Implementation

### Ivan Tranquilan, Kyle Johnston, Gregorius Baswara Wira Nuraga

# OLAF Neighbourhood protocol client

This is the client-side implementation of the OLAF Neighbourhood chat protocol. It supports features such as secure encrypted messaging using RSA and AES-GCM, public and private chats, and message signing for integrity verification.

## Features

- Secure messaging: Utilises RSA for asymmetric and AES-GCM for symmetric encryption for confidentiality

- Public chat: Allows for broadcasting public announcements to all connected clients

- Private chat: Supports sending private messages to one or more recipients

- File transfer: Allows for sending files to the server, with a link generated for download

- File listing: Supports listing all files uploaded to the server

- Clients: Supports listing all connected clients, with randomly generated nicknames for quality of life

## Install dependencies

Use `pip install -r requirements.txt`

## Running the client

Use the following command `python3 client.py`

This connects to the local WebSocket server

## Command-line Input

Once the client has begun running, you will be prompted to enter a message type. It is recommended to list the clients first, to see who is online.

- Public: Sends a public message to all clients. You will then be prompted to enter the message text

- Chat: Sends a private message to one or more specific clients. You will need to enter the nicknames of the recipients, and then the message text

- Clients: lists all currently connected client, by nickname

- /transfer: Sends a file to the server. You will need to enter the file name and the recipient's nickname (if sending privately). You can __download__ the files by clicking the link on the message

- Files: Lists all files uploaded to the server

- Exit: Disconnects from the server and exits the program

## Example Usage:

1. Sending a public chat message

- `Enter message type (public, chat, clients, /transfer, files): public`
- `Enter public chat message: Hello everyone!`
- `Sent public chat message: Hello everyone!`

2. Sending a Private Chat

   - `Enter message type (public, chat, clients, /transfer, files): chat`
   - `Enter recipient names, seperated by commas: Alice,Bob`
   - `Enter chat message: Hi guys`
   - `Sent chat message to Alice, Bob: Hi guys`

3. Listing Clients
   `Enter message type (public, chat, clients, /transfer, files): clients`

- `Connected clients:`
- `- Alice`
- `- Bob`
- `- Charlie`
- `- John (me)`

4. Sending file through Public Chat or Private Chat (Files need to be within the same directory!)
- File upload through public chat : `Enter message type (public, chat, clients, /transfer, files ): /transfer [file to upload]`
- `Enter message type (public, chat, clients, /transfer, files ): /transfer file.txt`
- `Public chat from [your username] : [file] https://localhost:9000/file/file.txt`
- File upload through private chat : `Enter message type (public, chat, clients, /transfer, files ): /transfer [file to upload] [recipient]`
- `Enter message type (public, chat, clients, /transfer, files ): /transfer file.txt Alice`
- `New chat from [your username] : [file] https://localhost:9000/file/file.txt`

5. View uploaded files

- `Enter message type (public, chat, clients, /transfer, files): files`
- `Uploaded files:`
- `{"files": ["file.txt"]}`

6. Exiting the client

- `Enter message type (public, chat, clients, /transfer, files): exit`

- `connection closed`

## File structure

- client.py: The main client implementation that handles WebSocket connection, encryption, and UI

- security/security_module.py: Contains encryption/ decryption and message signing methods.

- nickname_generator.py: Generates nicknames based on their fingerprints for easier identification of clients.

# OLAF Neighbourhood Protocol Server

This is tested in WSL Ubuntu 22.04

## Pre-Requisities

This program needs the following to be installed on the system:

- Python 3.10
- Pip

## How to use

To run an instance of the server:

1. Navigate to websocket_server dir `cd websocket_server`
2. Install the requirements `pip install -r requirements.txt`
3. Run the network of servers `python3 OlafServer.py`

# Notes

OlafServer.py runs two instances of the OLAF Websocket Server implementation on

- ws://localhost:9000
- ws://localhost:8001

Theese servers are in a neighbourhood of their own.

IF you wanted to connect to another server, update the neighbours dict (line 786 for server1 and line 792 for server2) to include neighbours in the format

```
{ server_addr : server_public_key }
```

`server_addr` must be in the format `ws::<server_hostname>:<server_port>`.
`server_public_key` must be copied in as a string.

You can also remove the an instance of the server by removing one of the start commands (Line 797 or 798).

## Future

- Proper frontend for the client either with a GUI or a web interface
