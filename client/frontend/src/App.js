import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');

  useEffect(() => {
    // Fetch initial messages from the server
    fetch('/api/messages')
      .then(response => response.json())
      .then(data => setMessages(data));
  }, []);

  const sendMessage = () => {
    if (input.trim() === '') return;

    const newMessage = { text: input, timestamp: new Date() };

    // Send the message to the server
    fetch('/api/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(newMessage),
    })
      .then(response => response.json())
      .then(data => {
        setMessages([...messages, data]);
        setInput('');
      });
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Chat Application</h1>
        <div className="chat-window">
          {messages.map((message, index) => (
            <div key={index} className="chat-message">
              <span>{message.text}</span>
              <span className="timestamp">{new Date(message.timestamp).toLocaleTimeString()}</span>
            </div>
          ))}
        </div>
        <div className="chat-input">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type a message..."
          />
          <button onClick={sendMessage}>Send</button>
        </div>
      </header>
    </div>
  );
}

export default App;
