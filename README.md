# Distributed Peer-to-Peer File Sharing System

## Overview
This project is a robust, distributed peer-to-peer (P2P) file sharing system implemented in Python. It enables multiple peers to securely share and download files through a combination of socket programming, multithreading, and a centralized bootstrap server for peer discovery.

## Features
- **Peer Discovery:**  
  A central bootstrap server allows peers to register and discover one another, enabling seamless file-sharing across the network.
- **Chunk-Based File Sharing:**  
  Files are split into 64KB chunks, with each chunk's integrity verified via SHA-256 to ensure 100% accuracy upon reassembly.
- **Multithreading:**  
  Utilizes Python's threading module to manage simultaneous file transfers and peer communications.
- **User-Friendly Interfaces:**  
  Offers both a command-line interface (CLI) and a Tkinter-based GUI to simplify configuration, file sharing, and downloads.
- **Automatic Retry Logic:**  
  Incorporates retry mechanisms for failed chunk transfers, ensuring robust and reliable file downloads.

## Prerequisites
- **Python 3.12+**
- Required libraries (included in the standard library):
  - `socket`
  - `threading`
  - `tkinter`
  - `json`
  - `hashlib`
  - `os`

