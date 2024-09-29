# OLAF Neighbourhood protocol client

This is the client-side implementation of the OLAF Neighbourhood chat protocol. It supports features such as secure encrypted messaging using RSA and AES-GCM, public and private chats, and message signing for integrity verification.

## Features

- Secure messaging: Utilises RSA for asymmetric and AES-GCM for symmetric encryption for confidentiality

- Public chat: Allows for broadcasting public announcements to all connected clients

- Private chat: Supports sending private messages to one or more recipients

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

- Exit: Disconnects from the server and exits the program

## Example Usage:

1. Sending a public chat message

`Enter message type (public, chat, clients): public`
`Enter public chat message: Hello everyone!`
`Sent public chat message: Hello everyone!`

2. Sending a Private Chat
   `Enter message type (public, chat, clients): chat`
   `Enter recipient names, seperated by commas: Alice,Bob`
   `Enter chat message: Hi guys`
   `Sent chat message to Alice, Bob: Hi guys`

3. Listing Clients
   `Enter message type (public, chat, clients): clients`

`Connected clients:`
`- Alice`
`- Bob`
`- Charlie`
`- John (me)`

4. Exiting the client

`Enter message type (public, chat, clients): exit`

`connection closed`

## File structure

- client.py: The main client implementation that handles WebSocket connection, encryption, and UI

- security/security_module.py: Contains encryption/ decryption and message signing methods.

- nickname_generator.py: Generates nicknames based on their fingerprints for easier identification of clients.

## Future

- File transfer between clients
- Proper frontend
