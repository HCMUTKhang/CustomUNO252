"""
TCP Socket Server with threading for multiplayer game support.
Handles client connections, message routing, and broadcasting.
Host-Authoritative: All game logic decisions are made here.
"""

import socket
import threading
from typing import Callable, Dict, Optional

from shared.message_protocol import NetworkMessage, parse_incoming_message


class NetworkServer:
    """
    TCP Socket Server for Custom UNO Online.
    Manages client connections, receives messages, and broadcasts updates.
    """

    def __init__(self, host: str = 'localhost', port: int = 5000, max_clients: int = 10):
        self.host = host
        self.port = port
        self.max_clients = max_clients

        self.server_socket: Optional[socket.socket] = None
        self.clients: Dict[int, socket.socket] = {}  # client_id -> socket
        self.client_addresses: Dict[int, tuple] = {}  # client_id -> (host, port)
        self.client_counter = 0
        self.running = False
        self.message_callback: Optional[Callable] = None
        self.disconnect_callback: Optional[Callable] = None  # called with (client_id)

        # Thread synchronization
        self.lock = threading.Lock()

    def start(self, message_callback: Callable, disconnect_callback: Optional[Callable] = None):
        """
        Start the server and begin accepting connections.

        Args:
            message_callback: Called on every received message — (client_id, NetworkMessage)
            disconnect_callback: Called when a client disconnects — (client_id,)
        """
        self.message_callback = message_callback
        self.disconnect_callback = disconnect_callback
        self.running = True
        
        # Create and bind socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(self.max_clients)
        
        print(f"[SERVER] Started on {self.host}:{self.port}")
        
        # Start accepting connections in a background thread
        accept_thread = threading.Thread(target=self._accept_connections, daemon=True)
        accept_thread.start()

    def _accept_connections(self):
        """Accept incoming connections in a loop."""
        while self.running:
            try:
                client_socket, client_addr = self.server_socket.accept()
                
                with self.lock:
                    client_id = self.client_counter
                    self.client_counter += 1
                    self.clients[client_id] = client_socket
                    self.client_addresses[client_id] = client_addr
                
                print(f"[SERVER] Client {client_id} connected from {client_addr}")
                
                # Spawn a thread to handle this client
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_id, client_socket),
                    daemon=True
                )
                client_thread.start()
                
            except Exception as e:
                if self.running:
                    print(f"[SERVER] Error accepting connection: {e}")

    def _handle_client(self, client_id: int, client_socket: socket.socket):
        """
        Receive messages from a client in a dedicated thread.
        
        Args:
            client_id: Unique identifier for this client
            client_socket: Socket connection to the client
        """
        try:
            # Set socket timeout to allow periodic checks
            client_socket.settimeout(60.0)
            
            while self.running:
                try:
                    # Receive data from client
                    data = client_socket.recv(4096)
                    
                    if not data:
                        # Client closed connection gracefully
                        print(f"[SERVER] Client {client_id} closed connection")
                        break
                    
                    # Decode JSON string
                    json_str = data.decode('utf-8')
                    
                    # Parse message
                    try:
                        message = parse_incoming_message(json_str)
                        
                        # Call the message callback
                        if self.message_callback:
                            self.message_callback(client_id, message)
                            
                    except ValueError as e:
                        print(f"[SERVER] Invalid message from client {client_id}: {e}")
                        
                except socket.timeout:
                    # Timeout is normal, just continue
                    continue
                    
        except ConnectionResetError:
            print(f"[SERVER] Client {client_id} forcefully disconnected")
        except Exception as e:
            print(f"[SERVER] Error handling client {client_id}: {e}")
        finally:
            # Remove client from active list
            with self.lock:
                if client_id in self.clients:
                    del self.clients[client_id]
                if client_id in self.client_addresses:
                    del self.client_addresses[client_id]

            try:
                client_socket.close()
            except Exception:
                pass

            print(f"[SERVER] Client {client_id} removed from server")

            # Notify game layer so it can update lobby / game state
            if self.disconnect_callback:
                self.disconnect_callback(client_id)

    def send_to_client(self, client_id: int, message: NetworkMessage):
        """
        Send a message to a specific client.
        
        Args:
            client_id: Identifier of the target client
            message: NetworkMessage to send
        """
        with self.lock:
            if client_id not in self.clients:
                print(f"[SERVER] Client {client_id} not found")
                return
            
            try:
                json_data = message.to_json()
                self.clients[client_id].send(json_data.encode('utf-8'))
                
            except Exception as e:
                print(f"[SERVER] Error sending to client {client_id}: {e}")

    def broadcast(self, message: NetworkMessage, exclude_id: Optional[int] = None):
        """
        Broadcast a message to all connected clients.
        
        Args:
            message: NetworkMessage to broadcast
            exclude_id: Optional client ID to exclude from broadcast
        """
        json_data = message.to_json()
        
        with self.lock:
            for client_id, client_socket in list(self.clients.items()):
                if exclude_id is not None and client_id == exclude_id:
                    continue
                
                try:
                    client_socket.send(json_data.encode('utf-8'))
                except Exception as e:
                    print(f"[SERVER] Error broadcasting to client {client_id}: {e}")

    def get_connected_clients(self) -> list:
        """
        Get a list of currently connected client IDs.
        
        Returns:
            List of client IDs
        """
        with self.lock:
            return list(self.clients.keys())

    def stop(self):
        """Stop the server and close all connections."""
        print("[SERVER] Shutting down...")
        self.running = False
        
        with self.lock:
            for client_id, client_socket in list(self.clients.items()):
                try:
                    client_socket.close()
                except:
                    pass
            self.clients.clear()
        
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        print("[SERVER] Shutdown complete")
