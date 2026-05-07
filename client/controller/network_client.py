"""
Non-blocking TCP Network Client for Pygame integration.
Uses queue.Queue to handle network I/O without blocking the Pygame render loop.
Background thread receives messages and queues them for the main game thread.
"""

import socket
import threading
import queue
from typing import List, Optional

from shared.message_protocol import NetworkMessage, parse_incoming_message


class NetworkClient:
    """
    TCP Network Client for Custom UNO Online.
    Thread-safe message queue for Pygame integration.
    """

    def __init__(self, host: str = 'localhost', port: int = 5000):
        """
        Initialize the network client.
        
        Args:
            host: Server host address
            port: Server port
        """
        self.host = host
        self.port = port
        
        self.socket: Optional[socket.socket] = None
        self.connected = False
        self.running = False
        
        # Thread-safe message queue for Pygame main loop
        self.message_queue: queue.Queue = queue.Queue()
        
        # Thread synchronization
        self.lock = threading.Lock()

    def connect(self) -> bool:
        """
        Connect to the server and start the receive thread.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            
            self.connected = True
            self.running = True
            
            print(f"[CLIENT] Connected to {self.host}:{self.port}")
            
            # Start receiving messages in a background thread
            receive_thread = threading.Thread(
                target=self._receive_loop,
                daemon=True
            )
            receive_thread.start()
            
            return True
            
        except Exception as e:
            print(f"[CLIENT] Connection failed: {e}")
            self.connected = False
            return False

    def _receive_loop(self):
        """
        Receive messages from server in a background thread.
        Parses JSON and queues messages for the Pygame main loop.
        """
        try:
            # Set socket timeout to allow periodic checks
            self.socket.settimeout(5.0)
            
            while self.running and self.connected:
                try:
                    # Receive data from server
                    data = self.socket.recv(4096)
                    
                    if not data:
                        # Server closed connection
                        print("[CLIENT] Server closed connection")
                        self.connected = False
                        break
                    
                    # Decode JSON string
                    json_str = data.decode('utf-8')
                    
                    # Parse message
                    try:
                        message = parse_incoming_message(json_str)
                        
                        # Queue the message for the main loop
                        self.message_queue.put(message)
                        
                    except ValueError as e:
                        print(f"[CLIENT] Invalid message from server: {e}")
                        
                except socket.timeout:
                    # Timeout is normal, just continue
                    continue
                    
        except ConnectionResetError:
            print("[CLIENT] Server forcefully disconnected")
            self.connected = False
        except OSError:
            # Socket closed during shutdown — expected
            pass
        except Exception as e:
            print(f"[CLIENT] Error in receive loop: {e}")
            self.connected = False
        finally:
            self._cleanup()

    def get_messages(self) -> List[NetworkMessage]:
        """
        Get all pending messages from the queue.
        SAFE TO CALL FROM PYGAME MAIN LOOP - does not block.
        
        Returns:
            List of NetworkMessage objects received since last call
        """
        messages = []
        try:
            # Get all messages currently in queue without blocking
            while True:
                message = self.message_queue.get_nowait()
                messages.append(message)
        except queue.Empty:
            # Queue is empty, this is expected
            pass
        
        return messages

    def send_message(self, message: NetworkMessage) -> bool:
        """
        Send a message to the server.
        
        Args:
            message: NetworkMessage to send
            
        Returns:
            True if message sent successfully
        """
        if not self.connected or self.socket is None:
            print("[CLIENT] Not connected to server")
            return False
        
        try:
            json_data = message.to_json()
            self.socket.send(json_data.encode('utf-8'))
            return True
            
        except Exception as e:
            print(f"[CLIENT] Error sending message: {e}")
            self.connected = False
            return False

    def is_connected(self) -> bool:
        """
        Check if currently connected to server.
        
        Returns:
            True if connected, False otherwise
        """
        return self.connected

    def disconnect(self):
        """Disconnect from the server."""
        print("[CLIENT] Disconnecting from server...")
        self.running = False
        self.connected = False
        if self.socket:
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
        self._cleanup()

    def _cleanup(self):
        """Clean up socket resources."""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        
        print("[CLIENT] Disconnected")

    def get_message_queue_size(self) -> int:
        """
        Get the number of pending messages in the queue.
        Useful for debugging.
        
        Returns:
            Number of messages queued
        """
        return self.message_queue.qsize()

