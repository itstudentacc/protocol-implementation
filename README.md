# Architecture Overview

Initial Architecture Overview document for Secure Programming Group Assignment. This Outlines the functions and their purposes.

# Client Layer

## Establish

``connect(): connect to WebSocket server``

## Generate and Manage RSA key Pairs
```
generate_RSA_keys(private_key, public_key) : generate pair of RSA keys
export_public_key(public_key): export the public key generated for end to end encryption
get_public_key(public_key): method to obtain public key from the code
get_private_key(private_key): method to obtain private key from the code
```
## Send and receive encrypted messages
```
send_hello(): Send hello message when connecting to server to establish public key
send_message(dest, message): Encrypt and send message to someone
receive_message(): Listen for incoming messages, decrypt and receive
```
## File uploads and downloads
```
upload_file(): Upload file, server saves and returns url
download_file(url): Download file from url
```
## View connected users

``request_client(): Request list of connected clients``

## Verify message signatures
## Processes
```
Startup: Generate key pair -> Connect to server -> send hello
Send message: Encrypt message -> Sign Data -> send to server
Receive Message: Receive message -> Verify Signature -> Decrypt Message
```
# Server Layer

**Attributes**
```
client_list [] : List of clients connected to server
neighbour_list [] : List of servers known to server
Address : Server address
start_server() : Start websocket server and begin listening for connections
```
## Manage Connections

 ```
 get_servers_list() : Get the list of servers connected to it,
 
 add_client(client) : Add a new client to list once connection is complete
 ```

## Route Messages

```
check_message(message) : Ensures the message receives follows protocol message format
```

## Communicate with other servers in neighbourhood

```
send_client_update(client_update): Send a client update messaege to other servers int he neighbourhood after client connects or disconnects.

request_client_update(): Ask neighbourhood for client update from all servers.
```

## File upload/download
```
handle_file_upload(file) : store the file upload somewhere and return unique link to file.

serve_fil(url) : send the file to client
```
## Processes
```
Startup: Start server-> load neighbours -> request client updates
Client Handling: Accept connection -> Process hello -> Update client list
Message routing: Identify dest -> send message to correct server 
```
# Neighbourhood layer

```
servers[]: List of servers in neighbourhood
client_map: client map
```

## All servers in neighbourhood have consisten client information

```
synchornise_client_list(): ensures all servers have the same current info about the client, if not refer to update_client_info().

update_client_info(client_info): update the local server's list on their clients' info

add_server(server_address): Add server to neighbourhood

remove_server(server_address): Remove server from neighbourhood
```

## Server to server communication and message routing

```
broadcast_message_to_all(message): Broadcast's message to every server in the "neighbourhood" (@everyone)

server_to_server(dest, message): Send message to a dedicated server in the neighbourhood
```
## Processes
```
Initialisation: Load known servers -> Request Updates -> Sync client lists
Server changes: Detect new server -> broadcast message -> sync with new server.
```

# Backdoor
Ideas:

 - Allow a DOS attack to happen
 - Allow malware to be uploaded
 - Allow SQL Injection
 - 
