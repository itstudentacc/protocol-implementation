import asyncio
import json
import logging
# import websockets
from websockets.asyncio.server import serve, broadcast
from websockets.asyncio.client import connect

logging.basicConfig()

CLIENTS = set()
NEIGHBOURS = set()
GLOBAL_CLIENTS = set()
MSG_TYPES = [
    'signed_data', 
    'client_list_request', 
    'client_list', 
    'client_update', 
    'client_update_request'
]

def check_message(message: str) -> bool:
    req_msg_keys = ['type', 'data', 'counter', 'signature']
    message_object = json.loads(message)
    print(type(message_object['data']))
    for key in message_object.keys():
        if key not in req_msg_keys:
            return False

    return True

async def add_client(websocket):
    global CLIENTS
    try:
        # Register Client
        async for message in websocket:
            msg_follows_protocol = check_message(message)
            if msg_follows_protocol:
                CLIENTS.add(message['data']['public_key'])
                await websocket.send("Success from server1")
    finally:
        CLIENTS.remove(websocket)

async def echo_message(websocket):
    print(websocket.remote_address[0])
    try:
        message = await websocket.recv()
        if type(message) == str:
            message = json.loads(message)
            print(message)
        reply = f"Data received as: {message}"
        await websocket.send(json.dumps(reply))
    except:
        print("Some error in server echo_message")

async def route_message(message):
    """
    This function routes the message to the server needed (out-going), or to the 
    all clients connected to it (in-coming). It sends the message to all clients,
    but not all can decode it.
    """
    data = message['data']
    dest_servers = data['destination_servers']

    for server_addr in dest_servers:
        uri = f"ws://{server_addr}"
        
        async with connect(uri) as websocket:
            try:
               await websocket.send(json.dumps(message)) 

            except:
                print(f"Error in sending message to server {server_addr}")


async def handle_signed_data(websocket, message: object):
    """
    Handles all type of signed data. Signed data means that it comes from a client.
    3 types of signed data:
        - Hello
        - Chat
        - Public Chat
    """
    data = message['data']
    
    match data['type']:
        case 'hello':
            await add_client(websocket)
        
        case 'chat':
            await route_message(message)

        case 'public_chat':
            await broadcast(data['message'])

async def handle_client_list_request(websocket):
    """
    This function handles any client list requests.
    """
    response = {
        "type" : "client_list",
        "servers" : list(GLOBAL_CLIENTS)
    }

    await websocket.send(json.dumps(response))

def handle_client_list(message):
    """
    This funtion takes the client_list message and updates the GLOBAL_CLIENTS set it has.
    """
    servers = message['servers']
    global GLOBAL_CLIENTS
    GLOBAL_CLIENTS = set(servers)


def handle_client_update(websocket, message):
    """
    Updates server's GLOBAL_CLIENTS according to message.
    """
    addr = websocket.remote_address[0]
    port = websocket.remote_address[1]

    server_to_update = f"{addr}:{port}"
    updated_clients = message['clients']

    global GLOBAL_CLIENTS
    for server_clients in GLOBAL_CLIENTS:
        server = server_clients['server']

        if server == server_to_update:
            GLOBAL_CLIENTS.remove(server_clients)
            updated_list = {
                "server" : server,
                "clients" : updated_clients
            }
            GLOBAL_CLIENTS.add(updated_list)
    

async def handle_client_update_request(websocket):
    """
    Sends a client_update message to the server that requested it.
    """
    client_update = {
        "type" : "client_update",
        "clients" : list(CLIENTS)
    }

    await websocket.send(json.dumps(client_update))


async def handle_message(websocket):
    """
    This functions checks whether an incoming message fits the protocol's structure.
    If so, fulfill request. Else, return a 'request rejected' message.
    """

    try:
        message = await websocket.recv()
        if type(message) == str: message = json.loads(message) # Change to object for easier processing.
        match message['type']:
            case 'signed_data':
                await handle_signed_data(websocket, message)

            case 'client_list_request':
                await handle_client_list_request(websocket)

            case 'client_list':
                print('client_list')
                handle_client_list(message)

            case 'client_update':
                handle_client_update(websocket, message)
                
            case 'client_update_request':
                await handle_client_update_request(websocket)

            case _:
                print('Unknown message type. request not fulfilled.')
                await websocket.send("Invalid Message...")

    except:
        print("Error in handle_message")

async def start_server(host = 'localhost', port = 8000) -> None:
    """
    Start the server and listen for connections
    """
    print(f"Listening on port {port}...")

    async with serve(echo_message, host, port):
        await asyncio.get_running_loop().create_future() # run forever


async def join_neighbourhood() -> bool:
    """
    This function asks for the address and ports of running servers,
    Attempts connection to each one of them, and sends a client_update_request.
    """
    print("Attempting to join neighbourhood...")

    num_servers = int(input("Enter no. of servers in neighbourhood (0 If this is first server in neighbourhood): "))
    global NEIGHBOURS, GLOBAL_CLIENTS

    for i in range(1, num_servers + 1):
        address = input(f"   Enter Server {i}'s address: ")
        NEIGHBOURS.add(address)
    
    for address in NEIGHBOURS:
        uri = f"ws://{address}"
        async with connect(uri) as websocket:
            try:
                client_update_request = {
                    "type": "client_update_request"
                }
                await websocket.send(json.dumps(client_update_request))

                client_update = await websocket.recv()
                if type(client_update) == str: json.loads(client_update)

                server_clients = {
                    "address" : address,
                    "clients" : client_update['clients'],
                }
                GLOBAL_CLIENTS.add(server_clients)

            except:
                print("Error in server's join_neighbourhood")
                return False
    
    return True


async def main():
    print("Server initialisation")

    in_neighbourhood = await join_neighbourhood()

    if in_neighbourhood:
        print("Neighbourhod joined.")
        await start_server()
    else:
        print("Failed to join neighbourhood. Unable to start server.")


if __name__ == "__main__":
    asyncio.run(main())