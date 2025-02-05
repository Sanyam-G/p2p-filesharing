#!/usr/bin/env python3
import os
import socket
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import shutil

# Import the P2P core functions.
# (Make sure these functions exist in your peer.py module.)
from peer import (
    register_with_bootstrap,
    server_listener,
    share_file,
    download_file,
    get_peer_list
)
import bootstrap_server  # so we can optionally start it from the GUI

# Ensure the "files" folder exists.
FILES_DIR = "files"
if not os.path.exists(FILES_DIR):
    os.makedirs(FILES_DIR)

# ------------------------------
# The Main GUI Class
# ------------------------------

class P2PGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("P2P File Sharing - Friendly Frontend")
        self.geometry("800x600")

        # Define the settings variables BEFORE creating any tabs
        self.bootstrap_ip_var = tk.StringVar(value="127.0.0.1")
        self.bootstrap_port_var = tk.StringVar(value="8000")
        self.local_ip_var = tk.StringVar(value=self.get_local_ip())
        self.local_port_var = tk.StringVar(value="10000")

        # Notebook (tabbed interface)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill='both')

        # Create tabs (frames)
        self.settings_tab = ttk.Frame(self.notebook)
        self.files_tab = ttk.Frame(self.notebook)
        self.peers_tab = ttk.Frame(self.notebook)
        self.log_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.settings_tab, text="Settings")
        self.notebook.add(self.files_tab, text="Files")
        self.notebook.add(self.peers_tab, text="Peers")
        self.notebook.add(self.log_tab, text="Log")

        # Setup each tab
        self.create_settings_tab()
        self.create_files_tab()
        self.create_peers_tab()
        self.create_log_tab()

    def create_settings_tab(self):
        frame = self.settings_tab

        # Bootstrap Server Settings
        ttk.Label(frame, text="Bootstrap Server IP:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.bs_ip_entry = ttk.Entry(frame, textvariable=self.bootstrap_ip_var, width=20)
        self.bs_ip_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Bootstrap Server Port:").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        self.bs_port_entry = ttk.Entry(frame, textvariable=self.bootstrap_port_var, width=10)
        self.bs_port_entry.grid(row=0, column=3, padx=5, pady=5)

        # Local Peer Settings
        ttk.Label(frame, text="Local IP:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.local_ip_entry = ttk.Entry(frame, textvariable=self.local_ip_var, width=20)
        self.local_ip_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Local Port:").grid(row=1, column=2, sticky="w", padx=5, pady=5)
        self.local_port_entry = ttk.Entry(frame, textvariable=self.local_port_var, width=10)
        self.local_port_entry.grid(row=1, column=3, padx=5, pady=5)

        # Buttons to start the peer node and/or the bootstrap server.
        self.start_peer_btn = ttk.Button(frame, text="Start Peer Node", command=self.start_peer_node)
        self.start_peer_btn.grid(row=2, column=0, columnspan=2, padx=5, pady=10)

        self.start_bs_btn = ttk.Button(frame, text="Start Bootstrap Server", command=self.start_bootstrap_server)
        self.start_bs_btn.grid(row=2, column=2, columnspan=2, padx=5, pady=10)

    def create_files_tab(self):
        frame = self.files_tab
        # Share File Section
        share_frame = ttk.LabelFrame(frame, text="Share File")
        share_frame.pack(fill="x", padx=10, pady=10)

        self.share_btn = ttk.Button(share_frame, text="Select & Share File", command=self.share_file_action)
        self.share_btn.pack(padx=5, pady=5)

        # Download File Section
        download_frame = ttk.LabelFrame(frame, text="Download File")
        download_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(download_frame, text="Filename:").pack(side="left", padx=5, pady=5)
        self.download_entry = ttk.Entry(download_frame, width=40)
        self.download_entry.pack(side="left", padx=5, pady=5)
        self.download_btn = ttk.Button(download_frame, text="Download", command=self.download_file_action)
        self.download_btn.pack(side="left", padx=5, pady=5)

    def create_peers_tab(self):
        frame = self.peers_tab

        # Listbox to display active peers
        self.peers_listbox = tk.Listbox(frame, height=15)
        self.peers_listbox.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        # Scrollbar for the listbox
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.peers_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.peers_listbox.config(yscrollcommand=scrollbar.set)

        # Button to refresh the list of peers.
        self.refresh_peers_btn = ttk.Button(frame, text="Refresh Peers", command=self.refresh_peers)
        self.refresh_peers_btn.pack(pady=5)

    def create_log_tab(self):
        frame = self.log_tab
        self.log_text = scrolledtext.ScrolledText(frame, state='disabled', wrap='word')
        self.log_text.pack(expand=True, fill="both", padx=10, pady=10)

    def log(self, message):
        """Append a message to the log text area."""
        self.log_text.configure(state='normal')
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.configure(state='disabled')
        self.log_text.see(tk.END)

    def get_local_ip(self):
        """Try to determine the local IP address."""
        try:
            # Connect to a public host (Google DNS) to determine our IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def start_peer_node(self):
        """Register with the bootstrap server and start the server listener."""
        bs_ip = self.bootstrap_ip_var.get()
        bs_port = int(self.bootstrap_port_var.get())
        local_ip = self.local_ip_var.get()
        local_port = int(self.local_port_var.get())

        # Update the bootstrap server settings in the peer module.
        # (Assuming that in peer.py, there is a global variable BOOTSTRAP_SERVER.)
        try:
            import peer
            peer.BOOTSTRAP_SERVER = (bs_ip, bs_port)
        except Exception as e:
            self.log(f"Error updating bootstrap settings in peer module: {e}")

        # Start registration and the listener in separate threads.
        def start_node():
            try:
                self.log(f"Registering peer with {bs_ip}:{bs_port} from {local_ip}:{local_port}...")
                register_with_bootstrap(local_ip, local_port)
                self.log("Registration complete.")
            except Exception as e:
                self.log(f"Error during registration: {e}")
            try:
                self.log(f"Starting server listener on port {local_port}...")
                server_listener(local_port)
            except Exception as e:
                self.log(f"Error starting listener: {e}")

        threading.Thread(target=start_node, daemon=True).start()
        self.log("Peer node startup initiated.")

    def start_bootstrap_server(self):
        """Start the bootstrap server in a background thread."""
        def start_bs():
            try:
                self.log("Starting bootstrap server...")
                bootstrap_server.main()
            except Exception as e:
                self.log(f"Bootstrap server error: {e}")

        threading.Thread(target=start_bs, daemon=True).start()
        self.log("Bootstrap server startup initiated.")

    def share_file_action(self):
        """Open a file dialog, copy the file to 'files', and share it."""
        filepath = filedialog.askopenfilename(title="Select file to share")
        if not filepath:
            return  # User canceled.
        filename = os.path.basename(filepath)
        target_path = os.path.join(FILES_DIR, filename)
        # Copy the file into our 'files' folder if not already there.
        if not os.path.exists(target_path):
            try:
                shutil.copy(filepath, target_path)
                self.log(f"Copied file to {target_path}")
            except Exception as e:
                self.log(f"Error copying file: {e}")
                return
        try:
            share_file(filename)
            self.log(f"Shared file: {filename}")
        except Exception as e:
            self.log(f"Error sharing file: {e}")

    def download_file_action(self):
        """Get the filename from the entry and download it in a background thread."""
        filename = self.download_entry.get().strip()
        if not filename:
            messagebox.showerror("Error", "Please enter a filename to download.")
            return

        def download_thread():
            try:
                self.log(f"Attempting to download file: {filename}")
                download_file(filename)
                self.log(f"Download complete for: {filename}")
            except Exception as e:
                self.log(f"Error downloading file: {e}")

        threading.Thread(target=download_thread, daemon=True).start()

    def refresh_peers(self):
        """Refresh the peer list by querying the bootstrap server."""
        try:
            peers = get_peer_list()
            self.peers_listbox.delete(0, tk.END)
            if not peers:
                self.peers_listbox.insert(tk.END, "No peers found.")
                self.log("No peers available.")
            else:
                for peer_info in peers:
                    peer_str = f"{peer_info.get('address')}:{peer_info.get('port')}"
                    self.peers_listbox.insert(tk.END, peer_str)
                self.log("Peer list refreshed.")
        except Exception as e:
            self.log(f"Error retrieving peer list: {e}")


# ------------------------------
# Main Program Entry
# ------------------------------

if __name__ == '__main__':
    app = P2PGUI()
    app.mainloop()
