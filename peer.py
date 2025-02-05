#!/usr/bin/env python3
import socket
import threading
import json
import os
import sys
import time

from utils import send_json, recv_json, CHUNK_SIZE, split_file, verify_chunk, encode_chunk, decode_chunk, ensure_files_dir

# Bootstrap server details (adjust if the server runs on a different host)
BOOTSTRAP_SERVER = ("127.0.0.1", 8000)

# Local dictionaries for shared files and ongoing transfers
shared_files = {}  # Format: { filename: { "num_chunks": int, "chunk_hashes": [...] } }
transfers = {}     # Placeholder for transfer status tracking

def register_with_bootstrap(my_address, my_port):
    """
    Registers this peer with the bootstrap server.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(BOOTSTRAP_SERVER)
        message = {"action": "register", "address": my_address, "port": my_port}
        send_json(s, message)
        response = recv_json(s)
        s.close()
        if response and response.get("status") == "registered":
            print("Successfully registered with the bootstrap server.")
    except Exception as e:
        print(f"Error registering with bootstrap server: {e}")

def get_peer_list():
    """
    Retrieves the list of active peers from the bootstrap server.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(BOOTSTRAP_SERVER)
        message = {"action": "get_peers"}
        send_json(s, message)
        response = recv_json(s)
        s.close()
        if response and "peers" in response:
            return response["peers"]
    except Exception as e:
        print(f"Error getting peer list: {e}")
    return []

def handle_client_connection(conn, addr):
    """
    Handles incoming requests from other peers.
    """
    try:
        file_obj = conn.makefile(mode='rw')
        line = file_obj.readline()
        if not line:
            return
        message = json.loads(line.strip())
        action = message.get("action")
        if action == "file_request":
            filename = message.get("filename")
            if filename in shared_files:
                # Prepare file metadata by re-splitting the file
                file_path = os.path.join("files", filename)
                _, chunk_hashes = split_file(file_path, CHUNK_SIZE)
                response = {
                    "action": "file_info",
                    "filename": filename,
                    "chunk_size": CHUNK_SIZE,
                    "num_chunks": len(chunk_hashes),
                    "chunk_hashes": chunk_hashes
                }
                file_obj.write(json.dumps(response) + "\n")
                file_obj.flush()
            else:
                response = {"action": "error", "message": "File not found"}
                file_obj.write(json.dumps(response) + "\n")
                file_obj.flush()
        elif action == "get_chunk":
            filename = message.get("filename")
            chunk_index = message.get("chunk_index")
            file_path = os.path.join("files", filename)
            if os.path.exists(file_path):
                with open(file_path, "rb") as f:
                    f.seek(chunk_index * CHUNK_SIZE)
                    chunk_data = f.read(CHUNK_SIZE)
                    # Encode the chunk so it can be sent in JSON
                    encoded_data = encode_chunk(chunk_data)
                    response = {
                        "action": "chunk_data",
                        "filename": filename,
                        "chunk_index": chunk_index,
                        "data": encoded_data
                    }
                    file_obj.write(json.dumps(response) + "\n")
                    file_obj.flush()
            else:
                response = {"action": "error", "message": "File not found"}
                file_obj.write(json.dumps(response) + "\n")
                file_obj.flush()
    except Exception as e:
        print(f"Error handling client connection from {addr}: {e}")
    finally:
        conn.close()

def server_listener(my_port):
    """
    Runs a server that listens for incoming connections from other peers.
    """
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", my_port))
    server.listen(5)
    print(f"Peer listening on port {my_port}")
    try:
        while True:
            conn, addr = server.accept()
            threading.Thread(target=handle_client_connection, args=(conn, addr), daemon=True).start()
    except Exception as e:
        print(f"Server listener error: {e}")
    finally:
        server.close()

def share_file(filename):
    """
    Shares a file by adding it to the local shared_files index.
    Ensure the file is placed in the 'files' directory.
    """
    file_path = os.path.join("files", filename)
    if not os.path.exists(file_path):
        print(f"File {filename} not found in the files/ directory.")
        return
    _, chunk_hashes = split_file(file_path, CHUNK_SIZE)
    shared_files[filename] = {
        "num_chunks": len(chunk_hashes),
        "chunk_hashes": chunk_hashes
    }
    print(f"File '{filename}' is now shared with peers.")

def download_file(filename):
    """
    Downloads a file from available peers chunk by chunk.
    """
    peers = get_peer_list()
    if not peers:
        print("No peers available.")
        return

    # Try each peer until the file is found
    for peer in peers:
        peer_addr = peer.get("address")
        peer_port = peer.get("port")
        try:
            print(f"Connecting to peer {peer_addr}:{peer_port} for file '{filename}'...")
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((peer_addr, peer_port))
            message = {"action": "file_request", "filename": filename}
            send_json(s, message)
            response = recv_json(s)
            s.close()
            if response.get("action") == "file_info":
                num_chunks = response.get("num_chunks")
                chunk_hashes = response.get("chunk_hashes")
                print(f"File info received: {num_chunks} chunks available.")
                # Download each chunk
                file_data = bytearray()
                for i in range(num_chunks):
                    success = False
                    # Try to get each chunk (with simple retry logic)
                    for attempt in range(3):
                        try:
                            s_chunk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            s_chunk.connect((peer_addr, peer_port))
                            chunk_request = {"action": "get_chunk", "filename": filename, "chunk_index": i}
                            send_json(s_chunk, chunk_request)
                            chunk_response = recv_json(s_chunk)
                            s_chunk.close()
                            if chunk_response.get("action") == "chunk_data":
                                encoded_data = chunk_response.get("data")
                                chunk_data = decode_chunk(encoded_data)
                                # Verify integrity of the chunk
                                if verify_chunk(chunk_data, chunk_hashes[i]):
                                    file_data.extend(chunk_data)
                                    print(f"Chunk {i+1}/{num_chunks} downloaded and verified.")
                                    success = True
                                    break
                                else:
                                    print(f"Chunk {i} failed integrity check. Retrying...")
                        except Exception as e:
                            print(f"Error downloading chunk {i} from {peer_addr}:{peer_port}: {e}")
                    if not success:
                        print(f"Failed to download chunk {i}. Aborting download.")
                        return
                # Save the assembled file into the files/ directory
                file_path = os.path.join("files", filename)
                with open(file_path, "wb") as f:
                    f.write(file_data)
                print(f"File '{filename}' downloaded successfully.")
                return
            else:
                print(f"Peer {peer_addr}:{peer_port} does not have file '{filename}'.")
        except Exception as e:
            print(f"Error connecting to peer {peer_addr}:{peer_port}: {e}")
    print(f"File '{filename}' not found on any peers.")

def print_status():
    """
    Prints the current transfer status (placeholder for more detailed tracking).
    """
    print("Current transfers:")
    if not transfers:
        print("No active transfers.")
    else:
        for filename, status in transfers.items():
            print(f"{filename}: {status}")

def cli_loop(my_address, my_port):
    """
    Command-line interface loop for user commands.
    """
    help_text = """
Available commands:
  share <filename>   - Share a file (ensure the file is in the 'files/' directory).
  list-peers         - List active peers from the bootstrap server.
  get <filename>     - Download a file from peers.
  status             - Show current file transfer status.
  exit               - Exit the program.
"""
    print(help_text)
    while True:
        try:
            command = input(">> ").strip()
            if not command:
                continue
            parts = command.split()
            cmd = parts[0]
            if cmd == "share":
                if len(parts) != 2:
                    print("Usage: share <filename>")
                    continue
                share_file(parts[1])
            elif cmd == "list-peers":
                peers = get_peer_list()
                print("Active peers:")
                for peer in peers:
                    print(f"{peer.get('address')}:{peer.get('port')}")
            elif cmd == "get":
                if len(parts) != 2:
                    print("Usage: get <filename>")
                    continue
                download_file(parts[1])
            elif cmd == "status":
                print_status()
            elif cmd == "exit":
                print("Exiting.")
                os._exit(0)
            else:
                print("Unknown command.")
        except KeyboardInterrupt:
            print("Exiting.")
            os._exit(0)

def main():
    ensure_files_dir()
    # Determine the local IP (for simplicity, using localhost) and port
    my_address = "127.0.0.1"
    my_port = 10000  # Default port; you can pass a different port as a command-line argument
    if len(sys.argv) > 1:
        my_port = int(sys.argv[1])
    # Register with the bootstrap server
    register_with_bootstrap(my_address, my_port)
    # Start the server listener in a separate thread
    server_thread = threading.Thread(target=server_listener, args=(my_port,), daemon=True)
    server_thread.start()
    # Start the CLI loop in the main thread
    cli_loop(my_address, my_port)

if __name__ == '__main__':
    main()
