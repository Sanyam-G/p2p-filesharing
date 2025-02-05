#!/usr/bin/env python3
import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import shutil

# Import functions from your peer module.
# If necessary, you may need to adjust the import paths.
from peer import share_file, download_file, get_peer_list, register_with_bootstrap, server_listener

# Global settings for this peer node.
MY_ADDRESS = "127.0.0.1"
MY_PORT = 10000  # Change if needed

# Create the main application window.
root = tk.Tk()
root.title("P2P File Sharing - GUI")

# A scrolled text area to display log messages.
log_text = scrolledtext.ScrolledText(root, state='disabled', width=80, height=20)
log_text.pack(padx=10, pady=10)

def log(message):
    """Append a message to the log text area."""
    log_text.config(state='normal')
    log_text.insert(tk.END, message + "\n")
    log_text.config(state='disabled')
    log_text.see(tk.END)

# Function to share a file.
def on_share_file():
    # Let the user choose a file from anywhere.
    filepath = filedialog.askopenfilename(title="Select file to share")
    if filepath:
        filename = os.path.basename(filepath)
        target_path = os.path.join("files", filename)
        # Ensure the 'files' directory exists.
        if not os.path.exists("files"):
            os.makedirs("files")
        # If the file is not already in the 'files' folder, copy it there.
        if not os.path.exists(target_path):
            shutil.copy(filepath, target_path)
        share_file(filename)
        log(f"Shared file: {filename}")

# Function to list active peers.
def on_list_peers():
    peers = get_peer_list()
    if not peers:
        log("No active peers found.")
    else:
        log("Active peers:")
        for peer in peers:
            log(f"{peer.get('address')}:{peer.get('port')}")

# Function to download a file.
def on_download_file():
    filename = file_entry.get().strip()
    if not filename:
        messagebox.showerror("Error", "Please enter a file name to download.")
        return

    def download_thread():
        download_file(filename)
        log(f"Download attempted for: {filename}")
    threading.Thread(target=download_thread, daemon=True).start()

# UI elements for downloading files.
file_label = tk.Label(root, text="File to download:")
file_label.pack(pady=(10, 0))
file_entry = tk.Entry(root, width=50)
file_entry.pack(pady=(0, 10))

download_button = tk.Button(root, text="Download File", command=on_download_file)
download_button.pack(pady=5)

share_button = tk.Button(root, text="Share File", command=on_share_file)
share_button.pack(pady=5)

list_button = tk.Button(root, text="List Peers", command=on_list_peers)
list_button.pack(pady=5)

# Function to start the peer node (register and run the server listener)
def start_peer_node():
    try:
        register_with_bootstrap(MY_ADDRESS, MY_PORT)
        threading.Thread(target=server_listener, args=(MY_PORT,), daemon=True).start()
        log(f"Peer node started on {MY_ADDRESS}:{MY_PORT}")
    except Exception as e:
        log(f"Error starting peer node: {e}")

# Start the peer node in a separate thread.
threading.Thread(target=start_peer_node, daemon=True).start()

# Start the Tkinter main loop.
root.mainloop()
