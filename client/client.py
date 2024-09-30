import json
import base64
import asyncio
import aioconsole
import websockets
import sys
import io
import tkinter as tk
from PIL import Image, ImageTk
from tkinter import filedialog, messagebox,simpledialog
from security.security_module import Encryption
from nickname_generator import generate_nickname


class Client:
    def __init__(self, server_address="ws://localhost:9000"):
        self.server_address = server_address
        self.encryption = Encryption()
        self.connection = None
        self.counter = 0
        self.public_key = None
        self.private_key = None
        self.last_counters = {} # {fingerprint: counter}
        self.received_messages = []  # Fixed typo
        self.clients = {} # {fingerprint: public_key}
        self.server_fingerprints = {} # {fingerprint: server_address}
        self.nicknames = {} # {fingerprint: nickname}  
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
    async def start(self):
        # Generate RSA key pair
        self.public_key_pem, self.private_key_pem = self.encryption.generate_rsa_key_pair()
        self.public_key = self.encryption.load_public_key(self.public_key_pem)
        self.private_key = self.encryption.load_private_key(self.private_key_pem)

        
        await self.connect()
        await self.input_prompt()
        self.loop.run_forever()
    
    def popup_upload(self):
        # Create a new tkinter window for uploading files
        self.root = tk.Tk()
        self.root.title("Chat Upload Window")
        self.root.geometry("400x400")

        # Add a text area to show file content preview
        self.file_preview_text = tk.Text(self.root, height=10, width=40)
        self.file_preview_text.pack(pady=10)

        # Create a button for choosing a file
        choose_button = tk.Button(self.root, text="Choose File", command=self.choose_file)
        choose_button.pack(pady=10)

        # Dropdown list for recipients
        self.recipient_var = tk.StringVar(self.root)
        self.recipient_var.set("Select recipient")
        self.update_recipient_list()  # Populate the dropdown list

        self.recipient_menu = tk.OptionMenu(self.root, self.recipient_var, *self.recipients_list)
        self.recipient_menu.pack(pady=10)

        # Create a button for uploading files
        upload_button = tk.Button(self.root, text="Upload File", command=self.start_upload_file)
        upload_button.pack(pady=10)

        # Bind the close event to handle the safe exit
        self.root.protocol("WM_DELETE_WINDOW", self.safe_exit)

        # Run the tkinter window
        self.root.mainloop()

    def update_recipient_list(self):
        # Generate a list of connected clients excluding the current user
        self.recipients_list = [nickname for fingerprint, nickname in self.nicknames.items() if fingerprint != self.encryption.generate_fingerprint(self.public_key_pem)]

    def choose_file(self):
        # Prompt the user to select a file
        self.file_path = filedialog.askopenfilename()
        if self.file_path:
            print(f"File chosen: {self.file_path}")
            messagebox.showinfo("Selected File", f"Selected file: {self.file_path}")

            # Clear previous content in the preview area
            self.file_preview_text.delete(1.0, tk.END)
            # Safely destroy img_label if it exists
            if hasattr(self, 'img_label') and self.img_label.winfo_exists():
                self.img_label.destroy()

            # Check if the file is an image
            if self.file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                try:
                    # Open the image file
                    img = Image.open(self.file_path)
                    img.thumbnail((200, 200))  # Resize image to fit the preview area
                    self.img = ImageTk.PhotoImage(img)

                    # Display the image inside the text box
                    self.file_preview_text.image_create(tk.END, image=self.img)

                except Exception as e:
                    print(f"Error displaying image: {e}")
                    messagebox.showerror("Error", f"Could not display image: {str(e)}")

            else:
                try:
                    # Preview the text content for non-image files
                    with open(self.file_path, 'r') as file:
                        content = file.read(200)  # Read the first 200 characters
                        self.file_preview_text.insert(tk.END, content)
                except Exception as e:
                    print(f"Error displaying file content: {e}")
                    messagebox.showerror("Error", f"Could not display file content: {str(e)}")

    def start_upload_file(self):
        # Check if a file has been selected
        if hasattr(self, 'file_path') and self.file_path:
            # Get the selected recipient from the dropdown
            recipient_nickname = self.recipient_var.get()
            if recipient_nickname == "Select recipient":
                messagebox.showerror("Error", "Please select a recipient.")
                return

            # Store the selected recipient
            self.recipients = [recipient_nickname]

            # Call the async upload_file method using the event loop
            asyncio.run_coroutine_threadsafe(self.upload_file(), self.loop)
        else:
            messagebox.showerror("Error", "No file selected. Please choose a file first.")

    async def upload_file(self):
        if self.file_path:
            try:
                with open(self.file_path, "rb") as file:
                    file_data = file.read()

                    if len(file_data) > 10 * 1024 * 1024:
                        messagebox.showerror("Error", "File size exceeds 10MB")
                        return

                    file_base64 = base64.b64encode(file_data).decode('utf-8')

                    self.counter += 1
                    fingerprint = self.encryption.generate_fingerprint(self.public_key_pem)

                    # Get the recipient public keys
                    recipients = [fingerprint for fingerprint, nickname in self.nicknames.items() if nickname in self.recipients]
                    if not recipients:
                        messagebox.showerror("Error", "No valid recipients found.")
                        return

                    recipient_public_keys = [self.clients[fingerprint] for fingerprint in recipients]
                    destination_servers = list({self.server_fingerprints.get(fingerprint) for fingerprint in recipients})

                    message_data = {
                        "type": "file_upload",
                        "sender": fingerprint,
                        "file_name": self.file_path.split('/')[-1],
                        "file_data": file_base64,
                        "destination_servers": destination_servers,
                        "recipients": recipients
                    }

                    message = self.build_signed_data(message_data)
                    message_json = json.dumps(message)

                    await self.send(message_json)
                    messagebox.showinfo("Success", f"Uploaded file: {self.file_path}")

            except FileNotFoundError:
                print("File not found. Please check the file path.")
            except Exception as e:
                messagebox.showerror("Error", f"Error uploading file: {str(e)}")

    async def close(self):
        if self.connection:
            try:
                await self.connection.close()
                print("Connection closed")
            except Exception as e:
                print(f"Failed to close connection: {e}")
            finally:
                self.connection = None

        # Stop the event loop
        if not self.loop.is_closed():
            self.loop.stop()

    def safe_exit(self):
        # Method to safely exit the popup window and close the upload process
        if hasattr(self, 'root') and self.root.winfo_exists():
            self.root.destroy()  # Destroy the popup window
        print("Safe exit initiated.")

        # Close the connection and stop the loop
        asyncio.run_coroutine_threadsafe(self.close(), self.loop)

    def handle_file_upload(self, message):
        data = message.get("data")
        
        sender_fingerprint = data.get("sender")
        sender_nickname = self.nicknames.get(sender_fingerprint, "unknown")
        
        file_name = data.get("file_name")
        file_data_base64 = data.get("file_data")

        # Decode base64 file data
        self.file_data = base64.b64decode(file_data_base64.encode('utf-8'))
        self.received_file_name = file_name

        # Create a popup window to notify the user about the received file
        self.file_popup = tk.Toplevel()
        self.file_popup.title("File Received")
        self.file_popup.geometry("300x200")

        # Display a label with the sender's information
        label = tk.Label(self.file_popup, text=f"Receiving file from {sender_nickname}")
        label.pack(pady=10)

        # Add a button to open the file
        open_button = tk.Button(self.file_popup, text="Open File", command=self.open_received_file)
        open_button.pack(pady=20)

def open_received_file(self):
    # Create a new popup to display the content of the file
    file_viewer = tk.Toplevel()
    file_viewer.title(f"Viewing {self.received_file_name}")
    file_viewer.geometry("400x400")

    # Add a text area to show the content of the file
    text_area = tk.Text(file_viewer, height=20, width=40)
    text_area.pack(pady=10)

    # Try to display the content based on the file type
    if self.received_file_name.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
        try:
            # Display image file
            img = Image.open(io.BytesIO(self.file_data))
            img.thumbnail((300, 300))
            self.img = ImageTk.PhotoImage(img)

            # Create an image label in the text area
            text_area.image_create(tk.END, image=self.img)

        except Exception as e:
            print(f"Error displaying image: {e}")
            messagebox.showerror("Error", f"Could not display image: {str(e)}")
    else:
        try:
            # Display text file content
            content = self.file_data.decode('utf-8', errors='ignore')
            text_area.insert(tk.END, content)
        except Exception as e:
            print(f"Error displaying file content: {e}")
            messagebox.showerror("Error", f"Could not display file content: {str(e)}")

    # Close the original file popup
    self.file_popup.destroy()

                
    def parse_message(self, message):
        try:
            message_dict = json.loads(message)
            return message_dict, None
        except json.JSONDecodeError as e:
            return None, f"Error parsing JSON: {str(e)}"

    def build_signed_data(self, data):
        message = {
            "data": data,
            "counter": self.counter
        }

        message_json = json.dumps(message, separators=(',', ':'), sort_keys=True)
        message_bytes = message_json.encode('utf-8')

        # Sign the message
        signature = self.encryption.sign_message(message_bytes, self.private_key_pem)
        signature_base64 = base64.b64encode(signature).decode('utf-8')

        # Prepare the signed message
        signed_data = {
            "type": "signed_data",
            "data": data,
            "counter": self.counter,
            "signature": signature_base64
        }

        return signed_data
    
    def build_chat_message(self, destination_servers, recipient_public_keys, chat):
        
        aes_key = self.encryption.generate_aes_key()
        iv = self.encryption.generate_iv()
        iv_base64 = base64.b64encode(iv).decode('utf-8')
        
        sender_fingerprint = self.encryption.generate_fingerprint(self.public_key_pem)
        participants = [sender_fingerprint] + [self.encryption.generate_fingerprint(public_key) for public_key in recipient_public_keys]
        
        chat_data = {
            "chat": {
                "participants": participants,
                "message": chat
            },
        }
        chat_data_json = json.dumps(chat_data)
        
        ciphertext, tag = self.encryption.encrypt_aes_gcm(chat_data_json.encode('utf-8'), aes_key, iv)
        chat_base64 = base64.b64encode(ciphertext + tag).decode('utf-8')
        
        symm_keys = []
        for public_key in recipient_public_keys:
            public_key_pem = self.encryption.load_public_key(public_key)
            encrypted_symm_key = self.encryption.encrypt_rsa(aes_key, public_key_pem)
            encrypted_symm_key_base64 = base64.b64encode(encrypted_symm_key).decode('utf-8')
            symm_keys.append(encrypted_symm_key_base64)
            
        signed_data = {
            "type": "chat",
            "destination_servers": destination_servers,
            "iv": iv_base64,
            "symm_keys": symm_keys,
            "chat": chat_base64
        }
        
        signed_data = self.build_signed_data(signed_data)
        return signed_data
    
    def print_clients(self):
        
        print("\nConnected clients:\n")
        
        if not self.clients:
            print("No clients connected")
        
        for fingerprint, public_key in self.clients.items():
            if fingerprint not in self.nicknames:
                nickname = generate_nickname(fingerprint)
                self.nicknames[fingerprint] = nickname
            else:
                nickname = self.nicknames[fingerprint]
            
            if fingerprint == self.encryption.generate_fingerprint(self.public_key_pem):
                print (f"   -{nickname} (me)")
            else:
                print (f"   -{nickname}")
        
        print("\n")
            
    async def input_prompt(self):
        while True:
            
            message = await aioconsole.ainput("Enter message type (public, chat, clients, upload): ")
            if message == "public":
                await self.request_client_list()
                chat = await aioconsole.ainput("Enter public chat message: ")
                await self.send_public_chat(chat)
            elif message == "chat":
                await self.request_client_list()
                recipients = await aioconsole.ainput("Enter recipient names, seperated by commas: ")
                chat = await aioconsole.ainput("Enter chat message: ")
                await self.send_chat(recipients.split(","), chat)
            elif message == "clients":
                await self.request_client_list()
                self.print_clients()
            elif message == "upload":
                self.popup_upload()
            elif message == "exit":
                await self.close()
                break
            else:
                print("Invalid message type")
                
                
    async def connect(self):
        try:
            self.connection = await websockets.connect(self.server_address)
            print(f"Connected to {self.server_address}")

            await self.send_hello()

            # Listen for incoming messages
            asyncio.ensure_future(self.receive())
            
            await self.request_client_list()

        except Exception as e:
            print(f"Failed to connect: {e}")
            sys.exit(1)

    async def close(self):
        if self.connection:
            try:
                await self.connection.close()
                print("Connection closed")
                sys.exit(0)
            except Exception as e:
                print(f"Failed to close connection: {e}")
            finally:
                self.connection = None

    async def send_hello(self):
        self.counter += 1
        
        public_pem = self.public_key_pem.decode('utf-8')
        

        message_data = {
            "type": "hello",
            "public_key": public_pem  
        }

        message = self.build_signed_data(message_data)

        
        json_message = json.dumps(message)
        
        await self.send(json_message)
        

    async def send_public_chat(self, chat):
        self.counter += 1
        
        fingerprint = self.encryption.generate_fingerprint(self.public_key_pem)

        message_data = {
            "type": "public_chat",
            "sender": fingerprint,
            "message": chat
        }

        message = self.build_signed_data(message_data)

        message_json = json.dumps(message)
        
        await self.send(message_json)
        print(f"Sent public chat message: {chat}")
        
        
    async def send_chat(self, recipients_nicknames, chat):
        
        recipients = [fingerprint for fingerprint, nickname in self.nicknames.items() if nickname in recipients_nicknames]
                    
        valid_recipients = [fingerprint for fingerprint in recipients if fingerprint in self.clients]
        
        if not valid_recipients:
            print("No valid recipients")
            return
            
        recipient_public_keys = []
        destination_servers_set = set()
        
        for fingerprint in valid_recipients:
            server_address = self.server_fingerprints.get(fingerprint)
            if server_address:
                destination_servers_set.add(server_address)
                recipient_public_keys.append(self.clients[fingerprint])
            else:
                print(f"No server address for fingerprint: {fingerprint}")
                return
            
        destination_servers = list(destination_servers_set)
        if not destination_servers:
            print("No destination servers")
            return
        
        self.counter += 1
        
        signed_data = self.build_chat_message(destination_servers, recipient_public_keys, chat)
        message_json = json.dumps(signed_data)
        await self.send(message_json)
        print(f"Sent chat message to {recipients_nicknames}: {chat}")

    async def request_client_list(self):
        message = {
            "type": "client_list_request"
        }

        message_json = json.dumps(message)
        await self.send(message_json)

    async def receive(self):
        try:
            async for message in self.connection:
                message_dict, error = self.parse_message(message)
                if error:
                    print(f"Error parsing message: {error}")
                    continue

                await self.handle_message(message_dict)
        except websockets.ConnectionClosed:
            print("Connection closed")
            sys.exit(1)

    async def handle_message(self, message):
        
        await self.request_client_list()

        message_type = message.get("type") or message.get("data", {}).get("type")
        
        if message_type == "signed_data":
            message_type = message.get("data", {}).get("type")

        if message_type == "public_chat":
            await self.handle_public_chat(message)
        elif message_type == "client_list":
            await self.handle_client_list(message)
        elif message_type == "chat":
            await self.handle_chat(message)
        elif message_type == "upload_file":
            self.handle_file_upload(message)
        else:
            print(f"Unknown message type: {message_type}")

    async def handle_public_chat(self, message):
        data = message.get("data")  
        
        sender_fingerprint = data.get("sender")
        chat = data.get("message")
        self.received_messages.append({
            "sender": sender_fingerprint,
            "message": chat
        })
        
        sender_nickname = self.nicknames.get(sender_fingerprint)
        
        # check if sender is me
        if sender_fingerprint == self.encryption.generate_fingerprint(self.public_key_pem):
            sender_nickname = "me"
        
        print(f"\nPublic chat from {sender_nickname}: {chat}")

    async def handle_client_list(self, message):
        servers = message.get("servers", [])
        for server in servers:
            server_address = server.get("address")
            clients_pem = server.get("clients", [])
            for public_key_pem_str in clients_pem:
                public_key_pem = public_key_pem_str.encode('utf-8')
                fingerprint = self.encryption.generate_fingerprint(public_key_pem)
                self.clients[fingerprint] = public_key_pem
                self.server_fingerprints[fingerprint] = server_address
    
    def handle_file_upload(self, message):
        data = message.get("data")
        
        sender_fingerprint = data.get("sender")
        sender_nickname = self.nicknames.get(sender_fingerprint, "unknown")
        
        file_name = data.get("file_name")
        file_data_base64 = data.get("file_data")

        # decode base64 file data
        file_data = base64.b64decode(file_data_base64.encode('utf-8'))

        # save the file to the client's local directory
        save_directory = filedialog.askdirectory()
        if save_directory:
            with open(f"{save_directory}/{file_name}", "wb") as file:
                file.write(file_data)
                print(f"File '{file_name}' received from {sender_nickname} and saved to {save_directory}")
                messagebox.showinfo("Success", f"File '{file_name}' received from {sender_nickname} and saved to {save_directory}")
        else:
            print("File not saved")     
                
                
    async def handle_chat(self, message):
        data = message.get("data")
        

        symm_keys_base64 = data.get("symm_keys", [])
        iv_base64 = data.get("iv")
        chat_base64 = data.get("chat")
        
        if not symm_keys_base64 or not iv_base64 or not chat_base64:
            print("Invalid chat message")
            return
        
        my_fingerprint = self.encryption.generate_fingerprint(self.public_key_pem)
        decrypted = False

        iv = base64.b64decode(iv_base64.encode('utf-8'))
        cipher_and_tag = base64.b64decode(chat_base64.encode('utf-8'))
        ciphertext = cipher_and_tag[:-16]
        tag = cipher_and_tag[-16:]

        
        for idx, symm_keys_base64 in enumerate(symm_keys_base64):
            symm_key_encrypted = base64.b64decode(symm_keys_base64.encode('utf-8'))
            try: 
                symm_key = self.encryption.decrypt_rsa(symm_key_encrypted, self.private_key)
                plaintext_bytes = self.encryption.decrypt_aes_gcm(ciphertext, symm_key, iv, tag)
                chat_data = json.loads(plaintext_bytes.decode('utf-8'))
                
                chat_content = chat_data.get("chat", {})
                participants = chat_content.get("participants", [])
                message = chat_content.get("message", "")
                
                                
                if my_fingerprint in participants:
                    sender_fingerprint = participants[0]
                    
                    sender_nickname = self.nicknames.get(sender_fingerprint)
                    
                    message_entry = {
                        "sender": sender_fingerprint,
                        "message": message
                    }
                    self.received_messages.append(message_entry)
                    
                    print(f"\nChat from {sender_nickname}: {message}")
                    decrypted = True
                    break
            except Exception as e:
                continue
            
        if not decrypted:
            return
            

    async def send(self, message_json):
        try:
            await self.connection.send(message_json)
        except Exception as e:
            print(f"Error sending message: {e}")


client = Client()

if __name__ == "__main__":
    try:
        asyncio.run(client.start())
    except KeyboardInterrupt:
        print("Exiting...")
        asyncio.run(client.close())
    
    
