"""
Server main entry point.
Initializes the server, manages game sessions, and routes client messages.
Host-Authoritative: All game decisions made here, clients are dumb terminals.
"""

import threading
import time
from typing import Dict, Optional
from server.network_server import NetworkServer
from server.game_engine import GameEngine
from shared.message_protocol import (
    NetworkMessage, parse_incoming_message, JoinRoom, EventBroadcast, ErrorMessage
)
from shared.enums import MessageType, GameState
from shared.data_structures import Player
from shared.constants import DEFAULT_HOST, DEFAULT_PORT

class GameServer:
    """
    Main server orchestrator.
    Manages network connections, game engine, and message routing.
    Host-Authoritative: All game decisions made here.
    """
    
    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
        """
        Initialize the game server.
        
        Args:
            host: Server host address
            port: Server port
        """
        self.host = host
        self.port = port
        
        # Network layer
        self.network = NetworkServer(host=host, port=port)
        
        # Game state
        self.game_state = GameState.LOBBY
        self.players: Dict[int, Player] = {}  # client_id -> Player
        self.host_client_id: Optional[int] = None
        self.game_engine: Optional[GameEngine] = None
        
        # Thread safety
        self.lock = threading.Lock()
        
        print(f"[GAMESERVER] Initialized at {host}:{port}")
    
    def start(self):
        """Start the server and listen for connections."""
        print("[GAMESERVER] Starting server...")
        self.network.start(
            message_callback=self.on_client_message,
            disconnect_callback=self.on_client_disconnect,
        )
        print("[GAMESERVER] Server started successfully")
    
    def stop(self):
        """Stop the server and close all connections."""
        print("[GAMESERVER] Stopping server...")
        self.network.stop()
        print("[GAMESERVER] Server stopped")
    
    def on_client_message(self, client_id: int, message: NetworkMessage):
        """
        Handle incoming message from a client.
        Routes message to appropriate handler based on message type.
        
        Args:
            client_id: ID of sending client
            message: Parsed NetworkMessage
        """
        try:
            msg_type = message.message_type
            
            print(f"[GAMESERVER] Received {msg_type.value} from client {client_id}")
            
            # Route to appropriate handler
            if msg_type == MessageType.JOIN_ROOM:
                self.handle_handshake(client_id, message)
            elif msg_type == MessageType.START_GAME:
                self.handle_start_game(client_id)
            elif msg_type == MessageType.PLAY_CARD:
                self.handle_play_card(client_id, message)
            elif msg_type == MessageType.DRAW_CARD:
                self.handle_draw_card(client_id)
            elif msg_type == MessageType.RULE_8_REACTION:
                self.handle_rule_8_reaction(client_id)
            else:
                print(f"[GAMESERVER] Unknown message type: {msg_type.value}")
                
        except Exception as e:
            print(f"[GAMESERVER] Error processing message from client {client_id}: {e}")
            # Send error to client
            error_msg = ErrorMessage(
                error_type="SERVER_ERROR",
                message=str(e)
            )
            self.network.send_to_client(client_id, error_msg)
    
    def on_client_connect(self, client_id: int, client_address: tuple):
        """
        Handle new client connection.
        
        Args:
            client_id: ID assigned to new client
            client_address: Client's address tuple (host, port)
        """
        print(f"[GAMESERVER] Client {client_id} connected from {client_address}")
    
    def on_client_disconnect(self, client_id: int):
        """
        Handle client disconnection.
        Removes player from game, reassigns host if necessary, broadcasts lobby update.
        """
        with self.lock:
            if client_id not in self.players:
                return

            player_name = self.players[client_id].name
            is_host = self.players[client_id].is_host

            del self.players[client_id]
            print(f"[GAMESERVER] Player {player_name} (client {client_id}) disconnected")

            # Reassign host if needed
            if is_host and self.players and self.game_state == GameState.LOBBY:
                new_host_id, new_host = next(iter(self.players.items()))
                new_host.is_host = True
                self.host_client_id = new_host_id
                print(f"[GAMESERVER] Host reassigned to client {new_host_id}")

        # Broadcast updated lobby to remaining players (outside lock to avoid deadlock)
        if self.players:
            self._broadcast_lobby_update()
    
    def handle_handshake(self, client_id: int, message: NetworkMessage):
        """
        Handle client handshake (player join).
        Assigns first player as host. Broadcasts lobby update.
        
        Args:
            client_id: ID of joining client
            message: JoinRoom message
        """
        if not isinstance(message, JoinRoom):
            print(f"[GAMESERVER] Invalid handshake message type")
            return
        
        username = message.username or f"Player{client_id}"
        
        with self.lock:
            # Check if player already exists
            if client_id in self.players:
                print(f"[GAMESERVER] Client {client_id} already in players list")
                return
            
            # First player becomes host
            is_host = len(self.players) == 0
            
            # Create player
            player = Player(
                player_id=client_id,
                name=username,
                is_host=is_host,
                is_connected=True
            )
            
            self.players[client_id] = player
            
            if is_host:
                self.host_client_id = client_id
                print(f"[GAMESERVER] Client {client_id} ({username}) joined as HOST")
            else:
                print(f"[GAMESERVER] Client {client_id} ({username}) joined as PLAYER")
        
        # Broadcast lobby update
        self._broadcast_lobby_update()
    
    def handle_start_game(self, client_id: int):
        """
        Handle START_GAME message from host.
        
        Args:
            client_id: ID of requesting client (should be host)
        """
        with self.lock:
            # Verify requester is host
            if client_id != self.host_client_id:
                error_msg = ErrorMessage(
                    error_type="NOT_HOST",
                    message="Only the host can start the game"
                )
                self.network.send_to_client(client_id, error_msg)
                return
            
            # Verify minimum players
            if len(self.players) < 2:
                error_msg = ErrorMessage(
                    error_type="NOT_ENOUGH_PLAYERS",
                    message="Need at least 2 players to start"
                )
                self.network.send_to_client(client_id, error_msg)
                return
            
            print(f"[GAMESERVER] Host initiated game start")
            # TODO: Initialize game engine and transition to PLAYING state
            # For now, just broadcast that game is starting
            event = EventBroadcast(
                event_name="GAME_STARTING",
                event_data={"message": "Game is starting..."}
            )
            self.broadcast_message(event)
    
    def handle_play_card(self, client_id: int, message: NetworkMessage):
        """
        Handle PLAY_CARD action from player.
        
        Args:
            client_id: ID of acting player
            message: PlayCard message
        """
        # Route to game engine for validation
        if self.game_engine:
            # TODO: Implement game engine logic
            print(f"[GAMESERVER] PlayCard from client {client_id}")
        else:
            error_msg = ErrorMessage(
                error_type="GAME_NOT_STARTED",
                message="Game has not started yet"
            )
            self.network.send_to_client(client_id, error_msg)
    
    def handle_draw_card(self, client_id: int):
        """
        Handle DRAW_CARD action from player.
        
        Args:
            client_id: ID of acting player
        """
        # Route to game engine for validation
        if self.game_engine:
            # TODO: Implement game engine logic
            print(f"[GAMESERVER] DrawCard from client {client_id}")
        else:
            error_msg = ErrorMessage(
                error_type="GAME_NOT_STARTED",
                message="Game has not started yet"
            )
            self.network.send_to_client(client_id, error_msg)
    
    def handle_rule_8_reaction(self, client_id: int):
        """
        Handle RULE_8_REACTION action from player.
        
        Args:
            client_id: ID of reacting player
        """
        # Route to game engine for validation
        if self.game_engine:
            # TODO: Implement game engine logic
            print(f"[GAMESERVER] Rule8Reaction from client {client_id}")
        else:
            error_msg = ErrorMessage(
                error_type="GAME_NOT_STARTED",
                message="Game has not started yet"
            )
            self.network.send_to_client(client_id, error_msg)
    
    def broadcast_game_state(self):
        """Broadcast current game state to all connected clients."""
        # TODO: Implement full game state broadcast using GameStateUpdate
        # This requires game engine implementation
        pass
    
    def broadcast_message(self, message: NetworkMessage, exclude_client_id: Optional[int] = None):
        """
        Broadcast a message to all clients.
        
        Args:
            message: Message to broadcast
            exclude_client_id: Optional client ID to exclude
        """
        self.network.broadcast(message, exclude_id=exclude_client_id)
    
    def _broadcast_lobby_update(self):
        """
        Broadcast a lobby update event to all connected players.
        Includes current player list and host information.
        """
        with self.lock:
            players_info = []
            for client_id, player in self.players.items():
                players_info.append({
                    "client_id": client_id,
                    "name": player.name,
                    "is_host": player.is_host,
                    "is_connected": player.is_connected
                })
            
            event = EventBroadcast(
                event_name="LOBBY_UPDATE",
                event_data={
                    "players": players_info,
                    "host_client_id": self.host_client_id,
                    "game_state": self.game_state.value,
                    "player_count": len(self.players)
                }
            )
        
        self.broadcast_message(event)


def main():
    """Entry point for the server application."""
    try:
        # Create and start server
        server = GameServer(host=DEFAULT_HOST, port=DEFAULT_PORT)
        server.start()
        
        print("\n" + "="*60)
        print("  Custom UNO Online - Server Running")
        print("="*60)
        print(f"  Host: {DEFAULT_HOST}")
        print(f"  Port: {DEFAULT_PORT}")
        print(f"  Waiting for player connections...")
        print("  Press Ctrl+C to stop")
        print("="*60 + "\n")
        
        # Keep server running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[MAIN] Shutdown signal received")
            server.stop()
            print("[MAIN] Server stopped")
            
    except Exception as e:
        print(f"[MAIN] Fatal error: {e}")
        raise


if __name__ == "__main__":
    main()
