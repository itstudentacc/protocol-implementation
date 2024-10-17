# Group 17 OLAF Protocol Implementation
### Ivan Tranquilan, Kyle Johnston, Gregorius Baswara Wira Nuraga
### To ensure OLAF Chat Protocol is working, please follow the steps below!

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
- /transfer: Sends a file to the server. You will need to enter the file name and the recipient's nickname (if sending privately). You can **download** the files by clicking the link on the message
- Files: Lists all files uploaded to the server
- Exit: Disconnects from the server and exits the program

## Example Usage:
1. Sending a public chat message
-  `Enter message type (public, chat, clients, /transfer, files): public`
-  `Enter public chat message: Hello everyone!`
-  `Sent public chat message: Hello everyone!`
2. Sending a Private Chat
-  `Enter message type (public, chat, clients, /transfer, files): chat`
-  `Enter recipient names, seperated by commas: Alice,Bob`
-  `Enter chat message: Hi guys`
-  `Sent chat message to Alice, Bob: Hi guys`
3. Listing Clients
`Enter message type (public, chat, clients, /transfer, files): clients`
-  `Connected clients:`
-  `- Alice`
-  `- Bob`
-  `- Charlie`
-  `- John (me)`
4. Sending file through Public Chat or Private Chat (Files need to be within the same directory!)
- File upload through public chat : `Enter message type (public, chat, clients, /transfer, files ): /transfer [file to upload]`
-  `Enter message type (public, chat, clients, /transfer, files ): /transfer file.txt`
-  `Public chat from [your username] : [file] https://localhost:9000/file/file.txt`
- File upload through private chat : `Enter message type (public, chat, clients, /transfer, files ): /transfer [file to upload] [recipient]`
-  `Enter message type (public, chat, clients, /transfer, files ): /transfer file.txt Alice`
-  `New chat from [your username] : [file] https://localhost:9000/file/file.txt`
5. View uploaded files
-  `Enter message type (public, chat, clients, /transfer, files): files`
-  `Uploaded files:`
-  `{"files": ["file.txt"]}`
6. Exiting the client
-  `Enter message type (public, chat, clients, /transfer, files): exit`
-  `connection closed`

## File structure
- client.py: The main client implementation that handles WebSocket connection, encryption, and UI
- security/security_module.py: Contains encryption/ decryption and message signing methods.
- nickname_generator.py: Generates nicknames based on their fingerprints for easier identification of clients.

# OLAF Neighbourhood Protocol Server
This is tested in WSL Ubuntu 22.04

## Pre-Requisities
This program needs the following to be installed on the system:
- Docker
- Docker Compose. Note that this was developed and tested with Docker Compose version v2.29.2-desktop.2 in WSL. Try to have the latest version of docker compose you can.

## How to use
To run the neighbourhood:
1. Navigate root dir
2. Run `docker compose up --build`
3. When finished with the servers: `docker compose down`

# Notes
OlafServer.py runs two instances of the OLAF Websocket Server implementation on
1.  ws://localhost:9000 and a corresponding http server on http://localhost:9001 for file transfers
2.  ws://localhost:8000 and a corresponding http server on http://localhost:8001 for file transfers
- The servers may recognise each other by the `HOST` env variable in the compose file, however connecting to them when you are not in the same docker network as them you can reach them via the above addresses.
- These servers are in a neighbourhood of their own. With the way the servers are set up, each server will generate its own `.pem` key pair and save it to the `server/server_keys` directory.
- If you are connecting to an external server, please ensure that the public keys for that server are in the `server/server_keys` directory and must be in the format `[host]_[port]_public_key.pem`. 
- The neighbours must also be listed in the environment variables `NEIGHBOURS` in the `docker-compose.yaml` in the root dir. They should be comma separated strings.
- Since the clients are not dockerised, the file urls will return a localhost link. This means that it will only be accessible from the machine that the containers are run on.


## Future
- Proper frontend for the client either with a GUI or a web interface
- Incorporate correct url for files.
