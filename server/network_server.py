"""
Network server for handling client connections via TCP.
Responsible for accepting connections, routing messages, and managing the game room.
"""

import socket
import threading
from typing import Dict, Optional, Callable


class NetworkServer:
    """
    TCP server for managing client connections.
    Runs on a separate thread.
    """
    
    def __init__(self, host: str, port: int, message_callback: Callable):
        """
        Initialize the network server.
        
        Args:
            host: Server host address
            port: Server port
            message_callback: Callback function to process incoming messages
        """
        pass
    
    def start(self):
        """Start the server and begin listening for connections."""
        pass
    
    def stop(self):
        """Stop the server and close all connections."""
        pass
    
    def accept_connections(self):
        """Accept incoming client connections (runs on server thread)."""
        pass
    
    def handle_client(self, client_socket: socket.socket, client_address: tuple):
        """
        Handle a single client connection.
        
        Args:
            client_socket: The client's socket
            client_address: Client's address tuple (host, port)
        """
        pass
    
    def broadcast_message(self, message: str, exclude_client_id: Optional[int] = None):
        """
        Broadcast a message to all connected clients.
        
        Args:
            message: JSON message string
            exclude_client_id: Optional client ID to exclude from broadcast
        """
        pass
    
    def send_to_client(self, client_id: int, message: str):
        """
        Send a message to a specific client.
        
        Args:
            client_id: ID of the recipient client
            message: JSON message string
        """
        pass
    
    def disconnect_client(self, client_id: int):
        """
        Disconnect a client.
        
        Args:
            client_id: ID of the client to disconnect
        """
        pass
    
    def get_connected_clients(self) -> Dict[int, tuple]:
        """
        Get dictionary of connected clients and their addresses.
        
        Returns:
            Dict mapping client_id to (socket, address)
        """
        pass
