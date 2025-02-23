# Distributed Peer-to-Peer File Sharing System

## Overview
This project is a robust, distributed peer-to-peer (P2P) file sharing system implemented in Python. It enables multiple peers to securely share and download files through a combination of socket programming, multithreading, and a centralized bootstrap server for peer discovery.

## Features
- **Peer Discovery:** A central bootstrap server allows peers to register and discover one another, enabling seamless file sharing across the network.
- **Chunk-Based File Sharing:** Files are split into 64KB chunks, with each chunk's integrity verified via SHA-256 to ensure 100% accuracy upon reassembly.
- **Multithreading:** Utilizes Python's threading module to manage simultaneous file transfers and peer communications.
- **User-Friendly Interfaces:** Offers both a command-line interface (CLI) and a Tkinter-based GUI to simplify configuration, file sharing, and downloads.
- **Automatic Retry Logic:** Incorporates retry mechanisms for failed chunk transfers, ensuring robust and reliable file downloads.

## Prerequisites
- **Python 3.12+**
- Required libraries (all standard):
  - `socket`, `threading`, `tkinter`, `json`, `hashlib`, `os`
- *Optional:* For encryption features, install:
```
pip install cryptography
```
## Project Structure
p2p_file_sharing/ 
├── bootstrap_server.py # Central server for peer registration and discovery 
├── peer.py # Peer node implementation (CLI interface) 
├── utils.py # Helper functions for file I/O, hashing, and networking 
├── good_frontend.py # Tkinter-based GUI frontend for the peer node 
├── README.md # This file 
└── files/ # Directory for shared/downloaded files

## Setup and Usage

### Starting the Bootstrap Server
1. Open a terminal and navigate to the project directory.
2. Run the bootstrap server:
'''
python3 bootstrap_server.py
'''
The server listens on port **8000** by default.

### Running a Peer Node (CLI)
1. Open a new terminal and navigate to the project directory.
2. Start a peer node on a unique port (e.g., **10000**):
'''
python3 peer.py 10000
'''
3. Use the following CLI commands:
- `share <filename>` – Share a file (ensure the file is in the `files/` directory).
- `list-peers` – Display a list of active peers.
- `get <filename>` – Download a file from a peer.
- `status` – View current transfer status.

### Running the GUI Frontend
1. Open a terminal and navigate to the project directory.
2. Run the GUI:
'''
python3 good_frontend.py
'''
3. In the **Settings** tab, configure the Bootstrap Server IP/Port and your local IP/Port.
4. Use the **Files** tab to share or download files and the **Peers** tab to view active peers.
