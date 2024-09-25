import asyncio
from client import Client

async def main():
    client = Client()
    
    await client.connect()  # Await the start method
    

if __name__ == "__main__":
    asyncio.run(main())  # Run the main function using asyncio
