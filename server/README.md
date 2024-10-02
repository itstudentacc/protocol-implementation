# OLAF Protocol Server

This is tested in WSL Ubuntu 22.04

## Pre-Requisities

This program needs the following to be installed on the system:
* Python 3.10
* Pip 

## How to use
To run an instance of the server:
1. Navigate to websocket_server dir `cd websocket_server`
2. Install the requirements `pip install -r requirements.txt`
3. Run the network of servers `python3 OlafServer.py`

# Notes
OlafServer.py runs two instances of the OLAF Websocket Server implementation on 

* ws://localhost:9000
* ws://localhost:8001

Theese servers are in a neighbourhood of their own.

IF you wanted to connect to another server, update the neighbours dict (line 786 for server1 and line 792 for server2) to include neighbours in the format
```
{ server_addr : server_public_key }
```
`server_addr` must be in the format `ws::<server_hostname>:<server_port>`.
`server_public_key` must be copied in as a string.

You can also remove the an instance of the server by removing one of the start commands (Line 797 or 798).

