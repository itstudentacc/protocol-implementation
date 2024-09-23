import asyncio
from client import Client

async def main():
    
    client = Client()
    
    while True:
        
        await client.connect()
        await client.send_hello()
        
        await client.receive_public_chat()
        
        await client.close()
    
        break

if __name__ == "__main__":
    asyncio.run(main())
        
        