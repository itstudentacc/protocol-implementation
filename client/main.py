import asyncio
from client import Client

async def main():
    client = Client()

    try:
        await client.connect()
    except ValueError as e:
        print(f"Failed to connect: {e}")
        return

    await client.send_hello()

    while True:
        try:
            # Display a prompt and read user input
            msg_type = input("Enter your message type ('public', 'private' or 'quit' to exit): ")

            if msg_type == "public":
                message = input("Enter your public message: ")
                await client.send_public_chat(message)

            elif msg_type == "private":
                recipient_fingerprint = input("Enter recipient fingerprint: ")
                chat_message = input("Enter your private message: ")
                await client.send_private_chat(recipient_fingerprint, chat_message)

            elif msg_type == "quit":
                await client.close()
                break

            else:
                print("Invalid message type. Please enter 'public', 'private', or 'quit'.")

        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
