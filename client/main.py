import asyncio
from client import Client


async def main():
    client = Client()
    await client.connect()
    await client.send_hello()
    
    while True:
        # Display a prompt and read user input
        message = input("Enter your message type (or 'quit' to exit): ")
        
        if message.lower() == 'public':
            await client.send_public_chat()
        if message.lower() == 'chat':
            # await client.send_chat()
            break
        if message.lower() == 'quit':
            break
    
    await client.close()
    
    

if __name__ == "__main__":
    asyncio.run(main())
