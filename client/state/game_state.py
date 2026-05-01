"""
Client-side game state management.
Stores the local representation of game state received from the server.
"""

from typing import List, Optional, Dict
from shared.data_structures import Card, Player, GameStatus
from shared.enums import GameState, PlayerState


class GameStateManager:
    """
    Manages client-side game state.
    Receives updates from server and maintains local state for UI rendering.
    """
    
    def __init__(self):
        """Initialize the game state manager."""
        pass
    
    def update_game_state(self, state_data: dict):
        """
        Update game state from server broadcast.
        
        Args:
            state_data: Dictionary containing game state from server
        """
        pass
    
    def set_local_player_id(self, player_id: int):
        """
        Set the ID of the local player.
        
        Args:
            player_id: Local player's ID
        """
        pass
    
    def get_local_player_id(self) -> Optional[int]:
        """Get the local player's ID."""
        pass
    
    def get_local_player(self) -> Optional[Player]:
        """Get the local player object."""
        pass
    
    def get_all_players(self) -> List[Player]:
        """Get all players in the game."""
        pass
    
    def get_player(self, player_id: int) -> Optional[Player]:
        """Get a specific player by ID."""
        pass
    
    def get_game_status(self) -> GameStatus:
        """Get current game status."""
        pass
    
    def get_current_player_id(self) -> Optional[int]:
        """Get the ID of the player whose turn it is."""
        pass
    
    def get_last_card_played(self) -> Optional[Card]:
        """Get the last card played (top of discard pile)."""
        pass
    
    def get_local_hand(self) -> List[Card]:
        """Get the local player's hand."""
        pass
    
    def is_local_player_turn(self) -> bool:
        """Check if it's the local player's turn."""
        pass
    
    def reset_state(self):
        """Reset state (used when starting new game or disconnecting)."""
        pass
    
    def serialize_state(self) -> dict:
        """Get state as a dictionary for debugging/logging."""
        pass
