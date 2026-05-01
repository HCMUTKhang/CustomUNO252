"""
Network client for communicating with the game server.
Handles TCP connection, message sending/receiving, and serialization.
"""

import socket
import threading
from typing import Callable, Optional
from shared.message_protocol import NetworkMessage
from shared.constants import MAX_MESSAGE_SIZE


class NetworkClient:
    """
    TCP client for connecting to the game server.
    Runs receive loop on separate thread.
    """
    
    def __init__(self, host: str, port: int, message_callback: Callable):
        """
        Initialize the network client.
        
        Args:
            host: Server host address
            port: Server port
            message_callback: Callback function for received messages
        """
        pass
    
    def connect(self) -> bool:
        """
        Connect to the server.
        
        Returns:
            True if connection successful
        """
        pass
    
    def disconnect(self):
        """Disconnect from the server."""
        pass
    
    def is_connected(self) -> bool:
        """Check if currently connected to server."""
        pass
    
    def send_message(self, message: NetworkMessage) -> bool:
        """
        Send a message to the server.
        
        Args:
            message: NetworkMessage to send
            
        Returns:
            True if message sent successfully
        """
        pass
    
    def receive_messages(self):
        """
        Receive and process messages from server (runs on thread).
        Calls message_callback for each received message.
        """
        pass
    
    def handle_disconnection(self):
        """Handle server disconnection."""
        pass
