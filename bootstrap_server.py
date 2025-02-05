#!/usr/bin/env python3
import socket
import threading
import json

# Global list of registered peers
PEERS = []  # Each peer is stored as {"address": ip, "port": port}
PEERS_LOCK = threading.Lock()

def handle_client(conn, addr):
    try:
        # Use a file-like object to read/write JSON lines
        file = conn.makefile(mode='rw')
        line = file.readline()
        if not line:
            return
        message = json.loads(line.strip())
        action = message.get("action")
        if action == "register":
            peer_info = {"address": message.get("address"), "port": message.get("port")}
            with PEERS_LOCK:
                if peer_info not in PEERS:
                    PEERS.append(peer_info)
                    print(f"Registered peer: {peer_info}")
            # Acknowledge registration
            response = {"status": "registered"}
            file.write(json.dumps(response) + "\n")
            file.flush()
        elif action == "get_peers":
            with PEERS_LOCK:
                response = {"peers": PEERS}
            file.write(json.dumps(response) + "\n")
            file.flush()
    except Exception as e:
        print(f"Error handling client {addr}: {e}")
    finally:
        conn.close()

def main():
    HOST = "0.0.0.0"
    PORT = 8000  # You can change this port if needed
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"Bootstrap server listening on {HOST}:{PORT}")
    try:
        while True:
            conn, addr = server.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
    except KeyboardInterrupt:
        print("Shutting down bootstrap server.")
    finally:
        server.close()

if __name__ == '__main__':
    main()
