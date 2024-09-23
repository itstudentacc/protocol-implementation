from OlafServer import WebSocketServer

def main():
    neighbours = {
        "ws://localhost:8000" : "server1_key"
    }
    olaf_server1 = WebSocketServer('localhost', 8001, neighbours)
    olaf_server1.run()

if __name__ == '__main__':
    main()
