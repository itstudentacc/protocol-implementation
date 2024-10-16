let socket;
let selectedChat = "public"; // Track chat type

// Initialize WebSocket connection
function connectToServer(serverAddress) {
    socket = new WebSocket(serverAddress);

    socket.onopen = () => {
        console.log("Connected to server:", serverAddress);
        sendHello();
    };

    socket.onmessage = (event) => {
        handleMessage(JSON.parse(event.data));
    };

    socket.onclose = () => {
        console.log("Disconnected from server");
    };
}

// Send a hello message
function sendHello() {
    const message = {
        type: "hello",
        public_key: "user_public_key", // Replace with actual key
    };
    socket.send(JSON.stringify(message));
}

// Handle received messages
function handleMessage(message) {
    if (message.type === "public_chat") {
        displayMessage("Public Chat", message.sender, message.message);
    } else if (message.type === "client_list") {
        updateUserList(message.clients);
    }
    // Add more handling as needed
}

// Display messages in chat
function displayMessage(chatType, sender, content) {
    const chatMessages = document.getElementById("chat-messages");
    const messageElement = document.createElement("div");
    messageElement.textContent = `${sender}: ${content}`;
    chatMessages.appendChild(messageElement);
}

// Update user list
function updateUserList(users) {
    const userList = document.getElementById("users");
    userList.innerHTML = ""; // Clear existing list
    users.forEach(user => {
        const userElement = document.createElement("li");
        userElement.textContent = user;
        userList.appendChild(userElement);
    });
}

// Send chat message
function sendMessage() {
    const messageBox = document.getElementById("message-box");
    const message = messageBox.value.trim();
    if (message) {
        const messageData = {
            type: selectedChat === "public" ? "public_chat" : "private_chat",
            message: message,
        };
        socket.send(JSON.stringify(messageData));
        messageBox.value = ""; // Clear input
    }
}

// Event listeners
document.getElementById("send-button").addEventListener("click", sendMessage);
document.getElementById("upload-button").addEventListener("click", () => {
    document.getElementById("file-input").click();
});
document.getElementById("view-logbook-button").addEventListener("click", () => {
    // Implement logbook retrieval
});

// File input change event for upload
document.getElementById("file-input").addEventListener("change", (event) => {
    const file = event.target.files[0];
    if (file) {
        uploadFile(file);
    }
});

// Function to upload file
function uploadFile(file) {
    const reader = new FileReader();
    reader.onload = () => {
        const fileData = reader.result;
        const messageData = {
            type: "file_upload",
            filename: file.name,
            filedata: fileData
        };
        socket.send(JSON.stringify(messageData));
        console.log(`Uploaded file: ${file.name}`);
    };
    reader.readAsDataURL(file);
}

// Initialize connection
connectToServer("ws://localhost:9000");
