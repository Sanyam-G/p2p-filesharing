#!/usr/bin/env python3
import json
import socket
import base64
import hashlib
import os

CHUNK_SIZE = 64 * 1024  # 64KB per chunk

def send_json(sock, message):
    """
    Send a JSON message over a socket, terminated by a newline.
    """
    data = json.dumps(message) + "\n"
    sock.sendall(data.encode())

def recv_json(sock):
    """
    Receive a JSON message from a socket. Assumes messages are newline-delimited.
    """
    buffer = ""
    while True:
        data = sock.recv(1024).decode()
        if not data:
            break
        buffer += data
        if "\n" in buffer:
            line, buffer = buffer.split("\n", 1)
            return json.loads(line)
    return None

def chunk_file(filepath, chunk_size=CHUNK_SIZE):
    """
    Generator that yields (chunk_index, chunk_data, chunk_hash) for each chunk.
    """
    with open(filepath, "rb") as f:
        index = 0
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            chunk_hash = hashlib.sha256(chunk).hexdigest()
            yield index, chunk, chunk_hash
            index += 1

def split_file(filepath, chunk_size=CHUNK_SIZE):
    """
    Splits a file into chunks and returns a tuple: (list_of_chunks, list_of_chunk_hashes).
    """
    chunks = []
    chunk_hashes = []
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            chunks.append(chunk)
            chunk_hashes.append(hashlib.sha256(chunk).hexdigest())
    return chunks, chunk_hashes

def verify_chunk(chunk_data, expected_hash):
    """
    Verifies that the SHA-256 hash of chunk_data matches expected_hash.
    """
    computed_hash = hashlib.sha256(chunk_data).hexdigest()
    return computed_hash == expected_hash

def encode_chunk(chunk_data):
    """
    Encode binary chunk data to a Base64 string (for JSON serialization).
    """
    return base64.b64encode(chunk_data).decode()

def decode_chunk(encoded_data):
    """
    Decode a Base64 string back to binary chunk data.
    """
    return base64.b64decode(encoded_data.encode())

def ensure_files_dir():
    """
    Ensure that the 'files' directory exists.
    """
    if not os.path.exists("files"):
        os.makedirs("files")
